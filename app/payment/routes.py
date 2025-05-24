import re
import binascii
import os
import logging
import time
from datetime import datetime
from flask import (Blueprint, render_template, request,session, redirect, url_for,current_app,
                   flash, jsonify, abort)
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import generate_csrf, validate_csrf
from wtforms import ValidationError
limiter = Limiter(get_remote_address)

from app.admin.models import PaymentMethod
from app.admin.models import Order         
from .crypto import encrypt_pan, luhn_checksum
from app import db
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import exc

security_logger = logging.getLogger('security')
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)
    security_logger.setLevel(logging.INFO)

payments_bp = Blueprint(
    'payments',
    __name__,
    subdomain='secure',
    url_prefix='/checkout',
    template_folder='templates/payments'
)

def json_response(success=True, message='', **kwargs):
    return jsonify({
        'success': success,
        'message': message,
        **kwargs
    })

def error_response(message, token=None, order=None):
    """Handles both JSON and HTML error responses with optional context."""
    if request.is_json:
        return jsonify({'error': message}), 400

    return render_template(
        'payments/checkout.html',
        error=message,
        payment_token=token,
        order=order,  
       
    ), 400



# Enhanced card brand detection with more accurate patterns
def detect_card_brand(pan: str) -> str:
    """Improved card brand detection with comprehensive pattern matching"""
    pan = sanitize_pan(pan)
    
    # Visa: starts with 4, length 13,16,19
    if re.match(r'^4[0-9]{12}(?:[0-9]{3})?$', pan):
        return 'VISA'
    
    # Mastercard: starts with 51-55 or 2221-2720
    if re.match(r'^(5[1-5][0-9]{14}|222[1-9][0-9]{12}|22[3-9][0-9]{13}|2[3-6][0-9]{14}|27[01][0-9]{13}|2720[0-9]{12})$', pan):
        return 'MASTERCARD'
    
    # American Express: starts with 34/37, length 15
    if re.match(r'^3[47][0-9]{13}$', pan):
        return 'AMEX'
    
    # Discover: starts with 6011, 644-649, 65
    if re.match(r'^(6011|65[0-9]{2}|64[4-9][0-9]|622[1-9][0-9][0-6])[0-9]*$', pan):
        return 'DISCOVER'
    
    return 'UNKNOWN'

def generate_secure_token() -> str:
    """Generate cryptographically secure token"""
    return binascii.hexlify(os.urandom(32)).decode()  # Increased to 32 bytes

def sanitize_pan(raw_pan: str) -> str:
    """PCI-compliant PAN sanitization"""
    return re.sub(r'\D+', '', raw_pan)[:19]  # Limit to max PAN length

def validate_payment_token(token: str) -> Order:
    """Validate payment token without checking user identity."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(
            token,
            salt='payment-token',
            max_age=3600  # 1 hour expiration
        )
        return Order.query.filter_by(
            id=data['order_id'],
            payment_status='Pending'
        ).first()
    except (BadSignature, SignatureExpired, KeyError):
        security_logger.warning(f"Invalid or expired payment token: {token}")
        return None
def clear_payment_session_data():
    session.pop('cart', None)
    session.pop('payment_data', None)
    session.pop('selected_method', None)



def validate_expiry(expiry_str: str) -> tuple:
    """Robust expiry date validation"""
    try:
        month, year = map(int, re.split(r'[/-]', expiry_str))
        year = year if year > 2000 else year + 2000
        return (month, year) if datetime(year, month, 1) > datetime.utcnow() else None
    except (ValueError, IndexError):
        return None

@payments_bp.route('/detect-brand', methods=['POST'])
@limiter.limit("30/minute")
def detect_brand_api():
    """Secure card brand detection endpoint"""
    try:
        if not request.is_json:
            return jsonify({'error': 'JSON content required'}), 400
            
        data = request.get_json()
        pan = sanitize_pan(data.get('pan', ''))
        
        if not pan or len(pan) < 2:
            return jsonify({'brand': ''}), 200
            
        brand = detect_card_brand(pan)
        return jsonify({
            'brand': brand,
            'valid_length': 15 if brand == 'AMEX' else 16
        }), 200
        
    except Exception as e:
        security_logger.error(f"Brand detection error: {str(e)}")
        return jsonify({'error': 'Processing error'}), 500

@payments_bp.route('/<string:payment_token>', methods=['GET', 'POST'])
def checkout(payment_token):
    """Secure payment processing endpoint with graceful token handling"""
    try:
        # 1) Enhanced token validation with state awareness
        order = validate_payment_token(payment_token)
        
        if not order:
            security_logger.warning(f"Invalid token access attempt: {payment_token}")
            return handle_expired_token()
            
        # 2) Handle different order states
        if order.payment_status == 'Paid':
            return handle_already_paid(order)
        elif order.payment_status == 'Failed':
            return handle_retry_payment(order)
        elif order.payment_status != 'Pending':
            abort(404)

        # 3) GET request - show payment form
        if request.method == 'GET':
            token = generate_csrf()
            return render_template(
                'payments/checkout.html',
                order=order,
                csrf_token=token,
                payment_token=payment_token,
                stripe_key=current_app.config.get('STRIPE_PUBLIC_KEY', '')
            )

        # 4) CSRF protection
        raw_csrf = (
            request.form.get('csrf_token')
            or request.headers.get('X-CSRFToken')
            or request.headers.get('X-XSRF-TOKEN')
        )
        try:
            validate_csrf(raw_csrf)
        except ValidationError:
            security_logger.warning(f"CSRF validation failed for order {order.id}")
            abort(403)

        # 5) Payment validation pipeline
        data = request.get_json(silent=True) or request.form
        pan = sanitize_pan(data.get('card_number', ''))
        expiry = data.get('expiry_date', '')
        cvv = data.get('cvv', '')
        
        validation_errors = validate_payment_details(pan, expiry, cvv, order.id)
        if validation_errors:
            return error_response(validation_errors, payment_token)

        # 6) Process payment
        try:
            # Encrypt PAN with versioned keys
            encrypted_data = encrypt_pan(pan)
            if not encrypted_data:
                raise ValueError("PAN encryption failed")
            
            # Create payment method record
            pm = PaymentMethod(
                brand=detect_card_brand(pan),
                last4=pan[-4:],
                exp_month=int(expiry.split('/')[0]),
                exp_year=int(expiry.split('/')[1]),
                token=generate_secure_token(),
                enc_pan=encrypted_data['ciphertext'],
                pan_nonce=encrypted_data['nonce'],
                key_version=encrypted_data['key_version'],
                masked_pan=f"{pan[:6]}******{pan[-4:]}"
            )
            db.session.add(pm)

            # Update order status
            order.payment_status = "Paid"
            order.payment_method = "card"
            order.payment_method_record = pm
            order.payment_token = None  # Invalidate token
            order.paid_at = datetime.utcnow()

            # Create payment event for audit trail
            payment_event = PaymentEvent(
                order_id=order.id,
                status="Paid",
                amount=order.total,
                details=f"Card ending in {pan[-4:]}"
            )
            db.session.add(payment_event)
            
            db.session.commit()

            # 7) Post-payment actions
            clear_payment_session_data()
            send_payment_confirmation_email(order)
            security_logger.info(f"Payment completed for order {order.id}")

            # 8) Response handling
            thank_you_url = url_for('main.list_products')
            
            if request.is_json:
                return json_response(
                    message="Payment successful",
                    redirect=thank_you_url,
                    order_id=order.id
                )
            return redirect(thank_you_url)

        except (exc.SQLAlchemyError, ValueError) as e:
            db.session.rollback()
            security_logger.error(f"Payment processing error for order {order.id}: {str(e)}")
            order.payment_status = "Failed"
            db.session.commit()
            return error_response("Payment processing failed. Please try again.", payment_token)

    except Exception as e:
        security_logger.error(f"Unexpected checkout error: {str(e)}", exc_info=True)
        return error_response("An unexpected error occurred. Please contact support.", payment_token)



@payments_bp.route('/thank-you/<int:order_id>')
def thank_you(order_id):
    # You can fetch order details here if needed
    return render_template('payments/thank_you.html', order_id=order_id)