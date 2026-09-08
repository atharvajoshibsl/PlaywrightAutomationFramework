"""The catalogue: search, category chips, sort, product cards and footer."""

import re

from framework.money import rupees
from pages.base import BasePage


class ProductCard:
    """One card in the listing."""

    def __init__(self, root):
        self.root = root
        self.name = root.get_by_test_id("product-name")
        self.brand = root.get_by_test_id("product-brand")
        self.price = root.get_by_test_id("product-price")
        self.rating = root.get_by_test_id("product-rating")
        self.stock = root.get_by_test_id("product-stock")
        self.link = root.locator("a").first

        # No test id on the image yet, so this one goes by class.
        self.image = root.locator(".card-image .emoji")

    def named(self):
        return self.name.inner_text().strip()

    def priced(self):
        return self.price.inner_text().strip()


class HomePage(BasePage):
    """The product listing at /."""

    def __init__(self, page):
        super().__init__(page)
        self.heading = page.get_by_test_id("page-title")
        self.result_count = page.get_by_test_id("result-count")
        self.cards = page.get_by_test_id("product-card")
        self.names = page.get_by_test_id("product-name")
        self.prices = page.get_by_test_id("product-price")
        self.chips = page.get_by_test_id("category-filters").locator("a")
        self.sort_select = page.get_by_test_id("sort-select")
        self.no_results = page.get_by_test_id("no-results")

        # Only rendered while a search is active.
        self.search_clear = page.get_by_test_id("search-clear")

        # Footer.
        self.footer_brand = page.get_by_test_id("footer-brand")
        self.footer_purpose = page.get_by_test_id("footer-purpose")
        self.footer_frameworks = (page.get_by_test_id("footer-frameworks")
                                  .locator("li"))
        self.footer_note = page.get_by_test_id("footer-note")
        self.footer_copyright = page.get_by_test_id("footer-copyright")

    def open(self, base_url):
        self.page.goto(base_url)

    def card(self, name):
        """The card for one product name."""
        return ProductCard(self.cards.filter(has_text=name))

    def first_card(self):
        return ProductCard(self.cards.first)

    def chip(self, slug):
        return self.page.get_by_test_id(f"category-{slug}")

    def search(self, term):
        self.search_input.fill(term)
        self.search_submit.click()
        self.page.wait_for_url(re.compile(f"q={term}"))

    def clear_search(self):
        self.search_clear.click()
        self.page.wait_for_url(lambda url: "q=" not in url)

    def open_category(self, slug):
        self.chip(slug).click()
        self.page.wait_for_url(re.compile(f"category={slug}"))

    def sort_by(self, value):
        """Pick a sort option; the form navigates on change."""
        self.sort_select.select_option(value)
        self.page.wait_for_url(re.compile(f"sort={value}"))

    def open_product(self, slug):
        self.page.get_by_test_id(f"product-link-{slug}").click()
        self.page.wait_for_url(re.compile(f"/product/{slug}"))

    def prices_shown(self):
        """Prices as integers, in display order."""
        return [rupees(text) for text in self.prices.all_text_contents()]
