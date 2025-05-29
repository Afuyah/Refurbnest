from app import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Enum, func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

from app.payment.crypto import decrypt_pan


import uuid
from enum import Enum


# ---------------------------------------
# Brand Model
# ---------------------------------------
class Brand(db.Model):
    __tablename__ = 'brands'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Name of the brand, unique and indexed for faster lookups
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Relationship with products: if a brand is deleted, all its products will be deleted too (cascade)
    products = relationship('Product', backref='brand', cascade='all, delete-orphan')
    
    # String representation of the model
    def __repr__(self):
        return f'<Brand {self.name}>'

# ---------------------------------------
# Category Model
# ---------------------------------------
from slugify import slugify  

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    slug = db.Column(db.String(100), nullable=False, unique=True, index=True)

    products = db.relationship('Product', backref='category', cascade='all, delete-orphan')

    def __init__(self, name):
        self.name = name
        self.slug = slugify(name)

    def __repr__(self):
        return f'<Category {self.name}>'

    

# Product Model
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)  # Optional
    price = db.Column(db.Float, nullable=False)

    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    sku = db.Column(db.String(50))

    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')
    specs = db.relationship('ProductSpec', backref='product', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Product {self.name}>'

# Flexible ProductSpec Model
class ProductSpec(db.Model):
    __tablename__ = 'product_specs'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "RAM", "Storage", "Battery"
    value = db.Column(db.String(200), nullable=False) # e.g., "8GB", "512GB SSD", "6000mAh"

    def __repr__(self):
        return f'<Spec {self.name}: {self.value}>'


# ---------------------------------------
# Enhanced Product Image Model
# ---------------------------------------
class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(500), nullable=False)  # Stores either URL or path
    is_primary = db.Column(db.Boolean, default=False, nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)  # For SEO accessibility

    

    def __repr__(self):
        return f'<ProductImage {self.id} for Product {self.product_id}>'

    @property
    def image_url(self):
        if self.image_path.startswith(('http://', 'https://')):
            return self.image_path
        return url_for('static', filename=f'uploads/{self.image_path}', _external=True)


# ---------------------------------------
# ProductVariety Model
# ---------------------------------------
class ProductVariety(db.Model):
    __tablename__ = 'product_varieties'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Specific fields for product variety (e.g., different colors, weight)
    weight = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    
    # SKU (Stock Keeping Unit), unique and indexed for fast lookups
    sku = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Price of the specific variety
    price = db.Column(db.Float, nullable=False)
    
    # Quantity in stock for this specific variety
    quantity_in_stock = db.Column(db.Integer, nullable=False)
    
    # Foreign key linking to the Product table
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    
    # String representation
    def __repr__(self):
        return f'<ProductVariety SKU: {self.sku}>'



# ---------------------------------------
# contact model
# ---------------------------------------

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContactMessage {self.subject} from {self.name}>"




class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)

    # Relationship to users
    users = db.relationship('User', back_populates='role', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to role
    role = db.relationship('Role', back_populates='users')
    orders = db.relationship('Order', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """Generate a hashed password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check the provided password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """Check if the user has a specific role."""
        return self.role.name == role_name

    def __repr__(self):
        return f'<User {self.username}>'


 # ---------------------------------------
# Wishlist Model
# ---------------------------------------
class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key linking to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Foreign key linking to the Product table
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('wishlists', lazy=True))
    product = db.relationship('Product', backref=db.backref('wishlists', lazy=True))
    
    # String representation
    def __repr__(self):
        return f'<Wishlist Item ID: {self.id}, Product ID: {self.product_id}>'       


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def generate_verification_token(self, salt='review-confirm-salt'):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({'review_id': self.id}, salt=salt)

    @staticmethod
    def verify_token(token, expiration=3600, salt='review-confirm-salt'):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, salt=salt, max_age=expiration)
            review_id = data.get('review_id')
            if review_id is None:
                return None
            return Review.query.get(review_id)
        except Exception as e:
            current_app.logger.error(f"Token verification failed: {e}")
            return None

    def __repr__(self):
        return f'<Review by {self.author} | Rating: {self.rating}>'
    
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    total = db.Column(db.Numeric(10,2), nullable=False)
    subtotal = db.Column(db.Numeric(10,2), nullable=False)
    tax = db.Column(db.Numeric(10,2), default=0.00)
    shipping_cost = db.Column(db.Numeric(10,2), default=0.00)
    payment_status = db.Column(db.String(20), default='Pending')
    payment_method = db.Column(db.String(20), nullable=True)
    payment_token = db.Column(db.String(256), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', back_populates='orders')
    shipping_address = db.relationship('ShippingAddress', backref='order', uselist=False, cascade='all, delete-orphan')
    payment_method_record = db.relationship('PaymentMethod',back_populates='order', uselist=False,cascade='all, delete-orphan', foreign_keys='PaymentMethod.order_id')

    def generate_payment_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        self.payment_token = s.dumps({
            'order_id': self.id,
            'ts': time.time()
        }, salt='payment-token')


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10,2), nullable=False)  # Price at time of purchase
    
    # Product details snapshot
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    
    product = db.relationship('Product')
    


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'  # Changed to plural for consistency
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(20), nullable=False)
    last4 = db.Column(db.String(4), nullable=False)
    exp_month = db.Column(db.Integer, nullable=False)
    exp_year = db.Column(db.Integer, nullable=False)
    token = db.Column(db.String(64), nullable=False)
    enc_pan = db.Column(db.LargeBinary, nullable=False)
    pan_nonce = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    key_version = db.Column(db.String(20), nullable=True)
    masked_pan = db.Column(db.String(32), nullable=True)

    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    order    = db.relationship('Order', back_populates='payment_method_record', uselist=False)

  


    def get_full_pan(self) -> str:
        return decrypt_pan(self.pan_nonce, self.enc_pan)

    def get_masked_pan(self) -> str:
        full = self.get_full_pan()
        return f"{full[:6]}{'*'*(len(full)-10)}{full[-4:]}"


class ShippingAddress(db.Model):
    __tablename__ = 'shipping_addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Contact Info
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Address Details
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    
    # Shipping Method
    shipping_method = db.Column(db.String(50), nullable=False)
    delivery_instructions = db.Column(db.Text)

class PaymentEvent(db.Model):
    __tablename__ = 'payment_events'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False)  # Paid/Failed/Refunded etc.
    amount = db.Column(db.Numeric(10,2), nullable=False)
    processor = db.Column(db.String(20), nullable=False)  # stripe/mpesa/etc
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    error_code = db.Column(db.String(50))
    ip_address = db.Column(db.String(45))

    # Relationship
    order = db.relationship('Order', backref='payment_events')