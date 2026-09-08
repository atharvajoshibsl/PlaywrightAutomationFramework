"""Suggest locator replacements when a testid is missing.

    py ai/self_heal.py [testid] ["what it is for"] [path]

Suggest-only: the model picks the element; Playwright tries locators live.
"""

import inspect
import json
import logging
import sys
from contextlib import contextmanager
from pathlib import Path

import allure
from google import genai
from google.genai import types
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

logging.getLogger("google_genai").setLevel(logging.ERROR)

BASE_URL = "https://atharvajoshi.pythonanywhere.com"
MODEL = "gemini-3.5-flash-lite"

# Weak suggestions are dropped; a missing element may be a real bug.
MIN_CONFIDENCE = 0.6

HERE = Path(__file__).parent
_client = None

# One row per testid (visible only). role/name feed get_by_role.
ELEMENTS_JS = """() => {
  const TAG_ROLES = {a: 'link', button: 'button', select: 'combobox',
    textarea: 'textbox', h1: 'heading', h2: 'heading', h3: 'heading',
    h4: 'heading', h5: 'heading', h6: 'heading', img: 'img', table: 'table',
    ul: 'list', ol: 'list', li: 'listitem', nav: 'navigation', form: 'form'};
  const INPUT_ROLES = {checkbox: 'checkbox', radio: 'radio', submit: 'button',
    button: 'button', number: 'spinbutton', search: 'searchbox'};

  const clean = (value) => (value || '').trim().replace(/\\s+/g, ' ');

  const roleOf = (element, tag) => {
    const explicit = element.getAttribute('role');
    if (explicit) return explicit;
    if (tag === 'input') return INPUT_ROLES[element.type] || 'textbox';
    return TAG_ROLES[tag] || '';
  };

  // Rough accessible name; locator count verifies later.
  const nameOf = (element, tag) => {
    const aria = element.getAttribute('aria-label');
    if (aria) return aria;
    const points = element.getAttribute('aria-labelledby');
    if (points && document.getElementById(points)) {
      return document.getElementById(points).innerText;
    }
    if (element.id) {
      const label = document.querySelector(`label[for="${element.id}"]`);
      if (label) return label.innerText;
    }
    if (tag === 'img') return element.getAttribute('alt') || '';
    if (tag === 'input') return element.getAttribute('placeholder') || '';
    return element.innerText || '';
  };

  const found = new Map();
  const targets = document.querySelectorAll(
      '[data-testid], a, button, input, select, textarea');

  for (const element of targets) {
    if (!element.getClientRects().length) continue;

    const tag = element.tagName.toLowerCase();
    const id = element.getAttribute('data-testid') || '';

    // Own text only; innerText on a wrapper includes children.
    const own = clean([...element.childNodes]
        .filter(node => node.nodeType === Node.TEXT_NODE)
        .map(node => node.textContent).join(' '));
    const text = clean(own || element.value || element.placeholder ||
                       element.getAttribute('aria-label') ||
                       element.innerText).slice(0, 40);

    const key = id || `${tag}|${text}`;
    const seen = found.get(key);
    if (seen) {
      seen.count += 1;
      if (text && seen.texts.length < 3 && !seen.texts.includes(text)) {
        seen.texts.push(text);
      }
      continue;
    }
    found.set(key, {
      tag: tag,
      testid: id,
      texts: text ? [text] : [],
      role: roleOf(element, tag),
      name: clean(nameOf(element, tag)).slice(0, 60),
      placeholder: clean(element.placeholder).slice(0, 40),
      count: 1,
    });
  }
  return [...found.values()];
}"""

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

ANSWER = {
    "type": "object",
    "properties": {
        "selector": {"type": "string"},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["selector", "confidence", "reason"],
}


def api():
    """Lazy client; import does not need an API key."""
    global _client
    if _client is None:
        key = (HERE / "api_key.txt").read_text(encoding="utf-8-sig").strip()
        _client = genai.Client(api_key=key)
    return _client


def elements(page):
    """Targetable elements on an open page."""
    found = page.evaluate(ELEMENTS_JS)
    for item in found:
        # Drop empty fields from the model payload.
        for field in [key for key, value in item.items() if not value]:
            del item[field]
        if item.get("count") == 1:
            del item["count"]
    return found


@contextmanager
def open_page(path):
    """A browser on one page of the shop. For the command line, not tests."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL + path, wait_until="domcontentloaded")
        try:
            yield page
        finally:
            browser.close()


def match(testid, found):
    """The element carrying this testid, or None."""
    if not testid:
        return None
    return next((item for item in found
                 if item.get("testid") == testid), None)


def suggest(testid, purpose, found):
    """Asks which element was meant. Returns a dict, not prose."""
    reply = api().models.generate_content(
        model=MODEL,
        contents=(f"The test wanted data-testid '{testid}', which is "
                  f"{purpose}.\n\nElements on the page now:\n"
                  f"{json.dumps(found)}"),
        config=types.GenerateContentConfig(
            temperature=0,
            system_instruction=RULES,
            response_mime_type="application/json",
            response_schema=ANSWER,
        ),
    )
    return reply.parsed


def is_ok(answer, found):
    """True if confidence is high and the selector is on the page."""
    return (answer["confidence"] >= MIN_CONFIDENCE
            and match(answer["selector"], found) is not None)


def options(page, item):
    """Locator expressions for one element, best first."""
    role, name = item.get("role"), item.get("name")
    tried = []
    if role and name:
        tried.append((f'page.get_by_role("{role}", name="{name}")',
                      page.get_by_role(role, name=name)))
    if item.get("testid"):
        tried.append((f'page.get_by_test_id("{item["testid"]}")',
                      page.get_by_test_id(item["testid"])))
    if item.get("placeholder"):
        tried.append((f'page.get_by_placeholder("{item["placeholder"]}")',
                      page.get_by_placeholder(item["placeholder"])))
    if role:
        tried.append((f'page.get_by_role("{role}")', page.get_by_role(role)))
    if item.get("texts"):
        tried.append((f'page.get_by_text("{item["texts"][0]}", exact=True)',
                      page.get_by_text(item["texts"][0], exact=True)))
    return tried


def best_locator(page, item):
    """First locator with count==1 on the live page, else best guess."""
    tried = options(page, item)
    for code, locator in tried:
        try:
            if locator.count() == 1:
                return code, True
        except PlaywrightError:
            # Bad role or text; try the next expression.
            continue
    return (tried[0][0], False) if tried else (None, False)


class Healer:
    """Collect testids via find(), then suggest fixes for missing ones."""

    def __init__(self, page):
        self.page = page
        self.wanted = {}

    def find(self, testid, purpose):
        """Remember testid, purpose, and caller file:line for suggestions."""
        caller = inspect.currentframe().f_back
        self.wanted[testid] = {
            "purpose": purpose,
            "at": f"{Path(caller.f_code.co_filename).name}:{caller.f_lineno}",
        }
        return self.page.get_by_test_id(testid)

    def report(self):
        """Print and attach suggestions for missing locators; silent if none."""
        found = elements(self.page)
        missing = [(testid, asked) for testid, asked in self.wanted.items()
                   if not match(testid, found)]
        if not missing:
            return ""

        text = "\n".join(
            self._block(number, testid, asked, found)
            for number, (testid, asked) in enumerate(missing, start=1))

        with allure.step(f"Healing suggestions for {len(missing)} of "
                         f"{len(self.wanted)} locators"):
            print(f"\n[heal] {len(missing)} of {len(self.wanted)} locators are "
                  f"not on the page:\n\n{text}")
            allure.attach(text, name="self-healing suggestions",
                          attachment_type=allure.attachment_type.TEXT)
        return text

    def _block(self, number, testid, asked, found):
        """The locator the test used, then the one to use instead."""
        answer = suggest(testid, asked["purpose"], found)
        if not is_ok(answer, found):
            fix = "nothing matches, may be a defect"
        else:
            code, only_one = best_locator(self.page,
                                          match(answer["selector"], found))
            fix = f"{code}  ({answer['confidence']:.2f})"
            if not only_one:
                fix += "  [add .first]"

        return (f"{number}) actual:    page.get_by_test_id(\"{testid}\")\n"
                f"   suggested: {fix}\n"
                f"   at:        {asked['at']}\n")


if __name__ == "__main__":
    testid = sys.argv[1] if len(sys.argv) > 1 else "add-to-cart-button"
    purpose = (sys.argv[2] if len(sys.argv) > 2
               else "the button that adds the selected variant to the cart")
    path = sys.argv[3] if len(sys.argv) > 3 else "/product/mechanical-keyboard"

    print(f"reading {BASE_URL}{path}")
    with open_page(path) as page:
        found = elements(page)
        print(f"  {len(found)} elements offered to the model\n")
        print(f'actual:    page.get_by_test_id("{testid}")')

        # Skip the model call if the testid is still on the page.
        if match(testid, found):
            print("suggested: nothing to heal, it is still on the page")
            sys.exit(0)

        answer = suggest(testid, purpose, found)
        if not is_ok(answer, found):
            print("suggested: nothing matches, may be a defect")
            print(f"reason:    {answer['reason']}")
            sys.exit(1)

        code, only_one = best_locator(page, match(answer["selector"], found))
        print(f"suggested: {code}  ({answer['confidence']:.2f})"
              f"{'' if only_one else '  [add .first]'}")
        print(f"reason:    {answer['reason']}")
