"""Checkout at /checkout/: address choice, summary and placing the order."""

import re

from framework.money import rupees
from pages.base import BasePage


class CheckoutPage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self.addresses = page.get_by_test_id("address-option")
        self.default_address = self.addresses.filter(
            has=page.get_by_test_id("address-default-tag"))

        self.rows = page.get_by_test_id("checkout-row")
        self.item_name = page.get_by_test_id("checkout-item-name")
        self.item_variant = page.get_by_test_id("checkout-item-variant")
        self.item_qty = page.get_by_test_id("checkout-item-qty")
        self.item_total = page.get_by_test_id("checkout-item-total")

        self.items_total = page.get_by_test_id("summary-item-total")
        self.discount = page.get_by_test_id("summary-discount")
        self.delivery = page.get_by_test_id("summary-delivery")
        self.grand_total = page.get_by_test_id("summary-grand-total")
        self.place_order_button = page.get_by_test_id("place-order")

    def open(self, base_url):
        self.page.goto(f"{base_url}/checkout/")

    def address_text(self, option):
        return option.get_by_test_id("address-text")

    def delivery_charge(self):
        """Delivery as an integer; the page reads FREE above the threshold."""
        text = self.delivery.inner_text()
        return 0 if "FREE" in text.upper() else rupees(text)

    def place_order(self):
        """Place the order and return the number from the payment URL."""
        self.place_order_button.click()
        self.page.wait_for_url(re.compile(r"/pay/"))
        return self.page.url.rsplit("/", 1)[1]
