from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length

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
