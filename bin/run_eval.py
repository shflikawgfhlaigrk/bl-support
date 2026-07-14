#!/usr/bin/env python3
"""run_eval.py — run the answerer over real inbound messages, record verdicts.

Reads data/inbound.json (produced by fetch_inbound.py, read-only IMAP), treats each
message's subject+body as a support question, and records the engine's verdict:
ANSWERED (with citation) or REFUSED (with escalation). Writes data/eval_results.json
and a human-readable data/eval_results.md with a per-message table.

v1.2: the eval runs with the **LIVE-verified price index active** (built the same way
gate step 4 builds it — served storefront + read-only Stripe must agree). A price
question that names a product with a proven price is now ANSWERED WITH A CITATION
(storefront URL + Stripe price_id) instead of refused; everything out-of-corpus still
REFUSES. If the live build fails (offline / Stripe down) the index is empty and price
questions fall CLOSED to refusal — never a guessed price.

This is an OFFLINE eval only — it never sends, replies, or exposes anything.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from support.answerer import Answerer

ROOT = Path(__file__).resolve().parent.parent
INBOUND = ROOT / "data" / "inbound.json"
OUT_JSON = ROOT / "data" / "eval_results.json"
OUT_MD = ROOT / "data" / "eval_results.md"


def _redact_sender(frm: str) -> str:
    """Domain-only, to keep committed eval artifacts free of personal addresses."""
    m = re.search(r"@([\w.-]+)", frm or "")
    return f"@{m.group(1)}" if m else "(no-domain)"


def as_question(m: dict) -> str:
    subj = (m.get("subject") or "").strip()
    body = (m.get("body") or "").strip()
    return f"{subj}. {body}"[:600]


def evaluate(msgs: list[dict], ans: Answerer) -> tuple[list[dict], dict]:
    """Run `ans` over `msgs` and return (rows, summary). Pure + hermetic: no network,
    no file I/O, so the eval lane can be tested with a fake price index."""
    rows = []
    for i, m in enumerate(msgs):
        r = ans.answer(as_question(m))
        rows.append({
            "idx": i,
            "from": _redact_sender(m.get("from", "")),
            "subject": m.get("subject", ""),
            "verdict": "ANSWERED" if r.answered else "REFUSED",
            "citation": r.source,
            "sensitive": r.sensitive,
            # a verified-price answer is tagged distinctly so we can count the new lane.
            "priced": r.answered and r.reason.startswith("verified-price"),
            "reason": r.reason,
        })

    answered = [r for r in rows if r["verdict"] == "ANSWERED"]
    # Every ANSWERED verdict MUST carry a real citation — else it's a fabrication.
    answered_with_citation = [r for r in answered if r["citation"]]
    uncited = [r for r in answered if not r["citation"]]
    priced = [r for r in answered if r["priced"]]
    summary = {
        "total": len(rows),
        "answered": len(answered),
        "answered_with_citation": len(answered_with_citation),
        "priced_answers": len(priced),
        "refused": len(rows) - len(answered),
        "uncited_answers": len(uncited),
        "price_index_active": bool(ans.price_index),
        "price_index_rows": len(ans.price_index),
        "source": "read-only IMAP INBOX, last 50 messages (data/inbound.json)",
        "note": ("Most real inbound is internal briefs / vendor / recruiting mail, "
                 "not product-support questions, so a high REFUSE rate is CORRECT — "
                 "the engine escalates rather than guessing. Price questions that name "
                 "a product with a LIVE-verified price answer WITH a citation."),
    }
    return rows, summary


def _build_live_index() -> list:
    """Build the live price index, fail-closed to empty on any error (offline/Stripe)."""
    try:
        from support.price_index import build_index
        rows, _log = build_index()
        return rows
    except Exception as e:  # offline / Stripe down -> empty index -> price qs refuse
        print(f"note: live price index unavailable ({e}); price questions will refuse")
        return []


def main() -> None:
    msgs = json.loads(INBOUND.read_text())
    ans = Answerer(price_index=_build_live_index())
    rows, summary = evaluate(msgs, ans)

    OUT_JSON.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))

    lines = [
        "# Support surface v1.2 — inbound eval (price index active)", "",
        f"- Total messages: **{summary['total']}** (source: {summary['source']})",
        f"- Price index: **{'ACTIVE' if summary['price_index_active'] else 'EMPTY (fail-closed)'}** "
        f"({summary['price_index_rows']} live-verified rows)",
        f"- ANSWERED with citation: **{summary['answered_with_citation']}** "
        f"(of which verified-price: **{summary['priced_answers']}**)",
        f"- REFUSED (escalated to human): **{summary['refused']}**",
        f"- Uncited answers (MUST be 0): **{summary['uncited_answers']}**", "",
        summary["note"], "",
        "| # | From | Subject | Verdict | Citation | Reason |",
        "|---|------|---------|---------|----------|--------|",
    ]
    for r in rows:
        frm = (r["from"] or "")[:28].replace("|", "/")
        subj = (r["subject"] or "")[:42].replace("|", "/")
        cite = (r["citation"] or "—")
        lines.append(f"| {r['idx']} | {frm} | {subj} | {r['verdict']} | {cite} | {r['reason']} |")
    OUT_MD.write_text("\n".join(lines) + "\n")

    print(f"eval: {summary['answered_with_citation']} answered-with-citation "
          f"({summary['priced_answers']} verified-price) / {summary['refused']} refused "
          f"/ {summary['uncited_answers']} uncited")
    print(f"wrote {OUT_JSON}\nwrote {OUT_MD}")
    if summary["uncited_answers"]:
        raise SystemExit("FAIL: answered verdict without a citation (fabrication risk)")


if __name__ == "__main__":
    main()
