# Black Label — Support surface v1.1

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
support/corpus.py       # load + strip + chunk real docs; per-source claim-lint admission
support/answerer.py     # extractive cite-or-refuse engine (stdlib retrieval, zero deps)
support/price_gate.py   # canonical price gate (non-canonical price -> RED)
support/price_index.py  # LIVE-verified price index (v1.1): served storefront + Stripe agree
bin/fetch_inbound.py    # READ-ONLY IMAP (EXAMINE + BODY.PEEK) last N inbound -> data/inbound.json
bin/run_eval.py         # run engine over inbound -> data/eval_results.{json,md} (senders redacted)
bin/build_price_index.py# build the live price index + prove >=5 cited answers (gate step 4)
bin/gate_battery.sh     # claim_linter + price_gate + tests + live price proof; ALL green
tests/test_support.py   # tests with TEETH (see below)
```

## Price index — v1.1 (answer "how much is X" WITH a citation)
v1 refused every price question. v1.1 answers a price question **only** for a product
whose price it can prove LIVE, in the same build, from four independent sources that
must agree — else it still refuses. Built by `support/price_index.py`:
1. **Served asset** — `blacklabelbots.com/assets/stripe-links.js` displays the price
   next to the exact checkout link the buyer clicks.
2. **Served product page** — the price token must appear in the live-curled page
   (e.g. `/trading` shows `$49/mo`).
3. **Stripe (read-only)** — the price object resolved by *following that payment link's
   line item* (never mapped by amount, so a stale duplicate can't be substituted).
4. **Canonical price gate** — the agreed price must pass `price_gate.CANONICAL`.

A row is admitted only when all four agree AND link/price/product are active; every row
cites its **storefront URL + Stripe `price_id`**. Fail-closed by construction: e.g.
`signals` is served at `$100/mo` but `$100/mo` isn't canonical → it stays **refused**.
Current live build: **9 verified rows / 0 refused** (Sovereign $500, Trading $49/mo,
Marketing $99/mo, Real Estate $99/mo, Academy $30/mo, Circuit $25/mo, Sunset $25,
Vigil $25/mo, Custom Website $300). Artifact: `data/price_index.json` (citations only,
no secrets). The read-only Stripe key is `~/.utah/secrets/stripe.json` (never committed).

## Corpus (real docs only)
- `~/.blacklabelbots/_deploy/help.html` (customer help center)
- `~/.blacklabelbots/_deploy/help/*.html` (per-product guides)
- curated shipped READMEs: Academy, LeadsAPI, RealEstate-Website
Current corpus: **236 chunks / 6 admitted sources / 0 excluded**.

## Tests with teeth (`PYTHONPATH=. python3 tests/test_support.py` — 15/15)
1. Planted **out-of-corpus** question → REFUSAL + escalation line.
2. Planted **fabricated price** in the corpus → price gate goes **RED** (and the
   answerer refuses to emit a poisoned chunk).
3. Every ANSWERED verdict carries a **real citation** (no uncited answers).
4. The refusal string is **verbatim** (never a soft generated variant).
5. Sensitive intents (refund/price) **refuse on weak grounding**.
6. The live corpus passes the claim-linter admission gate.
7. The price index admits only **four-way-verified** rows (each with `price_id` +
   storefront URL citations).
8. A **served/Stripe price mismatch** → row **refused** (fail closed).
9. A **non-canonical price** (served==Stripe but off the canonical gate) → refused.
10. A verified price question is **answered WITH a citation** (`price_id` + page + escalation).
11. **NEGATIVE CONTROL:** a poisoned price row ($9,999/mo) trips the price gate **RED**
    → refusal; the canonical row then answers green (prove-then-restore).
12. With an index loaded, an **unnamed / off-topic** price question **still refuses**.

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
python3 bin/fetch_inbound.py --limit 50            # read-only; writes gitignored data/inbound.json
PYTHONPATH=. python3 bin/run_eval.py              # per-message verdicts
PYTHONPATH=. python3 bin/build_price_index.py     # build live price index + prove cited answers
bash bin/gate_battery.sh                           # full battery, fail-closed
PYTHONPATH=. python3 -m support.price_index        # print the live verified price rows
PYTHONPATH=. python3 -m support.answerer "how much is trading"  # one-off (staging)
```

## Not done this cycle (next)
- **No public deploy — staging/localhost only.** No HTTP listener is opened and no
  `wrangler deploy` is run; exposure stays gated on a green battery **and** review.
- The live price proof reads outbound only (served storefront + read-only Stripe); it
  binds nothing and serves nothing.
- Next: fold verified price rows into the eval over real inbound, and widen the corpus
  with more per-product help pages as they ship.
