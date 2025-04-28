from flask import session
from decimal import Decimal
from typing import Dict, Any

class Cart:
    @staticmethod
    def add(product_id: int, name: str, price: float, quantity: int = 1) -> None:
        """Add or update a product in the cart with validation."""
        try:
            product_id = str(product_id)
            if quantity < 1:
                raise ValueError("Quantity must be at least 1")
            
            price_decimal = Decimal(str(price)).quantize(Decimal('0.00'))
            if price_decimal <= Decimal('0'):
                raise ValueError("Price must be positive")

            cart = session.get('cart', {})
            existing_item = cart.get(product_id)

            if existing_item:
                new_quantity = existing_item['quantity'] + quantity
                if new_quantity > 100:  # Prevent unreasonable quantities
                    raise ValueError("Maximum quantity exceeded")
                existing_item['quantity'] = new_quantity
            else:
                cart[product_id] = {
                    'name': name.strip(),
                    'price': float(price_decimal),
                    'quantity': quantity
                }

            session['cart'] = cart
            session.modified = True

        except (ValueError, TypeError) as e:
            raise CartError(f"Invalid cart operation: {str(e)}") from e

    @staticmethod
    def remove(product_id: int) -> None:
        """Remove a product from the cart completely."""
        product_id = str(product_id)
        cart = session.get('cart', {})
        if product_id in cart:
            del cart[product_id]
            session['cart'] = cart
            session.modified = True

    @staticmethod
    def update_quantity(product_id: int, quantity: int) -> None:
        """Update quantity of a specific cart item."""
        product_id = str(product_id)
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
            
        cart = session.get('cart', {})
        if product_id in cart:
            if quantity == 0:
                del cart[product_id]
            else:
                cart[product_id]['quantity'] = quantity
            session['cart'] = cart
            session.modified = True

    @staticmethod
    def clear() -> None:
        """Completely empty the cart."""
        if 'cart' in session:
            session.pop('cart')
            session.modified = True

    @staticmethod
    def get_cart() -> Dict[str, Dict[str, Any]]:
        """Get validated cart contents with consistent structure."""
        cart = session.get('cart', {})
        validated = {}
        
        for pid, item in cart.items():
            try:
                validated[pid] = {
                    'name': str(item['name']),
                    'price': float(item['price']),
                    'quantity': int(item['quantity'])
                }
            except (KeyError, TypeError, ValueError):
                continue  # Skip invalid items
                
        return validated

    @staticmethod
    def item_count() -> int:
        """Get total number of items in cart (sum of quantities)."""
        return sum(item['quantity'] for item in Cart.get_cart().values())

    @staticmethod
    def unique_items() -> int:
        """Get count of distinct products in cart."""
        return len(Cart.get_cart())

    @staticmethod
    def get_total() -> Decimal:
        """Calculate total with precise decimal arithmetic."""
        total = Decimal('0')
        for item in Cart.get_cart().values():
            price = Decimal(str(item['price']))
            quantity = Decimal(str(item['quantity']))
            total += price * quantity
        return total.quantize(Decimal('0.00'))

class CartError(Exception):
    """Custom exception for cart operations"""
    pass