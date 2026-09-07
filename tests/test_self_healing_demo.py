"""Self-healing demo - suggests fixes for locators this test gets wrong.

Three of the testids below never existed on the home page: the application
calls those elements something else. Their checks fail, and the healer then
reads the page once and suggests a replacement for each. A fourth asks for an
element that is genuinely absent, which it should refuse to heal rather than
point at the nearest lookalike.

Marked xfail because the failures are the whole demonstration - a permanently
red suite would be worse than no demo. To watch it fail for real:

    pytest tests/test_self_healing_demo.py -s --runxfail
"""

import allure
import pytest
from playwright.sync_api import expect

from ai.self_heal import Healer
from framework.soft_assert import SoftAssert

# The stale locators cannot be waited into existence, and four of them at the
# default five seconds is most of the run.
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

    # Before assert_all, so the suggestions reach the report even though the
    # test is about to fail. Adds a step only when something is broken.
    heal.report()

    soft.assert_all()
