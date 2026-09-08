"""TC04 - Cart quantities, line totals and clearing.

Line total is price x quantity, the subtotal is the sum of the lines, and a
typed quantity only counts once Update is pressed.
"""

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.money import money, plain, rupees
from framework.soft_assert import SoftAssert, holds
from pages import CartPage, HomePage, ProductPage

PRODUCT = config.CART_PRODUCT

# Quantity typed in step 3. Kept under the seeded stock for this variant.
NEW_QTY = 3


@allure.feature("Cart")
@allure.story("Quantities, totals and clearing")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC04 - Cart quantities, line totals and clearing")
@pytest.mark.smoke
@pytest.mark.regression
def test_cart_quantities_line_totals_and_clearing(shop):
    page = shop
    soft = SoftAssert()
    home, product, cart = HomePage(page), ProductPage(page), CartPage(page)

    with soft.step(f"Step 1 - add {PRODUCT['name']} and open the cart"):
        home.open_product(PRODUCT["slug"])

        soft.check(f"the variant on offer is {PRODUCT['variant']}",
                   lambda: expect(product.variant_select)
                   .to_contain_text(PRODUCT["variant"]))

        product.add_to_cart()

        soft.check("the cart holds one line",
                   lambda: expect(cart.rows).to_have_count(1))
        soft.check(f"the line names {PRODUCT['name']}",
                   lambda: expect(cart.item_name)
                   .to_have_text(PRODUCT["name"]))
        soft.check(f"the line names the variant {PRODUCT['variant']}",
                   lambda: expect(cart.item_variant)
                   .to_have_text(PRODUCT["variant"]))

        unit = cart.unit_price()
        allure.dynamic.parameter("unit price", money(unit))

        cart.capture("cart with one item")

    with soft.step("Step 2 - the arithmetic on one item"):
        soft.check("quantity starts at 1",
                   lambda: expect(cart.item_qty).to_have_value("1"))
        soft.check(f"line total reads {plain(unit)}, the unit price once",
                   lambda: expect(cart.item_total).to_have_text(money(unit)))
        soft.check(f"subtotal reads {plain(unit)} too",
                   lambda: expect(cart.subtotal).to_have_text(money(unit)))
        soft.check("subtotal equals the sum of the line totals",
                   holds(rupees(cart.subtotal.inner_text())
                         == sum(cart.line_totals()),
                         f"subtotal was {rupees(cart.subtotal.inner_text())} "
                         f"against lines {cart.line_totals()}"))
        soft.check("summary counts 1 item",
                   lambda: expect(cart.summary_count).to_have_text("1"))
        soft.check("header cart count reads 1",
                   lambda: expect(cart.cart_count).to_have_text("1"))

    with soft.step(f"Step 3 - type {NEW_QTY} without pressing Update"):
        cart.type_quantity(NEW_QTY)

        soft.check(f"the field now holds {NEW_QTY}",
                   lambda: expect(cart.item_qty).to_have_value(str(NEW_QTY)))
        # The page says so, and the totals must back it up.
        soft.check("the page says changes need Update",
                   lambda: expect(cart.qty_hint).to_contain_text("Update"))
        soft.check(f"line total is still {plain(unit)}",
                   lambda: expect(cart.item_total).to_have_text(money(unit)))
        soft.check(f"subtotal is still {plain(unit)}",
                   lambda: expect(cart.subtotal).to_have_text(money(unit)))
        soft.check("summary still counts 1 item",
                   lambda: expect(cart.summary_count).to_have_text("1"))
        soft.check("header cart count is still 1",
                   lambda: expect(cart.cart_count).to_have_text("1"))

        cart.capture(f"quantity typed as {NEW_QTY}, totals untouched")

    with soft.step("Step 4 - press Update"):
        cart.update()

        soft.check("a confirmation says the cart was updated",
                   lambda: expect(cart.success).to_have_text("Cart updated."))
        soft.check(f"the field kept {NEW_QTY} after the reload",
                   lambda: expect(cart.item_qty).to_have_value(str(NEW_QTY)))

    with soft.step(f"Step 5 - the arithmetic on {NEW_QTY} items"):
        expected = unit * NEW_QTY
        soft.check(f"line total reads {plain(expected)}, {NEW_QTY} x "
                   f"{plain(unit)}",
                   lambda: expect(cart.item_total)
                   .to_have_text(money(expected)))
        soft.check(f"subtotal follows at {plain(expected)}",
                   lambda: expect(cart.subtotal).to_have_text(money(expected)))
        soft.check("subtotal still equals the sum of the line totals",
                   holds(rupees(cart.subtotal.inner_text())
                         == sum(cart.line_totals()),
                         f"subtotal was {rupees(cart.subtotal.inner_text())} "
                         f"against lines {cart.line_totals()}"))
        soft.check(f"unit price is unchanged at {plain(unit)}",
                   lambda: expect(cart.item_price).to_have_text(money(unit)))
        soft.check(f"summary counts {NEW_QTY} items",
                   lambda: expect(cart.summary_count)
                   .to_have_text(str(NEW_QTY)))
        soft.check(f"header cart count reads {NEW_QTY}",
                   lambda: expect(cart.cart_count).to_have_text(str(NEW_QTY)))

        cart.capture(f"cart after updating to {NEW_QTY}")

    with soft.step("Step 6 - clear the cart"):
        cart.clear()

        soft.check("a confirmation says the cart was cleared",
                   lambda: expect(cart.success).to_have_text("Cart cleared."))
        soft.check("the empty state is shown",
                   lambda: expect(cart.empty_message)
                   .to_have_text(config.CART_EMPTY))
        soft.check("Continue shopping is offered",
                   lambda: expect(cart.continue_shopping).to_be_visible())
        soft.check("no cart lines are left",
                   lambda: expect(cart.rows).to_have_count(0))
        soft.check("the summary is gone with them",
                   lambda: expect(cart.summary).to_have_count(0))
        soft.check("header cart count is back to 0",
                   lambda: expect(cart.cart_count).to_have_text("0"))

        cart.capture("empty cart")

    soft.assert_all()
