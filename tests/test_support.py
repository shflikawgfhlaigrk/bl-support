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
from support import price_index as pidx                              # noqa: E402
from support.price_index import PriceRow, build_index                # noqa: E402


# --- hermetic fixtures for the LIVE price index (no network in tests) -------------
class FakeFetchers:
    """Injectable stand-in for LiveFetchers: served asset + page + Stripe price.

    `stripe` maps a checkout URL -> the resolved price dict (or None). `pages` maps a
    product page URL -> its served HTML. Lets a test force any disagreement.
    """

    ASSET = (
        "var LINKS = {\n"
        "  trading: 'https://buy.stripe.com/TRADING',\n"
        "  sovereign: 'https://buy.stripe.com/SOVEREIGN',\n"
        "};\n"
        "var TRIAL = {\n"
        "  trading:   { model: 'subscription', price: '$49/mo' },\n"
        "  sovereign: { model: 'guarantee',    price: '$500'   },\n"
        "};\n"
    )

    def __init__(self, stripe: dict, pages: dict):
        self._stripe = stripe
        self._pages = pages

    def get_asset(self, url):
        return self.ASSET

    def get_page(self, url):
        return self._pages.get(url, "")

    def stripe_price_for_link(self, checkout_url):
        return self._stripe.get(checkout_url)


def _good_stripe():
    return {
        "https://buy.stripe.com/TRADING": {
            "price_id": "price_TRADING", "price": "$49/mo",
            "price_active": True, "product_active": True, "link_active": True},
        "https://buy.stripe.com/SOVEREIGN": {
            "price_id": "price_SOV", "price": "$500",
            "price_active": True, "product_active": True, "link_active": True},
    }


def _good_pages():
    return {
        "https://blacklabelbots.com/trading": "<p>Trading Engine — $49/mo, cancel anytime.</p>",
        "https://blacklabelbots.com/sovereign": "<p>Own Sovereign for $500 flat.</p>",
    }


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


# --- Tooth 7: price index admits only four-way-verified rows ---------------------
def test_price_index_admits_verified_rows():
    rows, log = build_index(FakeFetchers(_good_stripe(), _good_pages()))
    keys = {r.key for r in rows}
    assert "trading" in keys and "sovereign" in keys, f"expected verified rows, got {keys}"
    tr = next(r for r in rows if r.key == "trading")
    assert tr.price == "$49/mo"
    assert tr.price_id == "price_TRADING"                 # Stripe citation
    # served-page citation must be on the storefront HOST. Not `.startswith(...)`:
    # that also accepts https://blacklabelbots.com.attacker.example/trading, so the
    # assertion would stay green through exactly the regression it exists to catch.
    assert pidx.is_storefront_url(tr.storefront_url), tr.storefront_url
    assert pidx.is_checkout_url(tr.checkout_url), tr.checkout_url


# --- Tooth 7b: citation/checkout host checks reject lookalike hosts ---------------
def test_url_host_check_rejects_lookalike_hosts():
    """Every URL this module cites to a buyer is host-checked, not prefix-checked."""
    good = [
        "https://blacklabelbots.com",
        "https://blacklabelbots.com/trading",
        "https://www.blacklabelbots.com/trading",   # subdomain is still us
    ]
    for u in good:
        assert pidx.is_storefront_url(u), u

    bad = [
        "https://blacklabelbots.com.attacker.example/trading",  # suffix attack
        "https://notblacklabelbots.com/trading",                # prefix glued
        "https://attacker.example/https://blacklabelbots.com",  # host in the path
        "https://attacker.example/?u=https://blacklabelbots.com",  # host in the query
        "https://attacker.example/#https://blacklabelbots.com",    # host in the fragment
        "https://blacklabelbots.com@attacker.example/trading",  # userinfo trick
        "http://blacklabelbots.com/trading",                    # downgraded scheme
        "javascript:alert(1)//blacklabelbots.com",
        "",
    ]
    for u in bad:
        assert not pidx.is_storefront_url(u), f"lookalike accepted: {u}"

    assert pidx.is_checkout_url("https://buy.stripe.com/TRADING")
    assert not pidx.is_checkout_url("https://buy.stripe.com.attacker.example/TRADING")
    assert not pidx.is_checkout_url("https://attacker.example/buy.stripe.com/TRADING")


def test_price_index_refuses_checkout_link_on_lookalike_host():
    """A served asset whose checkout link resolves to a lookalike host admits NOTHING.

    parse_served_asset's regex currently anchors the link to buy.stripe.com, so this
    patches the parse step to prove the host guard in build_index holds on its own —
    the guard is what survives if that regex is ever loosened.
    """
    real_parse = pidx.parse_served_asset

    def poisoned_parse(js):
        links, trial = real_parse(js)
        links["trading"] = "https://buy.stripe.com.attacker.example/TRADING"
        return links, trial

    pidx.parse_served_asset = poisoned_parse
    try:
        stripe = _good_stripe()
        stripe["https://buy.stripe.com.attacker.example/TRADING"] = {
            "price_id": "price_TRADING", "price": "$49/mo",
            "price_active": True, "product_active": True, "link_active": True}
        rows, log = build_index(FakeFetchers(stripe, _good_pages()))
    finally:
        pidx.parse_served_asset = real_parse

    assert "trading" not in {r.key for r in rows}, "lookalike checkout host must NOT be admitted"
    tr_log = next(e for e in log if e["key"] == "trading")
    assert "host is not" in tr_log["reason"], tr_log
    # the untouched product still admits — the guard is targeted, not a blanket refusal
    assert "sovereign" in {r.key for r in rows}


# --- Tooth 8: served/Stripe disagreement -> row REFUSED (fail closed) -------------
def test_price_index_refuses_on_served_stripe_mismatch():
    bad = _good_stripe()
    bad["https://buy.stripe.com/TRADING"] = {         # Stripe says $99, page/asset say $49
        "price_id": "price_X", "price": "$99/mo",
        "price_active": True, "product_active": True, "link_active": True}
    rows, log = build_index(FakeFetchers(bad, _good_pages()))
    keys = {r.key for r in rows}
    assert "trading" not in keys, "mismatched price must NOT be admitted"
    tr_log = next(e for e in log if e["key"] == "trading")
    assert "mismatch" in tr_log["reason"], tr_log


# --- Tooth 9: a NON-canonical price is refused even if served==stripe -------------
def test_price_index_refuses_noncanonical_even_if_sources_agree():
    # signals-shaped case: served asset + Stripe agree at $100/mo, but $100/mo is not
    # in the canonical price gate -> fail closed.
    stripe = _good_stripe()
    stripe["https://buy.stripe.com/TRADING"] = {
        "price_id": "price_100", "price": "$100/mo",
        "price_active": True, "product_active": True, "link_active": True}
    pages = dict(_good_pages())
    pages["https://blacklabelbots.com/trading"] = "<p>$100/mo</p>"
    # also make the served asset agree at $100/mo by patching the parsed TRIAL via a
    # subclass whose asset shows $100/mo for trading.
    class FF(FakeFetchers):
        ASSET = FakeFetchers.ASSET.replace("$49/mo", "$100/mo")
    rows, log = build_index(FF(stripe, pages))
    assert "trading" not in {r.key for r in rows}
    tr_log = next(e for e in log if e["key"] == "trading")
    assert "non-canonical" in tr_log["reason"], tr_log


# --- Tooth 10: verified price question is ANSWERED with a citation ----------------
def test_answerer_answers_verified_price_with_citation():
    row = PriceRow(key="trading", display="Black Label Trading", price="$49/mo",
                   aliases=frozenset({"trading"}), price_id="price_TRADING",
                   checkout_url="https://buy.stripe.com/TRADING",
                   storefront_url="https://blacklabelbots.com/trading")
    a = Answerer(_grounded_corpus(), price_index=[row])
    r = a.answer("How much is Black Label Trading?")
    assert r.answered is True, f"should answer, got {r.reason}"
    assert "$49/mo" in r.text
    assert "price_TRADING" in r.text                  # Stripe price_id cited
    assert "blacklabelbots.com/trading" in r.text     # served-page cited
    assert ESCALATION in r.text


# --- Tooth 11: NEGATIVE CONTROL — a poisoned price row trips the price gate RED ---
def test_poisoned_price_row_trips_gate_then_restores_green():
    # A row whose price is fabricated ($9,999/mo) must NOT be emitted: the price gate
    # fires on the assembled answer -> refusal.
    poisoned = PriceRow(key="trading", display="Black Label Trading", price="$9,999/mo",
                        aliases=frozenset({"trading"}), price_id="price_FAKE",
                        checkout_url="https://buy.stripe.com/TRADING",
                        storefront_url="https://blacklabelbots.com/trading")
    a_bad = Answerer(_grounded_corpus(), price_index=[poisoned])
    r_bad = a_bad.answer("How much is Trading?")
    assert r_bad.answered is False, "poisoned price must not be emitted"
    assert r_bad.reason == "price-gate-red", f"expected price-gate-red, got {r_bad.reason}"
    # Restore green: the same question with the canonical row answers cleanly.
    good = PriceRow(key="trading", display="Black Label Trading", price="$49/mo",
                    aliases=frozenset({"trading"}), price_id="price_TRADING",
                    checkout_url="https://buy.stripe.com/TRADING",
                    storefront_url="https://blacklabelbots.com/trading")
    r_good = Answerer(_grounded_corpus(), price_index=[good]).answer("How much is Trading?")
    assert r_good.answered is True and "$49/mo" in r_good.text


# --- Tooth 12: an out-of-corpus / unnamed price question still refuses w/ an index -
def test_price_index_present_still_refuses_unnamed_and_offtopic():
    row = PriceRow(key="trading", display="Black Label Trading", price="$49/mo",
                   aliases=frozenset({"trading"}), price_id="price_TRADING",
                   checkout_url="https://buy.stripe.com/TRADING",
                   storefront_url="https://blacklabelbots.com/trading")
    a = Answerer(_grounded_corpus(), price_index=[row])
    # names no product -> no verified match -> refuse (never guess a "default" price)
    assert a.answer("How much does it cost?").answered is False
    # off-topic -> refuse
    assert a.answer("What is the capital of France?").text == REFUSAL


# --- Tooth 13: EVAL LANE — evaluate() answers a price inbound, refuses off-topic ---
def test_eval_lane_prices_with_citation_and_refuses_offtopic():
    """The v1.2 eval lane, run hermetically over inbound-shaped messages with a fake
    live price index: a price question that NAMES a product is ANSWERED with a real
    citation and tagged priced=True; an out-of-corpus message REFUSES; and the eval
    NEVER emits an uncited answer (the fabrication guard)."""
    from bin.run_eval import evaluate                                # noqa: E402

    row = PriceRow(key="trading", display="Black Label Trading", price="$49/mo",
                   aliases=frozenset({"trading"}), price_id="price_TRADING",
                   checkout_url="https://buy.stripe.com/TRADING",
                   storefront_url="https://blacklabelbots.com/trading")
    ans = Answerer(_grounded_corpus(), price_index=[row])
    msgs = [
        {"from": "buyer@example.com", "subject": "How much is Black Label Trading?",
         "body": "Thinking of buying — what does it cost per month?"},
        {"from": "spammer@somewhere.io", "subject": "What is the capital of France?",
         "body": "totally unrelated"},
        {"from": "curious@example.com", "subject": "How much does it cost?",
         "body": "no product named"},   # names no product -> must refuse, never guess
    ]
    rows, summary = evaluate(msgs, ans)

    # message 0: verified-price answer WITH citation
    assert rows[0]["verdict"] == "ANSWERED", rows[0]
    assert rows[0]["priced"] is True
    assert rows[0]["citation"] == "https://blacklabelbots.com/trading"
    # messages 1 & 2: refuse (off-topic; unnamed price question never guesses)
    assert rows[1]["verdict"] == "REFUSED"
    assert rows[2]["verdict"] == "REFUSED"
    # eval-lane invariants
    assert summary["answered_with_citation"] == 1
    assert summary["priced_answers"] == 1
    assert summary["refused"] == 2
    assert summary["uncited_answers"] == 0          # a fabrication would trip this


# --- Tooth 14: EVAL LANE — an ANSWERED verdict can NEVER be uncited ---------------
def test_eval_lane_answered_implies_cited():
    """Across a grounded answer AND a price answer, evaluate() must record a citation
    for every ANSWERED row — an uncited answer is a fabrication and must be impossible."""
    from bin.run_eval import evaluate                                # noqa: E402

    row = PriceRow(key="trading", display="Black Label Trading", price="$49/mo",
                   aliases=frozenset({"trading"}), price_id="price_TRADING",
                   checkout_url="https://buy.stripe.com/TRADING",
                   storefront_url="https://blacklabelbots.com/trading")
    ans = Answerer(_grounded_corpus(), price_index=[row])
    msgs = [
        {"from": "a@b.com", "subject": "set up sending mailbox on port 465 in Leads",
         "body": "how do I connect my SMTP mailbox to start the lead finder?"},
        {"from": "a@b.com", "subject": "How much is Black Label Trading?", "body": ""},
    ]
    rows, summary = evaluate(msgs, ans)
    for r in rows:
        if r["verdict"] == "ANSWERED":
            assert r["citation"], f"ANSWERED row must be cited: {r}"
    assert summary["answered_with_citation"] == summary["answered"]
    assert summary["uncited_answers"] == 0


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
