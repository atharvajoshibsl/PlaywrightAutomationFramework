"""TC06 - Login rejects bad credentials without revealing which.

A wrong password and an unknown email must fail identically, so the form
cannot be used to find out which addresses have accounts.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from framework import actions, config
from framework.soft_assert import SoftAssert, holds

ACCOUNT = config.DEMO_ACCOUNT
REJECTED = config.LOGIN_REJECTED

UNKNOWN_EMAIL = "nobody@shop.test"
WRONG_PASSWORD = "NotThePassword1"


def attempt(page, base_url, email, password):
    """Submit the login form and return the error it comes back with."""
    page.goto(f"{base_url}/login")
    page.get_by_test_id("login-email").fill(email)
    page.get_by_test_id("login-password").fill(password)
    page.get_by_test_id("login-submit").click()
    error = page.get_by_test_id("login-error")
    error.wait_for()
    return error.inner_text().strip()


@allure.feature("Authentication")
@allure.story("Rejecting bad credentials")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC06 - Login rejects bad credentials without revealing which")
@pytest.mark.sanity
@pytest.mark.regression
def test_login_rejects_bad_credentials_without_revealing_which(shop, base_url):
    page = shop
    soft = SoftAssert()

    signed_out = page.get_by_test_id("nav-login")

    with soft.step("Step 1 - a real account with the wrong password"):
        wrong_password = attempt(page, base_url, ACCOUNT["email"],
                                 WRONG_PASSWORD)
        allure.dynamic.parameter("wrong password says", wrong_password)

        soft.check("the attempt is refused",
                   holds(wrong_password == REJECTED,
                         f"the page said {wrong_password!r}"))
        soft.check("no session is created",
                   lambda: expect(signed_out).to_be_visible())

        actions.capture(page, "wrong password")

    with soft.step("Step 2 - an email with no account"):
        unknown_email = attempt(page, base_url, UNKNOWN_EMAIL,
                                ACCOUNT["password"])
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
        empty = attempt(page, base_url, "", "")

        soft.check("the empty form is refused too",
                   holds(empty == REJECTED, f"the page said {empty!r}"))
        soft.check("no session is created",
                   lambda: expect(signed_out).to_be_visible())
        soft.check("the login form is still on the page",
                   lambda: expect(page.get_by_test_id("login-form"))
                   .to_be_visible())

        actions.capture(page, "empty form refused")

    with soft.step("Step 5 - registering an address already in use"):
        page.goto(f"{base_url}/register")
        actions.register(page, {**config.NEW_ACCOUNT,
                                "email": ACCOUNT["email"]})
        page.get_by_test_id("error-email").wait_for()

        soft.check("the duplicate is named as the problem",
                   lambda: expect(page.get_by_test_id("error-email"))
                   .to_have_text(config.EMAIL_TAKEN))
        soft.check("no second account is created and nobody is signed in",
                   lambda: expect(signed_out).to_be_visible())
        soft.check("the visitor stays on the registration page",
                   holds(re.search(r"/register", page.url) is not None,
                         f"landed on {page.url}"))

        actions.capture(page, "duplicate registration refused")

    soft.assert_all()
