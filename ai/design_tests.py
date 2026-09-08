"""Draft test cases from ai/feature.txt.

    py ai/design_tests.py

Writes ai/ai_test_cases.csv. Does not touch TEST_PLAN.xlsx.
"""

import csv
import json
import logging
from pathlib import Path

from google import genai
from google.genai import types

logging.getLogger("google_genai").setLevel(logging.ERROR)

MODEL = "gemini-3.5-flash-lite"

# AI ids use their own prefix, separate from hand-written TC01-TC17.
ID_PREFIX = "AI"

HERE = Path(__file__).parent
FEATURE_FILE = HERE / "feature.txt"
OUT_FILE = HERE / "ai_test_cases.csv"

# Same columns as the Test Cases sheet.
HEADERS = ["Test Case ID", "Feature Area", "Suite", "Scope", "Priority",
           "Test Case Name", "Preconditions", "Steps", "Expected Result",
           "Automation Status", "Notes"]

# Model fills eight fields; enums restrict Suite, Scope and Priority.
SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "Feature Area": {"type": "string"},
            "Suite": {"type": "string",
                      "enum": ["Smoke", "Sanity", "Regression"]},
            "Scope": {"type": "string",
                      "enum": ["Feature", "End-to-End", "Negative"]},
            "Priority": {"type": "string", "enum": ["P1", "P2"]},
            "Test Case Name": {"type": "string"},
            "Preconditions": {"type": "string"},
            "Steps": {"type": "string"},
            "Expected Result": {"type": "string"},
        },
        "required": ["Feature Area", "Suite", "Scope", "Priority",
                     "Test Case Name", "Preconditions", "Steps",
                     "Expected Result"],
    },
}

# Two real plan cases as style examples (TC01 covers full-page rendering).
EXAMPLES = """{
  "Feature Area": "Interface",
  "Suite": "Smoke",
  "Scope": "Feature",
  "Priority": "P1",
  "Test Case Name": "Home page renders the full expected interface",
  "Preconditions": "Shop reset to its starting state: 16 products, 53 variants, 2 accounts, no orders",
  "Steps": "1. Open the site root.\\n2. Inspect the header: wordmark, tagline, search box, theme toggle, cart link with count, Sign in and Register links.\\n3. Inspect the filter and sort controls: all four category filters and every sort option.\\n4. Inspect the result count and the anatomy of one product card: image, brand, name, price, rating, stock badge.\\n5. Inspect the footer: framework list and copyright line.",
  "Expected Result": "Every element is present and populated, and the count reads 16 products found. This is the only interface-rendering case in the plan; every other case asserts behaviour, not presence."
}
{
  "Feature Area": "Catalogue",
  "Suite": "Smoke",
  "Scope": "Feature",
  "Priority": "P1",
  "Test Case Name": "Catalogue search, clear, category filter and sort",
  "Preconditions": "Shop reset to its starting state: 16 products, 53 variants, 2 accounts, no orders",
  "Steps": "1. Open the site root and confirm the count reads 16 products found.\\n2. Search for 'sandal'; confirm only Trail Sandals is listed and the count reads 1.\\n3. Clear the search box using the Clear control; confirm all 16 products return and the box is empty.",
  "Expected Result": "Every step behaves as described. Clearing the search used to leave the filtered listing in place, so step 3 is a regression guard."
}"""

CONVENTIONS = f"""You write functional test cases for a QA team, in their house
style. Return 3 to 6 cases, unless the tester asks for a particular number, in
which case return exactly that many.

- Functional behaviour only. One case per page or per flow, never one per click.
- Never split presence checks by page section. A page's rendering is one single
  case, with one step per area - header, controls, listing, footer - not a case
  each. At most one rendering case exists per feature; everything else asserts
  behaviour rather than presence.
- Use Negative scope only when rejecting bad input is the whole point of a case.
- Steps are numbered lines - "1. ", "2. " - each an action followed by what to
  confirm once it is done.
- Preconditions name the starting state, such as the shop reset to 16 products,
  53 variants, 2 accounts and no orders.
- Expected Result must name concrete values: counts, exact strings, the specific
  behaviour. Never write correctly, properly, accurately, successfully or as
  expected - a tester cannot fail a case against those words. Say plainly if a
  step guards against a past regression.
- Suite is the lowest suite a case belongs to. Smoke is the minimum confidence
  that the build is usable, Sanity is a focused check on one area, Regression is
  everything else.
- Feature Area: use the area the tester asks for. Otherwise reuse one of
  Interface, Catalogue, Product detail, Cart, Auth, Guest flow, Checkout,
  Payment, Orders, Profile, Test API.
- Cover every acceptance criterion, including any conditional one such as an
  element hidden at a given window width. Invent no behaviour the feature does
  not mention, and write nothing for what it lists as out of scope.

Here are two of the team's existing cases, as examples of the style and the
level of detail expected:

{EXAMPLES}"""

client = genai.Client(
    api_key=(HERE / "api_key.txt").read_text(encoding="utf-8-sig").strip())


def draft(feature, notes, previous=None):
    """One schema-constrained call. previous is set when redrafting."""
    request = [f"Feature:\n\n{feature}"]
    if notes:
        request.append(f"What the tester asked for:\n{notes}")
    if previous:
        request.append(f"Your previous draft:\n{json.dumps(previous, indent=2)}"
                       "\n\nRewrite it to address the tester's latest note. "
                       "Leave anything they did not mention as it was.")

    response = client.models.generate_content(
        model=MODEL,
        contents="\n\n".join(request),
        config=types.GenerateContentConfig(
            temperature=0,
            system_instruction=CONVENTIONS,
            response_mime_type="application/json",
            response_schema=SCHEMA,
        ),
    )
    return response.parsed


def uncovered(feature, cases):
    """Names acceptance criteria no case covers, so a gap is not silent."""
    response = client.models.generate_content(
        model=MODEL,
        contents=(f"Feature:\n\n{feature}\n\nCases:\n"
                  f"{json.dumps(cases, indent=2)}"),
        config=types.GenerateContentConfig(
            temperature=0,
            system_instruction=(
                "List the acceptance criteria from the feature that none of "
                "these cases check. Quote each briefly. Ignore anything the "
                "feature lists as out of scope. Return an empty list if nothing "
                "is missing."),
            response_mime_type="application/json",
            response_schema={"type": "array", "items": {"type": "string"}},
        ),
    )
    return response.parsed


def next_number():
    """Continues the numbering, so a later run cannot reuse an id."""
    if not OUT_FILE.exists():
        return 1
    with OUT_FILE.open(encoding="utf-8-sig", newline="") as handle:
        used = [row["Test Case ID"].removeprefix(ID_PREFIX)
                for row in csv.DictReader(handle)
                if row["Test Case ID"].startswith(ID_PREFIX)]
    return max((int(number) for number in used), default=0) + 1


def id_number(row):
    """The numeric part of an id, or 0 for a row this script did not write."""
    name = row["Test Case ID"]
    return int(name.removeprefix(ID_PREFIX)) if name.startswith(ID_PREFIX) else 0


def save(cases, first):
    """Write rows for this run; redraft replaces the same ids in place."""
    kept = []
    if OUT_FILE.exists():
        with OUT_FILE.open(encoding="utf-8-sig", newline="") as handle:
            kept = [row for row in csv.DictReader(handle)
                    if id_number(row) < first]

    with OUT_FILE.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(kept)
        for offset, case in enumerate(cases):
            writer.writerow({**case,
                             "Test Case ID": f"{ID_PREFIX}{first + offset:02d}",
                             "Automation Status": "Not started",
                             "Notes": "AI drafted"})


def report(feature, cases, first):
    """One line per case. The detail belongs in the CSV, not the terminal."""
    print(f"\n{len(cases)} case(s) in {OUT_FILE.name}:")
    for offset, case in enumerate(cases):
        print(f"  {ID_PREFIX}{first + offset:02d}  {case['Suite']:<10} "
              f"{case['Test Case Name']}")
    for gap in uncovered(feature, cases):
        print(f"  [not covered: {gap}]")


feature = FEATURE_FILE.read_text(encoding="utf-8-sig")
print(f"Feature loaded from {FEATURE_FILE.name}, {len(feature.split())} words.")

notes = input("\nHow many cases, which feature area, anything to focus on? "
              "(enter to leave it open) > ").strip()

first = next_number()
cases = draft(feature, notes)
save(cases, first)
report(feature, cases, first)

while True:
    answer = input("\n[enter] if you are happy, or say what to improve > ").strip()
    if not answer or answer in {"quit", "exit"}:
        break
    cases = draft(feature, answer, previous=cases)
    save(cases, first)
    report(feature, cases, first)

print(f"\nDone. Open {OUT_FILE.name} to read the cases in full.")
