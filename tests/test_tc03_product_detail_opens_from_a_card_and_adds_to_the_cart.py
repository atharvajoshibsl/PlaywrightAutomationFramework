"""TC03 - Product detail opens from a card and adds to the cart.

Card values must carry over to the detail page, and adding must stock the cart.
"""

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds
from pages import CartPage, HomePage, ProductPage

PRODUCT = config.DETAIL_PRODUCT


@allure.feature("Product detail")
@allure.story("Open a product and add it to the cart")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC03 - Product detail opens from a card and adds to the cart")
@pytest.mark.smoke
@pytest.mark.regression
def test_product_detail_opens_from_a_card_and_adds_to_the_cart(shop):
    page = shop
    soft = SoftAssert()
    home, product, cart = HomePage(page), ProductPage(page), CartPage(page)

    card = home.card(PRODUCT["name"])

    with soft.step("Step 1 - read the card on the listing"):
        soft.check(f"exactly one card for {PRODUCT['name']}",
                   lambda: expect(card.root).to_have_count(1))

        name_on_card = card.named()
        price_on_card = card.priced()
        allure.dynamic.parameter("card", f"{name_on_card} at {price_on_card}")

        soft.check(f"card names it {PRODUCT['name']}",
                   holds(name_on_card == PRODUCT["name"],
                         f"the card read {name_on_card!r}"))
        soft.check("card price is in rupees",
                   holds(price_on_card.startswith("\u20b9"),
                         f"the card read {price_on_card!r}"))
        soft.check(f"card names the brand {PRODUCT['brand']}",
                   lambda: expect(card.brand).to_have_text(PRODUCT["brand"]))
        soft.check("card says the product is in stock",
                   lambda: expect(card.stock).to_have_text("In stock"))

        home.capture("the card before opening it")

    with soft.step("Step 2 - open the card"):
        home.open_product(PRODUCT["slug"])

        soft.check("the URL carries the product slug",
                   holds(page.url.endswith(f"/product/{PRODUCT['slug']}"),
                         f"landed on {page.url}"))
        soft.check("the tab title names the product",
                   lambda: expect(page)
                   .to_have_title(f"{PRODUCT['name']} | AItomationKart"))
        soft.check(f"breadcrumbs place it under {PRODUCT['category']}",
                   lambda: expect(product.breadcrumbs)
                   .to_contain_text(PRODUCT["category"]))

    with soft.step("Step 3 - the detail page matches the card"):
        soft.check("detail name matches the card",
                   lambda: expect(product.name).to_have_text(name_on_card))
        soft.check("detail price matches the card",
                   lambda: expect(product.price).to_have_text(price_on_card))
        soft.check("detail brand matches the card",
                   lambda: expect(product.brand)
                   .to_have_text(PRODUCT["brand"]))
        soft.check(f"SKU reads {PRODUCT['sku']}",
                   lambda: expect(product.sku)
                   .to_contain_text(PRODUCT["sku"]))
        soft.check("a rating is shown",
                   lambda: expect(product.rating).not_to_be_empty())
        soft.check("a description is shown",
                   lambda: expect(product.description).not_to_be_empty())
        soft.check("the variant selector is visible",
                   lambda: expect(product.variant_select).to_be_visible())
        soft.check("the variant table lists at least one row",
                   lambda: expect(product.variant_rows.first).to_be_visible())
        soft.check("quantity starts at 1",
                   lambda: expect(product.qty_input).to_have_value("1"))
        soft.check("Add to cart is enabled",
                   lambda: expect(product.add_button).to_be_enabled())

        product.capture("detail page for the same product")

    with soft.step("Step 4 - read the cart count before adding"):
        before = product.items_in_cart()
        soft.check("a freshly reset shop starts with an empty cart",
                   holds(before == 0, f"the header showed {before}"))

    with soft.step("Step 5 - add the in-stock variant"):
        index, label = product.variant_with_stock()
        assert index is not None, "no variant option had stock left"
        allure.dynamic.parameter("variant", label)

        # Labels carry the stock count; the cart shows only the variant name.
        variant = label.split("\u2014")[0].strip()

        product.choose_variant(index)
        product.add_to_cart()

        soft.check("a confirmation names the product just added",
                   lambda: expect(cart.success)
                   .to_have_text(f"{name_on_card} added to your cart."))
        soft.check(f"header cart count went from {before} to {before + 1}",
                   lambda: expect(cart.cart_count)
                   .to_have_text(str(before + 1)))
        soft.check("the cart holds one line",
                   lambda: expect(cart.rows).to_have_count(1))
        soft.check("the line names the product",
                   lambda: expect(cart.item_name).to_have_text(name_on_card))
        soft.check(f"the line names the variant {variant}",
                   lambda: expect(cart.item_variant).to_have_text(variant))
        soft.check("the line price matches the card",
                   lambda: expect(cart.item_price).to_have_text(price_on_card))
        soft.check("the line holds one of them",
                   lambda: expect(cart.item_qty).to_have_value("1"))

        cart.capture("cart after adding the product")

    soft.assert_all()
