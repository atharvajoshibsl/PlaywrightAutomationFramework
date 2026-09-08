"""TC08 - Checkout summary is accurate and places the order.

Checkout must preselect the default address, repeat the cart exactly, add
delivery correctly, and issue an order that is waiting to be paid.
"""

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.money import money, plain, rupees
from framework.soft_assert import SoftAssert, holds
from pages import (CartPage, CheckoutPage, HomePage, LoginPage, PaymentPage,
                   ProductPage)

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
    home, product, cart = HomePage(page), ProductPage(page), CartPage(page)
    login, checkout, payment = (LoginPage(page), CheckoutPage(page),
                                PaymentPage(page))

    with soft.step("Step 1 - sign in and put an item in the cart"):
        login.open(base_url)
        login.sign_in(ACCOUNT)

        home.open(base_url)
        home.open_product(PRODUCT["slug"])
        product.add_to_cart()

        line = {
            "name": cart.item_name.inner_text(),
            "variant": cart.item_variant.inner_text(),
            "qty": cart.item_qty.input_value(),
            "total": cart.item_total.inner_text(),
        }
        items = rupees(cart.subtotal.inner_text())
        allure.dynamic.parameter("cart total", money(items))

        soft.check(f"the cart holds {PRODUCT['name']}",
                   holds(line["name"] == PRODUCT["name"],
                         f"the cart read {line['name']!r}"))

        cart.checkout()

        soft.check("checkout opens",
                   lambda: expect(page)
                   .to_have_title("Checkout | AItomationKart"))

    with soft.step("Step 2 - the default address is preselected"):
        default = checkout.default_address

        soft.check("the account has a default address",
                   lambda: expect(default).to_have_count(1))
        soft.check("it is the one already selected",
                   lambda: expect(default.locator("input")).to_be_checked())
        soft.check("it names the account holder",
                   lambda: expect(checkout.address_text(default))
                   .to_contain_text(ACCOUNT["name"]))

        checkout.capture("checkout with the default address selected")

    with soft.step("Step 3 - the summary repeats the cart, plus delivery"):
        soft.check("one line, as in the cart",
                   lambda: expect(checkout.rows).to_have_count(1))
        soft.check("the same product",
                   lambda: expect(checkout.item_name)
                   .to_have_text(line["name"]))
        soft.check("the same variant",
                   lambda: expect(checkout.item_variant)
                   .to_have_text(line["variant"]))
        soft.check("the same quantity",
                   lambda: expect(checkout.item_qty)
                   .to_have_text(line["qty"]))
        soft.check("the same line total",
                   lambda: expect(checkout.item_total)
                   .to_have_text(line["total"]))
        soft.check(f"item total carries over as {plain(items)}",
                   lambda: expect(checkout.items_total)
                   .to_have_text(money(items)))

        discount = rupees(checkout.discount.inner_text())
        delivery = checkout.delivery_charge()
        grand = rupees(checkout.grand_total.inner_text())
        allure.dynamic.parameter("delivery",
                                 checkout.delivery.inner_text())

        soft.check("no discount without a coupon",
                   holds(discount == 0, f"discount was {discount}"))
        soft.check(f"to pay is items minus discount plus delivery: "
                   f"{plain(items)} - {discount} + {delivery} = "
                   f"{plain(grand)}",
                   holds(grand == items - discount + delivery,
                         f"the page showed {grand}"))

    with soft.step("Step 4 - place the order"):
        number = checkout.place_order()
        allure.dynamic.parameter("order", number)

        soft.check("an order number is issued",
                   holds(bool(number) and len(number) > 4,
                         f"the URL gave {number!r}"))
        soft.check("the payment page opens for that order",
                   holds(page.url.endswith(f"/pay/{number}"),
                         f"landed on {page.url}"))
        soft.check("the order is waiting to be paid",
                   lambda: expect(payment.order_number)
                   .to_have_text(f"Order {number} \u2014 awaiting payment"))
        soft.check("the amount to pay matches the checkout total",
                   lambda: expect(payment.grand_total)
                   .to_have_text(money(grand)))
        soft.check("the pay button names the same amount",
                   lambda: expect(payment.pay_button)
                   .to_have_text(f"Pay {money(grand)}"))

        payment.capture("payment page for the new order")

    soft.assert_all()
