"""TC01 - Home page renders the full expected interface.

Checks header, filters, product cards, and footer on load.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert
from pages import HomePage


@allure.feature("Catalogue")
@allure.story("Home page")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC01 - Home page renders the full expected interface")
@pytest.mark.smoke
@pytest.mark.regression
def test_home_page_renders_full_expected_interface(shop):
    page = shop
    soft = SoftAssert()
    home = HomePage(page)

    # Read width before anything resizes the window; used for tagline branch.
    width = page.evaluate("window.innerWidth")
    allure.dynamic.parameter("window width", f"{width}px")

    with soft.step("Step 1 - page loads"):
        soft.check("page title mentions Products",
                   lambda: expect(page)
                   .to_have_title("Products | AItomationKart"))
        soft.check("page heading reads Products",
                   lambda: expect(home.heading).to_have_text("Products"))

        # Screenshot here so it files under Step 1, not at test end.
        home.capture("home page on load")

    with soft.step("Step 2 - header"):
        soft.check("wordmark reads AItomationKart",
                   lambda: expect(home.brand).to_have_text("AItomationKart"))

        # Tagline hides below breakpoint; assert the right state for width.
        if width >= config.TAGLINE_BREAKPOINT:
            soft.check("tagline is visible beside the wordmark",
                       lambda: expect(home.tagline).to_be_visible())
        else:
            soft.check("tagline is hidden on a narrow window",
                       lambda: expect(home.tagline).to_be_hidden())

        soft.check("tagline reads read it correct through automation",
                   lambda: expect(home.tagline)
                   .to_contain_text(config.TAGLINE))
        soft.check("search input is visible",
                   lambda: expect(home.search_input).to_be_visible())
        soft.check("search button is visible",
                   lambda: expect(home.search_submit).to_be_visible())
        soft.check("theme toggle is visible",
                   lambda: expect(home.theme_toggle).to_be_visible())
        soft.check("cart link is visible",
                   lambda: expect(home.cart_link).to_be_visible())
        soft.check("cart count starts at 0",
                   lambda: expect(home.cart_count).to_have_text("0"))
        soft.check("Sign in link is visible to a guest",
                   lambda: expect(home.login_link).to_be_visible())
        soft.check("Register link is visible to a guest",
                   lambda: expect(home.register_link).to_be_visible())

    with soft.step("Step 3 - filter and sort controls"):
        # to_have_text(list) checks count, text, and order together.
        soft.check(f"{len(config.CATEGORIES)} category chips are offered",
                   lambda: expect(home.chips)
                   .to_have_count(len(config.CATEGORIES)))
        soft.check("category chips read All, Apparel, Electronics, Footwear, "
                   "Home & Kitchen",
                   lambda: expect(home.chips).to_have_text(config.CATEGORIES))

        soft.check("sort dropdown is visible",
                   lambda: expect(home.sort_select).to_be_visible())
        soft.check(f"{len(config.SORT_OPTIONS)} sort options are offered",
                   lambda: expect(home.sort_select.locator("option"))
                   .to_have_text(config.SORT_OPTIONS))

    with soft.step("Step 4 - result count and product card anatomy"):
        count = config.EXPECTED_PRODUCT_COUNT
        soft.check(f"result count reads {count} products found",
                   lambda: expect(home.result_count)
                   .to_have_text(f"{count} products found"))
        soft.check(f"{count} product cards are rendered",
                   lambda: expect(home.cards).to_have_count(count))

        card = home.first_card()
        soft.check("first card shows a brand",
                   lambda: expect(card.brand).not_to_be_empty())
        soft.check("first card shows a name",
                   lambda: expect(card.name).not_to_be_empty())
        soft.check("first card shows a price",
                   lambda: expect(card.price).not_to_be_empty())
        soft.check("first card shows a rating",
                   lambda: expect(card.rating).not_to_be_empty())
        soft.check("first card shows a stock badge",
                   lambda: expect(card.stock).not_to_be_empty())
        soft.check("first card shows an image",
                   lambda: expect(card.image).not_to_be_empty())
        soft.check("first card price is in rupees",
                   lambda: expect(card.price).to_contain_text("\u20b9"))
        soft.check("first card links to a product page",
                   lambda: expect(card.link)
                   .to_have_attribute("href", re.compile(r"/product/")))

    with soft.step("Step 5 - footer"):
        soft.check("footer wordmark reads AItomationKart",
                   lambda: expect(home.footer_brand)
                   .to_have_text("AItomationKart"))
        soft.check("footer repeats the tagline",
                   lambda: expect(home.footer_purpose)
                   .to_contain_text(config.TAGLINE))
        soft.check(f"footer lists {len(config.FRAMEWORKS)} frameworks",
                   lambda: expect(home.footer_frameworks)
                   .to_have_text(config.FRAMEWORKS))
        soft.check("footer carries the no-real-payments note",
                   lambda: expect(home.footer_note)
                   .to_contain_text("No real payments"))
        soft.check("footer carries the copyright",
                   lambda: expect(home.footer_copyright)
                   .to_contain_text("Atharva Joshi"))

        # Scroll footer into view before the screenshot.
        home.footer_copyright.scroll_into_view_if_needed()
        home.capture("footer", full_page=False)

    soft.assert_all()
