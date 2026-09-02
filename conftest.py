"""Fixtures every test case gets for free.

pytest finds this file automatically - tests never import it. The browser and
page fixtures come from pytest-playwright; the two overrides below only adjust
how it launches. Everything else here exists so a test case can open with a
known-good shop and say nothing about setup.
"""

from pathlib import Path

import pytest

from framework import reporting

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"

# Wiped by --clean-alluredir on every run.
ALLURE_RESULTS = REPORTS / "allure-results"

# The multi-file report, generated only so its history folder can be kept.
ALLURE_REPORT = REPORTS / "allure-report"

# Survives the wipe, and is what makes each report cumulative.
ALLURE_HISTORY = REPORTS / "allure-history"
BUILD_COUNTER = ALLURE_HISTORY / "build-order.txt"

# One zipped copy of each run's raw results, never overwritten. Small enough
# to keep forever, and tools/view_run.py renders any of them back to HTML.
RUNS = REPORTS / "runs"

# The only HTML kept, rewritten every run. Stable path, so you can leave it
# open in a browser tab and refresh.
LATEST_REPORT = REPORTS / "latest-report.html"


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Maximises the window, on top of whatever pytest-playwright decided.

    Takes the plugin's own dict as an argument and adds to it, so --headed,
    --slowmo and friends keep working instead of being overwritten.
    """
    return {**browser_type_launch_args, "args": ["--start-maximized"]}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Lets the page fill the real window instead of a fixed 1280x720.

    Without this, --start-maximized gives you a maximised window with a small
    page painted inside it.
    """
    return {**browser_context_args, "no_viewport": True}


@pytest.fixture
def shop(page, base_url):
    """A loaded home page whose shop is back at its seeded starting state.

    The reset is explicit rather than relying on a fresh browser profile.
    Every visitor gets their own database keyed to a session cookie, so a new
    browser happens to start clean - but "happens to" is how test suites rot.
    Asking for the reset means the precondition in TEST_PLAN.xlsx is a step
    that runs, and is visible in the report.
    """
    # Load once so the session cookie exists: reset acts on the caller's own
    # copy of the shop, identified by that cookie.
    page.goto(base_url, wait_until="domcontentloaded")

    # Fired from inside the page rather than through page.request, so it uses
    # the browser's certificate store. Playwright's own HTTP client ships its
    # own CA list and rejects a corporate TLS proxy that the browser accepts.
    outcome = page.evaluate(
        """async () => {
            const response = await fetch('/api/test/reset', {method: 'POST'});
            return {ok: response.ok, status: response.status};
        }"""
    )
    assert outcome["ok"], (
        f"could not reset the shop: HTTP {outcome['status']}. The endpoint "
        "allows 12 resets a minute, so a 429 means the suite resets too often."
    )

    page.reload(wait_until="domcontentloaded")
    return page


def pytest_sessionfinish(session, exitstatus):
    """Builds the HTML report at the end of every run.

    Done here rather than in a separate command so that "run the tests" and
    "have an up to date report" are the same action, and so no run can be
    left unrecorded by forgetting the second step.
    """
    if not ALLURE_RESULTS.exists():
        return

    config = session.config
    order, moment = reporting.write_executor(ALLURE_RESULTS, BUILD_COUNTER)
    reporting.write_environment(ALLURE_RESULTS, {
        "Target": config.getoption("--base-url") or "(pytest.ini default)",
        # getoption returns a list because --browser is repeatable.
        "Browser": ", ".join(config.getoption("--browser") or ["chromium"]),
        "Headed": config.getoption("--headed"),
        "Run": f"{order} at {moment:%d %b %Y, %H:%M:%S}",
        "Test plan": "TEST_PLAN.xlsx",
    })

    html = reporting.build(ALLURE_RESULTS, ALLURE_REPORT, ALLURE_HISTORY,
                           LATEST_REPORT)
    if not html:
        return

    # Archived after the build, so the zip includes the history that was
    # copied in and the run renders identically when replayed.
    archive = reporting.archive_results(ALLURE_RESULTS, RUNS, order, moment)
    kept, megabytes = reporting.summarise(RUNS)

    print(f"\n[report] run {order} at {moment:%d %b %Y, %H:%M:%S}")
    print(f"[report] report:  {html}")
    print(f"[report] archive: {archive.name} "
          f"({archive.stat().st_size / 1024:.0f} KB)")
    print(f"[report] {kept} run(s) archived, {megabytes:.1f} MB total")
