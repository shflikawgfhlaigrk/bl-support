#!/usr/bin/env bash
# gate_battery.sh — the full pre-exposure gate battery for the support surface.
# ALL must pass (exit 0) before this surface is allowed anywhere public.
#   1. claim_linter (canonical ProjectUtah gate) over corpus + emitted-answer probe
#   2. price_gate over the assembled corpus text
#   3. tests-with-teeth suite
# Fail-closed: any red -> non-zero exit, no exposure.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OPS="$HOME/ProjectUtah/ops"
fail=0

echo "== [1/3] claim_linter over live corpus sources =="
# Dump the admitted corpus text and lint it as one artifact; also lint the help dir.
PYTHONPATH="$ROOT:$OPS" python3 - <<'PY'
import sys
from support.corpus import load_corpus
chunks, log = load_corpus(verbose=True)
open("/tmp/_support_corpus_dump.txt","w").write("\n\n".join(c.text for c in chunks))
print(f"corpus: {len(chunks)} chunks; excluded={sum(1 for a in log if not a['admitted'])}")
PY
if python3 "$OPS/claim_linter.py" /tmp/_support_corpus_dump.txt; then
  echo "   claim_linter: GREEN"
else
  echo "   claim_linter: RED"; fail=1
fi

echo "== [2/3] price_gate over corpus =="
if PYTHONPATH="$ROOT" python3 -m support.price_gate < /tmp/_support_corpus_dump.txt; then
  echo "   price_gate: GREEN"
else
  echo "   price_gate: RED"; fail=1
fi

echo "== [3/3] tests-with-teeth =="
if python3 tests/test_support.py; then
  echo "   tests: GREEN"
else
  echo "   tests: RED"; fail=1
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "GATE BATTERY: ALL GREEN (still staging-only — no public deploy this cycle)"
else
  echo "GATE BATTERY: RED — do not expose"; exit 1
fi
