from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask import jsonify
from app.admin.models import Product, Brand, Category, ContactMessage, Wishlist, ProductImage, Review
from app.main.forms import InquiryForm, ContactForm, WishlistForm, VerifyPurchaseForm,ReviewForm
from app.admin.forms import ProductForm
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
    categories        = Category.query.all()
    hot_products      = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    testimonials      = Review.query.filter_by(verified=True).order_by(Review.date.desc()).limit(3).all()
    featured_products = Product.query.filter_by(is_featured=True).order_by(Product.updated_at.desc()).limit(8).all()

    return render_template(
        'main/home.html',
        categories=categories,
        hot_products=hot_products,
        testimonials=testimonials,
        featured_products=featured_products
    )

# ---------------------------------------
# Product Routes
# ---------------------------------------

@main_bp.route('/products', methods=['GET'])
def list_products():
    # Get brand and category filters from query parameters
    brand_id = request.args.get('brand')
    category_id = request.args.get('category')

    query = Product.query

    # Apply brand filtering if specified
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)

    # Apply category filtering if specified
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.all()
    product_data = []

    # If no products are found, consider an empty list or alternative action
    if not products:
        flash("No products available at this moment.", "info")  # Inform the user

    for product in products:
        # If no image exists, provide the correct fallback image path
        first_image = product.images[0].image_path if product.images else 'default.jpg'

        product_data.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'brand_id': product.brand_id,
            'category_id': product.category_id,
            'image_url': first_image 
        })

    form = ProductForm()
    return render_template('main/list_products.html', products=product_data, form=form)

@main_bp.route('/products/<int:product_id>', methods=['GET'])
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    image_url = product.images[0].image_path if product.images else 'default.jpg'

    recent_reviews = Review.query.filter_by(product_id=product_id).order_by(Review.date.desc()).limit(5).all()
    total_reviews = Review.query.filter_by(product_id=product_id).count()

    form = InquiryForm()

    # Check if there's a verified review session for this product
    verified_review_id = session.pop('verified_review', None)
    show_review_modal = False
    review_to_edit = None

    if verified_review_id:
        review_to_edit = Review.query.get(verified_review_id)
        if review_to_edit and review_to_edit.product_id == product.id and not review_to_edit.verified:
            show_review_modal = True

    return render_template(
        'main/view_product.html',
        product=product,
        form=form,
        image_url=image_url,
        reviews=recent_reviews,
        total_reviews=total_reviews,
        show_review_modal=show_review_modal,
        verified_review=verified_review_id,
        review_to_edit=review_to_edit
    )



@main_bp.route('/category/', defaults={'category_slug': None}, strict_slashes=False)
@main_bp.route('/category/<string:category_slug>')
def products_by_category(category_slug):
    if not category_slug:
        # No slug provided → fallback to all products
        return redirect(url_for('main.list_products'))

    # Slug provided → fetch and display filtered products
    category = Category.query.filter_by(slug=category_slug).first_or_404()
    products = (
        Product.query
               .filter_by(category_id=category.id)
               .order_by(Product.created_at.desc())
               .all()
    )

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


@main_bp.route('/product/<int:product_id>/reviews')
def all_reviews(product_id):
    product = Product.query.get_or_404(product_id)
    all_reviews = Review.query.filter_by(product_id=product_id).order_by(Review.date.desc()).all()
    
    return render_template('main/all_reviews.html', product=product, reviews=all_reviews)


from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
import re

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
            return jsonify({'error': 'Missing required fields', 'message': 'Both email and product ID are required'}), 400

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'error': 'Invalid email format', 'message': 'Please provide a valid email address'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found', 'message': 'The specified product does not exist'}), 404

        # Create new unverified review
        review = Review(
            product_id=product_id,
            author=email.split('@')[0],
            rating=0,  # Temp placeholder
            comment='',  # Placeholder
            verified=False
        )
        db.session.add(review)
        db.session.commit()

        token = review.generate_verification_token()
        verification_url = url_for('main.verify_review_token', token=token, _external=True)

        msg = Message(
            subject="Verify Your Purchase",
            recipients=[email],
            html=get_verification_email(product, token, verification_url),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)

        current_app.logger.info(f"Verification email sent to {email} for product {product_id}")

        return jsonify({'success': True, 'message': 'Verification email sent! Please check your inbox.'}), 200

    except Exception as e:
        current_app.logger.error(f"Error in verify_purchase: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred.'}), 500



@main_bp.route('/verify-review/<token>', methods=['GET'])
def verify_review_token(token):
    review = Review.verify_token(token)
    
    if not review:
        flash('Invalid or expired verification link', 'error')
        return redirect(url_for('main.home'))

    review.verified = True
    db.session.commit()

    flash('Purchase verified! You can now submit your review.', 'success')
    
    # Redirect to the review form page
    return redirect(url_for('main.submit_review', review_id=review.id))




@main_bp.route('/submit-review/<int:review_id>', methods=['GET', 'POST'])
def submit_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if not review.verified:
        flash('You must verify your purchase before submitting a review.', 'error')
        return redirect(url_for('main.home'))

    form = ReviewForm()  # Make sure this form exists with `comment` and `rating` fields

    if form.validate_on_submit():
        review.rating = form.rating.data
        review.comment = form.comment.data
        db.session.commit()

        flash('Thanks for your review!', 'success')
        return redirect(url_for('main.home'))

    return render_template('partials/submit_review.html', form=form, product=review.product)
