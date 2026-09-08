"""TC05 - Sign in, sign out and registration.

The header swaps between guest and account, signing out closes the session,
and a new account lands signed in with an empty wallet.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds
from pages import HomePage, LoginPage, RegisterPage

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
    home = HomePage(page)
    login, register = LoginPage(page), RegisterPage(page)

    with soft.step(f"Step 1 - sign in as {ACCOUNT['email']}"):
        home.login_link.click()
        page.wait_for_url(re.compile("/login"))
        login.sign_in(ACCOUNT)

        soft.check(f"a confirmation names {ACCOUNT['name']}",
                   lambda: expect(home.success)
                   .to_have_text(f"Signed in as {ACCOUNT['name']}."))
        soft.check("signing in lands on the catalogue",
                   lambda: expect(page)
                   .to_have_title("Products | AItomationKart"))

        home.capture("signed in")

    with soft.step("Step 2 - the header shows the account"):
        soft.check(f"the greeting names {ACCOUNT['name']}",
                   lambda: expect(home.profile_link)
                   .to_have_text(f"Hi, {ACCOUNT['name']}"))
        soft.check("the wallet balance is shown",
                   lambda: expect(home.wallet_balance)
                   .to_have_text(ACCOUNT["wallet"]))
        soft.check("Orders is offered",
                   lambda: expect(home.orders_link).to_be_visible())
        soft.check("Sign out is offered",
                   lambda: expect(home.logout_link).to_be_visible())
        soft.check("Sign in is no longer offered",
                   lambda: expect(home.login_link).to_have_count(0))
        soft.check("Register is no longer offered",
                   lambda: expect(home.register_link).to_have_count(0))

    with soft.step("Step 3 - sign out"):
        home.sign_out()

        soft.check("Sign in is back",
                   lambda: expect(home.login_link).to_be_visible())
        soft.check("Register is back",
                   lambda: expect(home.register_link).to_be_visible())
        soft.check("Sign out is gone",
                   lambda: expect(home.logout_link).to_have_count(0))
        soft.check("the wallet is gone from the header",
                   lambda: expect(home.wallet).to_have_count(0))

        # A closed session must not leave account pages reachable.
        for path in PRIVATE:
            page.goto(f"{base_url}{path}")
            soft.check(f"{path} sends a guest to login, remembering the page",
                       holds(f"/login?next={path}" in page.url,
                             f"landed on {page.url}"))

        home.capture("guest asking for an account page")

    with soft.step(f"Step 4 - register {NEW['email']}"):
        home.register_link.click()
        page.wait_for_url(re.compile("/register"))
        register.register(NEW)
        home.logout_link.wait_for()

        soft.check("a confirmation welcomes the new account",
                   lambda: expect(home.success)
                   .to_have_text("Account created. Welcome!"))
        soft.check(f"the greeting names {NEW['name']}",
                   lambda: expect(home.profile_link)
                   .to_have_text(f"Hi, {NEW['name']}"))
        soft.check("the new wallet is empty",
                   lambda: expect(home.wallet_balance).to_have_text("\u20b90"))
        soft.check("the new account is signed in",
                   lambda: expect(home.logout_link).to_be_visible())

        home.capture("newly registered account")

    soft.assert_all()
