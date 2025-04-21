
def get_verification_email(product, token, verification_url):
    return f"""
    <html>
        <body>
            <h2>Verify Your Purchase of {product.name}</h2>
            <p>Click the link below to verify your purchase and leave a review:</p>
            <a href="{verification_url}">
                Verify Purchase
            </a>
            <p>This link will expire in 1 hour.</p>
        </body>
    </html>
    """
