"""Assertions that record a failure instead of ending the test.

A rendering case verifies dozens of independent facts about one page. With
plain asserts the first bad one hides the rest, so you fix, re-run, and
discover the next - once per defect. Collecting them means one run tells you
everything.

This is only right for *verifications*. Actions must still fail hard: if
"Add to cart" does not click, every later assertion about the cart is noise
pointing at the wrong thing. So use plain Playwright calls for actions, and
SoftAssert.check for the observations that follow them.
"""

import allure


def holds(condition, detail):
    """Wraps a plain true-or-false fact so SoftAssert.check can run it.

    check() wants a callable, and Playwright's expect() is one - but expect()
    only talks about elements. This covers the few checks about values already
    read off the page, such as whether prices came back in order, where there
    is no single element to point at.
    """
    def assertion():
        assert condition, detail

    return assertion


class SoftAssert:
    """Collects check outcomes, then fails the test once at the end."""

    def __init__(self):
        self.failures = []
        self.passed = 0

    def check(self, label, assertion):
        """Runs one assertion, records the outcome, and never raises.

        The assertion arrives as a callable rather than a value because it
        has to run *inside* the try block. Passing expect(...).to_be_x()
        directly would execute it at the call site and raise there.
        """
        try:
            # Wrapping in allure.step first means the report shows this check
            # as a failed step: the exception sets the step status on its way
            # out, and the except below catches it after the step has closed.
            with allure.step(label):
                assertion()
        except AssertionError as error:
            # Playwright's expect() raises with a multi-line diff. The first
            # line carries the useful part.
            detail = str(error).strip().splitlines()[0]
            self.failures.append((label, detail))
            print(f"  FAIL  {label}\n        {detail}")
        else:
            self.passed += 1
            print(f"  ok    {label}")

    def assert_all(self):
        """Fails the test if anything was recorded as failed.

        Called explicitly at the end of a test rather than in fixture
        teardown, because pytest reports a teardown exception as an error
        rather than a failure and that muddies the report.
        """
        total = self.passed + len(self.failures)
        summary = (f"{self.passed} passed, {len(self.failures)} failed, "
                   f"{total} checks total")
        print(f"\n{summary}")
        allure.attach(summary, name="check summary",
                      attachment_type=allure.attachment_type.TEXT)

        if self.failures:
            lines = "\n".join(f"  - {label}: {detail}"
                              for label, detail in self.failures)
            raise AssertionError(
                f"{len(self.failures)} of {total} checks failed:\n{lines}")
