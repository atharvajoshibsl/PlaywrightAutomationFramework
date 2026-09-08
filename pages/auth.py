"""Login and registration."""

from pages.base import BasePage


class LoginPage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self.form = page.get_by_test_id("login-form")
        self.email = page.get_by_test_id("login-email")
        self.password = page.get_by_test_id("login-password")
        self.submit = page.get_by_test_id("login-submit")
        self.message = page.get_by_test_id("login-error")

        # Carries the page the visitor was sent here from.
        self.next_field = page.locator("input[name='next']")

    def open(self, base_url):
        self.page.goto(f"{base_url}/login")

    def fill(self, email, password):
        self.email.fill(email)
        self.password.fill(password)
        self.submit.click()

    def sign_in(self, account):
        """Sign in and wait for the header to show a session."""
        self.fill(account["email"], account["password"])
        self.logout_link.wait_for()

    def attempt(self, email, password):
        """Submit credentials that should fail and return what the page said."""
        self.fill(email, password)
        self.message.wait_for()
        return self.message.inner_text().strip()


class RegisterPage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self.name = page.get_by_test_id("register-name")
        self.email = page.get_by_test_id("register-email")
        self.phone = page.get_by_test_id("register-phone")
        self.password = page.get_by_test_id("register-password")
        self.confirm_password = page.get_by_test_id("register-confirm-password")
        self.submit = page.get_by_test_id("register-submit")
        self.email_error = page.get_by_test_id("error-email")

    def open(self, base_url):
        self.page.goto(f"{base_url}/register")

    def register(self, account):
        self.name.fill(account["name"])
        self.email.fill(account["email"])
        self.phone.fill(account["phone"])
        self.password.fill(account["password"])
        self.confirm_password.fill(account["password"])
        self.submit.click()
