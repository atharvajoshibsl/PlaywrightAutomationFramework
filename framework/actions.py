"""Helpers shared by the tests: screenshots, money, and common journeys.

Actions here fail hard, like any other action in a test. Only checks are soft.
"""

import re

import allure

from framework import config


def capture(page, name):
    """Attach a full-page JPEG screenshot to the current Allure step."""
    allure.attach(page.screenshot(full_page=True, type="jpeg", quality=70),
                  name=name, attachment_type=allure.attachment_type.JPG)


def rupees(text):
    """A displayed price as an integer: "\u20b93,499" -> 3499."""
    return int(re.sub(r"\D", "", text))


def money(amount):
    """An integer in the app's format: 3499 -> "\u20b93,499"."""
    return f"\u20b9{amount:,}"


def plain(amount):
    """The same number without the rupee sign, for labels the console prints."""
    return f"{amount:,}"


def add_to_cart(page, slug):
    """From the listing, open a product and add its default variant."""
    page.get_by_test_id(f"product-link-{slug}").click()
    page.wait_for_url(re.compile(f"/product/{slug}"))
    page.get_by_test_id("add-to-cart").click()
    page.wait_for_url(re.compile("/cart/"))


def sign_in(page, account=None):
    """Submit the login form on the page already open."""
    account = account or config.DEMO_ACCOUNT
    page.get_by_test_id("login-email").fill(account["email"])
    page.get_by_test_id("login-password").fill(account["password"])
    page.get_by_test_id("login-submit").click()
    page.get_by_test_id("nav-logout").wait_for()


def register(page, account=None):
    """Submit the registration form on the page already open."""
    account = account or config.NEW_ACCOUNT
    page.get_by_test_id("register-name").fill(account["name"])
    page.get_by_test_id("register-email").fill(account["email"])
    page.get_by_test_id("register-phone").fill(account["phone"])
    page.get_by_test_id("register-password").fill(account["password"])
    page.get_by_test_id("register-confirm-password").fill(account["password"])
    page.get_by_test_id("register-submit").click()


def place_order(page):
    """Place the order at checkout and return the order number."""
    page.get_by_test_id("place-order").click()
    page.wait_for_url(re.compile(r"/pay/"))
    return page.url.rsplit("/", 1)[1]


def pay_by_card(page, number):
    """Submit the card form with one of the demo card numbers."""
    page.get_by_test_id("card-number").fill(number)
    page.get_by_test_id("card-name").fill(config.CARD_HOLDER)
    page.get_by_test_id("card-expiry").fill(config.CARD_EXPIRY)
    page.get_by_test_id("card-cvv").fill(config.CARD_CVV)
    page.get_by_test_id("pay-card").click()
    page.wait_for_load_state()
