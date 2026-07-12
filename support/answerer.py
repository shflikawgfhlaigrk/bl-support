#!/usr/bin/env python3
"""answerer.py — extractive, cite-or-refuse FAQ engine.

Contract (like Academy's tutor):
  * An answer is composed ONLY of sentences pulled VERBATIM from the corpus, each
    tagged with its real source file. The engine never paraphrases or generates
    prose about price / refund / capability — it can only quote grounded text.
  * If the best grounded match is too weak (out-of-corpus), OR the emitted text
    would trip the claim linter or price gate, the engine returns a fixed REFUSAL
    that escalates to a human at info@blacklabelbots.com.
  * Sensitive intents (price, refund, cancel, guarantee, legal, account) require a
    STRONGER grounded hit than general questions — a weak match refuses rather
    than approximate.

Zero runtime deps: stdlib retrieval by token overlap. No LLM, no network.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .corpus import Chunk, load_corpus, tokenize
from . import price_gate

# ProjectUtah/ops on path for claim_linter (also handled in corpus.py).
_OPS = Path.home() / "ProjectUtah" / "ops"
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

ESCALATION = "info@blacklabelbots.com"
REFUSAL = (
    "That isn't covered by Black Label's published product documentation, so I "
    "won't guess. For help with this — including pricing details, refunds, or "
    f"account-specific questions — please email a human at {ESCALATION} and the "
    "team will help you directly."
)

# Intents where a wrong answer is most costly: demand a stronger grounded hit.
SENSITIVE = {
    "price", "prices", "pricing", "cost", "costs", "refund", "refunds", "money",
    "back", "cancel", "cancellation", "guarantee", "guaranteed", "return",
    "returns", "chargeback", "billing", "charge", "charged", "legal", "liability",
    "warranty", "profit", "earnings", "roi",
}

# Retrieval bars.
# Brand / product-name tokens: matching ONLY these means the question name-drops a
# product but its actual subject isn't in the corpus -> refuse, don't blurb.
BRAND = {
    "black", "label", "labels", "bots", "leads", "sovereign", "vigil", "academy",
    "trading", "marketing", "circuit", "estate", "real", "homefront", "ace",
}
MIN_CONTENT_OVERLAP = 2  # shared NON-brand tokens required to answer at all
MIN_OVERLAP = 3          # min shared query<->chunk tokens for a general answer
MIN_COVERAGE = 0.34      # min fraction of query tokens covered by the chunk
SENSITIVE_OVERLAP = 4    # stronger bar for sensitive intents
SENSITIVE_COVERAGE = 0.50


@dataclass
class Answer:
    answered: bool
    text: str
    source: str | None       # citation label, or None on refusal
    score: float
    sensitive: bool
    reason: str              # why answered / refused (audit trail)


def _claim_clean(text: str) -> bool:
    """True if the emitted answer text carries no unsupported claim."""
    try:
        import claim_linter
    except Exception:
        return False  # fail closed: no linter -> don't emit
    tmp = Path("/tmp/_support_answer_probe.txt")
    tmp.write_text(text)
    try:
        return len(claim_linter.lint([tmp])) == 0
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


class Answerer:
    def __init__(self, chunks: list[Chunk] | None = None):
        if chunks is None:
            chunks, _ = load_corpus()
        self.chunks = chunks

    def _rank(self, q_tokens: frozenset[str]) -> tuple[Chunk | None, float, int]:
        best, best_score, best_overlap = None, 0.0, 0
        for c in self.chunks:
            shared = q_tokens & c.tokens
            if not shared:
                continue
            overlap = len(shared)
            coverage = overlap / max(1, len(q_tokens))
            # score favors coverage of the question, lightly rewards raw overlap, and
            # breaks ties toward substantive paragraphs over bare headings.
            richness = min(len(c.tokens), 30) / 30
            score = coverage + 0.05 * overlap + 0.03 * richness
            if score > best_score:
                best, best_score, best_overlap = c, score, overlap
        return best, best_score, best_overlap

    def answer(self, question: str) -> Answer:
        q_tokens = frozenset(tokenize(question))
        sensitive = bool(q_tokens & SENSITIVE)
        if not q_tokens:
            return Answer(False, REFUSAL, None, 0.0, sensitive, "empty-question")

        best, score, overlap = self._rank(q_tokens)
        coverage = overlap / max(1, len(q_tokens))
        content_overlap = len((q_tokens & best.tokens) - BRAND) if best else 0
        min_overlap = SENSITIVE_OVERLAP if sensitive else MIN_OVERLAP
        min_cov = SENSITIVE_COVERAGE if sensitive else MIN_COVERAGE

        if (best is None or overlap < min_overlap or coverage < min_cov
                or content_overlap < MIN_CONTENT_OVERLAP):
            fails = []
            if best is None:
                fails.append("no-overlap")
            else:
                if overlap < min_overlap:
                    fails.append(f"overlap={overlap}<{min_overlap}")
                if coverage < min_cov:
                    fails.append(f"coverage={coverage:.2f}<{min_cov}")
                if content_overlap < MIN_CONTENT_OVERLAP:
                    fails.append(f"content-overlap={content_overlap}<{MIN_CONTENT_OVERLAP}")
            tag = "sensitive-" if sensitive else ""
            return Answer(False, REFUSAL, None, score, sensitive,
                          f"below-{tag}threshold({', '.join(fails)})")

        emitted = f"{best.text}\n\n— Source: {best.source} · Questions we can't cover: {ESCALATION}"

        # Fail closed: an extractive hit still must clear the compliance gates.
        if not price_gate.check(best.text):
            return Answer(False, REFUSAL, None, score, sensitive, "price-gate-red")
        if not _claim_clean(best.text):
            return Answer(False, REFUSAL, None, score, sensitive, "claim-linter-red")

        return Answer(True, emitted, best.source, score, sensitive,
                      f"grounded(overlap={overlap}, coverage={coverage:.2f})")


if __name__ == "__main__":
    a = Answerer()
    q = " ".join(sys.argv[1:]) or "How do I fix email being held back?"
    r = a.answer(q)
    print(f"Q: {q}\nANSWERED: {r.answered} ({r.reason})\n")
    print(r.text)
