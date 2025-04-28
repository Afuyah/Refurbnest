from flask import Blueprint, request, redirect, url_for, flash, render_template,jsonify
from app.cart.cart import Cart
from app.admin.models import Product  
from flask import request, redirect, flash, url_for, render_template
from app.admin.models import Order, OrderItem, db
from app.email.confirm_email import send_order_confirmation
from decimal import Decimal
from .cart import CartError  


cart_bp = Blueprint('cart', __name__)



@cart_bp.route('/cart/json', methods=['GET'])
def cart_json():
    cart_data = Cart.get_cart()
    items = []
    total = 0.0
    count = 0

    for pid, item in cart_data.items():
        # Convert string ID back to integer for database lookup
        product_id = int(pid)
        product = Product.query.get(product_id)
        
        # Skip items for deleted products
        if not product:
            continue
            
        # Use cart-stored price but verify product status
        item_price = item['price']
        qty = item['quantity']
        
        items.append({
            'id': product_id,
            'name': item['name'],  # Use cart-stored name
            'price': float(item_price),
            'quantity': qty,
            'current_price': float(product.price),  # Show current price for reference
            'available': product.is_active
        })
        
        total += item_price * qty
        count += qty

    return jsonify({
        'items': items,
        'total': float(Cart.get_total()),  # Use precise cart calculation
        'count': Cart.item_count(),
        'unique_items': Cart.unique_items()
    })




@cart_bp.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if your Product model actually has 'is_active' column
        # If not, use the correct column name like 'available' or 'in_stock'
        if not product.is_active:  # ⚠️ Verify this matches your model
            return jsonify({
                'error': 'This product is currently unavailable',
                'code': 'PRODUCT_UNAVAILABLE'
            }), 400

        Cart.add(
            product_id=product.id,
            name=product.name,
            price=float(product.price),
            quantity=1
        )

        return jsonify({
            'cart_count': Cart.item_count(),
            'unique_items': Cart.unique_items(),
            'total': float(Cart.get_total()),
            'message': f'{product.name} added to cart'
        })

    except CartError as e:
        return jsonify({'error': str(e), 'code': 'CART_ERROR'}), 400
        
    except Exception as e:
        return jsonify({'error': 'Failed to add item to cart', 'code': 'SERVER_ERROR'}), 500  # Fixed status code0



@cart_bp.route('/remove/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    try:
        # Convert to string to match session storage format
        str_product_id = str(product_id)
        
        # Get current cart
        cart = Cart.get_cart()
        
        # Check if item exists in cart
        if str_product_id not in cart:
            return jsonify({
                'success': False,
                'error': 'Item not found in cart',
                'code': 'ITEM_NOT_FOUND'
            }), 404

        # Remove item from cart
        Cart.remove(product_id)
        
        # Get updated cart data
        updated_cart = Cart.get_cart()
        count = Cart.item_count()
        total = Cart.get_total()

        return jsonify({
            'success': True,
            'count': count,
            'total': float(total),
            'remaining_items': len(updated_cart),
            'message': 'Item successfully removed',
            'cart': updated_cart
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'SERVER_ERROR'
        }), 500






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




