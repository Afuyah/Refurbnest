import time
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect, url_for,current_app,
                   flash, jsonify, abort)
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address)

from app.admin.models import PaymentMethod
from app.admin.models import Order         
from .crypto import encrypt_pan, luhn_checksum
import logging
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
    """Secure token validation with expiration"""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(
            token,
            salt='payment-token',
            max_age=3600  # 1 hour expiration
        )
        return Order.query.filter_by(
            id=data['order_id'],
            user_id=current_user.id,
            payment_status='Pending'
        ).first()
    except (BadSignature, SignatureExpired, KeyError):
        security_logger.warning(f"Invalid payment token: {token}")
        return None

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
    """Secure payment processing endpoint"""
    try:
        # 1) Token validationn
        order = validate_payment_token(payment_token)
        if not order:
            security_logger.warning(f"Invalid order access: {payment_token}")
            abort(404)

        # 2) GET request - show payment form
        if request.method == 'GET':
            return render_template(
                'payments/checkout.html',
                order=order,
                csrf_token=generate_csrf(),
                payment_token=payment_token
            )

        # 3) CSRF protection
        if not validate_csrf(request.form.get('csrf_token')):
            abort(403)

        # 4) Payment validation pipeline
        pan = sanitize_pan(request.form.get('card_number', ''))
        expiry = request.form.get('expiry_date', '')
        cvv = request.form.get('cvv', '')
        
        validation_errors = []
        
        # Enhanced PAN validation
        if not (13 <= len(pan) <= 19 and pan.isdigit() and luhn_checksum(pan)):
            validation_errors.append("Invalid card number")
            security_logger.warning(f"Invalid PAN attempt for order {order.id}")
        
        # Expiry validation
        expiry_data = validate_expiry(expiry)
        if not expiry_data:
            validation_errors.append("Invalid or expired date")
        else:
            month, year = expiry_data
            
        # CVV validation
        brand = detect_card_brand(pan)
        expected_cvv_length = 4 if brand == 'AMEX' else 3
        if not (cvv.isdigit() and len(cvv) == expected_cvv_length):
            validation_errors.append(f"CVV must be {expected_cvv_length} digits")

        if validation_errors:
            return error_response(validation_errors, payment_token)

        # 5) Process payment
        try:
            # Encrypt PAN with versioned keys
            encrypted_data = encrypt_pan(pan)
            
            # Create payment method record
            pm = PaymentMethod(
                brand=brand,
                last4=pan[-4:],
                exp_month=month,
                exp_year=year,
                token=generate_secure_token(),
                enc_pan=encrypted_data['ciphertext'],
                pan_nonce=encrypted_data['nonce'],
                key_version=encrypted_data['key_version'],
                masked_pan=f"{pan[:6]}******{pan[-4:]}"
            )
            db.session.add(pm)
            
            # Update order status
            order.payment_method = pm
            order.payment_status = 'Paid'
            order.payment_token = None  # Invalidate token
            
            db.session.commit()

            # 6) Post-payment actions
            clear_payment_session_data()
            security_logger.info(f"Payment completed for order {order.id}")

            # 7) Response handling
            thank_you_url = url_for('payments.thank_you', payment_token=payment_token)
            return json_response(
                message="Payment successful",
                redirect=thank_you_url
            ) if request.is_json else redirect(thank_you_url)
            
        except (exc.SQLAlchemyError, ValueError) as e:
            db.session.rollback()
            security_logger.error(f"Payment processing error: {str(e)}")
            return error_response("Payment processing failed", payment_token)

    except Exception as e:
        security_logger.error(f"Checkout error: {str(e)}", exc_info=True)
        return error_response("Processing error occurred", payment_token)


@payments_bp.route('/cards', methods=['GET'])
@login_required
def list_cards():
    cards = (
        PaymentMethod.query
        .filter_by(user_id=current_user.id)
        .order_by(PaymentMethod.created_at.desc())
        .all()
    )
    return render_template('payments/cards.html', cards=cards)




@payments_bp.route('/thank-you/<int:order_id>')
def thank_you(order_id):
    # You can fetch order details here if needed
    return render_template('payments/thank_you.html', order_id=order_id)