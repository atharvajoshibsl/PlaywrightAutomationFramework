"""TC06 - Login rejects bad credentials without revealing which.

A wrong password and an unknown email must fail identically, so the form
cannot be used to find out which addresses have accounts.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import config
from framework.soft_assert import SoftAssert, holds
from pages import LoginPage, RegisterPage

ACCOUNT = config.DEMO_ACCOUNT
REJECTED = config.LOGIN_REJECTED

UNKNOWN_EMAIL = "nobody@shop.test"
WRONG_PASSWORD = "NotThePassword1"


@allure.feature("Authentication")
@allure.story("Rejecting bad credentials")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC06 - Login rejects bad credentials without revealing which")
@pytest.mark.sanity
@pytest.mark.regression
def test_login_rejects_bad_credentials_without_revealing_which(shop, base_url):
    page = shop
    soft = SoftAssert()
    login, register = LoginPage(page), RegisterPage(page)

    signed_out = login.login_link

    with soft.step("Step 1 - a real account with the wrong password"):
        login.open(base_url)
        wrong_password = login.attempt(ACCOUNT["email"], WRONG_PASSWORD)
        allure.dynamic.parameter("wrong password says", wrong_password)

        soft.check("the attempt is refused",
                   holds(wrong_password == REJECTED,
                         f"the page said {wrong_password!r}"))
        soft.check("no session is created",
                   lambda: expect(signed_out).to_be_visible())

        login.capture("wrong password")

    with soft.step("Step 2 - an email with no account"):
        login.open(base_url)
        unknown_email = login.attempt(UNKNOWN_EMAIL, ACCOUNT["password"])
        allure.dynamic.parameter("unknown email says", unknown_email)

        soft.check("the attempt is refused",
                   holds(unknown_email == REJECTED,
                         f"the page said {unknown_email!r}"))
        soft.check("no session is created",
                   lambda: expect(signed_out).to_be_visible())

    with soft.step("Step 3 - the two failures are indistinguishable"):
        # The point of the case: identical wording either way.
        soft.check("both failures use the same wording",
                   holds(wrong_password == unknown_email,
                         f"{wrong_password!r} against {unknown_email!r}"))
        soft.check("the wording names neither the email nor the password",
                   holds("email or password" in wrong_password.lower(),
                         f"the page said {wrong_password!r}"))

    with soft.step("Step 4 - an empty form"):
        login.open(base_url)
        empty = login.attempt("", "")

        soft.check("the empty form is refused too",
                   holds(empty == REJECTED, f"the page said {empty!r}"))
        soft.check("no session is created",
                   lambda: expect(signed_out).to_be_visible())
        soft.check("the login form is still on the page",
                   lambda: expect(login.form).to_be_visible())

        login.capture("empty form refused")

    with soft.step("Step 5 - registering an address already in use"):
        register.open(base_url)
        register.register({**config.NEW_ACCOUNT, "email": ACCOUNT["email"]})
        register.email_error.wait_for()

        soft.check("the duplicate is named as the problem",
                   lambda: expect(register.email_error)
                   .to_have_text(config.EMAIL_TAKEN))
        soft.check("no second account is created and nobody is signed in",
                   lambda: expect(signed_out).to_be_visible())
        soft.check("the visitor stays on the registration page",
                   holds(re.search(r"/register", page.url) is not None,
                         f"landed on {page.url}"))

        register.capture("duplicate registration refused")

    soft.assert_all()
