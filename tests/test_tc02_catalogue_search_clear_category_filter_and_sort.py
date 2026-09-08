"""TC02 - Catalogue search, clear, category filter and sort.

Exercises search, clear, each category filter, sort, and combined filters.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds


def capture(page, name):
    """Attach a full-page JPEG screenshot to the current Allure step."""
    allure.attach(page.screenshot(full_page=True, type="jpeg", quality=70),
                  name=name, attachment_type=allure.attachment_type.JPG)


def prices_shown(page):
    """Return product prices as integers, in display order."""
    texts = page.get_by_test_id("product-price").all_text_contents()
    # Strip rupee sign and commas: "₹3,299" -> 3299.
    return [int(re.sub(r"\D", "", text)) for text in texts]


def search_for(page, term):
    """Fill search, submit, and wait for the query in the URL."""
    page.get_by_test_id("search-input").fill(term)
    page.get_by_test_id("search-submit").click()
    page.wait_for_url(re.compile(f"q={term}"))


def open_category(page, slug):
    """Click a category chip and wait for the filtered URL."""
    page.get_by_test_id(f"category-{slug}").click()
    page.wait_for_url(re.compile(f"category={slug}"))


@allure.feature("Catalogue")
@allure.story("Search, filter and sort")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC02 - Catalogue search, clear, category filter and sort")
@pytest.mark.smoke
@pytest.mark.regression
def test_catalogue_search_clear_category_filter_and_sort(shop):
    page = shop
    soft = SoftAssert()

    total = config.EXPECTED_PRODUCT_COUNT
    cards = page.get_by_test_id("product-card")
    names = page.get_by_test_id("product-name")
    result_count = page.get_by_test_id("result-count")
    sort_select = page.get_by_test_id("sort-select")

    with allure.step("Step 1 - the unfiltered listing"):
        soft.check(f"result count reads {total} products found",
                   lambda: expect(result_count)
                   .to_have_text(f"{total} products found"))
        soft.check(f"{total} product cards are rendered",
                   lambda: expect(cards).to_have_count(total))

        capture(page, "all 16 products, nothing selected")

    with allure.step("Step 2 - search for sandal"):
        search_for(page, "sandal")

        # Singular "product" when the result count is 1.
        soft.check('result count reads 1 product found for "sandal"',
                   lambda: expect(result_count)
                   .to_have_text('1 product found for "sandal"'))
        # to_have_text(list) checks count, text, and order together.
        soft.check("only Trail Sandals is listed",
                   lambda: expect(names).to_have_text(["Trail Sandals"]))

        capture(page, "search results for sandal")

    with allure.step("Step 3 - clear the search"):
        # Clearing must restore the full listing, not leave filters behind.
        page.get_by_test_id("search-clear").click()
        page.wait_for_url(lambda url: "q=" not in url)

        soft.check(f"all {total} products return",
                   lambda: expect(cards).to_have_count(total))
        soft.check(f"result count reads {total} products found again",
                   lambda: expect(result_count)
                   .to_have_text(f"{total} products found"))
        soft.check("search box is empty",
                   lambda: expect(page.get_by_test_id("search-input"))
                   .to_have_value(""))
        # Clear button only renders while a search is active.
        soft.check("Clear control is no longer offered",
                   lambda: expect(page.get_by_test_id("search-clear"))
                   .to_have_count(0))

        capture(page, "listing after clearing the search")

    with allure.step("Step 4 - filter by each category in turn"):
        counts = []
        for slug, products in config.CATEGORY_PRODUCTS.items():
            open_category(page, slug)
            counts.append(cards.count())

            soft.check(f"{slug} chip is the active one",
                       lambda: expect(page.get_by_test_id(f"category-{slug}"))
                       .to_have_class(re.compile("chip-active")))
            soft.check(f"{slug} lists its {len(products)} products and nothing "
                       f"else",
                       lambda: expect(names).to_have_text(products))
            soft.check(f"result count reads {len(products)} products found",
                       lambda: expect(result_count)
                       .to_have_text(f"{len(products)} products found"))

            capture(page, f"{slug} listing")

        # Each product is in one category; counts should sum to the total.
        soft.check(f"the four category counts add up to {total}",
                   holds(sum(counts) == total,
                         f"counts were {counts}, adding up to {sum(counts)}"))

    with allure.step("Step 5 - sort Footwear by price, low to high"):
        footwear = config.CATEGORY_PRODUCTS["footwear"]
        open_category(page, "footwear")

        # select_option triggers navigation via the form onchange.
        sort_select.select_option("price-asc")
        page.wait_for_url(re.compile("sort=price-asc"))

        soft.check(f"still only the {len(footwear)} Footwear products",
                   lambda: expect(cards).to_have_count(len(footwear)))
        ascending = prices_shown(page)
        soft.check("prices run low to high",
                   holds(ascending == sorted(ascending),
                         f"prices came back as {ascending}"))
        soft.check("sort dropdown shows Price: low to high",
                   lambda: expect(sort_select).to_have_value("price-asc"))

        capture(page, "Footwear sorted low to high")

    with allure.step("Step 6 - sort Footwear by price, high to low"):
        sort_select.select_option("price-desc")
        page.wait_for_url(re.compile("sort=price-desc"))

        descending = prices_shown(page)
        soft.check("prices run high to low",
                   holds(descending == sorted(descending, reverse=True),
                         f"prices came back as {descending}"))
        soft.check("the same prices came back, only reordered",
                   holds(sorted(descending) == sorted(ascending),
                         f"{descending} is not a reordering of {ascending}"))

        capture(page, "Footwear sorted high to low")

    with allure.step("Step 7 - search inside the filtered, sorted listing"):
        # Search must keep the active category and sort.
        search_for(page, "shoes")

        soft.check('result count reads 1 product found for "shoes"',
                   lambda: expect(result_count)
                   .to_have_text('1 product found for "shoes"'))
        soft.check("only the Footwear match is listed",
                   lambda: expect(names).to_have_text(["Running Shoes"]))
        soft.check("Footwear chip is still the active one",
                   lambda: expect(page.get_by_test_id("category-footwear"))
                   .to_have_class(re.compile("chip-active")))
        soft.check("sort dropdown still shows Price: high to low",
                   lambda: expect(sort_select).to_have_value("price-desc"))

        remaining = prices_shown(page)
        soft.check("what is left is still ordered high to low",
                   holds(remaining == sorted(remaining, reverse=True),
                         f"prices came back as {remaining}"))

        capture(page, "search inside Footwear, sort still applied")

    with allure.step("Step 8 - search for something that matches nothing"):
        search_for(page, "zzzzqx")

        soft.check('result count reads 0 products found for "zzzzqx"',
                   lambda: expect(result_count)
                   .to_have_text('0 products found for "zzzzqx"'))
        soft.check("the empty state is shown",
                   lambda: expect(page.get_by_test_id("no-results"))
                   .to_be_visible())
        soft.check("no product cards are left",
                   lambda: expect(cards).to_have_count(0))
        # No-match search should stay on the catalogue page, not an error.
        soft.check("this is still the catalogue, not an error page",
                   lambda: expect(page)
                   .to_have_title("Products | AItomationKart"))

        capture(page, "empty state for a no-match search")

    soft.assert_all()
