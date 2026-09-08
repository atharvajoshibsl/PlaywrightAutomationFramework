"""TC09 - Checkout is refused with an empty cart.

Asking for the checkout URL directly must not create an empty order.
"""

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds
from pages import CartPage, CheckoutPage, LoginPage, OrdersPage

ACCOUNT = config.DEMO_ACCOUNT


@allure.feature("Checkout")
@allure.story("Refusing an empty cart")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC09 - Checkout is refused with an empty cart")
@pytest.mark.regression
def test_checkout_is_refused_with_an_empty_cart(shop, base_url):
    page = shop
    soft = SoftAssert()
    login, cart = LoginPage(page), CartPage(page)
    checkout, orders = CheckoutPage(page), OrdersPage(page)

    with soft.step("Step 1 - sign in with nothing in the cart"):
        login.open(base_url)
        login.sign_in(ACCOUNT)

        soft.check("the header counts no items",
                   lambda: expect(cart.cart_count).to_have_text("0"))

        cart.open_cart()
        soft.check("the cart shows its empty state",
                   lambda: expect(cart.empty_message)
                   .to_have_text(config.CART_EMPTY))

    with soft.step("Step 2 - go straight to the checkout URL"):
        checkout.open(base_url)

        soft.check("checkout is not shown",
                   holds("/checkout" not in page.url,
                         f"landed on {page.url}"))
        soft.check("the visitor is sent back to the cart",
                   holds(page.url.endswith("/cart/"),
                         f"landed on {page.url}"))
        soft.check("and told why",
                   lambda: expect(cart.error).to_have_text(config.CART_EMPTY))
        soft.check("no address or place-order control is offered",
                   lambda: expect(checkout.place_order_button)
                   .to_have_count(0))

        cart.capture("checkout refused with an empty cart")

    with soft.step("Step 3 - no empty order was created"):
        orders.open_orders()

        soft.check("order history is still empty",
                   lambda: expect(orders.empty_message).to_be_visible())
        soft.check("not a single order row exists",
                   lambda: expect(orders.rows).to_have_count(0))

        orders.capture("order history untouched")

    soft.assert_all()
