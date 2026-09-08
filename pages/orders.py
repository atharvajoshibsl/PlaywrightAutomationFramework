"""Order history at /orders/ and one order at /orders/<number>."""

from pages.base import BasePage


class OrdersPage(BasePage):
    """The history list."""

    def __init__(self, page):
        super().__init__(page)
        self.rows = page.get_by_test_id("order-row")
        self.numbers = page.get_by_test_id("order-number")
        self.payment_status = page.get_by_test_id("order-payment-status")
        self.empty_message = page.get_by_test_id("no-orders")

    def open(self, base_url):
        self.page.goto(f"{base_url}/orders/")


class OrderPage(BasePage):
    """One order."""

    def __init__(self, page):
        super().__init__(page)
        self.status = page.get_by_test_id("order-status")
        self.payment_status = page.get_by_test_id("payment-status")
        self.payment_reference = page.get_by_test_id("payment-ref")

    def open(self, base_url, number):
        self.page.goto(f"{base_url}/orders/{number}")
