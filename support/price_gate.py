#!/usr/bin/env python3
"""price_gate.py — fail closed if any price in the corpus/answer isn't canonical.

The support answerer is extractive, so the ONLY way it can ever emit a wrong price
is if the corpus itself is poisoned with one. This gate is the teeth for that: it
extracts every price token from a body of text and rejects any token not on the
canonical price list. A planted fabricated price ("$9,999", "$5/mo") -> exit 1.

Canonical prices trace to the live storefront help center (help.html) and the
company price memory: Sovereign $500, Website $300, Circuit/Vigil $25/mo,
Academy $30/mo, Trading $49/mo, Marketing/Real Estate $99/mo, plus the $25 Vigil
sensor node. Update this set ONLY when a founder-confirmed price changes.
"""
from __future__ import annotations

import re
import sys

# Canonical, founder/storefront-confirmed price tokens (normalized, no thousands sep).
CANONICAL = {
    "$500",     # Sovereign, own it outright
    "$300",     # Custom website one-time
    "$25/mo",   # Circuit, Vigil
    "$25",      # Vigil sensor node (one-time)
    "$30/mo",   # Academy
    "$49/mo",   # Trading
    "$99/mo",   # Marketing, Real Estate
}

# A price token: $ + digits (optional thousands/decimal) + optional /mo|/month|/yr.
_PRICE = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?(?:\s?/\s?(?:mo|month|yr|year))?", re.I)


def _normalize(tok: str) -> str:
    t = tok.replace(" ", "").replace(",", "").lower()
    t = t.replace("/month", "/mo").replace("/year", "/yr")
    return t


def find_violations(text: str) -> list[str]:
    """Return the list of non-canonical price tokens found in `text`."""
    canon = {_normalize(c) for c in CANONICAL}
    bad = []
    for m in _PRICE.finditer(text):
        norm = _normalize(m.group(0))
        # "$0"/"$0.00" is a legitimate real-count zero (ships empty), never a price claim.
        if re.fullmatch(r"\$0(\.00)?", norm):
            continue
        if norm not in canon:
            bad.append(m.group(0).strip())
    return bad


def check(text: str) -> bool:
    """True if `text` contains no non-canonical price."""
    return not find_violations(text)


if __name__ == "__main__":
    body = sys.stdin.read() if not sys.stdin.isatty() else ""
    v = find_violations(body)
    if v:
        print("PRICE GATE RED — non-canonical prices:", sorted(set(v)), file=sys.stderr)
        sys.exit(1)
    print("PRICE GATE GREEN")
