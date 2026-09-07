"""Suggests a replacement for a locator the page no longer has.

Usage: py ai/heal_locator.py [testid] ["what it is for"] [path]

The default run asks for "add-to-cart-button" on a page that labels its button
"add-to-cart" - a test left stale by a rename. Nothing is repaired; the
suggestion is printed for a human to accept.
"""

import json
import logging
import sys
from pathlib import Path

from google import genai
from google.genai import types

from page_inventory import BASE_URL, collect

logging.getLogger("google_genai").setLevel(logging.ERROR)

MODEL = "gemini-3.5-flash-lite"

# A missing element may be a real bug, so weak suggestions are thrown away.
MIN_CONFIDENCE = 0.6

HERE = Path(__file__).parent
client = genai.Client(
    api_key=(HERE / "api_key.txt").read_text(encoding="utf-8-sig").strip())

RULES = """You repair broken test locators. A test looked for an element by its
data-testid and no longer finds it. You are given what the test wanted, a
description of its purpose, and an inventory of the elements now on the page.

- Choose a testid from the inventory. Never invent one.
- Match on what an element does, not on how much its name resembles the old one.
  A form or a navigation link that merely mentions the same words is not the
  control itself; prefer the element a user would actually operate.
- confidence runs from 0 to 1.
- If nothing in the inventory does the job, return an empty selector with low
  confidence. A missing element may be a genuine bug, and a guess would hide it."""

SCHEMA = {
    "type": "object",
    "properties": {
        "selector": {"type": "string"},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["selector", "confidence", "reason"],
}


def suggest(wanted, intent, inventory):
    """Asks for one replacement testid as a dict, not prose."""
    response = client.models.generate_content(
        model=MODEL,
        contents=(f"The test wanted data-testid '{wanted}', which is "
                  f"{intent}.\n\nElements on the page now:\n"
                  f"{json.dumps(inventory)}"),
        config=types.GenerateContentConfig(
            temperature=0,
            system_instruction=RULES,
            response_mime_type="application/json",
            response_schema=SCHEMA,
        ),
    )
    return response.parsed


def row_for(testid, inventory):
    """The inventory row carrying this testid, or None."""
    if not testid:
        return None
    return next((item for item in inventory
                 if item["testid"] == testid), None)


def accept(proposal, inventory):
    """The model proposes, code decides. Returns why it was refused, or None."""
    if proposal["confidence"] < MIN_CONFIDENCE:
        return f"confidence {proposal['confidence']} is below {MIN_CONFIDENCE}"
    if not row_for(proposal["selector"], inventory):
        return f"'{proposal['selector']}' is not on the page"
    return None


wanted = sys.argv[1] if len(sys.argv) > 1 else "add-to-cart-button"
intent = (sys.argv[2] if len(sys.argv) > 2
          else "the button that adds the selected variant to the cart")
path = sys.argv[3] if len(sys.argv) > 3 else "/product/mechanical-keyboard"

print(f"reading {BASE_URL}{path}")
inventory = collect(path)[1]
print(f"  {len(inventory)} elements offered to the model\n")

print(f"broken locator: get_by_test_id(\"{wanted}\")")
print(f"  intent:     {intent}")

# Checked before anything is spent: a working locator is not a heal.
if row_for(wanted, inventory):
    print("\nStill on the page. Nothing to heal.")
    sys.exit(0)

proposal = suggest(wanted, intent, inventory)
print(f"  suggestion: {proposal['selector'] or '(none)'}")
print(f"  confidence: {proposal['confidence']}")
print(f"  reason:     {proposal['reason']}")

refused = accept(proposal, inventory)
if refused:
    print(f"\nRejected: {refused}")
    print("The test should fail. Do not heal what might be a real bug.")
    sys.exit(1)

print("\nAccepted. Suggested fix for the test:")
print(f"  page.get_by_test_id(\"{proposal['selector']}\")")

# A shared testid is still the right answer, but cannot stand alone.
matches = row_for(proposal["selector"], inventory).get("count", 1)
if matches > 1:
    print(f"  ...but it matches {matches} elements, so narrow it with "
          ".first, .nth() or a parent")
