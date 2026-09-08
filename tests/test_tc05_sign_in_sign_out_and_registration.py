"""TC05 - Sign in, sign out and registration.

The header swaps between guest and account, signing out closes the session,
and a new account lands signed in with an empty wallet.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import actions, config
from framework.soft_assert import SoftAssert, holds

ACCOUNT = config.DEMO_ACCOUNT
NEW = config.NEW_ACCOUNT

# Pages a guest must not reach.
PRIVATE = ["/orders/", "/profile/", "/wallet/"]


@allure.feature("Authentication")
@allure.story("Sign in, sign out and registration")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC05 - Sign in, sign out and registration")
@pytest.mark.sanity
@pytest.mark.regression
def test_sign_in_sign_out_and_registration(shop, base_url):
    page = shop
    soft = SoftAssert()

    with soft.step(f"Step 1 - sign in as {ACCOUNT['email']}"):
        page.get_by_test_id("nav-login").click()
        page.wait_for_url(re.compile("/login"))
        actions.sign_in(page, ACCOUNT)

        soft.check(f"a confirmation names {ACCOUNT['name']}",
                   lambda: expect(page.get_by_test_id("flash-success"))
                   .to_have_text(f"Signed in as {ACCOUNT['name']}."))
        soft.check("signing in lands on the catalogue",
                   lambda: expect(page)
                   .to_have_title("Products | AItomationKart"))

        actions.capture(page, "signed in")

    with soft.step("Step 2 - the header shows the account"):
        soft.check(f"the greeting names {ACCOUNT['name']}",
                   lambda: expect(page.get_by_test_id("nav-profile"))
                   .to_have_text(f"Hi, {ACCOUNT['name']}"))
        soft.check("the wallet balance is shown",
                   lambda: expect(page.get_by_test_id("nav-wallet-balance"))
                   .to_have_text(ACCOUNT["wallet"]))
        soft.check("Orders is offered",
                   lambda: expect(page.get_by_test_id("nav-orders"))
                   .to_be_visible())
        soft.check("Sign out is offered",
                   lambda: expect(page.get_by_test_id("nav-logout"))
                   .to_be_visible())
        soft.check("Sign in is no longer offered",
                   lambda: expect(page.get_by_test_id("nav-login"))
                   .to_have_count(0))
        soft.check("Register is no longer offered",
                   lambda: expect(page.get_by_test_id("nav-register"))
                   .to_have_count(0))

    with soft.step("Step 3 - sign out"):
        page.get_by_test_id("nav-logout").click()
        page.get_by_test_id("nav-login").wait_for()

        soft.check("Sign in is back",
                   lambda: expect(page.get_by_test_id("nav-login"))
                   .to_be_visible())
        soft.check("Register is back",
                   lambda: expect(page.get_by_test_id("nav-register"))
                   .to_be_visible())
        soft.check("Sign out is gone",
                   lambda: expect(page.get_by_test_id("nav-logout"))
                   .to_have_count(0))
        soft.check("the wallet is gone from the header",
                   lambda: expect(page.get_by_test_id("nav-wallet"))
                   .to_have_count(0))

        # A closed session must not leave account pages reachable.
        for path in PRIVATE:
            page.goto(f"{base_url}{path}")
            soft.check(f"{path} sends a guest to login, remembering the page",
                       holds(f"/login?next={path}" in page.url,
                             f"landed on {page.url}"))

        actions.capture(page, "guest asking for an account page")

    with soft.step(f"Step 4 - register {NEW['email']}"):
        page.get_by_test_id("nav-register").click()
        page.wait_for_url(re.compile("/register"))
        actions.register(page, NEW)
        page.get_by_test_id("nav-logout").wait_for()

        soft.check("a confirmation welcomes the new account",
                   lambda: expect(page.get_by_test_id("flash-success"))
                   .to_have_text("Account created. Welcome!"))
        soft.check(f"the greeting names {NEW['name']}",
                   lambda: expect(page.get_by_test_id("nav-profile"))
                   .to_have_text(f"Hi, {NEW['name']}"))
        soft.check("the new wallet is empty",
                   lambda: expect(page.get_by_test_id("nav-wallet-balance"))
                   .to_have_text("\u20b90"))
        soft.check("the new account is signed in",
                   lambda: expect(page.get_by_test_id("nav-logout"))
                   .to_be_visible())

        actions.capture(page, "newly registered account")

    soft.assert_all()
