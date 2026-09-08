"""Self-healing demo: wrong testids fail, healer suggests fixes.

Three renamed locators plus one missing element. Marked xfail on purpose.

    pytest tests/test_self_healing_demo.py -s --runxfail
"""

import allure
import pytest
from playwright.sync_api import expect

from ai.self_heal import Healer
from framework.soft_assert import SoftAssert

# Short timeout; stale locators would block too long at default.
GONE = 2000


@allure.feature("Framework")
@allure.story("Self-healing locators")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Self-healing suggests fixes for stale locators")
@pytest.mark.xfail(reason="the stale locators are deliberate - see docstring")
def test_self_healing_suggests_fixes_for_stale_locators(shop):
    page = shop
    soft = SoftAssert()
    heal = Healer(page)

    with soft.step("Step 1 - locators that still resolve"):
        soft.check("wordmark is visible",
                   lambda: expect(heal.find(
                       "nav-brand", "the site wordmark in the header"))
                   .to_be_visible())
        soft.check("cart count is visible",
                   lambda: expect(heal.find(
                       "cart-count", "the number of items in the cart"))
                   .to_be_visible())

    with soft.step("Step 2 - locators the application renamed"):
        soft.check("search box is visible",
                   lambda: expect(heal.find(
                       "search-box", "the text field for searching products"))
                   .to_be_visible(timeout=GONE))
        soft.check("sort dropdown is visible",
                   lambda: expect(heal.find(
                       "sort-dropdown", "the dropdown that chooses the sort "
                       "order of the results"))
                   .to_be_visible(timeout=GONE))
        soft.check("result count is visible",
                   lambda: expect(heal.find(
                       "products-count", "the line saying how many products "
                       "were found"))
                   .to_be_visible(timeout=GONE))

    with soft.step("Step 3 - a locator for something the page does not have"):
        soft.check("place order button is visible",
                   lambda: expect(heal.find(
                       "checkout-now", "the button that places the order"))
                   .to_be_visible(timeout=GONE))

    # Run before assert_all so suggestions reach the report.
    heal.report()

    soft.assert_all()
