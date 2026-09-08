"""What every page shares: the header, flash messages and screenshots.

Page objects hold locators and actions. Checks stay in the tests.
"""

import re

import allure


class BasePage:
    """Header and flash locators, available on every page object."""

    def __init__(self, page):
        self.page = page

        # Header.
        self.brand = page.get_by_test_id("nav-brand")
        self.tagline = page.get_by_test_id("tagline")
        self.search_input = page.get_by_test_id("search-input")
        self.search_submit = page.get_by_test_id("search-submit")
        self.theme_toggle = page.get_by_test_id("theme-toggle")
        self.cart_link = page.get_by_test_id("nav-cart")
        self.cart_count = page.get_by_test_id("cart-count")
        self.login_link = page.get_by_test_id("nav-login")
        self.register_link = page.get_by_test_id("nav-register")
        self.logout_link = page.get_by_test_id("nav-logout")
        self.profile_link = page.get_by_test_id("nav-profile")
        self.orders_link = page.get_by_test_id("nav-orders")
        self.wallet = page.get_by_test_id("nav-wallet")
        self.wallet_balance = page.get_by_test_id("nav-wallet-balance")

        # Flash messages, shown once after an action.
        self.success = page.get_by_test_id("flash-success")
        self.error = page.get_by_test_id("flash-error")

    @property
    def url(self):
        return self.page.url

    def items_in_cart(self):
        """The number in the header cart badge."""
        return int(self.cart_count.inner_text())

    def open_cart(self):
        self.cart_link.click()
        self.page.wait_for_url(re.compile("/cart/"))

    def open_orders(self):
        self.orders_link.click()
        self.page.wait_for_url(re.compile("/orders/"))

    def sign_out(self):
        self.logout_link.click()
        self.login_link.wait_for()

    def capture(self, name, full_page=True):
        """Attach a screenshot to the Allure step that is open."""
        allure.attach(
            self.page.screenshot(full_page=full_page, type="jpeg", quality=70),
            name=name, attachment_type=allure.attachment_type.JPG)
