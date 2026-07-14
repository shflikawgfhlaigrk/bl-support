#!/usr/bin/env python3
"""build_price_index.py — build the LIVE price index and PROVE it, fail-closed.

Run at gate time. It:
  1. Builds the price index LIVE (served storefront asset + product pages + read-only
     Stripe price objects). Every admitted row is four-way verified this same session.
  2. Writes the committed artifact data/price_index.json (citations only — no secrets).
  3. Proves the answerer answers a battery of real price questions WITH a citation,
     and that an out-of-corpus question still REFUSES.
Exit non-zero (RED) if fewer than MIN_VERIFIED rows verify, if any battery price
question is unanswered/uncited, or if the out-of-corpus control fails to refuse.

Usage:
  PYTHONPATH=. python3 bin/build_price_index.py           # build + write + prove
  PYTHONPATH=. python3 bin/build_price_index.py --gate    # same, quiet-ish, for battery
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from support.price_index import build_index, index_to_dicts   # noqa: E402
from support.answerer import Answerer, ESCALATION             # noqa: E402

OUT = ROOT / "data" / "price_index.json"
MIN_VERIFIED = 5

# Real, buyer-shaped price questions. Each MUST answer with a citation.
BATTERY = [
    "How much is Black Label Trading?",
    "What does Sovereign cost?",
    "How much does Academy cost per month?",
    "What is the price of Circuit?",
    "How much is the Marketing engine?",
    "What's the cost of Vigil?",
    "How much for a custom website?",
]
CONTROL = "What is the capital of France, and can you file my taxes?"  # must REFUSE


def main() -> int:
    gate = "--gate" in sys.argv
    rows, log = build_index()
    refused = [e for e in log if not e.get("admitted")]
    print(f"price index: {len(rows)} verified rows, {len(refused)} refused")

    OUT.write_text(json.dumps({
        "verified": index_to_dicts(rows),
        "refused": [{"key": e["key"], "reason": e.get("reason")} for e in refused],
    }, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")

    fail = 0
    if len(rows) < MIN_VERIFIED:
        print(f"RED: only {len(rows)} verified rows (< {MIN_VERIFIED})")
        fail = 1

    a = Answerer(price_index=rows)
    answered = 0
    for q in BATTERY:
        r = a.answer(q)
        cited = r.answered and (r.source in r.text) and (ESCALATION in r.text) \
            and ("Stripe price price_" in r.text)
        mark = "OK " if cited else "RED"
        if cited:
            answered += 1
        else:
            fail = 1
        if not gate or not cited:
            print(f"  [{mark}] {q}  ->  {r.text.splitlines()[0] if r.answered else 'REFUSED'}")
    print(f"battery: {answered}/{len(BATTERY)} answered WITH citation")
    if answered < MIN_VERIFIED:
        print(f"RED: only {answered} cited price answers (< {MIN_VERIFIED})")
        fail = 1

    ctrl = a.answer(CONTROL)
    if ctrl.answered:
        print(f"RED: out-of-corpus control was ANSWERED: {ctrl.text[:80]}")
        fail = 1
    else:
        print("control: out-of-corpus question REFUSED (correct)")

    print("PRICE INDEX PROOF:", "RED" if fail else "GREEN")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
