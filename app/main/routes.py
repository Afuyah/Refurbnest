from flask import Blueprint, render_template, redirect, url_for, flash
from app.admin.models import Product, Brand, Category, ContactMessage, Wishlist, ProductImage
from app.main.forms import InquiryForm, ContactForm, WishlistForm
from app.admin.forms import ProductForm
from functools import wraps
from app import db
from flask import current_app
from flask_login import login_required, login_user, logout_user, current_user
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


@main_bp.route('/')
def home():
    return render_template('main/home.html')

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

    form = InquiryForm()
    return render_template('main/view_product.html', product=product, form=form,image_url=image_url)

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

       
        your_whatsapp_number = "254700622298"  
        whatsapp_url = f"https://wa.me/{your_whatsapp_number}?text={encoded_message}"

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
