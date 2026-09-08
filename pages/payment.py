"""The payment page at /pay/<order>."""

from framework import config
from pages.base import BasePage


class PaymentPage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self.order_number = page.get_by_test_id("payment-order-number")
        self.grand_total = page.get_by_test_id("payment-grand-total")
        self.card_panel = page.get_by_test_id("panel-card")
        self.card_number = page.get_by_test_id("card-number")
        self.card_name = page.get_by_test_id("card-name")
        self.card_expiry = page.get_by_test_id("card-expiry")
        self.card_cvv = page.get_by_test_id("card-cvv")
        self.pay_button = page.get_by_test_id("pay-card")

    def open(self, base_url, order):
        self.page.goto(f"{base_url}/pay/{order}")

    def amount(self):
        return self.grand_total.inner_text()

    def pay_by_card(self, number):
        """Pay with one of the demo cards from config."""
        self.card_number.fill(number)
        self.card_name.fill(config.CARD_HOLDER)
        self.card_expiry.fill(config.CARD_EXPIRY)
        self.card_cvv.fill(config.CARD_CVV)
        self.pay_button.click()
        self.page.wait_for_load_state()
