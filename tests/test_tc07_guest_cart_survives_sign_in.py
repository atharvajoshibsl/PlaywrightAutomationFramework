"""TC07 - Guest cart survives sign-in, and login returns the guest to their
page.

A guest basket must follow the visitor into an existing account and into a
newly registered one, and an interrupted guest must land where they asked.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import actions, config
from framework.soft_assert import SoftAssert, holds

ACCOUNT = config.DEMO_ACCOUNT
NEW = config.NEW_ACCOUNT

# Two different products, so the merge has more than one line to keep.
FIRST = config.CART_PRODUCT
SECOND = config.DETAIL_PRODUCT


def cart_lines(page):
    """Names, quantities and line totals of the cart, in display order."""
    return {
        "names": page.get_by_test_id("cart-item-name").all_text_contents(),
        "quantities": [box.input_value() for box
                       in page.get_by_test_id("cart-item-qty").all()],
        "totals": page.get_by_test_id("cart-item-total").all_text_contents(),
    }


@allure.feature("Guest flow")
@allure.story("Cart survives sign-in and registration")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC07 - Guest cart survives sign-in and login returns the guest "
              "to their page")
@pytest.mark.sanity
@pytest.mark.regression
def test_guest_cart_survives_sign_in(shop, base_url):
    page = shop
    soft = SoftAssert()

    with soft.step("Step 1 - as a guest, add two products"):
        actions.add_to_cart(page, FIRST["slug"])
        page.goto(base_url)
        actions.add_to_cart(page, SECOND["slug"])

        soft.check("the cart holds two lines",
                   lambda: expect(page.get_by_test_id("cart-row"))
                   .to_have_count(2))
        soft.check("the header counts two items",
                   lambda: expect(page.get_by_test_id("cart-count"))
                   .to_have_text("2"))

        as_guest = cart_lines(page)
        allure.dynamic.parameter("guest cart", ", ".join(as_guest["names"]))

        actions.capture(page, "guest cart with two products")

    with soft.step("Step 2 - ask for an account page as a guest"):
        page.goto(f"{base_url}/orders/")

        soft.check("the guest is sent to login",
                   holds("/login" in page.url, f"landed on {page.url}"))
        soft.check("the URL remembers the page that was asked for",
                   holds("next=/orders/" in page.url,
                         f"landed on {page.url}"))
        soft.check("the form carries the same destination",
                   lambda: expect(page.locator("input[name='next']"))
                   .to_have_value("/orders/"))

    with soft.step("Step 3 - sign in from there"):
        actions.sign_in(page, ACCOUNT)

        soft.check("the visitor lands on the orders page they asked for",
                   holds(page.url.endswith("/orders/"),
                         f"landed on {page.url}"))
        soft.check("this is the orders page, not the catalogue",
                   lambda: expect(page)
                   .to_have_title(re.compile("orders", re.IGNORECASE)))

        actions.capture(page, "landed on the requested page after sign-in")

    with soft.step("Step 4 - the guest cart came along"):
        page.get_by_test_id("nav-cart").click()
        page.wait_for_url(re.compile("/cart/"))
        as_account = cart_lines(page)

        soft.check("both guest lines are still there",
                   holds(as_account["names"] == as_guest["names"],
                         f"{as_account['names']} against "
                         f"{as_guest['names']}"))
        soft.check("quantities are intact",
                   holds(as_account["quantities"] == as_guest["quantities"],
                         f"{as_account['quantities']} against "
                         f"{as_guest['quantities']}"))
        soft.check("line totals are intact",
                   holds(as_account["totals"] == as_guest["totals"],
                         f"{as_account['totals']} against "
                         f"{as_guest['totals']}"))

        actions.capture(page, "cart after signing in")

    with soft.step("Step 5 - sign out and start again as a guest"):
        page.get_by_test_id("nav-logout").click()
        page.get_by_test_id("nav-login").wait_for()

        # Signing out closes the basket with the session.
        soft.check("the signed-out visitor starts with an empty cart",
                   lambda: expect(page.get_by_test_id("cart-count"))
                   .to_have_text("0"))

        page.goto(base_url)
        actions.add_to_cart(page, FIRST["slug"])

        soft.check(f"the guest cart holds {FIRST['name']}",
                   lambda: expect(page.get_by_test_id("cart-item-name"))
                   .to_have_text(FIRST["name"]))

    with soft.step(f"Step 6 - register {NEW['email']} and open the cart"):
        page.goto(f"{base_url}/register")
        actions.register(page, NEW)
        page.get_by_test_id("nav-logout").wait_for()

        page.get_by_test_id("nav-cart").click()
        page.wait_for_url(re.compile("/cart/"))

        soft.check("the new account inherits the guest cart",
                   lambda: expect(page.get_by_test_id("cart-row"))
                   .to_have_count(1))
        soft.check(f"and the line is still {FIRST['name']}",
                   lambda: expect(page.get_by_test_id("cart-item-name"))
                   .to_have_text(FIRST["name"]))
        soft.check("the header counts it too",
                   lambda: expect(page.get_by_test_id("cart-count"))
                   .to_have_text("1"))

        actions.capture(page, "cart after registering")

    soft.assert_all()
