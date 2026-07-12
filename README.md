# Black Label — Support surface v1

An **extractive, cite-or-refuse** FAQ answerer for customer support, grounded
**only** in real, shipped product docs. It behaves like Academy's tutor: it either
quotes a grounded sentence **with a citation**, or it **refuses and escalates to a
human** at `info@blacklabelbots.com`. It never generates a guess about price,
refund, or capability.

> **Status: STAGING / LOCALHOST ONLY.** This cycle ships the engine + tests + eval.
> There is **no public deploy** and no server is exposed. Exposure is gated on a
> green gate battery **and** a follow-up review.

## Why it's safe by construction
- **Extractive, not generative.** An answer is verbatim corpus text + a source label.
  The engine cannot author a novel claim about price/refund/capability — it can only
  quote grounded text or refuse.
- **Admission gate.** `corpus.py` admits a source only if it passes the canonical
  `ProjectUtah/ops/claim_linter.py`. A doc that trips the linter is excluded, so the
  corpus can never become the vector that ships an unsupported claim.
- **Fail-closed emission.** Even a strong retrieval hit is dropped (→ refusal) if its
  text trips the claim linter or the price gate.
- **Sensitive-intent bar.** Price / refund / cancel / guarantee questions require a
  stronger grounded hit than general questions; a weak match refuses.
- **Brand-name guard.** A question that only name-drops a product (matches on brand
  tokens alone) refuses instead of returning a generic blurb.

## Layout
```
support/corpus.py     # load + strip + chunk real docs; per-source claim-lint admission
support/answerer.py   # extractive cite-or-refuse engine (stdlib retrieval, zero deps)
support/price_gate.py # canonical price gate (non-canonical price -> RED)
bin/fetch_inbound.py  # READ-ONLY IMAP (EXAMINE + BODY.PEEK) last N inbound -> data/inbound.json
bin/run_eval.py       # run engine over inbound -> data/eval_results.{json,md} (senders redacted)
bin/gate_battery.sh   # claim_linter + price_gate + tests; ALL must be green
tests/test_support.py # tests with TEETH (see below)
```

## Corpus (real docs only)
- `~/.blacklabelbots/_deploy/help.html` (customer help center)
- `~/.blacklabelbots/_deploy/help/*.html` (per-product guides)
- curated shipped READMEs: Academy, LeadsAPI, RealEstate-Website
Current corpus: **236 chunks / 6 admitted sources / 0 excluded**.

## Tests with teeth (`python3 tests/test_support.py` — 9/9)
1. Planted **out-of-corpus** question → REFUSAL + escalation line.
2. Planted **fabricated price** in the corpus → price gate goes **RED** (and the
   answerer refuses to emit a poisoned chunk).
3. Every ANSWERED verdict carries a **real citation** (no uncited answers).
4. The refusal string is **verbatim** (never a soft generated variant).
5. Sensitive intents (refund/price) **refuse on weak grounding**.
6. The live corpus passes the claim-linter admission gate.

## Eval — last 50 real inbound (read-only)
`data/eval_results.md` records a per-message verdict over the **last 50 real inbound
messages** (read-only IMAP, senders redacted to domain). Result this run:
**0 answered / 50 refused / 0 uncited.** That high refuse rate is **correct** — the
real inbox this cycle is internal briefs, recruiting replies, and vendor/marketing
mail, **not** product-support questions, so the engine escalates rather than guessing.
The answer path is exercised by the teeth tests against a controlled grounded corpus.

> The HQ `/api/brief` surface only exposes *today's* inbound (6 msgs, `SINCE today`);
> the 50-message set is pulled directly via read-only IMAP by `bin/fetch_inbound.py`.

## Run it
```
python3 bin/fetch_inbound.py --limit 50     # read-only; writes gitignored data/inbound.json
PYTHONPATH=. python3 bin/run_eval.py        # per-message verdicts
bash bin/gate_battery.sh                     # full battery, fail-closed
python3 -m support.answerer "your question" # one-off (staging)
```

## Not done this cycle (next)
- No public deploy — staging/localhost only, pending review.
- Retrieval is deliberately conservative (prefers refusal). A structured price/FAQ
  index would let it safely answer common price questions instead of refusing.
