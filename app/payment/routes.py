import time
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, jsonify, abort)
from flask_login import login_required, current_user

from app.admin.models import PaymentMethod
from app.admin.models import Order         
from .crypto import encrypt_pan, luhn_checksum

from app import db

payments_bp = Blueprint(
    'payments', __name__,
    url_prefix='/payments',
    template_folder='templates/payments'
)


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


@payments_bp.route('/detect-brand', methods=['POST'])
@login_required
def detect_brand_api():
    data = request.get_json() or {}
    pan = data.get('pan', '').replace(' ', '')
    brand = detect_card_brand(pan) if len(pan) >= 2 else ''
    return jsonify({'brand': brand}), 200


@payments_bp.route('/<int:order_id>/checkout', methods=['GET', 'POST'])
def checkout(order_id):
    # 1) Load order — no user check
    order = Order.query.get_or_404(order_id)

    # 2) GET → show form
    if request.method == 'GET':
        return render_template(
            'payments/checkout.html',
            order_id=order.id,
            order_total=order.total
        )

    # 3) POST → validate
    data       = request.get_json(silent=True) or request.form
    pan        = data.get('card_number', '').replace(' ', '')
    expiry     = data.get('expiry_date', '')
    cvv        = data.get('cvv', '')
    cardholder = data.get('cardholder_name', '')

    # 4a) Luhn
    if not luhn_checksum(pan):
        msg = "Invalid card number."
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, "danger")
        return redirect(url_for('payments.checkout', order_id=order.id))

    # 4b) Expiry
    try:
        m, y = map(int, expiry.split('/'))
        y += 2000 if y < 100 else 0
        now = datetime.utcnow()
        if y < now.year or (y == now.year and m < now.month):
            raise ValueError
    except Exception:
        msg = "Invalid or expired expiry date."
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, "danger")
        return redirect(url_for('payments.checkout', order_id=order.id))

    # 4c) CVV
    if not (cvv.isdigit() and len(cvv) in (3,4)):
        msg = "Invalid CVV."
        if request.is_json:
            return jsonify({'message': msg}), 400
        flash(msg, "danger")
        return redirect(url_for('payments.checkout', order_id=order.id))

    # 5) Encrypt & store
    nonce, ct = encrypt_pan(pan)
    token     = f"TOK_{pan[-4:]}_{int(time.time())}"
    pm = PaymentMethod(
        brand      = detect_card_brand(pan),
        last4      = pan[-4:],
        exp_month  = m,
        exp_year   = y,
        token      = token,
        enc_pan    = ct,
        pan_nonce  = nonce
    )
    db.session.add(pm)

    # 6) Link to order
    order.payment_method_id = pm.id
    order.payment_status    = 'Paid'
    db.session.commit()

    # 7) Respond
    thank_you = url_for('payments.thank_you', order_id=order.id)
    success   = "Payment successful!"
    if request.is_json:
        return jsonify({'message': success, 'next': thank_you}), 200

    flash(success, "success")
    return redirect(thank_you)



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