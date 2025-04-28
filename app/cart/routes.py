from flask import Blueprint, request, redirect, url_for, flash, render_template,jsonify, current_app as app
from app.cart.cart import Cart
from app.admin.models import Product  
from flask import request, redirect, flash, url_for, render_template
from app.admin.models import Order, OrderItem, db
from app.email.confirm_email import send_order_confirmation
from decimal import Decimal
from .cart import CartError  
from werkzeug.exceptions import HTTPException


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
    cart = Cart()  # loads/validates session once :contentReference[oaicite:8]{index=8}
    items_out = []

    for pid, item in cart.get_items().items():
        product = Product.query.get(pid)
        if not product or not product.is_active:
            continue  # skip deleted or inactive products

        items_out.append({
            'id': pid,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'current_price': float(product.price),
            'available': product.is_active
        })

    response = {
        'items': items_out,
        'total': float(cart.total),
        'count': cart.item_count,
        'unique_items': cart.unique_items
    }
    # Optionally add caching headers here for performance :contentReference[oaicite:9]{index=9}
    return jsonify(response), 200


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


@cart_bp.route('/checkout', methods=['POST'])
def checkout():
    cart = Cart()
    if cart.item_count == 0:
        abort(400, description="Cart is empty")

    data = request.get_json()
    name = data.get('name', '').strip()
    address = data.get('address', '').strip()
    phone = data.get('phone', '').strip()

    if not all([name, address, phone]):
        abort(400, description="Missing required fields")

    order = Order(
        name=name,
        address=address,
        phone=phone,
        total=cart.total,
        payment_status='Pending'
    )
    db.session.add(order)
    db.session.flush()  # get order.id before committing

    for pid, item in cart.get_items().items():
        order_item = OrderItem(
            order_id=order.id,
            product_id=pid,
            name=item['name'],
            price=item['price'],
            quantity=item['quantity']
        )
        db.session.add(order_item)

    db.session.commit()

    return jsonify({
        'order_id': order.id,
        'message': 'Order created, ready for payment'
    }), 200



@cart_bp.route('/summary')
def cart_summary():
    cart = Cart()
    payload = {
        'items': cart.get_items(),     # {'product_id': {name, price, quantity}}
        'count': cart.item_count,       # total quantity of all products
        'unique_items': cart.unique_items,  # how many different products
        'total': float(cart.total),     # grand total
    }
    return jsonify(payload), 200

