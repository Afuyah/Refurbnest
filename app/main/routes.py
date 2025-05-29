from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask import jsonify
from app.admin.models import Product, Brand, Category, ContactMessage, Wishlist, ProductImage, Review, Order, ShippingAddress, OrderItem
from app.main.forms import InquiryForm, ContactForm, WishlistForm, VerifyPurchaseForm,ReviewForm
from app.admin.forms import ProductForm
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError  
from werkzeug.exceptions import abort
from functools import wraps
from app import db, mail, csrf
from flask import current_app
from flask_login import login_required, login_user, logout_user, current_user
from app.email.email_templates import get_verification_email
import re

# Create a blueprint for main routes
main_bp = Blueprint('main', __name__)


def login_required_with_message(view):
    """Custom decorator that requires user login with a flash message."""
    @wraps(view)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login')) 
        return view(*args, **kwargs)
    return decorated_view


# ---------------------------------------
# Home Route
# ---------------------------------------



@main_bp.route('/', methods=['GET'])
def home():
    try:
        categories = Category.query.all()
        products = Product.query.all()
        hot_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
        testimonials = Review.query.filter_by(verified=True).order_by(Review.date.desc()).limit(3).all()

        return render_template(
            'main/home.html',
            categories=categories,
            hot_products=hot_products,
            testimonials=testimonials,
            products=products 
        )
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in home route: {str(e)}")
        abort(500)

@main_bp.route('/api/featured-products')
def get_featured_products():
    try:
        # Eager load images to prevent N+1 query problem
        featured = Product.query.options(joinedload(Product.images))\
                     .filter_by(is_featured=True)\
                     .order_by(Product.updated_at.desc())\
                     .limit(6)\
                     .all()

        return jsonify(serialize_featured_products(featured))
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in featured products: {str(e)}")
        return jsonify({"error": "Could not retrieve products"}), 500

def serialize_featured_products(products):
    serialized = []
    for p in products:
        serialized.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price) if p.price else None,
           
            "image": get_primary_image_url(p),
            
        })
    return serialized

def get_primary_image_url(product):
    if not product.images:
        return url_for('static', filename='/placeholder.svg')
    
    try:
        filename = product.images[0].image_path.split('/')[-1]
        return url_for('product_image', filename=filename)
    except (AttributeError, IndexError):
        current_app.logger.warning(f"Invalid image path for product {product.id}")
        return url_for('static', filename='images/placeholder.svg')


# ---------------------------------------
# Product Routes 
# ---------------------------------------
from sqlalchemy.orm import joinedload

@main_bp.route('/products', methods=['GET'])
def list_products():
    # Get pagination and filter parameters
    page = request.args.get('page', 1, type=int)
    brand_id = request.args.get('brand')
    category_id = request.args.get('category')

    # Base query with eager loading of related data
    query = Product.query.options(
        joinedload(Product.brand),
        joinedload(Product.category),
        joinedload(Product.images)
    )

    # Apply filters if provided
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Paginate results (8 per page)
    pagination = query.paginate(page=page, per_page=8, error_out=False)
    products = pagination.items

    # Prepare product data with first image or default image
    product_data = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'brand': product.brand.name,
        'category': product.category.name,
        'image_url': url_for('product_image', filename=product.images[0].image_path)
                     if product.images else url_for('static', filename='images/default.jpg')
    } for product in products]

    # Get all brands and selected category for filter UI
    brands = Brand.query.all()
    selected_category = Category.query.get(category_id) if category_id else None

    # Inform user if no results
    if not pagination.total:
        flash("No products found matching your criteria.", "info")

    return render_template(
        'main/list_products.html',
        products=product_data,
        pagination=pagination,
        brands=brands,
        selected_brand_id=brand_id,
        selected_category=selected_category
    )

@main_bp.route('/products/<int:product_id>', methods=['GET'])
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    image_url = product.images[0].image_path if product.images else 'default.jpg'

    # Get recent reviews
    recent_reviews = Review.query.filter_by(product_id=product_id).order_by(Review.date.desc()).limit(5).all()
    total_reviews = Review.query.filter_by(product_id=product_id).count()

    # Load inquiry form
    form = InquiryForm()

    # Handle verified review modal
    verified_review_id = session.pop('verified_review', None)
    show_review_modal = False
    review_to_edit = None

    if verified_review_id:
        review_to_edit = Review.query.get(verified_review_id)
        if review_to_edit and review_to_edit.product_id == product.id and not review_to_edit.verified:
            show_review_modal = True

    # Fetch all flexible specs (assuming Product.specs is a relationship)
    specs = product.specs  # List of ProductSpec(name, value)

    return render_template(
        'main/view_product.html',
        product=product,
        form=form,
        image_url=image_url,
        reviews=recent_reviews,
        total_reviews=total_reviews,
        show_review_modal=show_review_modal,
        verified_review=verified_review_id,
        review_to_edit=review_to_edit,
        specs=specs  # Pass specs to the template
    )

from flask import request

@main_bp.route('/category/', defaults={'category_slug': None}, strict_slashes=False)
@main_bp.route('/category/<string:category_slug>')
def products_by_category(category_slug):
    if not category_slug:
        return redirect(url_for('main.list_products'))

    category = Category.query.filter_by(slug=category_slug).first_or_404()

    page = request.args.get('page', 1, type=int)
    per_page = 12  

    pagination = (
        Product.query
               .filter_by(category_id=category.id)
               .order_by(Product.created_at.desc())
               .paginate(page=page, per_page=per_page)
    )
    products = pagination.items

    product_data = []
    for p in products:
        first_image = p.images[0].image_path if p.images else 'default.jpg'
        product_data.append({
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'brand_id': p.brand_id,
            'category_id': p.category_id,
            'image_url': first_image
        })

    form = ProductForm()
    return render_template(
        'main/list_products.html',
        products=product_data,
        pagination=pagination,
        form=form,
        selected_category=category
    )

@main_bp.route('/products/<int:product_id>/feature', methods=['POST'])
def mark_product_featured(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_featured = True
    db.session.commit()
    flash(f'{product.name} has been marked as featured.', 'success')
    return redirect(url_for('main.list_products'))


@main_bp.route('/products/<int:product_id>/unfeature', methods=['POST'])
def unmark_product_featured(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_featured = False
    db.session.commit()
    flash(f'{product.name} has been removed from featured.', 'info')
    return redirect(url_for('main.list_products'))


from urllib.parse import quote

@main_bp.route('/inquire/<int:product_id>', methods=['POST'])
def inquire_product(product_id):
    form = InquiryForm()
    if form.validate_on_submit():
        product = Product.query.get_or_404(product_id)

        # Prepare the WhatsApp message with product details
        message = (
            f"Hi, I'm interested in the *{product.name}*.\n"
            f"*Description:* {product.description}\n"
            f"*Price:* Ksh{product.price}\n"
            f"*Image:* {url_for('static', filename=product.image_url, _external=True)}\n"
            f"*Contact me at:* {form.contact.data}"
        )

        # Encode the message for the WhatsApp URL
        encoded_message = quote(message)
        whatsapp_url = f"https://wa.me/254711667718?text={encoded_message}"

        flash('Inquiry sent! You will be redirected to WhatsApp.', 'success')
        return redirect(whatsapp_url)

    flash('Please fill in your contact information.', 'danger')
    return redirect(url_for('main.view_product', product_id=product_id))



# ---------------------------------------
# Brand Routes
# ---------------------------------------

@main_bp.route('/brands', methods=['GET'])
def list_brands():
    brands = Brand.query.all()
    return render_template('main/list_brands.html', brands=brands)

# ---------------------------------------
# Category Routes
# ---------------------------------------

@main_bp.route('/categories', methods=['GET'])
def list_categories():
    categories = Category.query.all()
    return render_template('main/list_categories.html', categories=categories)

# ---------------------------------------
# Error Handling
# ---------------------------------------

@main_bp.errorhandler(404)
def not_found(error):
    return render_template('main/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    current_app.logger.error(f'Server Error: {error}, route: {request.url}')
    return render_template('main/500.html'), 500
# View Wishlist
@main_bp.route('/wishlist')
@login_required
def view_wishlist():
    form = WishlistForm()
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('main/wishlist.html', wishlist_items=wishlist_items, form=form)

# Add Product to Wishlist
@main_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required_with_message
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)

    # Check if the product is already in the user's wishlist
    existing_wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    
    if existing_wishlist_item:
        flash('Product is already in your wishlist.', 'info')
    else:
        new_wishlist_item = Wishlist(user_id=current_user.id, product_id=product.id)
        db.session.add(new_wishlist_item)
        db.session.commit()
        flash('Product added to your wishlist!', 'success')

    # Redirect to the wishlist view
    return redirect(url_for('main.view_wishlist'))

# Remove Product from Wishlist
@main_bp.route('/wishlist/remove/<int:wishlist_item_id>', methods=['POST'])
@login_required_with_message
def remove_from_wishlist(wishlist_item_id):
    form = WishlistForm()
    wishlist_item = Wishlist.query.get_or_404(wishlist_item_id)
    
    if wishlist_item.user_id != current_user.id:
        flash('You are not authorized to remove this item.', 'danger')
        return redirect(url_for('main.view_wishlist'))
    
    db.session.delete(wishlist_item)
    db.session.commit()
    flash('Product removed from your wishlist.', 'success')
    
    return redirect(url_for('main.view_wishlist'))

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Save contact message to the database
        contact_message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(contact_message)
        db.session.commit()
        
        # Flash message for success
        flash('Your message has been sent. We will get back to you shortly.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('main/contact.html', title='Contact Us', form=form)

@main_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('main/privacy_policies.html')


@main_bp.route('/about')
def about():
    return render_template('main/about.html')    


@main_bp.route('/process')
def process():
    return render_template('main/process.html')    

@main_bp.route('/business')
def business():
    return render_template('main/business.html')    


@main_bp.route('/product/<int:product_id>/reviews')
def all_reviews(product_id):
    product = Product.query.get_or_404(product_id)
    all_reviews = Review.query.filter_by(product_id=product_id).order_by(Review.date.desc()).all()
    
    return render_template('main/all_reviews.html', product=product, reviews=all_reviews)


from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
import re
import jwt
from datetime import datetime, timedelta
from flask import current_app

def generate_verification_token(email, product_id):
    """Generate a JWT token for email verification"""
    payload = {
        'email': email,
        'product_id': product_id,
        'exp': datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_verification_token(token):
    """Verify the JWT token and return email and product_id"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload['email'], payload['product_id']
    except jwt.ExpiredSignatureError:
        return None, None
    except jwt.InvalidTokenError:
        return None, None

def get_review_id_from_token(token):
    """Get review ID from token (if stored in token)"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload.get('review_id')
    except:
        return None

@csrf.exempt
@main_bp.route('/verify-purchase', methods=['POST'])
def verify_purchase():
    try:
        if not request.is_json:
            return jsonify({'error': 'Invalid content type', 'message': 'Request must be JSON'}), 415

        data = request.get_json()
        email = data.get('email')
        product_id = data.get('product_id')

        if not email or not product_id:
            return jsonify({'error': 'Missing fields', 'message': 'Email and Product ID are required'}), 400

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'error': 'Invalid email format'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # 🔒 Check if this email purchased this product in a completed order
        order = (
            db.session.query(Order)
            .join(ShippingAddress)
            .join(OrderItem)
            .filter(
                ShippingAddress.email == email,
                OrderItem.product_id == product_id,
                Order.payment_status.in_(['Paid'])  
            )
            .first()
        )

        if not order:
            return jsonify({
                'error': 'Not a verified purchase',
                'message': 'No completed order found for this email and product.'
            }), 403

        # ✅ Valid — send verification email
        token = generate_verification_token(email, product_id)
        verification_url = url_for('main.verify_review_token', token=token, _external=True)

        msg = Message(
            subject="Verify Your Purchase",
            recipients=[email],
            html=get_verification_email(product, token, verification_url),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)

        current_app.logger.info(f"Sent verification email to {email} for product {product_id}")

        return jsonify({
            'success': True,
            'message': 'Verification email sent. Check your inbox.',
            'token': token 
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in verify_purchase: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500




@main_bp.route('/verify-review/<token>', methods=['GET'])
def verify_review_token(token):
    try:
        # Decode the token to extract email and product_id
        email, product_id = verify_verification_token(token)
        if not email or not product_id:
            flash('Invalid or expired verification link', 'error')
            return redirect(url_for('main.home'))

        # Check for existing unverified review
        review = Review.query.filter_by(
            product_id=product_id,
            author=email.split('@')[0],
            verified=False
        ).order_by(Review.id.desc()).first()

        if not review:
            flash('No pending review found for verification', 'error')
            return redirect(url_for('main.home'))

        # Mark the review as verified
        review.verified = True
        db.session.commit()

        # Optionally store in session (not required if using token in frontend)
        session['pending_review_id'] = review.id

        flash('Purchase verified! You can now submit your review.', 'success')

        # Redirect to review form page with token and product_id
        return redirect(url_for('main.review_form', product_id=product_id, token=token))

    except Exception as e:
        current_app.logger.error(f"Error verifying token: {str(e)}")
        flash('Verification failed. Please try again.', 'error')
        return redirect(url_for('main.home'))



@csrf.exempt
@main_bp.route('/submit-review', methods=['POST'])
def submit_review():
    try:
        if not request.is_json:
            return jsonify({'error': 'Invalid content type'}), 415

        data = request.get_json()
        token = data.get('token')
        rating = data.get('rating')
        comment = data.get('comment')

        if not token or not rating or not comment:
            return jsonify({'error': 'Missing required fields'}), 400

        # Verify the token and get email and product_id
        email, product_id = verify_verification_token(token)
        if not email or not product_id:
            return jsonify({'error': 'Invalid or expired token'}), 400

        # Find the verified review
        review = Review.query.filter_by(
            product_id=product_id,
            author=email.split('@')[0],
            verified=True
        ).order_by(Review.id.desc()).first()

        if not review:
            return jsonify({'error': 'Review not found or not verified'}), 404

        # Update the review
        review.rating = rating
        review.comment = comment
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Review submitted successfully!',
            'review': {
                'id': review.id,
                'author': review.author,
                'rating': review.rating,
                'comment': review.comment,
                'date': review.date.strftime('%B %d, %Y'),
                'verified': review.verified
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error submitting review: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500