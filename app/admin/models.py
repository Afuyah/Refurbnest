from app import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Enum, func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from enum import Enum

# Enum for RAM size options
class RAMType(Enum):
    RAM_2GB = "RAM_2GB"
    RAM_4GB = "RAM_4GB"
    RAM_8GB = "RAM_8GB"
    RAM_16GB = "RAM_16GB"
    RAM_32GB = "RAM_32GB"

# Enum for types of storage
class StorageType(Enum):
    HDD = "HDD"
    SSD = "SSD"

# Enum for types of processors
class ProcessorType(Enum):
    Intel_Core_i3 = "Intel_Core_i3"
    Intel_Core_i5 = "Intel_Core_i5"
    Intel_Core_i7 = "Intel_Core_i7"
    Intel_Core_i9 = "Intel_Core_i9"



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
class Category(db.Model):
    __tablename__ = 'categories'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Name of the category, unique and indexed
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Relationship with products: if a category is deleted, all its products will be deleted (cascade)
    products = relationship('Product', backref='category', cascade='all, delete-orphan')
    
    # String representation of the model
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    storage = db.Column(db.String(50), nullable=False)
    ram = db.Column(db.Enum(RAMType), nullable=False)
    processor = db.Column(db.Enum(ProcessorType), nullable=False)
    storage_type = db.Column(db.Enum(StorageType), nullable=False)
    generation = db.Column(db.String(50), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # This backref will handle the relationship
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(500), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # No explicit 'product' relationship needed, as the backref in Product handles it
    def __repr__(self):
        return f'<ProductImage {self.image_path}>'


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


