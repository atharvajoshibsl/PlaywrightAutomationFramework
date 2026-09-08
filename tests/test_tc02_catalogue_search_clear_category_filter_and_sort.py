"""TC02 - Catalogue search, clear, category filter and sort.

Exercises search, clear, each category filter, sort, and combined filters.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds
from pages import HomePage


@allure.feature("Catalogue")
@allure.story("Search, filter and sort")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC02 - Catalogue search, clear, category filter and sort")
@pytest.mark.smoke
@pytest.mark.regression
def test_catalogue_search_clear_category_filter_and_sort(shop):
    page = shop
    soft = SoftAssert()
    home = HomePage(page)

    total = config.EXPECTED_PRODUCT_COUNT

    with soft.step("Step 1 - the unfiltered listing"):
        soft.check(f"result count reads {total} products found",
                   lambda: expect(home.result_count)
                   .to_have_text(f"{total} products found"))
        soft.check(f"{total} product cards are rendered",
                   lambda: expect(home.cards).to_have_count(total))

        home.capture("all 16 products, nothing selected")

    with soft.step("Step 2 - search for sandal"):
        home.search("sandal")

        # Singular "product" when the result count is 1.
        soft.check('result count reads 1 product found for "sandal"',
                   lambda: expect(home.result_count)
                   .to_have_text('1 product found for "sandal"'))
        # to_have_text(list) checks count, text, and order together.
        soft.check("only Trail Sandals is listed",
                   lambda: expect(home.names).to_have_text(["Trail Sandals"]))

        home.capture("search results for sandal")

    with soft.step("Step 3 - clear the search"):
        # Clearing must restore the full listing, not leave filters behind.
        home.clear_search()

        soft.check(f"all {total} products return",
                   lambda: expect(home.cards).to_have_count(total))
        soft.check(f"result count reads {total} products found again",
                   lambda: expect(home.result_count)
                   .to_have_text(f"{total} products found"))
        soft.check("search box is empty",
                   lambda: expect(home.search_input).to_have_value(""))
        # Clear button only renders while a search is active.
        soft.check("Clear control is no longer offered",
                   lambda: expect(home.search_clear).to_have_count(0))

        home.capture("listing after clearing the search")

    with soft.step("Step 4 - filter by each category in turn"):
        counts = []
        for slug, products in config.CATEGORY_PRODUCTS.items():
            home.open_category(slug)
            counts.append(home.cards.count())

            soft.check(f"{slug} chip is the active one",
                       lambda: expect(home.chip(slug))
                       .to_have_class(re.compile("chip-active")))
            soft.check(f"{slug} lists its {len(products)} products and nothing "
                       f"else",
                       lambda: expect(home.names).to_have_text(products))
            soft.check(f"result count reads {len(products)} products found",
                       lambda: expect(home.result_count)
                       .to_have_text(f"{len(products)} products found"))

            home.capture(f"{slug} listing")

        # Each product is in one category; counts should sum to the total.
        soft.check(f"the four category counts add up to {total}",
                   holds(sum(counts) == total,
                         f"counts were {counts}, adding up to {sum(counts)}"))

    with soft.step("Step 5 - sort Footwear by price, low to high"):
        footwear = config.CATEGORY_PRODUCTS["footwear"]
        home.open_category("footwear")
        home.sort_by("price-asc")

        soft.check(f"still only the {len(footwear)} Footwear products",
                   lambda: expect(home.cards).to_have_count(len(footwear)))
        ascending = home.prices_shown()
        soft.check("prices run low to high",
                   holds(ascending == sorted(ascending),
                         f"prices came back as {ascending}"))
        soft.check("sort dropdown shows Price: low to high",
                   lambda: expect(home.sort_select).to_have_value("price-asc"))

        home.capture("Footwear sorted low to high")

    with soft.step("Step 6 - sort Footwear by price, high to low"):
        home.sort_by("price-desc")

        descending = home.prices_shown()
        soft.check("prices run high to low",
                   holds(descending == sorted(descending, reverse=True),
                         f"prices came back as {descending}"))
        soft.check("the same prices came back, only reordered",
                   holds(sorted(descending) == sorted(ascending),
                         f"{descending} is not a reordering of {ascending}"))

        home.capture("Footwear sorted high to low")

    with soft.step("Step 7 - search inside the filtered, sorted listing"):
        # Search must keep the active category and sort.
        home.search("shoes")

        soft.check('result count reads 1 product found for "shoes"',
                   lambda: expect(home.result_count)
                   .to_have_text('1 product found for "shoes"'))
        soft.check("only the Footwear match is listed",
                   lambda: expect(home.names).to_have_text(["Running Shoes"]))
        soft.check("Footwear chip is still the active one",
                   lambda: expect(home.chip("footwear"))
                   .to_have_class(re.compile("chip-active")))
        soft.check("sort dropdown still shows Price: high to low",
                   lambda: expect(home.sort_select).to_have_value("price-desc"))

        remaining = home.prices_shown()
        soft.check("what is left is still ordered high to low",
                   holds(remaining == sorted(remaining, reverse=True),
                         f"prices came back as {remaining}"))

        home.capture("search inside Footwear, sort still applied")

    with soft.step("Step 8 - search for something that matches nothing"):
        home.search("zzzzqx")

        soft.check('result count reads 0 products found for "zzzzqx"',
                   lambda: expect(home.result_count)
                   .to_have_text('0 products found for "zzzzqx"'))
        soft.check("the empty state is shown",
                   lambda: expect(home.no_results).to_be_visible())
        soft.check("no product cards are left",
                   lambda: expect(home.cards).to_have_count(0))
        # No-match search should stay on the catalogue page, not an error.
        soft.check("this is still the catalogue, not an error page",
                   lambda: expect(page)
                   .to_have_title("Products | AItomationKart"))

        home.capture("empty state for a no-match search")

    soft.assert_all()
