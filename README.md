# AItomationKart — Playwright Automation Framework

Python + Playwright + pytest test suite for [AItomationKart](https://atharvajoshi.pythonanywhere.com),
a demo e-commerce site built specifically to be automated against.

> **Status: work in progress.** The framework skeleton, fixtures and Allure
> reporting are in place, and 2 of the 17 planned test cases are automated.
> The remaining cases are written up in `TEST_PLAN.xlsx` and are being added
> one at a time, so this repository grows case by case rather than landing
> fully formed.

- **Application under test:** https://atharvajoshi.pythonanywhere.com
- **Application source:** https://github.com/atharvajoshibsl/AItomationKart
- **Test plan:** `TEST_PLAN.xlsx` — 17 active cases, 9 deferred to a later phase

## Automation status

| Case | Name | Area | Suite | Status |
|------|------|------|-------|--------|
| TC01 | Home page renders the full expected interface | Interface | Smoke | Automated |
| TC02 | Catalogue search, clear, category filter and sort | Catalogue | Smoke | Automated |
| TC03 | Product detail opens from a card and adds to the cart | Product detail | Smoke | Planned |
| TC04 | Cart quantities, line totals and clearing | Cart | Smoke | Planned |
| TC05 | Sign in, sign out and registration | Auth | Smoke | Planned |
| TC06 | Login rejects bad credentials without revealing which | Auth | Regression | Planned |
| TC07 | Guest cart survives sign-in | Guest flow | Regression | Planned |
| TC08 | Checkout summary is accurate and places the order | Checkout | Smoke | Planned |
| TC09 | Checkout is refused with an empty cart | Checkout | Regression | Planned |
| TC10 | Card payment: decline, expiry and successful retry | Payment | Regression | Planned |
| TC11 | UPI payment approves after its window | Payment | Regression | Planned |
| TC12 | Wallet payment succeeds and is refused when short | Payment | Regression | Planned |
| TC13 | Order history and detail match what was bought | Orders | Regression | Planned |
| TC14 | Another account's order is not reachable | Orders | Regression | Planned |
| TC15 | Profile details and address book | Profile | Regression | Planned |
| TC16 | Health and reset return a known starting state | Test API | Smoke | Planned |
| TC17 | Each visitor is isolated from another's reset | Test API | Regression | Planned |

The full steps, preconditions and expected results for every case live in
`TEST_PLAN.xlsx`. The nine `TCF_*` rows below the active table are deferred
scope, kept outside the autofilter range so they never mix with the working set.

## Prerequisites

| Requirement | Why |
|-------------|-----|
| Python 3.10+ | Runs the suite |
| Playwright browsers | Downloaded separately from the pip package |
| Java 11+ (JDK) | The Allure CLI is a Java tool |
| Allure CLI | Renders the JSON that `allure-pytest` writes into HTML |

Node is only needed if you install the Allure CLI through npm, which is the
easiest route on Windows.

## Setup

```powershell
git clone https://github.com/atharvajoshibsl/PlaywrightAutomationFramework.git
cd PlaywrightAutomationFramework

py -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install
```

Then install the reporting toolchain:

```powershell
winget install --id Microsoft.OpenJDK.21
npm install -g allure-commandline
```

Both must be on `PATH`. Verify with `java -version` and `allure --version`,
restarting the terminal first so it picks up the new `PATH`. If `allure` is
missing the suite still runs and still passes — it just prints where the raw
results are instead of building HTML.

## Running the suite

```powershell
py -m pytest                                  # everything, headless
py -m pytest --headed                         # watch it drive the browser
py -m pytest -m smoke                         # one suite
py -m pytest tests/test_tc01_home_page_renders_full_expected_interface.py
py -m pytest --base-url http://127.0.0.1:8000 # a local copy of the app
py -m pytest --browser firefox --browser webkit
```

`pytest.ini` points `base_url` at the hosted site, so a plain `py -m pytest`
tests production without any arguments. The `--headed`, `--browser`, `--slowmo`
and `--tracing` flags come from `pytest-playwright`.

Because `addopts` carries `--clean-alluredir`, each run starts from an empty
results directory and the report never mixes two runs. Run a single file and
the report contains only that file.

## Reporting

Every run ends by building its own report — running the tests and having an
up-to-date report are the same action, so no run can go unrecorded.

- **`reports/latest-report.html`** — the report you open. A self-contained
  single file with screenshots base64-embedded, so it can be emailed or
  attached as-is. Overwritten every run, so you can leave it open in a tab and
  refresh. Roughly 4 MB.
- **`reports/runs/run-NNN_<timestamp>.zip`** — a permanent record of each run's
  raw results, including screenshots. Between 120 KB and 1 MB per run, versus
  ~4 MB if finished HTML were kept, because most of a single-file report is a
  byte-identical copy of Allure's viewer.
- **`reports/allure-history/`** — carried across runs so each report shows the
  trend chart and each test's record of earlier executions.

Re-render any archived run on demand:

```powershell
py tools/view_run.py        # list what is archived
py tools/view_run.py 18     # rebuild run 18 and open it
```

Nothing under `reports/` is committed. It is all rebuilt by a run, and the
directories are created automatically.

### Screenshots

Screenshots are never written as loose files. `page.screenshot()` returns bytes
and `allure.attach` files them against the open step, so they appear inside the
step that produced them rather than in a pile at the end of the test. They are
JPEG at quality 70 — around a quarter the size of PNG, for evidence nobody
inspects pixel by pixel.

## Layout

```
PlaywrightAutomation/
├─ conftest.py        Fixtures every test gets for free, plus the end-of-run
│                     report build. pytest finds this automatically.
├─ pytest.ini         Target URL, Allure output, marker declarations
├─ requirements.txt
├─ TEST_PLAN.xlsx     The reviewable plan: 17 active cases, 9 deferred
├─ framework/
│  ├─ config.py       What the app is expected to contain — the suite's oracle
│  ├─ soft_assert.py  Assertions that record a failure instead of ending the test
│  └─ reporting.py    History handling, report generation, run archiving
├─ tests/
│  ├─ test_tc01_home_page_renders_full_expected_interface.py
│  └─ test_tc02_catalogue_search_clear_category_filter_and_sort.py
├─ ai/
│  ├─ design_tests.py  Drafts test cases from a feature, in the plan's format
│  └─ feature.txt      The feature to draft from — replace with your own ticket
└─ tools/
   ├─ build_test_plan.py  Regenerates TEST_PLAN.xlsx from Python source
   └─ view_run.py         Rebuilds an archived run into HTML
```

## AI capability (exploratory)

`ai/` is where the LLM work goes. Nothing in `tests/` imports it, and that
separation is deliberate: everything in `framework/` reaches the same verdict on
the same page every time, and a model does not promise that.

`ai/design_tests.py` drafts test cases from a feature description, in the same
columns as the Test Cases sheet. It is how the plan is meant to grow — from a
ticket or an HLD, rather than by reading the finished site and writing tests to
match it.

Paste your Gemini key into `ai/api_key.txt` once, put a feature into
`ai/feature.txt`, then:

```powershell
py ai/design_tests.py
```

It asks how many cases you want and which feature area, writes them to
`ai/ai_test_cases.csv`, and lists any acceptance criterion no case covers. Read
the CSV, type what to improve, and the same rows are rewritten. Copy the cases
worth keeping into `TEST_PLAN.xlsx` yourself — the AI never writes to the plan.

Two things carry the output quality: the response schema, whose enums make an
invalid Suite, Scope or Priority impossible, and TC01 and TC02 embedded in the
prompt as worked examples. Without those examples the model splits one rendering
case into one case per page section.

The model is `gemini-3.5-flash-lite`, one constant at the top of the file.
Flash-Lite is the free tier's workhorse at roughly 15 calls a minute; plain
Flash is stronger but a new key only gets around 20 calls a day on it. Pro
models left the free tier in April 2026, and `gemini-2.5-flash` now 404s for
newly created keys, so older tutorials will mislead you.

## Design decisions

**Soft assertions for verifications, hard failures for actions.** A rendering
case verifies dozens of independent facts about one page. With plain asserts the
first bad one hides the rest, so you fix, re-run, and discover the next — once
per defect. `SoftAssert.check` collects outcomes and fails once at the end, so
one run tells you everything. Actions stay hard: if "Add to cart" does not
click, every later assertion about the cart is noise pointing at the wrong
thing.

**Expected data lives in `framework/config.py`, not in assertions.** The answer
to "what is correct" sits in one readable place. When the shop adds a category,
one line changes there and every test that cares fails until it does.

**Locators are `data-testid` only.** The application was built with test ids
throughout, so no test depends on CSS structure or visible copy. The single
exception is the product card image, which has no id yet.

**Every test starts from a known state.** The `shop` fixture calls the app's
reset endpoint, so a case opens with 16 products, 53 variants, 2 accounts and no
orders. Each visitor gets a database keyed to their session cookie, so runs
cannot interfere with each other or with anyone browsing the live site. The
reset is explicit rather than relying on a fresh browser profile: "happens to
start clean" is how suites rot.

**One case per page or flow, not one per click.** Several checks on the same
page are steps inside one case. Interface rendering is covered exactly once, by
TC01; every other case asserts behaviour rather than presence.

## Adding a test case

1. Read the case in `TEST_PLAN.xlsx`.
2. Copy `tests/test_tc02_*.py` as the pattern: module docstring naming the case,
   `@allure.feature`/`story`/`severity`/`title`, pytest suite markers, then one
   `allure.step` per plan step in the plan's own wording.
3. Take the `shop` fixture for a reset home page. Use plain Playwright calls for
   actions and `soft.check` for the observations that follow them.
4. Put any new expected values in `framework/config.py`.
5. Call `soft.assert_all()` last.
6. Name the file `test_tcNN_<case name in snake case>.py` so the file, the
   report title and the plan row all read the same.

## Editing the test plan

`TEST_PLAN.xlsx` is generated, so edit `tools/build_test_plan.py` and re-run it
rather than editing the workbook. That keeps the plan reviewable as a diff in
git instead of only inside a binary file.

```powershell
py tools/build_test_plan.py
```

Close the workbook first — Excel holds a write lock while it is open.

## Roadmap

- Automate TC03 onward, one case at a time
- Refactor the shared page interactions into page objects once enough cases
  exist to show what actually repeats
- GitHub Actions workflow with the report published to Pages
- Parallel execution once the cases are independent enough to allow it
- An API-level layer alongside the UI cases
- More of the AI side: retrieval over the existing plan so drafts do not
  duplicate coverage, then AI-assisted triage of failures in the report

## Author

Atharva Joshi — built alongside
[AItomationKart](https://github.com/atharvajoshibsl/AItomationKart), the demo
shop it tests.
