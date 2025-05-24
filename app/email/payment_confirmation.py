from flask_mail import Message
from app import mail 

def send_payment_confirmation_email(order):
    msg = Message(
        subject="Payment Confirmation",
        recipients=[order.user.email if order.user else "support@example.com"],
        body=f"Hello {order.name},\n\nYour payment for Order #{order.id} was successful.\n\nThank you!",
    )
    mail.send(msg)
