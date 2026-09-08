"""The product detail page at /product/<slug>."""

import re

from pages.base import BasePage

# Option labels read "Standard / Default - 5 left" while stock remains.
IN_STOCK = "left"


class ProductPage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self.breadcrumbs = page.get_by_test_id("breadcrumbs")
        self.name = page.get_by_test_id("detail-name")
        self.price = page.get_by_test_id("detail-price")
        self.brand = page.get_by_test_id("detail-brand")
        self.sku = page.get_by_test_id("detail-sku")
        self.rating = page.get_by_test_id("detail-rating")
        self.description = page.get_by_test_id("detail-description")
        self.variant_select = page.get_by_test_id("variant-select")
        self.variant_rows = page.get_by_test_id("variant-row")
        self.qty_input = page.get_by_test_id("qty-input")
        self.add_button = page.get_by_test_id("add-to-cart")

    def open(self, base_url, slug):
        self.page.goto(f"{base_url}/product/{slug}")

    def variant_with_stock(self):
        """Index and tidied label of the first variant that still has stock."""
        labels = self.variant_select.locator("option").all_text_contents()
        for index, label in enumerate(labels):
            if IN_STOCK in label:
                return index, " ".join(label.split())
        return None, None

    def choose_variant(self, index):
        self.variant_select.select_option(index=index)

    def add_to_cart(self):
        """Add the selected variant; the app lands on the cart."""
        self.add_button.click()
        self.page.wait_for_url(re.compile("/cart/"))
