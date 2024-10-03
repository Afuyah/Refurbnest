from flask import Blueprint, render_template, redirect, url_for, flash,current_app as app
from app import db
from app.auth.routes import roles_required
from app.admin.forms import BrandForm, CategoryForm, ProductForm, ProductVarietyForm,ProductImageForm
from app.admin.models import Brand, Category, Product, ProductImage, ProductVariety
from flask_login import login_required
import os

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

@admin_bp.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.all()]
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            storage=form.storage.data,
            ram=form.ram.data,
            processor=form.processor.data,
            storage_type=form.storage_type.data,
            generation=form.generation.data,
            brand_id=form.brand_id.data,
            category_id=form.category_id.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.list_products'))

    return render_template('admin/add_product.html', form=form)

@admin_bp.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.all()]
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.storage = form.storage.data
        product.ram = form.ram.data
        product.processor = form.processor.data
        product.storage_type = form.storage_type.data
        product.generation = form.generation.data
        product.brand_id = form.brand_id.data
        product.category_id = form.category_id.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.list_products'))

    return render_template('admin/edit_product.html', form=form)


@admin_bp.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    
    if product:
        try:
            print(f'Attempting to delete product: {product.name}')
            print(f'Associated images before deletion: {[image.id for image in product.images]}')

            db.session.delete(product)  # This should cascade delete associated images
            db.session.commit()
            flash('Product deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting product: ' + str(e), 'error')
            print(f'Delete error: {e}')
    else:
        flash('Product not found.', 'error')

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


@admin_bp.route('admin/add_product_images', methods=['GET', 'POST'])
def add_product_images():
    form = ProductImageForm()

    # Populate product options dynamically from the database
    form.product_id.choices = [(product.id, product.name) for product in Product.query.all()]

    if form.validate_on_submit():
        # Create a folder if it doesn't exist
        product_images_path = os.path.join(app.root_path, 'static/products')
        if not os.path.exists(product_images_path):
            os.makedirs(product_images_path)

        # Save the images and associate them with the product
        product_id = form.product_id.data
        for image_field in [form.image1, form.image2, form.image3, form.image4]:
            if image_field.data:
                filename = secure_filename(image_field.data.filename)
                image_path = os.path.join(product_images_path, filename)
                image_field.data.save(image_path)

                # Save image path in the database
                product_image = ProductImage(
                    image_path=f'products/{filename}',
                    product_id=product_id
                )
                db.session.add(product_image)

        db.session.commit()

        flash('Images added successfully!', 'success')
        return redirect(url_for('admin.add_product_images'))

    return render_template('admin/add_product_images.html', form=form)