from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional
from wtforms import ValidationError
from .models import Brand, Category, RAMType, StorageType, ProcessorType, ProductVariety
from flask_wtf.file import FileField, FileAllowed

class BrandForm(FlaskForm):
    name = StringField('Brand Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Add Brand')

    def validate_name(self, name):
        brand = Brand.query.filter_by(name=name.data).first()
        if brand:
            raise ValidationError('This brand name is already in use. Please choose a different name.')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Add Category')

    def validate_name(self, name):
        category = Category.query.filter_by(name=name.data).first()
        if category:
            raise ValidationError('This category name is already in use. Please choose a different name.')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    
    # Display user-friendly labels for RAM options
    ram = SelectField('RAM', choices=[(ram.value, ram.value) for ram in RAMType], validators=[DataRequired()])
    
    # Display user-friendly labels for Processor options
    processor = SelectField('Processor', choices=[(proc.value, proc.value) for proc in ProcessorType], validators=[DataRequired()])
    
    # Display user-friendly labels for Storage Type options
    storage_type = SelectField('Storage Type', choices=[(st.value, st.value) for st in StorageType], validators=[DataRequired()])
    
    storage = StringField('Storage', validators=[DataRequired(), Length(max=50)])
    generation = StringField('Generation', validators=[DataRequired(), Length(max=50)])
    
    # Brand and Category should be populated from the database
    brand_id = SelectField('Brand', coerce=int, validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    
    submit = SubmitField('Add Product')


class ProductVarietyForm(FlaskForm):
    weight = StringField('Weight', validators=[Optional(), Length(max=50)])
    color = StringField('Color', validators=[Optional(), Length(max=50)])
    sku = StringField('SKU', validators=[DataRequired(), Length(max=100)])
    price = FloatField('Price', validators=[DataRequired()])
    quantity_in_stock = IntegerField('Quantity in Stock', validators=[DataRequired()])
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Product Variety')

    def validate_sku(self, sku):
        variety = ProductVariety.query.filter_by(sku=sku.data).first()
        if variety:
            raise ValidationError('This SKU is already in use. Please choose a different one.')

class ProductImageForm(FlaskForm):
    # Select the product to which images will be added
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    
    # File fields for multiple images
    image1 = FileField('Image 1', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    image2 = FileField('Image 2', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    image3 = FileField('Image 3', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    image4 = FileField('Image 4', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    
    submit = SubmitField('Add Images')
            