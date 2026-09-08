"""TC01 - Home page renders the full expected interface.

Checks header, filters, product cards, and footer on load.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert


@allure.feature("Catalogue")
@allure.story("Home page")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC01 - Home page renders the full expected interface")
@pytest.mark.smoke
@pytest.mark.regression
def test_home_page_renders_full_expected_interface(shop):
    page = shop
    soft = SoftAssert()

    # Read width before anything resizes the window; used for tagline branch.
    width = page.evaluate("window.innerWidth")
    allure.dynamic.parameter("window width", f"{width}px")

    with allure.step("Step 1 - page loads"):
        soft.check("page title mentions Products",
                   lambda: expect(page)
                   .to_have_title("Products | AItomationKart"))
        soft.check("page heading reads Products",
                   lambda: expect(page.get_by_test_id("page-title"))
                   .to_have_text("Products"))

        # Screenshot here so it files under Step 1, not at test end.
        allure.attach(page.screenshot(full_page=True, type="jpeg", quality=70),
                      name="home page on load",
                      attachment_type=allure.attachment_type.JPG)

    with allure.step("Step 2 - header"):
        soft.check("wordmark reads AItomationKart",
                   lambda: expect(page.get_by_test_id("nav-brand"))
                   .to_have_text("AItomationKart"))

        # Tagline hides below breakpoint; assert the right state for width.
        if width >= config.TAGLINE_BREAKPOINT:
            soft.check("tagline is visible beside the wordmark",
                       lambda: expect(page.get_by_test_id("tagline"))
                       .to_be_visible())
        else:
            soft.check("tagline is hidden on a narrow window",
                       lambda: expect(page.get_by_test_id("tagline"))
                       .to_be_hidden())

        soft.check("tagline reads read it correct through automation",
                   lambda: expect(page.get_by_test_id("tagline"))
                   .to_contain_text(config.TAGLINE))
        soft.check("search input is visible",
                   lambda: expect(page.get_by_test_id("search-input"))
                   .to_be_visible())
        soft.check("search button is visible",
                   lambda: expect(page.get_by_test_id("search-submit"))
                   .to_be_visible())
        soft.check("theme toggle is visible",
                   lambda: expect(page.get_by_test_id("theme-toggle"))
                   .to_be_visible())
        soft.check("cart link is visible",
                   lambda: expect(page.get_by_test_id("nav-cart"))
                   .to_be_visible())
        soft.check("cart count starts at 0",
                   lambda: expect(page.get_by_test_id("cart-count"))
                   .to_have_text("0"))
        soft.check("Sign in link is visible to a guest",
                   lambda: expect(page.get_by_test_id("nav-login"))
                   .to_be_visible())
        soft.check("Register link is visible to a guest",
                   lambda: expect(page.get_by_test_id("nav-register"))
                   .to_be_visible())

    with allure.step("Step 3 - filter and sort controls"):
        chips = page.get_by_test_id("category-filters").locator("a")
        # to_have_text(list) checks count, text, and order together.
        soft.check(f"{len(config.CATEGORIES)} category chips are offered",
                   lambda: expect(chips)
                   .to_have_count(len(config.CATEGORIES)))
        soft.check("category chips read All, Apparel, Electronics, Footwear, "
                   "Home & Kitchen",
                   lambda: expect(chips).to_have_text(config.CATEGORIES))

        sort_select = page.get_by_test_id("sort-select")
        soft.check("sort dropdown is visible",
                   lambda: expect(sort_select).to_be_visible())
        soft.check(f"{len(config.SORT_OPTIONS)} sort options are offered",
                   lambda: expect(sort_select.locator("option"))
                   .to_have_text(config.SORT_OPTIONS))

    with allure.step("Step 4 - result count and product card anatomy"):
        count = config.EXPECTED_PRODUCT_COUNT
        soft.check(f"result count reads {count} products found",
                   lambda: expect(page.get_by_test_id("result-count"))
                   .to_have_text(f"{count} products found"))
        soft.check(f"{count} product cards are rendered",
                   lambda: expect(page.get_by_test_id("product-card"))
                   .to_have_count(count))

        card = page.get_by_test_id("product-card").first
        soft.check("first card shows a brand",
                   lambda: expect(card.get_by_test_id("product-brand"))
                   .not_to_be_empty())
        soft.check("first card shows a name",
                   lambda: expect(card.get_by_test_id("product-name"))
                   .not_to_be_empty())
        soft.check("first card shows a price",
                   lambda: expect(card.get_by_test_id("product-price"))
                   .not_to_be_empty())
        soft.check("first card shows a rating",
                   lambda: expect(card.get_by_test_id("product-rating"))
                   .not_to_be_empty())
        soft.check("first card shows a stock badge",
                   lambda: expect(card.get_by_test_id("product-stock"))
                   .not_to_be_empty())

        # Card image has no testid; located by CSS for now.
        soft.check("first card shows an image",
                   lambda: expect(card.locator(".card-image .emoji"))
                   .not_to_be_empty())

        soft.check("first card price is in rupees",
                   lambda: expect(card.get_by_test_id("product-price"))
                   .to_contain_text("\u20b9"))
        soft.check("first card links to a product page",
                   lambda: expect(card.locator("a").first)
                   .to_have_attribute("href", re.compile(r"/product/")))

    with allure.step("Step 5 - footer"):
        soft.check("footer wordmark reads AItomationKart",
                   lambda: expect(page.get_by_test_id("footer-brand"))
                   .to_have_text("AItomationKart"))
        soft.check("footer repeats the tagline",
                   lambda: expect(page.get_by_test_id("footer-purpose"))
                   .to_contain_text(config.TAGLINE))
        soft.check(f"footer lists {len(config.FRAMEWORKS)} frameworks",
                   lambda: expect(page.get_by_test_id("footer-frameworks")
                                  .locator("li"))
                   .to_have_text(config.FRAMEWORKS))
        soft.check("footer carries the no-real-payments note",
                   lambda: expect(page.get_by_test_id("footer-note"))
                   .to_contain_text("No real payments"))
        soft.check("footer carries the copyright",
                   lambda: expect(page.get_by_test_id("footer-copyright"))
                   .to_contain_text("Atharva Joshi"))

        # Scroll footer into view before the screenshot.
        page.get_by_test_id("footer-copyright").scroll_into_view_if_needed()
        allure.attach(page.screenshot(type="jpeg", quality=70), name="footer",
                      attachment_type=allure.attachment_type.JPG)

    soft.assert_all()
