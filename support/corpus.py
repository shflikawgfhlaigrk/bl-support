#!/usr/bin/env python3
"""corpus.py — build the grounding corpus from REAL, shipped product docs.

Sources (all real, all on disk — nothing invented):
  * ~/.blacklabelbots/_deploy/help.html                    (customer help center)
  * ~/.blacklabelbots/_deploy/help/*.html                  (per-product guides)
  * a curated allow-list of shipped product READMEs

Every source is admitted ONLY if it passes the canonical storefront claim_linter
(ProjectUtah/ops/claim_linter.py). A doc that trips the linter is EXCLUDED and
logged — the corpus can never become the vector that ships an unsupported claim.

The corpus is a list of Chunk(source, text, tokens). `source` is a short,
human-readable citation label (e.g. "help/leads.html") that the answerer surfaces
verbatim so every answer is traceable to a real file.
"""
from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()
DEPLOY = HOME / ".blacklabelbots" / "_deploy"

# ProjectUtah/ops must be importable for the claim_linter admission gate.
_OPS = HOME / "ProjectUtah" / "ops"
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

# Curated allow-list of shipped, customer-relevant READMEs. Kept small and explicit
# on purpose — a README is admitted only if it exists AND passes the claim gate.
README_ALLOW = [
    HOME / "BlackLabelAcademy" / "README.md",
    HOME / "BlackLabelLeadsAPI" / "README.md",
    HOME / "BlackLabelRealEstate-Website" / "README.md",
]

_STOP = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are",
    "be", "it", "this", "that", "your", "you", "with", "as", "at", "by", "from",
    "if", "so", "but", "not", "no", "do", "does", "how", "what", "why", "can",
    "i", "my", "we", "our", "will", "has", "have", "was", "were", "they", "them",
}


def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 1]


@dataclass
class Chunk:
    source: str            # citation label, e.g. "help/leads.html"
    text: str              # visible text of the chunk (a paragraph-ish unit)
    tokens: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def make(cls, source: str, text: str) -> "Chunk":
        return cls(source=source, text=text, tokens=frozenset(tokenize(text)))


def strip_html(raw: str) -> str:
    """Visible text only: drop <script>/<style>/<nav>/<footer>, unescape entities."""
    t = re.sub(r"(?is)<(script|style|nav|footer|head)\b.*?</\1>", " ", raw)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    return t


def _split_units(text: str) -> list[str]:
    """Split into paragraph/sentence-ish units; keep only substantial ones."""
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}|(?<=\.)\s{2,}", text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p) >= 40 and len(tokenize(p)) >= 4:
            out.append(p)
    return out


def _claim_clean(path: Path) -> tuple[bool, list[str]]:
    """True if `path` passes the canonical claim_linter (no unsupported claims)."""
    try:
        import claim_linter  # from ProjectUtah/ops
    except Exception as e:  # pragma: no cover - environment guard
        return False, [f"claim_linter unavailable: {e}"]
    findings = claim_linter.lint([path])
    return (len(findings) == 0), [getattr(f, "phrase", str(f)) for f in findings]


def _label(path: Path) -> str:
    try:
        rel = path.relative_to(DEPLOY)
        return str(rel)
    except ValueError:
        # product README -> "<Product>/README.md"
        return f"{path.parent.name}/{path.name}"


def load_corpus(verbose: bool = False) -> tuple[list[Chunk], list[dict]]:
    """Return (chunks, admission_log). Only claim-clean sources contribute chunks."""
    sources: list[Path] = []
    hp = DEPLOY / "help.html"
    if hp.exists():
        sources.append(hp)
    help_dir = DEPLOY / "help"
    if help_dir.is_dir():
        sources.extend(sorted(help_dir.glob("*.html")))
    for r in README_ALLOW:
        if r.exists():
            sources.append(r)

    chunks: list[Chunk] = []
    admission: list[dict] = []
    for path in sources:
        clean, findings = _claim_clean(path)
        label = _label(path)
        if not clean:
            admission.append({"source": label, "admitted": False,
                              "reason": "claim_linter findings", "findings": findings})
            if verbose:
                print(f"  EXCLUDED {label}: {findings}", file=sys.stderr)
            continue
        raw = path.read_text(errors="replace")
        text = strip_html(raw) if path.suffix.lower() in (".html", ".htm") else raw
        units = _split_units(text)
        for u in units:
            chunks.append(Chunk.make(label, u))
        admission.append({"source": label, "admitted": True, "chunks": len(units)})
        if verbose:
            print(f"  admitted {label}: {len(units)} chunks", file=sys.stderr)
    return chunks, admission


if __name__ == "__main__":
    chunks, log = load_corpus(verbose=True)
    print(f"\ncorpus: {len(chunks)} chunks from "
          f"{sum(1 for a in log if a['admitted'])} admitted sources "
          f"({sum(1 for a in log if not a['admitted'])} excluded)")
