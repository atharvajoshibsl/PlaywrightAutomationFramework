"""TC10 - Card payment: decline, expiry and successful retry.

A decline must keep the order payable and the basket intact, an expired card
must fail as expired rather than declined, and the retry must pay the same
order exactly once.
"""

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds
from pages import (CartPage, CheckoutPage, HomePage, LoginPage, OrderPage,
                   OrdersPage, PaymentPage, ProductPage)

ACCOUNT = config.DEMO_ACCOUNT
PRODUCT = config.CART_PRODUCT
CARDS = config.CARDS


@allure.feature("Payment")
@allure.story("Card decline, expiry and retry")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC10 - Card payment: decline, expiry and successful retry")
@pytest.mark.sanity
@pytest.mark.regression
def test_card_payment_decline_expiry_and_successful_retry(shop, base_url):
    page = shop
    soft = SoftAssert()
    home, product, cart = HomePage(page), ProductPage(page), CartPage(page)
    login, checkout, payment = (LoginPage(page), CheckoutPage(page),
                                PaymentPage(page))
    order, orders = OrderPage(page), OrdersPage(page)

    with soft.step("Step 1 - place an order to pay for"):
        login.open(base_url)
        login.sign_in(ACCOUNT)

        home.open(base_url)
        home.open_product(PRODUCT["slug"])
        product.add_to_cart()
        cart.checkout()

        number = checkout.place_order()
        total = payment.amount()
        allure.dynamic.parameter("order", number)
        allure.dynamic.parameter("to pay", total)

        soft.check("the order is awaiting payment",
                   lambda: expect(payment.order_number)
                   .to_have_text(f"Order {number} \u2014 awaiting payment"))
        soft.check("the Card tab is the one open",
                   lambda: expect(payment.card_panel).to_be_visible())

    with soft.step("Step 2 - the card that always declines"):
        payment.pay_by_card(CARDS["declined"])
        declined = payment.error.inner_text().strip()
        allure.dynamic.parameter("decline says", declined)

        soft.check("the decline is stated plainly",
                   holds(declined == config.CARD_DECLINED,
                         f"the page said {declined!r}"))
        soft.check("the order still exists and is still payable",
                   lambda: expect(payment.pay_button).to_be_visible())
        soft.check("the visitor stays on the payment page for that order",
                   holds(page.url.endswith(f"/pay/{number}"),
                         f"landed on {page.url}"))
        soft.check("the amount to pay is unchanged",
                   lambda: expect(payment.grand_total).to_have_text(total))
        # A failed payment must never quietly empty the basket.
        soft.check("the basket is still there",
                   lambda: expect(payment.cart_count).to_have_text("1"))

        payment.capture("declined card")

    with soft.step("Step 3 - the card that has expired"):
        payment.pay_by_card(CARDS["expired"])
        expired = payment.error.inner_text().strip()
        allure.dynamic.parameter("expiry says", expired)

        soft.check("it fails as expired",
                   holds(expired == config.CARD_EXPIRED,
                         f"the page said {expired!r}"))
        # The two failures must be told apart, not merged into one message.
        soft.check("expiry is not reported as a generic decline",
                   holds(expired != declined,
                         f"both said {expired!r}"))
        soft.check("the order is still payable",
                   lambda: expect(payment.pay_button).to_be_visible())

        payment.capture("expired card")

    with soft.step("Step 4 - the card that succeeds"):
        payment.pay_by_card(CARDS["success"])

        soft.check("payment is confirmed",
                   lambda: expect(order.success)
                   .to_have_text(config.PAYMENT_CONFIRMED))
        soft.check("the same order opens, not a new one",
                   holds(page.url.endswith(f"/orders/{number}"),
                         f"landed on {page.url}"))
        soft.check("the order is placed",
                   lambda: expect(order.status).to_have_text("PLACED"))
        soft.check("the order is paid",
                   lambda: expect(order.payment_status)
                   .to_have_text("Payment: PAID"))
        soft.check("a payment reference is recorded",
                   lambda: expect(order.payment_reference)
                   .to_contain_text("TXN"))
        soft.check("the paid order empties the basket",
                   lambda: expect(order.cart_count).to_have_text("0"))

        order.capture("order paid after the retry")

    with soft.step("Step 5 - paid once, and only one order"):
        orders.open_orders()

        soft.check("the three attempts produced one order",
                   lambda: expect(orders.rows).to_have_count(1))
        soft.check(f"and it is {number}",
                   lambda: expect(orders.numbers).to_have_text(number))
        soft.check("history reports it as paid",
                   lambda: expect(orders.payment_status).to_have_text("PAID"))

        # Asking to pay again must not offer a second payment.
        payment.open(base_url, number)
        soft.check("the payment page now sends the visitor to the order",
                   holds(page.url.endswith(f"/orders/{number}"),
                         f"landed on {page.url}"))
        soft.check("no card form is offered for a paid order",
                   lambda: expect(payment.pay_button).to_have_count(0))

        orders.capture("order history after the retry")

    soft.assert_all()
