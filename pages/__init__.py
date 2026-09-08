"""Page objects: one class per page, so tests name what they use."""

from pages.auth import LoginPage, RegisterPage
from pages.cart import CartPage
from pages.checkout import CheckoutPage
from pages.home import HomePage, ProductCard
from pages.orders import OrderPage, OrdersPage
from pages.payment import PaymentPage
from pages.product import ProductPage

__all__ = [
    "CartPage",
    "CheckoutPage",
    "HomePage",
    "LoginPage",
    "OrderPage",
    "OrdersPage",
    "PaymentPage",
    "ProductCard",
    "ProductPage",
    "RegisterPage",
]
