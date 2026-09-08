"""TC07 - Guest cart survives sign-in, and login returns the guest to their
page.

A guest basket must follow the visitor into an existing account and into a
newly registered one, and an interrupted guest must land where they asked.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds
from pages import CartPage, HomePage, LoginPage, ProductPage, RegisterPage

ACCOUNT = config.DEMO_ACCOUNT
NEW = config.NEW_ACCOUNT

# Two different products, so the merge has more than one line to keep.
FIRST = config.CART_PRODUCT
SECOND = config.DETAIL_PRODUCT


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
    home, product, cart = HomePage(page), ProductPage(page), CartPage(page)
    login, register = LoginPage(page), RegisterPage(page)

    with soft.step("Step 1 - as a guest, add two products"):
        home.open_product(FIRST["slug"])
        product.add_to_cart()
        home.open(base_url)
        home.open_product(SECOND["slug"])
        product.add_to_cart()

        soft.check("the cart holds two lines",
                   lambda: expect(cart.rows).to_have_count(2))
        soft.check("the header counts two items",
                   lambda: expect(cart.cart_count).to_have_text("2"))

        as_guest = cart.lines()
        allure.dynamic.parameter("guest cart", ", ".join(as_guest["names"]))

        cart.capture("guest cart with two products")

    with soft.step("Step 2 - ask for an account page as a guest"):
        page.goto(f"{base_url}/orders/")

        soft.check("the guest is sent to login",
                   holds("/login" in page.url, f"landed on {page.url}"))
        soft.check("the URL remembers the page that was asked for",
                   holds("next=/orders/" in page.url,
                         f"landed on {page.url}"))
        soft.check("the form carries the same destination",
                   lambda: expect(login.next_field)
                   .to_have_value("/orders/"))

    with soft.step("Step 3 - sign in from there"):
        login.sign_in(ACCOUNT)

        soft.check("the visitor lands on the orders page they asked for",
                   holds(page.url.endswith("/orders/"),
                         f"landed on {page.url}"))
        soft.check("this is the orders page, not the catalogue",
                   lambda: expect(page)
                   .to_have_title(re.compile("orders", re.IGNORECASE)))

        home.capture("landed on the requested page after sign-in")

    with soft.step("Step 4 - the guest cart came along"):
        cart.open_cart()
        as_account = cart.lines()

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

        cart.capture("cart after signing in")

    with soft.step("Step 5 - sign out and start again as a guest"):
        cart.sign_out()

        # Signing out closes the basket with the session.
        soft.check("the signed-out visitor starts with an empty cart",
                   lambda: expect(cart.cart_count).to_have_text("0"))

        home.open(base_url)
        home.open_product(FIRST["slug"])
        product.add_to_cart()

        soft.check(f"the guest cart holds {FIRST['name']}",
                   lambda: expect(cart.item_name).to_have_text(FIRST["name"]))

    with soft.step(f"Step 6 - register {NEW['email']} and open the cart"):
        register.open(base_url)
        register.register(NEW)
        register.logout_link.wait_for()
        register.open_cart()

        soft.check("the new account inherits the guest cart",
                   lambda: expect(cart.rows).to_have_count(1))
        soft.check(f"and the line is still {FIRST['name']}",
                   lambda: expect(cart.item_name).to_have_text(FIRST["name"]))
        soft.check("the header counts it too",
                   lambda: expect(cart.cart_count).to_have_text("1"))

        cart.capture("cart after registering")

    soft.assert_all()
