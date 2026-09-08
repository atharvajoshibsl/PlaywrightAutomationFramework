"""Prices the way the app shows them, and back again."""

import re


def rupees(text):
    """A displayed price as an integer: "\u20b93,499" -> 3499."""
    return int(re.sub(r"\D", "", text))


def money(amount):
    """An integer in the app's format: 3499 -> "\u20b93,499"."""
    return f"\u20b9{amount:,}"


def plain(amount):
    """The same number without the rupee sign, for labels the console prints."""
    return f"{amount:,}"
