"""TC04 - Cart quantities, line totals and clearing.

Line total is price x quantity, the subtotal is the sum of the lines, and a
typed quantity only counts once Update is pressed.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds

PRODUCT = config.CART_PRODUCT

# Quantity typed in step 3. Kept under the seeded stock for this variant.
NEW_QTY = 3


def capture(page, name):
    """Attach a full-page JPEG screenshot to the current Allure step."""
    allure.attach(page.screenshot(full_page=True, type="jpeg", quality=70),
                  name=name, attachment_type=allure.attachment_type.JPG)


def rupees(text):
    """Turn a displayed price into an integer: "\u20b93,499" -> 3499."""
    return int(re.sub(r"\D", "", text))


def money(amount):
    """Format an integer the way the app does: 3499 -> "\u20b93,499"."""
    return f"\u20b9{amount:,}"


def plain(amount):
    """Same number without the rupee sign, for labels the console prints."""
    return f"{amount:,}"


def line_totals(page):
    """Every line total in the cart, as integers."""
    return [rupees(text) for text
            in page.get_by_test_id("cart-item-total").all_text_contents()]


@allure.feature("Cart")
@allure.story("Quantities, totals and clearing")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC04 - Cart quantities, line totals and clearing")
@pytest.mark.smoke
@pytest.mark.regression
def test_cart_quantities_line_totals_and_clearing(shop):
    page = shop
    soft = SoftAssert()

    qty = page.get_by_test_id("cart-item-qty")
    line_total = page.get_by_test_id("cart-item-total")
    subtotal = page.get_by_test_id("summary-item-total")
    summary_count = page.get_by_test_id("summary-count")
    header_count = page.get_by_test_id("cart-count")

    with soft.step(f"Step 1 - add {PRODUCT['name']} and open the cart"):
        page.get_by_test_id(f"product-link-{PRODUCT['slug']}").click()
        page.wait_for_url(re.compile(f"/product/{PRODUCT['slug']}"))

        soft.check(f"the variant on offer is {PRODUCT['variant']}",
                   lambda: expect(page.get_by_test_id("variant-select"))
                   .to_contain_text(PRODUCT["variant"]))

        page.get_by_test_id("add-to-cart").click()
        page.wait_for_url(re.compile("/cart/"))

        soft.check("the cart holds one line",
                   lambda: expect(page.get_by_test_id("cart-row"))
                   .to_have_count(1))
        soft.check(f"the line names {PRODUCT['name']}",
                   lambda: expect(page.get_by_test_id("cart-item-name"))
                   .to_have_text(PRODUCT["name"]))
        soft.check(f"the line names the variant {PRODUCT['variant']}",
                   lambda: expect(page.get_by_test_id("cart-item-variant"))
                   .to_have_text(PRODUCT["variant"]))

        unit = rupees(page.get_by_test_id("cart-item-price").inner_text())
        allure.dynamic.parameter("unit price", money(unit))

        capture(page, "cart with one item")

    with soft.step("Step 2 - the arithmetic on one item"):
        soft.check("quantity starts at 1",
                   lambda: expect(qty).to_have_value("1"))
        soft.check(f"line total reads {plain(unit)}, the unit price once",
                   lambda: expect(line_total).to_have_text(money(unit)))
        soft.check(f"subtotal reads {plain(unit)} too",
                   lambda: expect(subtotal).to_have_text(money(unit)))
        soft.check("subtotal equals the sum of the line totals",
                   holds(rupees(subtotal.inner_text()) == sum(line_totals(page)),
                         f"subtotal was {rupees(subtotal.inner_text())} "
                         f"against lines {line_totals(page)}"))
        soft.check("summary counts 1 item",
                   lambda: expect(summary_count).to_have_text("1"))
        soft.check("header cart count reads 1",
                   lambda: expect(header_count).to_have_text("1"))

    with soft.step(f"Step 3 - type {NEW_QTY} without pressing Update"):
        qty.fill(str(NEW_QTY))

        soft.check(f"the field now holds {NEW_QTY}",
                   lambda: expect(qty).to_have_value(str(NEW_QTY)))
        # The page says so, and the totals must back it up.
        soft.check("the page says changes need Update",
                   lambda: expect(page.get_by_test_id("cart-qty-hint"))
                   .to_contain_text("Update"))
        soft.check(f"line total is still {plain(unit)}",
                   lambda: expect(line_total).to_have_text(money(unit)))
        soft.check(f"subtotal is still {plain(unit)}",
                   lambda: expect(subtotal).to_have_text(money(unit)))
        soft.check("summary still counts 1 item",
                   lambda: expect(summary_count).to_have_text("1"))
        soft.check("header cart count is still 1",
                   lambda: expect(header_count).to_have_text("1"))

        capture(page, f"quantity typed as {NEW_QTY}, totals untouched")

    with soft.step("Step 4 - press Update"):
        page.get_by_test_id("cart-item-update").click()
        page.wait_for_url(re.compile("/cart/"))

        soft.check("a confirmation says the cart was updated",
                   lambda: expect(page.get_by_test_id("flash-success"))
                   .to_have_text("Cart updated."))
        soft.check(f"the field kept {NEW_QTY} after the reload",
                   lambda: expect(qty).to_have_value(str(NEW_QTY)))

    with soft.step(f"Step 5 - the arithmetic on {NEW_QTY} items"):
        expected = unit * NEW_QTY
        soft.check(f"line total reads {plain(expected)}, {NEW_QTY} x "
                   f"{plain(unit)}",
                   lambda: expect(line_total).to_have_text(money(expected)))
        soft.check(f"subtotal follows at {plain(expected)}",
                   lambda: expect(subtotal).to_have_text(money(expected)))
        soft.check("subtotal still equals the sum of the line totals",
                   holds(rupees(subtotal.inner_text()) == sum(line_totals(page)),
                         f"subtotal was {rupees(subtotal.inner_text())} "
                         f"against lines {line_totals(page)}"))
        soft.check(f"unit price is unchanged at {plain(unit)}",
                   lambda: expect(page.get_by_test_id("cart-item-price"))
                   .to_have_text(money(unit)))
        soft.check(f"summary counts {NEW_QTY} items",
                   lambda: expect(summary_count).to_have_text(str(NEW_QTY)))
        soft.check(f"header cart count reads {NEW_QTY}",
                   lambda: expect(header_count).to_have_text(str(NEW_QTY)))

        capture(page, f"cart after updating to {NEW_QTY}")

    with soft.step("Step 6 - clear the cart"):
        page.get_by_test_id("clear-cart").click()
        page.wait_for_url(re.compile("/cart/"))

        soft.check("a confirmation says the cart was cleared",
                   lambda: expect(page.get_by_test_id("flash-success"))
                   .to_have_text("Cart cleared."))
        soft.check("the empty state is shown",
                   lambda: expect(page.get_by_test_id("empty-cart"))
                   .to_have_text("Your cart is empty."))
        soft.check("Continue shopping is offered",
                   lambda: expect(page.get_by_test_id("continue-shopping"))
                   .to_be_visible())
        soft.check("no cart lines are left",
                   lambda: expect(page.get_by_test_id("cart-row"))
                   .to_have_count(0))
        soft.check("the summary is gone with them",
                   lambda: expect(page.get_by_test_id("cart-summary"))
                   .to_have_count(0))
        soft.check("header cart count is back to 0",
                   lambda: expect(header_count).to_have_text("0"))

        capture(page, "empty cart")

    soft.assert_all()
