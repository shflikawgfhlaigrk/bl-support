#!/usr/bin/env python3
"""fetch_inbound.py — read-only pull of the last N inbound messages for eval.

Mirrors the safe posture of HQ's email_brief.py: IMAP4_SSL EXAMINE (read-only) +
BODY.PEEK exclusively, so NOTHING is marked read, moved, or deleted. Output is a
JSON list of {from, subject, date, body} written to data/inbound.json. Used only
to build the offline eval set — never wired to any sender.

Creds: ~/.utah/secrets/gmail.json  ({from, app_password, ...}).
Usage:  python3 bin/fetch_inbound.py [--limit 50]
"""
from __future__ import annotations

import argparse
import email
import imaplib
import json
import re
from email.header import decode_header, make_header
from pathlib import Path

HOME = Path.home()
SECRETS = HOME / ".utah" / "secrets" / "gmail.json"
OUT = Path(__file__).resolve().parent.parent / "data" / "inbound.json"
IMAP_HOST, IMAP_PORT = "imap.gmail.com", 993


def _decode(v: str) -> str:
    try:
        return str(make_header(decode_header(v)))
    except Exception:
        return v or ""


def _plain_body(msg, limit=1200) -> str:
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    text = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace")
                    break
                except Exception:
                    continue
        if not text:  # fall back to stripped HTML
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    try:
                        h = part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="replace")
                        text = re.sub(r"(?s)<[^>]+>", " ", h)
                        break
                    except Exception:
                        continue
    else:
        try:
            text = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            text = str(msg.get_payload())
    return re.sub(r"\s+", " ", text).strip()[:limit]


def fetch(limit: int) -> list[dict]:
    creds = json.loads(SECRETS.read_text())
    user = creds.get("from") or creds.get("user")
    pw = creds.get("app_password") or creds.get("password")
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    try:
        conn.login(user, pw)
        conn.select("INBOX", readonly=True)          # EXAMINE — never sets \Seen
        typ, data = conn.search(None, "ALL")
        if typ != "OK":
            raise RuntimeError(f"IMAP search failed: {typ}")
        ids = data[0].split()
        newest = ids[-limit:] if len(ids) > limit else ids
        out = []
        for mid in reversed(newest):                 # newest first
            typ, body = conn.fetch(mid, "(BODY.PEEK[])")   # PEEK — read-only
            if typ != "OK" or not body or not body[0]:
                continue
            msg = email.message_from_bytes(body[0][1])
            out.append({
                "from": _decode(msg.get("From", "")),
                "subject": _decode(msg.get("Subject", "")),
                "date": msg.get("Date", ""),
                "body": _plain_body(msg),
            })
        return out
    finally:
        try:
            conn.logout()
        except Exception:
            pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()
    msgs = fetch(args.limit)
    OUT.write_text(json.dumps(msgs, indent=2))
    print(f"wrote {len(msgs)} messages -> {OUT}")
