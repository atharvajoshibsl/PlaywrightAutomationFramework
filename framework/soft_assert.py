"""Soft assertions: collect failures and fail once at the end.

Use for verifications only; actions should fail hard on first error.
"""

from contextlib import contextmanager

import allure


class _StepFailed(AssertionError):
    """Marks an Allure step failed (not broken)."""


def holds(condition, detail):
    """Wrap a boolean check as a callable for SoftAssert.check."""
    def assertion():
        assert condition, detail

    return assertion


class SoftAssert:
    """Collects check outcomes, then fails the test once at the end."""

    def __init__(self):
        self.failures = []
        self.passed = 0

    @contextmanager
    def step(self, name):
        """Allure step that turns red if a soft check inside failed."""
        before = len(self.failures)
        try:
            with allure.step(name):
                yield
                if len(self.failures) > before:
                    raise _StepFailed(
                        f"{len(self.failures) - before} of this step's checks "
                        "failed")
        except _StepFailed:
            pass

    def check(self, label, assertion):
        """Run one assertion; record failure without raising."""
        try:
            # Run inside allure.step so failures show in the report.
            with allure.step(label):
                assertion()
        except AssertionError as error:
            # First line is enough from Playwright's multi-line error.
            detail = str(error).strip().splitlines()[0]
            self.failures.append((label, detail))
            print(f"  FAIL  {label}\n        {detail}")
        else:
            self.passed += 1
            print(f"  ok    {label}")

    def assert_all(self):
        """Fail if any checks failed. Call at end of test, not teardown."""
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
