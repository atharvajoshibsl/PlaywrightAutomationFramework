"""TC09 - Checkout is refused with an empty cart.

Asking for the checkout URL directly must not create an empty order.
"""

import allure
import pytest
from playwright.sync_api import expect

from framework import actions, config
from framework.soft_assert import SoftAssert, holds

ACCOUNT = config.DEMO_ACCOUNT


@allure.feature("Checkout")
@allure.story("Refusing an empty cart")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC09 - Checkout is refused with an empty cart")
@pytest.mark.regression
def test_checkout_is_refused_with_an_empty_cart(shop, base_url):
    page = shop
    soft = SoftAssert()

    with soft.step("Step 1 - sign in with nothing in the cart"):
        page.goto(f"{base_url}/login")
        actions.sign_in(page, ACCOUNT)

        soft.check("the header counts no items",
                   lambda: expect(page.get_by_test_id("cart-count"))
                   .to_have_text("0"))

        page.get_by_test_id("nav-cart").click()
        soft.check("the cart shows its empty state",
                   lambda: expect(page.get_by_test_id("empty-cart"))
                   .to_have_text(config.CART_EMPTY))

    with soft.step("Step 2 - go straight to the checkout URL"):
        page.goto(f"{base_url}/checkout/")

        soft.check("checkout is not shown",
                   holds("/checkout" not in page.url,
                         f"landed on {page.url}"))
        soft.check("the visitor is sent back to the cart",
                   holds(page.url.endswith("/cart/"),
                         f"landed on {page.url}"))
        soft.check("and told why",
                   lambda: expect(page.get_by_test_id("flash-error"))
                   .to_have_text(config.CART_EMPTY))
        soft.check("no address or place-order control is offered",
                   lambda: expect(page.get_by_test_id("place-order"))
                   .to_have_count(0))

        actions.capture(page, "checkout refused with an empty cart")

    with soft.step("Step 3 - no empty order was created"):
        page.get_by_test_id("nav-orders").click()

        soft.check("order history is still empty",
                   lambda: expect(page.get_by_test_id("no-orders"))
                   .to_be_visible())
        soft.check("not a single order row exists",
                   lambda: expect(page.get_by_test_id("order-row"))
                   .to_have_count(0))

        actions.capture(page, "order history untouched")

    soft.assert_all()
