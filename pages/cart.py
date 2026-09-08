"""The cart at /cart/: lines, the summary, and the controls on them."""

import re

from framework.money import rupees
from pages.base import BasePage


class CartPage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self.rows = page.get_by_test_id("cart-row")
        self.item_name = page.get_by_test_id("cart-item-name")
        self.item_variant = page.get_by_test_id("cart-item-variant")
        self.item_price = page.get_by_test_id("cart-item-price")
        self.item_qty = page.get_by_test_id("cart-item-qty")
        self.item_total = page.get_by_test_id("cart-item-total")
        self.qty_hint = page.get_by_test_id("cart-qty-hint")
        self.update_button = page.get_by_test_id("cart-item-update")
        self.clear_button = page.get_by_test_id("clear-cart")
        self.checkout_button = page.get_by_test_id("checkout")

        # Summary and empty state; each replaces the other.
        self.summary = page.get_by_test_id("cart-summary")
        self.summary_count = page.get_by_test_id("summary-count")
        self.subtotal = page.get_by_test_id("summary-item-total")
        self.empty_message = page.get_by_test_id("empty-cart")
        self.continue_shopping = page.get_by_test_id("continue-shopping")

    def open(self, base_url):
        self.page.goto(f"{base_url}/cart/")

    def unit_price(self):
        return rupees(self.item_price.inner_text())

    def line_totals(self):
        return [rupees(text) for text in self.item_total.all_text_contents()]

    def lines(self):
        """Names, quantities and line totals, in display order."""
        return {
            "names": self.item_name.all_text_contents(),
            "quantities": [box.input_value() for box in self.item_qty.all()],
            "totals": self.item_total.all_text_contents(),
        }

    def type_quantity(self, quantity):
        """Type a quantity without submitting it."""
        self.item_qty.fill(str(quantity))

    def update(self):
        self.update_button.click()
        self.page.wait_for_url(re.compile("/cart/"))

    def clear(self):
        self.clear_button.click()
        self.page.wait_for_url(re.compile("/cart/"))

    def checkout(self):
        self.checkout_button.click()
        self.page.wait_for_url(re.compile("/checkout/"))
