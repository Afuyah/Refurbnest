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


# ——————— DELETE Remove from Cart ———————
@cart_bp.route('/remove/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id: int):
    cart = Cart()
    if str(product_id) not in cart.get_items():
        abort(404, description='Item not in cart')  # clear 404 path :contentReference[oaicite:13]{index=13}

    cart.remove(product_id)
    payload = {
        'items': cart.get_items(),
        'count': cart.item_count,
        'unique_items': cart.unique_items,
        'total': float(cart.total),
        'message': 'Item removed successfully'
    }
    return jsonify(payload), 200


@cart_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = Cart.get_cart()
    total = Cart.get_total()

    if request.method == 'POST':
        email = request.form.get('email')
        if not email or not cart:
            flash("Invalid checkout attempt.", "danger")
            return redirect(url_for('cart.checkout'))

        # Create Order
        new_order = Order(email=email, total_amount=total)
        db.session.add(new_order)
        db.session.flush()  # Get new_order.id without committing yet

        for product_id, item in cart.items():
            order_item = OrderItem(
                product_name=item['name'],
                product_price=item['price'],
                quantity=item['quantity'],
                order=new_order
            )
            db.session.add(order_item)

        db.session.commit()

        # Clear Cart
        Cart.clear()

        # Send Email
        send_order_confirmation(email, new_order)

        flash("Order placed successfully! Check your email.", "success")
        return redirect(url_for('home'))

    return render_template('checkout.html', cart=cart, total=total)




