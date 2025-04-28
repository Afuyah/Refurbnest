from flask import session
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional


class CartError(Exception):
    """Custom exception for cart operations."""
    pass


class CartItem:
    __slots__ = ('product_id', 'name', 'price', 'quantity')

    def __init__(self, product_id: str, name: str, price: Decimal, quantity: int) -> None:
        self.product_id = product_id
        self.name = name
        self.price = price
        self.quantity = quantity

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'price': float(self.price),
            'quantity': self.quantity
        }


class Cart:
    SESSION_KEY = 'cart'
    MAX_QUANTITY = 100

    def __init__(self) -> None:
        # Load or initialize the cart once per request
        raw: Dict[str, Any] = session.get(self.SESSION_KEY, {})
        self._items: Dict[str, CartItem] = {}
        for pid, data in raw.items():
            try:
                price = Decimal(str(data['price'])).quantize(Decimal('0.00'))
                qty   = int(data['quantity'])
                if price <= 0 or qty < 0:
                    raise ValueError
                self._items[pid] = CartItem(pid, str(data['name']), price, qty)
            except (KeyError, TypeError, ValueError, InvalidOperation):
                # skip invalid entries
                continue

    def _save(self) -> None:
        """Persist current cart back into the session in one shot."""
        session[self.SESSION_KEY] = {
            pid: item.to_dict() for pid, item in self._items.items()
        }
        session.modified = True

    def add(self, product_id: int, name: str, price: float, quantity: int = 1) -> None:
        """Add or increment an item in the cart, with full validation."""
        pid = str(product_id)
        name = name.strip()
        if not name:
            raise CartError("Product name cannot be empty")
        if quantity < 1:
            raise CartError("Quantity must be at least 1")
        try:
            price_dec = Decimal(str(price)).quantize(Decimal('0.00'))
        except InvalidOperation:
            raise CartError("Invalid price format")
        if price_dec <= 0:
            raise CartError("Price must be positive")

        item = self._items.get(pid)
        if item:
            new_qty = item.quantity + quantity
            if new_qty > self.MAX_QUANTITY:
                raise CartError(f"Cannot have more than {self.MAX_QUANTITY} of a single item")
            item.quantity = new_qty
        else:
            if quantity > self.MAX_QUANTITY:
                raise CartError(f"Cannot add more than {self.MAX_QUANTITY} at once")
            self._items[pid] = CartItem(pid, name, price_dec, quantity)

        self._save()

    def remove(self, product_id: int) -> None:
        """Remove an item entirely from the cart."""
        pid = str(product_id)
        if pid in self._items:
            del self._items[pid]
            self._save()

    def update_quantity(self, product_id: int, quantity: int) -> None:
        """Set a specific quantity; zero means remove."""
        pid = str(product_id)
        if quantity < 0:
            raise CartError("Quantity cannot be negative")
        if pid not in self._items:
            return  # nothing to do

        if quantity == 0:
            del self._items[pid]
        else:
            if quantity > self.MAX_QUANTITY:
                raise CartError(f"Cannot exceed {self.MAX_QUANTITY} units")
            self._items[pid].quantity = quantity

        self._save()

    def clear(self) -> None:
        """Empty the cart."""
        if self._items:
            session.pop(self.SESSION_KEY, None)
            session.modified = True
            self._items.clear()

    def get_items(self) -> Dict[str, Dict[str, Any]]:
        """Return raw dict for JSON serialization."""
        return {pid: item.to_dict() for pid, item in self._items.items()}

    @property
    def unique_items(self) -> int:
        """Count of distinct products."""
        return len(self._items)

    @property
    def item_count(self) -> int:
        """Sum of all quantities."""
        return sum(item.quantity for item in self._items.values())

    @property
    def total(self) -> Decimal:
        """Total price, with two-decimal precision."""
        total = sum((item.price * item.quantity for item in self._items.values()), Decimal('0'))
        return total.quantize(Decimal('0.00'))
