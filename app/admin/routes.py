from flask import Blueprint, render_template, redirect, url_for, flash,current_app as app
from app import db
from app.auth.routes import roles_required
from app.admin.forms import BrandForm, CategoryForm, ProductForm, ProductVarietyForm,ProductImageForm
from app.admin.models import Brand, Category, Product, ProductImage, ProductVariety
from flask_login import login_required
import os
from slugify import slugify

from werkzeug.utils import secure_filename

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__)

# ---------------------------------------
# Brand Routes
# ---------------------------------------

@admin_bp.route('/admin/brands', methods=['GET'])
def list_brands():
    brands = Brand.query.all()
    return render_template('admin/list_brands.html', brands=brands)

@admin_bp.route('/admin/add_brand', methods=['GET', 'POST'])
def add_brand():
    form = BrandForm()
    if form.validate_on_submit():
        brand = Brand(name=form.name.data)
        db.session.add(brand)
        db.session.commit()
        flash('Brand added successfully!', 'success')
        return redirect(url_for('admin.list_brands'))
    return render_template('admin/add_brand.html', form=form)

@admin_bp.route('/admin/edit_brand/<int:brand_id>', methods=['GET', 'POST'])
def edit_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    form = BrandForm(obj=brand)
    if form.validate_on_submit():
        brand.name = form.name.data
        db.session.commit()
        flash('Brand updated successfully!', 'success')
        return redirect(url_for('admin.list_brands'))
    return render_template('admin/edit_brand.html', form=form)

@admin_bp.route('/admin/delete_brand/<int:brand_id>', methods=['POST'])
def delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    db.session.delete(brand)
    db.session.commit()
    flash('Brand deleted successfully!', 'success')
    return redirect(url_for('admin.list_brands'))

# ---------------------------------------
# Category Routes
# ---------------------------------------

@admin_bp.route('/admin/categories', methods=['GET'])
def list_categories():
    form= CategoryForm()
    categories = Category.query.all()
    return render_template('admin/list_categories.html', categories=categories, form=form)

@admin_bp.route('/admin/add_category', methods=['GET', 'POST'])
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin.list_categories'))
    return render_template('admin/add_category.html', form=form)

@admin_bp.route('/admin/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.list_categories'))
    return render_template('admin/add_category.html', form=form)

@admin_bp.route('/admin/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):

    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.list_categories'))

# ---------------------------------------
# Product Routes
# ---------------------------------------

@admin_bp.route('/admin/products', methods=['GET'])
def list_products():
    form= ProductForm()
    products = Product.query.all()
    return render_template('admin/list_products.html', products=products, form=form)

from flask import request, jsonify, render_template
from sqlalchemy.exc import SQLAlchemyError

@admin_bp.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.order_by(Brand.name).all()]
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    if request.method == 'POST':
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return jsonify(success=False, message='Invalid request type.')

        # Collect and clean input data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        brand_id = request.form.get('brand_id')
        category_id = request.form.get('category_id')

        specs_names = request.form.getlist('spec_name')
        specs_values = request.form.getlist('spec_value')
        filled_specs = [
            (n.strip(), v.strip())
            for n, v in zip(specs_names, specs_values)
            if n.strip() and v.strip()
        ]

        # Basic validation
        if not name or not price or not brand_id or not category_id:
            return jsonify(success=False, message='All required fields must be filled.')

        if not (2 <= len(filled_specs) <= 10):
            return jsonify(success=False, message='Provide between 2 and 10 valid specifications.')

        try:
            price_val = float(price)
        except ValueError:
            return jsonify(success=False, message='Invalid price format. Use numbers only.')

        # Save product and specs to database
        try:
            product = Product(
                name=name,
                description=description,
                price=price_val,
                brand_id=brand_id,
                category_id=category_id
            )
            db.session.add(product)
            db.session.flush()  # Get product.id before committing

            for spec_name, spec_value in filled_specs:
                spec = ProductSpec(
                    name=spec_name,
                    value=spec_value,
                    product_id=product.id
                )
                db.session.add(spec)

            db.session.commit()
            return jsonify(success=True, message='Product added successfully.')

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify(success=False, message=f'An error occurred: {str(e)}')

    return render_template('admin/add_product.html', form=form)

@admin_bp.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.all()]
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = request.form.get('price')
        product.brand_id = request.form.get('brand_id')
        product.category_id = request.form.get('category_id')

        specs_names = request.form.getlist('spec_name')
        specs_values = request.form.getlist('spec_value')

        if len(specs_names) < 2 or len(specs_names) > 10:
            flash('You must provide at least 2 and at most 10 specifications.', 'danger')
            return render_template('admin/edit_product.html', form=form, specs=product.specs)

        try:
            # Remove old specs
            ProductSpec.query.filter_by(product_id=product.id).delete()

            # Add new specs
            for name, value in zip(specs_names, specs_values):
                if name.strip() and value.strip():
                    spec = ProductSpec(name=name.strip(), value=value.strip(), product_id=product.id)
                    db.session.add(spec)

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.list_products'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')

    return render_template('admin/edit_product.html', form=form, specs=product.specs)


@admin_bp.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{product.name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
        current_app.logger.error(f'Delete error for product ID {product_id}: {e}')
    
    return redirect(url_for('admin.list_products'))



@admin_bp.route('/products/<int:product_id>/<action>', methods=['POST'])
def toggle_featured(product_id, action):
    product = Product.query.get_or_404(product_id)
    if action == 'feature':
        product.is_featured = True
    elif action == 'unfeature':
        product.is_featured = False
    else:
        flash('Invalid action.', 'error')
        return redirect(url_for('admin.list_products'))

    db.session.commit()
    flash(f'Product {action}d successfully.', 'success')
    return redirect(url_for('admin.list_products'))




# ---------------------------------------
# Product Variety Routes
# ---------------------------------------

@admin_bp.route('/admin/product_varieties', methods=['GET'])
def list_product_varieties():
    varieties = ProductVariety.query.all()
    return render_template('admin/list_varieties.html', varieties=varieties)

@admin_bp.route('/admin/add_variety', methods=['GET', 'POST'])
def add_variety():
    form = ProductVarietyForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]

    if form.validate_on_submit():
        variety = ProductVariety(
            weight=form.weight.data,
            color=form.color.data,
            sku=form.sku.data,
            price=form.price.data,
            quantity_in_stock=form.quantity_in_stock.data,
            product_id=form.product_id.data
        )
        db.session.add(variety)
        db.session.commit()
        flash('Product variety added successfully!', 'success')
        return redirect(url_for('admin.list_product_varieties'))

    return render_template('admin/add_variety.html', form=form)

@admin_bp.route('/admin/edit_variety/<int:variety_id>', methods=['GET', 'POST'])
def edit_variety(variety_id):
    variety = ProductVariety.query.get_or_404(variety_id)
    form = ProductVarietyForm(obj=variety)
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]

    if form.validate_on_submit():
        variety.weight = form.weight.data
        variety.color = form.color.data
        variety.sku = form.sku.data
        variety.price = form.price.data
        variety.quantity_in_stock = form.quantity_in_stock.data
        variety.product_id = form.product_id.data
        db.session.commit()
        flash('Product variety updated successfully!', 'success')
        return redirect(url_for('admin.list_product_varieties'))

    return render_template('admin/edit_variety.html', form=form, variety=variety)

@admin_bp.route('/admin/delete_variety/<int:variety_id>', methods=['POST'])
def delete_variety(variety_id):
    variety = ProductVariety.query.get_or_404(variety_id)
    db.session.delete(variety)
    db.session.commit()
    flash('Product variety deleted successfully!', 'success')
    return redirect(url_for('admin.list_product_varieties'))


@admin_bp.route('/admin/dashboard', methods=['GET'])
def dashboard():
    brand_count = Brand.query.count()
    category_count = Category.query.count()
    product_count = Product.query.count()
    variety_count = ProductVariety.query.count()
    return render_template('admin/dashboard.html', 
                           brand_count=brand_count, 
                           category_count=category_count, 
                           product_count=product_count, 
                           variety_count=variety_count)


import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# ---------------------------------------
# Enhanced Upload Route with Cloud Storage Option
# ---------------------------------------
def generate_image_filename(product, original_filename):
    """Generate SEO-friendly unique filename"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    name_slug = slugify(product.name)[:30]
    ext = os.path.splitext(original_filename)[1].lower()
    return f"{name_slug}-{timestamp}-{unique_id}{ext}"

@admin_bp.route('/add_product_images', methods=['GET', 'POST'])
def add_product_images():
    form = ProductImageForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.order_by(Product.name).all()]

    if form.validate_on_submit():
        product = Product.query.get_or_404(form.product_id.data)
        
        try:
            for idx, field in enumerate([form.image1, form.image2, form.image3, form.image4]):
                if field.data:
                    filename = generate_image_filename(product, field.data.filename)
                    secure_name = secure_filename(filename)
                    
                    # Local storage option
                    upload_dir = app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_dir, exist_ok=True)
                    filepath = os.path.join(upload_dir, secure_name)
                    field.data.save(filepath)
                    
                    # For cloud storage (example using AWS S3):
                    # s3.upload_fileobj(field.data, 'your-bucket', f"products/{secure_name}")
                    
                    # Create image record
                    img = ProductImage(
                        image_path=secure_name,  # or f"https://your-bucket.s3.amazonaws.com/products/{secure_name}"
                        product_id=product.id,
                        is_primary=(idx == 0),  # First image is primary
                        alt_text=f"{product.name} product image {idx + 1}"
                    )
                    db.session.add(img)
            
            db.session.commit()
            flash('Product images uploaded successfully!', 'success')
            return redirect(url_for('admin.product_list'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Image upload failed: {str(e)}")
            flash('Error uploading images. Please try again.', 'danger')

    return render_template('admin/add_product_images.html', form=form)