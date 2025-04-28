from flask_mail import Message
from app import mail

def send_order_confirmation(email, order):
    msg = Message(
        "Order Confirmation",
        recipients=[email],
        body=f"Thank you for your order!\nTotal: ${order.total_amount:.2f}\nOrder ID: {order.id}"
    )
    mail.send(msg)
