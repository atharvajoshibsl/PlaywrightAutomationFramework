"""Shared pytest fixtures. Tests never import this file."""

from pathlib import Path

import pytest

from framework import reporting

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"

# Cleared each run by --clean-alluredir.
ALLURE_RESULTS = REPORTS / "allure-results"

# Multi-file report; kept for its history folder.
ALLURE_REPORT = REPORTS / "allure-report"

# Persists across runs for trend history.
ALLURE_HISTORY = REPORTS / "allure-history"
BUILD_COUNTER = ALLURE_HISTORY / "build-order.txt"

# One zip per run; replay with tools/view_run.py.
RUNS = REPORTS / "runs"

# Latest HTML; stable path to refresh in a browser tab.
LATEST_REPORT = REPORTS / "latest-report.html"


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Add --start-maximized to pytest-playwright launch args."""
    return {**browser_type_launch_args, "args": ["--start-maximized"]}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Disable fixed viewport so page fills the maximized window."""
    return {**browser_context_args, "no_viewport": True}


@pytest.fixture
def shop(page, base_url):
    """Load home page and reset shop to seeded state."""
    # Load first so session cookie exists for reset.
    page.goto(base_url, wait_until="domcontentloaded")

    # fetch() uses browser TLS certs, not Playwright's HTTP client.
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
    """Build Allure HTML report after the test session."""
    if not ALLURE_RESULTS.exists():
        return

    config = session.config
    order, moment = reporting.write_executor(ALLURE_RESULTS, BUILD_COUNTER)
    reporting.write_environment(ALLURE_RESULTS, {
        "Target": config.getoption("--base-url") or "(pytest.ini default)",
        # --browser is repeatable; getoption returns a list.
        "Browser": ", ".join(config.getoption("--browser") or ["chromium"]),
        "Headed": config.getoption("--headed"),
        "Run": f"{order} at {moment:%d %b %Y, %H:%M:%S}",
        "Test plan": "TEST_PLAN.xlsx",
    })

    html = reporting.build(ALLURE_RESULTS, ALLURE_REPORT, ALLURE_HISTORY,
                           LATEST_REPORT)
    if not html:
        return

    # Archive after build so zip includes copied history.
    archive = reporting.archive_results(ALLURE_RESULTS, RUNS, order, moment)
    kept, megabytes = reporting.summarise(RUNS)

    print(f"\n[report] run {order} at {moment:%d %b %Y, %H:%M:%S}")
    print(f"[report] report:  {html}")
    print(f"[report] archive: {archive.name} "
          f"({archive.stat().st_size / 1024:.0f} KB)")
    print(f"[report] {kept} run(s) archived, {megabytes:.1f} MB total")
