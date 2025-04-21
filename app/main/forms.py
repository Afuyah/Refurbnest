from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email, Length
from wtforms.validators import DataRequired, NumberRange

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=100)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Send Message')
class InquiryForm(FlaskForm):
    contact = StringField('Your Contact Info', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Inquire')


class WishlistForm(FlaskForm):
    product_id = HiddenField('Product ID', validators=[DataRequired()])


class VerifyPurchaseForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    product_id = HiddenField('Product ID', validators=[DataRequired()])



    
class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5 Stars)', validators=[
        DataRequired(),
        NumberRange(min=1, max=5, message="Rating must be between 1 and 5")
    ])
    comment = TextAreaField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit Review')
