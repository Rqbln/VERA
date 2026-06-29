#!/usr/bin/env bash
# VERA — set up the NATIVE benchmark stack so the evaluation uses real harnesses (no heuristic
# fallbacks). Run from the repo root:  bash scripts/setup_native.sh
#
# Installs the [benchmarks,lab,pdf] extras, checks system libs + Ollama models, and prints the
# environment the paper run expects. Idempotent; safe to re-run.
set -u

green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
amber() { printf '\033[0;33m%s\033[0m\n' "$1"; }
red()   { printf '\033[0;31m%s\033[0m\n' "$1"; }

PANEL=(
  "qwen2.5:32b-instruct-q4_K_M"   # principal (strong) — needs ~20 GB
  "mistral-small:24b"             # mid (different family)
  "llama3.1:8b-instruct-q8_0"     # small baseline (also the judge)
)
JUDGE="llama3.1:8b-instruct-q8_0"
OLLAMA_BASE="${OLLAMA_API_BASE:-http://127.0.0.1:11434}"

echo "== 1. Python native extras =="
if python -c "import lm_eval, garak, datasets, detoxify, presidio_analyzer, Levenshtein, sacrebleu" 2>/dev/null; then
  green "  all native harness deps importable"
else
  amber "  installing .[benchmarks,lab,pdf] (this is large; first run can take a while)…"
  pip install -e '.[benchmarks,lab,pdf]' || red "  pip install reported errors — see output above"
fi

echo "== 2. System libs for PDF export (weasyprint) =="
if python -c "import weasyprint" 2>/dev/null; then
  green "  weasyprint OK"
else
  amber "  weasyprint missing system libs — on macOS: brew install cairo pango gdk-pixbuf libffi"
fi

echo "== 3. spaCy model for Presidio (R05 PII) =="
python -c "import spacy; spacy.load('en_core_web_lg')" 2>/dev/null \
  && green "  en_core_web_lg present" \
  || { amber "  downloading en_core_web_lg…"; python -m spacy download en_core_web_lg >/dev/null 2>&1 \
       && green "  done" || amber "  spaCy model download skipped (Presidio will use a smaller model)"; }

echo "== 4. Ollama + panel models =="
if curl -s --max-time 4 "$OLLAMA_BASE/api/tags" >/dev/null 2>&1; then
  green "  Ollama reachable at $OLLAMA_BASE"
  HAVE=$(curl -s "$OLLAMA_BASE/api/tags" | python3 -c "import sys,json;print(' '.join(m['name'] for m in json.load(sys.stdin).get('models',[])))")
  for m in "${PANEL[@]}"; do
    if echo "$HAVE" | grep -q "$m"; then green "  ✓ $m"; else amber "  ✗ $m  → ollama pull $m"; fi
  done
else
  red "  Ollama not reachable — start it (ollama serve) and pull the panel models"
fi

echo "== 5. Environment for the run =="
cat <<EOF
  export OLLAMA_API_BASE=$OLLAMA_BASE
  export VERA_WATERMARK_MODE=statistical
  export VERA_HF_TRUST_REMOTE_CODE=true
  export VERA_JUDGE_MODEL=ollama/$JUDGE
  export VERA_REQUIRE_NATIVE=1          # fail instead of silently falling back (garak/Mac excepted)
  export VERA_MLFLOW_DISABLED=1 VERA_ARTIFACT_BACKEND=local
EOF
green "Setup check complete. Next: python scripts/gen_banking_corpus.py && python scripts/run_paper_eval.py"
