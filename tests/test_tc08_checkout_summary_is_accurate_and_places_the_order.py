"""TC08 - Checkout summary is accurate and places the order.

Checkout must preselect the default address, repeat the cart exactly, add
delivery correctly, and issue an order that is waiting to be paid.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import actions, config
from framework.soft_assert import SoftAssert, holds

ACCOUNT = config.DEMO_ACCOUNT
PRODUCT = config.CART_PRODUCT


@allure.feature("Checkout")
@allure.story("Summary and placing the order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC08 - Checkout summary is accurate and places the order")
@pytest.mark.sanity
@pytest.mark.regression
def test_checkout_summary_is_accurate_and_places_the_order(shop, base_url):
    page = shop
    soft = SoftAssert()

    with soft.step("Step 1 - sign in and put an item in the cart"):
        page.goto(f"{base_url}/login")
        actions.sign_in(page, ACCOUNT)

        page.goto(base_url)
        actions.add_to_cart(page, PRODUCT["slug"])

        cart = {
            "name": page.get_by_test_id("cart-item-name").inner_text(),
            "variant": page.get_by_test_id("cart-item-variant").inner_text(),
            "qty": page.get_by_test_id("cart-item-qty").input_value(),
            "total": page.get_by_test_id("cart-item-total").inner_text(),
        }
        items = actions.rupees(
            page.get_by_test_id("summary-item-total").inner_text())
        allure.dynamic.parameter("cart total", actions.money(items))

        soft.check(f"the cart holds {PRODUCT['name']}",
                   holds(cart["name"] == PRODUCT["name"],
                         f"the cart read {cart['name']!r}"))

        page.get_by_test_id("checkout").click()
        page.wait_for_url(re.compile("/checkout/"))

        soft.check("checkout opens",
                   lambda: expect(page)
                   .to_have_title("Checkout | AItomationKart"))

    with soft.step("Step 2 - the default address is preselected"):
        options = page.get_by_test_id("address-option")
        default = options.filter(
            has=page.get_by_test_id("address-default-tag"))

        soft.check("the account has a default address",
                   lambda: expect(default).to_have_count(1))
        soft.check("it is the one already selected",
                   lambda: expect(default.locator("input")).to_be_checked())
        soft.check("it names the account holder",
                   lambda: expect(default.get_by_test_id("address-text"))
                   .to_contain_text(ACCOUNT["name"]))

        actions.capture(page, "checkout with the default address selected")

    with soft.step("Step 3 - the summary repeats the cart, plus delivery"):
        soft.check("one line, as in the cart",
                   lambda: expect(page.get_by_test_id("checkout-row"))
                   .to_have_count(1))
        soft.check("the same product",
                   lambda: expect(page.get_by_test_id("checkout-item-name"))
                   .to_have_text(cart["name"]))
        soft.check("the same variant",
                   lambda: expect(page.get_by_test_id("checkout-item-variant"))
                   .to_have_text(cart["variant"]))
        soft.check("the same quantity",
                   lambda: expect(page.get_by_test_id("checkout-item-qty"))
                   .to_have_text(cart["qty"]))
        soft.check("the same line total",
                   lambda: expect(page.get_by_test_id("checkout-item-total"))
                   .to_have_text(cart["total"]))
        soft.check(f"item total carries over as {actions.plain(items)}",
                   lambda: expect(page.get_by_test_id("summary-item-total"))
                   .to_have_text(actions.money(items)))

        discount = actions.rupees(
            page.get_by_test_id("summary-discount").inner_text())
        delivery_text = page.get_by_test_id("summary-delivery").inner_text()
        # Delivery reads FREE above the threshold and a fee below it.
        delivery = 0 if "FREE" in delivery_text.upper() else actions.rupees(
            delivery_text)
        grand = actions.rupees(
            page.get_by_test_id("summary-grand-total").inner_text())
        allure.dynamic.parameter("delivery", delivery_text)

        soft.check("no discount without a coupon",
                   holds(discount == 0, f"discount was {discount}"))
        soft.check(f"to pay is items minus discount plus delivery: "
                   f"{actions.plain(items)} - {discount} + {delivery} = "
                   f"{actions.plain(grand)}",
                   holds(grand == items - discount + delivery,
                         f"the page showed {grand}"))

    with soft.step("Step 4 - place the order"):
        number = actions.place_order(page)
        allure.dynamic.parameter("order", number)

        soft.check("an order number is issued",
                   holds(bool(number) and len(number) > 4,
                         f"the URL gave {number!r}"))
        soft.check("the payment page opens for that order",
                   holds(page.url.endswith(f"/pay/{number}"),
                         f"landed on {page.url}"))
        soft.check("the order is waiting to be paid",
                   lambda: expect(page.get_by_test_id("payment-order-number"))
                   .to_have_text(f"Order {number} \u2014 awaiting payment"))
        soft.check("the amount to pay matches the checkout total",
                   lambda: expect(page.get_by_test_id("payment-grand-total"))
                   .to_have_text(actions.money(grand)))
        soft.check("the pay button names the same amount",
                   lambda: expect(page.get_by_test_id("pay-card"))
                   .to_have_text(f"Pay {actions.money(grand)}"))

        actions.capture(page, "payment page for the new order")

    soft.assert_all()
