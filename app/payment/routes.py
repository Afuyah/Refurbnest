import time
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect, url_for,
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


payments_bp = Blueprint(
    'payments',
    __name__,
    subdomain='secure',
    url_prefix='/checkout',
    template_folder='templates/payments'
)

security_logger = logging.getLogger('payment.security')


def detect_card_brand(pan: str) -> str:
    if pan.startswith('4'):
        return 'VISA'
    if pan[:2] in ('51', '52', '53', '54', '55'):
        return 'MASTERCARD'
    if pan.startswith(('34', '37')):
        return 'AMEX'
    if pan.startswith('6'):
        return 'DISCOVER'
    return 'UNKNOWN'

def generate_secure_token():
    return binascii.hexlify(os.urandom(16)).decode()

def sanitize_pan(raw_pan: str) -> str:
    return re.sub(r'\D+', '', raw_pan)[:19]

def validate_payment_token(token: str):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='payment-token', max_age=3600)
        return Order.query.filter_by(id=data['order_id'], user_id=current_user.id).first()
    except (BadSignature, SignatureExpired, KeyError):
        return None

def error_response(errors, payment_token):
    if request.is_json:
        return jsonify({'errors': errors}), 400
    for error in errors:
        flash(error, "danger")
    return redirect(url_for('payments.checkout', payment_token=payment_token))


@payments_bp.route('/detect-brand', methods=['POST'])
@login_required
def detect_brand_api():
    data = request.get_json() or {}
    pan = data.get('pan', '').replace(' ', '')
    brand = detect_card_brand(pan) if len(pan) >= 2 else ''
    return jsonify({'brand': brand}), 200


@payments_bp.route('/<string:payment_token>', methods=['GET', 'POST'])
@login_required
@limiter.limit("5/minute")
def checkout(payment_token):
    try:
        # 1) Secure order access
        order = validate_payment_token(payment_token)
        if not order:
            security_logger.warning(f"Invalid order access attempt: {payment_token}")
            abort(404)

        # 2) GET request handling
        if request.method == 'GET':
            return render_template(
                'payments/checkout.html',
                order_total=order.total,
                amount=order.total,
                csrf_token=generate_csrf(),
                payment_token=payment_token
            )

        # 3) CSRF validation
        if not validate_csrf(request.form.get('csrf_token')):
            abort(403)

        # 4) Payment validation pipeline
        pan = sanitize_pan(request.form.get('card_number', ''))
        expiry = request.form.get('expiry_date', '')
        cvv = request.form.get('cvv', '')
        
        validation_errors = []
        
        # PAN validation
        if not (13 <= len(pan) <= 19 and pan.isdigit() and luhn_checksum(pan)):

            validation_errors.append("Invalid card number")
            
        # Expiry validation
        if not re.match(r'^(0[1-9]|1[0-2])\/(2[2-9]|[3-9][0-9])$', expiry):
            validation_errors.append("Invalid expiration date format")
        else:
            m, y = map(int, expiry.split('/'))
            if datetime(y + 2000, m, 1) < datetime.utcnow():
                validation_errors.append("Card has expired")
                
        # CVV validation
        brand = detect_card_brand(pan)
        cvv_length = 4 if brand == 'AMEX' else 3
        if not (cvv.isdigit() and len(cvv) == cvv_length):
            validation_errors.append("Invalid CVV")

        if validation_errors:
            return error_response(validation_errors, payment_token)

        # 5) Process payment
        try:
            encrypted_pan = encrypt_pan(pan)
            token = generate_secure_token()
            
            pm = PaymentMethod(
                brand=brand,
                last4=pan[-4:],
                exp_month=m,
                exp_year=y + 2000,
                token=token,
                enc_pan=encrypted_pan['ciphertext'],
                pan_nonce=encrypted_pan['nonce'],
                key_version=encrypted_pan['key_version'],
                masked_pan=f"{pan[:6]}******{pan[-4:]}"
            )
            db.session.add(pm)
            
            order.payment_method_id = pm.id
            order.payment_status = 'Paid'
            order.payment_token = None
            
            db.session.commit()
            
            # 6) Post-payment cleanup
            security_logger.info(f"Payment completed for order {order.id}")
            
            # 7) Response
            thank_you_url = url_for('payments.thank_you', payment_token=payment_token)
            if request.is_json:
                return jsonify({
                    'message': 'Payment successful',
                    'redirect': thank_you_url
                }), 200
            return redirect(thank_you_url)
            
        except (exc.SQLAlchemyError, ValueError) as e:
            db.session.rollback()
            security_logger.error(f"Payment error: {str(e)}")
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