from flask import Blueprint, request, redirect, url_for, flash, render_template,jsonify, current_app as app
from app.cart.cart import Cart
from flask_login import current_user
from app import db,csrf
from app.admin.models import Product  
from flask import request, redirect, flash, url_for, render_template
from app.admin.models import Order, OrderItem,ShippingAddress
from app.email.confirm_email import send_order_confirmation
from decimal import Decimal, ROUND_HALF_UP
from .cart import CartError  
from werkzeug.exceptions import HTTPException
from itsdangerous import URLSafeTimedSerializer

cart_bp = Blueprint('cart', __name__)


# ——————— Centralized Error Handlers ———————
@cart_bp.errorhandler(CartError)
def handle_cart_error(err: CartError):
    return jsonify({'error': str(err), 'code': 'CART_ERROR'}), 400  # Bad Request :contentReference[oaicite:5]{index=5}

@cart_bp.errorhandler(404)
def handle_not_found(err):
    return jsonify({'error': err.description or 'Not Found', 'code': 'NOT_FOUND'}), 404  # :contentReference[oaicite:6]{index=6}

@cart_bp.errorhandler(Exception)
def handle_exception(err):
    if isinstance(err, HTTPException):
        return err
    app.logger.exception(err)
    return jsonify({'error': 'Internal server error', 'code': 'SERVER_ERROR'}), 500  # :contentReference[oaicite:7]{index=7}


# ——————— GET Cart JSON ———————
@cart_bp.route('/json', methods=['GET'])
def get_cart_json():
    cart = Cart()
    items_out = []
    for pid, item in cart.get_items().items():
        product = Product.query.get(pid)
        if not product or not product.is_active:
            continue
        items_out.append({
            'id': pid,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'current_price': float(product.price),
            'available': product.is_active
        })
    return jsonify({
        'items': items_out,
        'total': float(cart.total),
        'count': cart.item_count,
        'unique_items': cart.unique_items
    }), 200


# ——————— POST Add to Cart ———————
@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id: int):
    product = Product.query.get_or_404(product_id)  # 404 if missing :contentReference[oaicite:10]{index=10}
    if not product.is_active:
        abort(400, description='Product currently unavailable')  # 400 on client error :contentReference[oaicite:11]{index=11}

    cart = Cart()
    cart.add(product_id, product.name, float(product.price))

    payload = {
        'items': cart.get_items(),
        'count': cart.item_count,
        'unique_items': cart.unique_items,
        'total': float(cart.total),
        'message': f"Added '{product.name}' to cart"
    }
    return jsonify(payload), 201  # 201 Created :contentReference[oaicite:12]{index=12}

@cart_bp.route('/remove/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id: int):
    cart = Cart()
    if str(product_id) not in cart.get_items():
        abort(404, description='Item not in cart')

    cart.remove(product_id)
    payload = {
        'items': cart.get_items(),
        'count': cart.item_count,
        'unique_items': cart.unique_items,
        'total': float(cart.total),
        'message': 'Item removed successfully'
    }
    return jsonify(payload), 200

from decimal import Decimal

@cart_bp.route('/checkout', methods=['GET'])
def checkout_page():
    cart = Cart()
    if cart.item_count == 0:
        return redirect(url_for('cart.cart_summary'))

    cart_items = []
    for pid, item in cart.get_items().items():
        cart_items.append({
            'name': item['name'],
            'quantity': item['quantity'],
            'price': item['price'],
            'image_url': item.get('image')
        })

    subtotal = cart.total  # assuming cart.total is a Decimal
    shipping = Decimal('5.00')
    total = subtotal + shipping

    return render_template(
        'cart/checkout.html',
        cart_items=cart_items,
        subtotal=subtotal,
        total=total
    )


@cart_bp.route('/summary', methods=['GET'])
def cart_summary():
    cart = Cart()
    return jsonify({
        'items': cart.get_items(),
        'count': cart.item_count,
        'unique_items': cart.unique_items,
        'total': float(cart.total)
    }), 200


def generate_payment_token(order):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return s.dumps(
        {'order_id': order.id}, 
        salt='payment-token'
    )


def calculate_shipping_cost(shipping_method: str, country: str) -> float:
    # Example logic, adjust as needed
    if shipping_method == 'express':
        return 12.00
    elif shipping_method == 'standard':
        return 5.00
    else:
        return 0.00

from decimal import Decimal, ROUND_HALF_UP

def calculate_tax(subtotal: Decimal, country: str, state: str) -> Decimal:
    # Define tax rates by country/state (example)
    if country == 'US':
        if state in ('CA', 'NY', 'TX'):
            tax_rate = Decimal('0.08')  # 8%
        else:
            tax_rate = Decimal('0.05')  # 5%
    else:
        tax_rate = Decimal('0.00')  # no tax
    
    tax_amount = (subtotal * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return tax_amount



@cart_bp.route('/checkout', methods=['POST'])
def checkout():
    cart = Cart()
    if cart.item_count == 0:
        abort(400, description="Cart is empty")

    data = request.get_json() or {}
    
    # Validate required fields
    required_fields = {
        'contact': ['first_name', 'last_name', 'email', 'phone'],
        'shipping': ['address_line1', 'city', 'state', 'postal_code', 'country', 'shipping_method']
    }
    
    errors = []
    for field_group, fields in required_fields.items():
        for field in fields:
            if not data.get(field):
                errors.append(f"Missing required {field_group} field: {field}")
    
    if errors:
        return jsonify({"errors": errors}), 400

    # Calculate totals
    subtotal = cart.subtotal
    shipping_cost = calculate_shipping_cost(data['shipping_method'], data['country'])
    tax = calculate_tax(subtotal, data['country'], data['state'])
    total = subtotal + Decimal(str(shipping_cost)) + Decimal(str(tax))

    # Create order
    order = Order(
        user_id=current_user.id if current_user.is_authenticated else None,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax=tax,
        total=total,
        payment_status='Pending'
    )
    db.session.add(order)
    db.session.flush()

    # Create shipping address
    shipping_address = ShippingAddress(
        order_id=order.id,
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        address_line1=data['address_line1'],
        address_line2=data.get('address_line2', ''),
        city=data['city'],
        state=data['state'],
        postal_code=data['postal_code'],
        country=data['country'],
        shipping_method=data['shipping_method'],
        delivery_instructions=data.get('delivery_instructions', '')
    )
    db.session.add(shipping_address)

    # Add order items
    for pid, item in cart.get_items().items():
        product = Product.query.get(pid)
        if not product:
            continue
            
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=pid,
            quantity=item['quantity'],
            price=item['price'],
            name=product.name,
            sku=product.sku,
           
        ))

    # Generate payment token
    token = generate_payment_token(order)
    order.payment_token = token
    db.session.commit()

    # Clear cart only after successful commit
    cart.clear()

    return jsonify({
        'success': True,
        'message': 'Order created, ready for payment',
        'order_id': order.id,
        'redirect': f"https://secure.salesta.store/checkout/{token}",
        'payment_token': token
    })