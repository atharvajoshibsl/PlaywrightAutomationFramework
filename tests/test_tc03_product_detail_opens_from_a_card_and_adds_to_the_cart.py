"""TC03 - Product detail opens from a card and adds to the cart.

Card values must carry over to the detail page, and adding must stock the cart.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds

PRODUCT = config.DETAIL_PRODUCT

# Option labels read "Standard / Default - 5 left" when stock remains.
IN_STOCK = "left"


def capture(page, name):
    """Attach a full-page JPEG screenshot to the current Allure step."""
    allure.attach(page.screenshot(full_page=True, type="jpeg", quality=70),
                  name=name, attachment_type=allure.attachment_type.JPG)


def in_stock_option(select):
    """Index and label of the first variant option that still has stock."""
    for index, label in enumerate(select.locator("option")
                                  .all_text_contents()):
        if IN_STOCK in label:
            return index, " ".join(label.split())
    return None, None


@allure.feature("Product detail")
@allure.story("Open a product and add it to the cart")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC03 - Product detail opens from a card and adds to the cart")
@pytest.mark.smoke
@pytest.mark.regression
def test_product_detail_opens_from_a_card_and_adds_to_the_cart(shop):
    page = shop
    soft = SoftAssert()

    card = page.get_by_test_id("product-card").filter(has_text=PRODUCT["name"])

    with soft.step("Step 1 - read the card on the listing"):
        soft.check(f"exactly one card for {PRODUCT['name']}",
                   lambda: expect(card).to_have_count(1))

        name_on_card = card.get_by_test_id("product-name").inner_text().strip()
        price_on_card = (card.get_by_test_id("product-price")
                         .inner_text().strip())
        allure.dynamic.parameter("card", f"{name_on_card} at {price_on_card}")

        soft.check(f"card names it {PRODUCT['name']}",
                   holds(name_on_card == PRODUCT["name"],
                         f"the card read {name_on_card!r}"))
        soft.check("card price is in rupees",
                   holds(price_on_card.startswith("\u20b9"),
                         f"the card read {price_on_card!r}"))
        soft.check(f"card names the brand {PRODUCT['brand']}",
                   lambda: expect(card.get_by_test_id("product-brand"))
                   .to_have_text(PRODUCT["brand"]))
        soft.check("card says the product is in stock",
                   lambda: expect(card.get_by_test_id("product-stock"))
                   .to_have_text("In stock"))

        capture(page, "the card before opening it")

    with soft.step("Step 2 - open the card"):
        page.get_by_test_id(f"product-link-{PRODUCT['slug']}").click()
        page.wait_for_url(re.compile(f"/product/{PRODUCT['slug']}"))

        soft.check("the URL carries the product slug",
                   holds(page.url.endswith(f"/product/{PRODUCT['slug']}"),
                         f"landed on {page.url}"))
        soft.check("the tab title names the product",
                   lambda: expect(page)
                   .to_have_title(f"{PRODUCT['name']} | AItomationKart"))
        soft.check(f"breadcrumbs place it under {PRODUCT['category']}",
                   lambda: expect(page.get_by_test_id("breadcrumbs"))
                   .to_contain_text(PRODUCT["category"]))

    with soft.step("Step 3 - the detail page matches the card"):
        soft.check("detail name matches the card",
                   lambda: expect(page.get_by_test_id("detail-name"))
                   .to_have_text(name_on_card))
        soft.check("detail price matches the card",
                   lambda: expect(page.get_by_test_id("detail-price"))
                   .to_have_text(price_on_card))
        soft.check("detail brand matches the card",
                   lambda: expect(page.get_by_test_id("detail-brand"))
                   .to_have_text(PRODUCT["brand"]))
        soft.check(f"SKU reads {PRODUCT['sku']}",
                   lambda: expect(page.get_by_test_id("detail-sku"))
                   .to_contain_text(PRODUCT["sku"]))
        soft.check("a rating is shown",
                   lambda: expect(page.get_by_test_id("detail-rating"))
                   .not_to_be_empty())
        soft.check("a description is shown",
                   lambda: expect(page.get_by_test_id("detail-description"))
                   .not_to_be_empty())
        soft.check("the variant selector is visible",
                   lambda: expect(page.get_by_test_id("variant-select"))
                   .to_be_visible())
        soft.check("the variant table lists at least one row",
                   lambda: expect(page.get_by_test_id("variant-row").first)
                   .to_be_visible())
        soft.check("quantity starts at 1",
                   lambda: expect(page.get_by_test_id("qty-input"))
                   .to_have_value("1"))
        soft.check("Add to cart is enabled",
                   lambda: expect(page.get_by_test_id("add-to-cart"))
                   .to_be_enabled())

        capture(page, "detail page for the same product")

    with soft.step("Step 4 - read the cart count before adding"):
        before = int(page.get_by_test_id("cart-count").inner_text())
        soft.check("a freshly reset shop starts with an empty cart",
                   holds(before == 0, f"the header showed {before}"))

    with soft.step("Step 5 - add the in-stock variant"):
        select = page.get_by_test_id("variant-select")
        index, label = in_stock_option(select)
        assert index is not None, "no variant option had stock left"
        allure.dynamic.parameter("variant", label)

        # Labels carry the stock count; the cart shows only the variant name.
        variant = label.split("\u2014")[0].strip()

        select.select_option(index=index)
        page.get_by_test_id("add-to-cart").click()
        page.wait_for_url(re.compile("/cart/"))

        soft.check("a confirmation names the product just added",
                   lambda: expect(page.get_by_test_id("flash-success"))
                   .to_have_text(f"{name_on_card} added to your cart."))
        soft.check(f"header cart count went from {before} to {before + 1}",
                   lambda: expect(page.get_by_test_id("cart-count"))
                   .to_have_text(str(before + 1)))
        soft.check("the cart holds one line",
                   lambda: expect(page.get_by_test_id("cart-row"))
                   .to_have_count(1))
        soft.check("the line names the product",
                   lambda: expect(page.get_by_test_id("cart-item-name"))
                   .to_have_text(name_on_card))
        soft.check(f"the line names the variant {variant}",
                   lambda: expect(page.get_by_test_id("cart-item-variant"))
                   .to_have_text(variant))
        soft.check("the line price matches the card",
                   lambda: expect(page.get_by_test_id("cart-item-price"))
                   .to_have_text(price_on_card))
        soft.check("the line holds one of them",
                   lambda: expect(page.get_by_test_id("cart-item-qty"))
                   .to_have_value("1"))

        capture(page, "cart after adding the product")

    soft.assert_all()
