"""Describes a live page as a short list of elements a test could target.

Usage: py ai/page_inventory.py [path]
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://atharvajoshi.pythonanywhere.com"
OUT_FILE = Path(__file__).parent / "inventory.json"

# Skips anything not rendered, and keeps one row per testid with a count, so 16
# product cards do not become 16 copies of the same testids.
INVENTORY_JS = """() => {
  const found = new Map();
  const candidates = document.querySelectorAll(
      '[data-testid], a, button, input, select, textarea');

  for (const element of candidates) {
    if (!element.getClientRects().length) continue;

    const tag = element.tagName.toLowerCase();
    const testid = element.getAttribute('data-testid') || '';

    // Own text nodes first: innerText on a wrapper repeats all its children.
    const own = [...element.childNodes]
        .filter(node => node.nodeType === Node.TEXT_NODE)
        .map(node => node.textContent).join(' ');
    const label = (own.trim() || element.value || element.placeholder ||
                   element.getAttribute('aria-label') || element.innerText || '')
                  .trim().replace(/\\s+/g, ' ').slice(0, 40);

    const key = testid || `${tag}|${label}`;
    const already = found.get(key);
    if (already) {
      already.count += 1;
      continue;
    }
    found.set(key, {tag: tag, testid: testid, text: label, count: 1});
  }
  return [...found.values()];
}"""


def collect(path):
    """Returns the page's raw HTML and its inventory."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL + path, wait_until="domcontentloaded")
        html, inventory = page.content(), page.evaluate(INVENTORY_JS)
        browser.close()

    for item in inventory:
        if item["count"] == 1:
            del item["count"]
    return html, inventory


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/"
    html, inventory = collect(path)
    OUT_FILE.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    # Tokens run at roughly a quarter of the characters for text like this.
    inventory_chars = len(json.dumps(inventory))
    print(f"{BASE_URL}{path}")
    print(f"  {len(inventory)} distinct elements -> {OUT_FILE.name}")
    print(f"  raw HTML:  {len(html):>6} chars (~{len(html) // 4} tokens)")
    print(f"  inventory: {inventory_chars:>6} chars "
          f"(~{inventory_chars // 4} tokens)")
    print(f"  {len(html) / inventory_chars:.0f}x smaller\n")

    for item in inventory[:8]:
        print(f"  {item}")
    print("  ...")
