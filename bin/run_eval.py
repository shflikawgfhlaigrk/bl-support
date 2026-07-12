#!/usr/bin/env python3
"""run_eval.py — run the answerer over real inbound messages, record verdicts.

Reads data/inbound.json (produced by fetch_inbound.py, read-only IMAP), treats each
message's subject+body as a support question, and records the engine's verdict:
ANSWERED (with citation) or REFUSED (with escalation). Writes data/eval_results.json
and a human-readable data/eval_results.md with a per-message table.

This is an OFFLINE eval only — it never sends, replies, or exposes anything.
"""
from __future__ import annotations

import json
from pathlib import Path

from support.answerer import Answerer

ROOT = Path(__file__).resolve().parent.parent
INBOUND = ROOT / "data" / "inbound.json"
OUT_JSON = ROOT / "data" / "eval_results.json"
OUT_MD = ROOT / "data" / "eval_results.md"


def _redact_sender(frm: str) -> str:
    """Domain-only, to keep committed eval artifacts free of personal addresses."""
    import re
    m = re.search(r"@([\w.-]+)", frm or "")
    return f"@{m.group(1)}" if m else "(no-domain)"


def as_question(m: dict) -> str:
    subj = (m.get("subject") or "").strip()
    body = (m.get("body") or "").strip()
    return f"{subj}. {body}"[:600]


def main() -> None:
    msgs = json.loads(INBOUND.read_text())
    ans = Answerer()
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
            "reason": r.reason,
        })

    answered = sum(1 for r in rows if r["verdict"] == "ANSWERED")
    refused = len(rows) - answered
    # Every ANSWERED verdict MUST carry a real citation — else it's a fabrication.
    uncited = [r for r in rows if r["verdict"] == "ANSWERED" and not r["citation"]]
    summary = {
        "total": len(rows), "answered": answered, "refused": refused,
        "uncited_answers": len(uncited),
        "source": "read-only IMAP INBOX, last 50 messages (data/inbound.json)",
        "note": ("Most real inbound is internal briefs / vendor / recruiting mail, "
                 "not product-support questions, so a high REFUSE rate is CORRECT — "
                 "the engine escalates rather than guessing."),
    }
    OUT_JSON.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))

    lines = [
        "# Support surface v1 — inbound eval", "",
        f"- Total messages: **{summary['total']}** (source: {summary['source']})",
        f"- ANSWERED (grounded + cited): **{answered}**",
        f"- REFUSED (escalated to human): **{refused}**",
        f"- Uncited answers (MUST be 0): **{len(uncited)}**", "",
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

    print(f"eval: {answered} answered / {refused} refused / {len(uncited)} uncited")
    print(f"wrote {OUT_JSON}\nwrote {OUT_MD}")
    if uncited:
        raise SystemExit("FAIL: answered verdict without a citation (fabrication risk)")


if __name__ == "__main__":
    main()
