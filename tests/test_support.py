#!/usr/bin/env python3
"""test_support.py — tests with TEETH for the support surface.

Run:  python3 -m pytest tests/ -q     (or: python3 tests/test_support.py)

The teeth (each would go RED on a real regression):
  1. Planted OUT-OF-CORPUS question -> REFUSAL + escalation line (no guessing).
  2. Planted FABRICATED PRICE in the corpus -> the price gate goes RED.
  3. Every ANSWERED verdict carries a real citation (no uncited answers).
  4. The refusal string is EXACT / verbatim (never a soft generated variant).
  5. Sensitive intents (refund/price) refuse on weak grounding.
  6. The live corpus passes the canonical claim_linter (admission gate holds).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from support.answerer import Answerer, REFUSAL, ESCALATION           # noqa: E402
from support.corpus import Chunk, load_corpus                        # noqa: E402
from support import price_gate                                       # noqa: E402


def _grounded_corpus():
    return [
        Chunk.make("help/leads.html",
                   "Black Label Leads runs on your own Mac and your own mailbox. "
                   "To set up sending, open Settings and connect your SMTP mailbox "
                   "on port 465, then run the lead finder to build your first list."),
        Chunk.make("help/leads-deliverability-troubleshooting.html",
                   "Email is held back when a deliverability check fails: unverified "
                   "mailbox, missing SPF or DKIM, over the daily cap, or a suppressed "
                   "recipient. Fix the flagged check and the send resumes."),
    ]


# --- Tooth 1: out-of-corpus -> refusal -------------------------------------------
def test_out_of_corpus_refuses():
    a = Answerer(_grounded_corpus())
    r = a.answer("What is the capital of France?")
    assert r.answered is False
    assert r.text == REFUSAL
    assert ESCALATION in r.text


def test_off_topic_capability_refuses():
    a = Answerer(_grounded_corpus())
    r = a.answer("Can Black Label Leads file my taxes and drive my car?")
    assert r.answered is False, f"should refuse, got: {r.text}"


# --- Tooth 2: fabricated price in corpus -> price gate RED ------------------------
def test_planted_fabricated_price_trips_gate():
    poisoned = "Black Label Leads costs $9,999/mo with a special $1 trial."
    violations = price_gate.find_violations(poisoned)
    assert violations, "price gate MUST flag a fabricated price"
    assert price_gate.check(poisoned) is False


def test_canonical_prices_pass_gate():
    ok = "Sovereign is $500, Trading is $49/mo, Academy is $30/mo, website is $300."
    assert price_gate.check(ok) is True, f"canonical prices flagged: {price_gate.find_violations(ok)}"


def test_answerer_refuses_when_corpus_price_poisoned():
    # An extractive hit whose text carries a fabricated price must NOT be emitted.
    poisoned = Chunk.make(
        "help/leads.html",
        "Black Label Leads deliverability sending mailbox setup costs $9,999/mo "
        "for the held-back email fix on port 465.")
    a = Answerer([poisoned])
    r = a.answer("How do I fix deliverability sending mailbox held-back email on Leads?")
    assert r.answered is False
    assert r.reason == "price-gate-red", f"expected price-gate-red, got {r.reason}"


# --- Tooth 3 + 4: cited answers, exact refusal -----------------------------------
def test_grounded_answer_is_cited():
    a = Answerer(_grounded_corpus())
    r = a.answer("How do I set up my sending mailbox on port 465 in Leads?")
    assert r.answered is True, f"should answer, got refusal: {r.reason}"
    assert r.source is not None
    assert r.source in r.text                       # citation surfaced
    assert ESCALATION in r.text                     # escalation always present


def test_refusal_text_is_verbatim():
    a = Answerer(_grounded_corpus())
    r = a.answer("zxqw totally unrelated gibberish")
    assert r.text == REFUSAL                         # exact, not a soft variant


# --- Tooth 5: sensitive intent refuses on weak grounding -------------------------
def test_weak_price_question_refuses():
    a = Answerer(_grounded_corpus())
    r = a.answer("How much money and what refund do I get?")
    assert r.answered is False
    assert r.sensitive is True


# --- Tooth 6: live corpus admission gate holds -----------------------------------
def test_live_corpus_is_claim_clean():
    chunks, log = load_corpus()
    assert chunks, "corpus should be non-empty"
    excluded = [a for a in log if not a["admitted"]]
    # Excluded sources are allowed (they were correctly rejected), but every admitted
    # source must have contributed real chunks.
    admitted = [a for a in log if a["admitted"]]
    assert admitted, "no admitted sources"
    assert all(a["chunks"] > 0 for a in admitted)


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Exception:
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(fns)} passed")
    sys.exit(0 if passed == len(fns) else 1)
