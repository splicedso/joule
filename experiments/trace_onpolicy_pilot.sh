#!/bin/sh
# Trace on-policy pilot, as pre-registered (docs/predictions.md, entry headed 14:30, committed 14:17 in d825a8f):
# TVD, LR 3e-6, 300 steps, GEN 128, teacher the Q4_0 7B dequantized into transformers (98.8% top-1 agreement
# with its llama.cpp tokens, results/drafter/teacher-check-halo.json), two starts: stock and the 35k checkpoint.
# Then every draft scored on the same held-out set, converted, and the speculative eval against the Q4_0 7B
# at k=4, p 0.5, one request, two passes (evaluate.py sets --spec-type draft-simple); the stock, 35k and pilot
# drafts also at p 0.4 and p 0.3, so each draft is judged at its best threshold. The eval is an ENERGY
# run: one model pair alone on the GPU. Decision rule: under 1 point of acceptance over the best off-policy
# draft and Trace pauses for a write-up.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
T=models/quant/7b-Q4_0.gguf
echo "=== on-policy from stock $(date) ==="
STEPS=300 GEN=128 LR=3e-6 DIV=tvd .venv-torch/bin/python experiments/drafter/train_onpolicy.py data/drafter/teacher.jsonl $T models/trace-0.5b-onq4-stock
echo "=== on-policy from the 35k checkpoint $(date) ==="
STUDENT=models/trace-0.5b-v1-35k STEPS=300 GEN=128 LR=3e-6 DIV=tvd .venv-torch/bin/python experiments/drafter/train_onpolicy.py data/drafter/teacher.jsonl $T models/trace-0.5b-onq4-35k
echo "=== score every draft on the held-out set $(date) ==="
.venv-torch/bin/python experiments/drafter/score_drafts.py data/drafter/teacher.jsonl results/drafter/score-onpolicy-halo.json \
  stock=models/hf-0.5b v1-9k=models/trace-0.5b-v1-lr3e6 v1-35k=models/trace-0.5b-v1-35k \
  onq4-stock=models/trace-0.5b-onq4-stock onq4-35k=models/trace-0.5b-onq4-35k
echo "=== convert $(date) ==="
sh experiments/drafter/convert.sh models/trace-0.5b-v1-lr3e6 models/quant/drafter-v19k
sh experiments/drafter/convert.sh models/trace-0.5b-onq4-stock models/quant/drafter-onq4s
sh experiments/drafter/convert.sh models/trace-0.5b-onq4-35k models/quant/drafter-onq4k
if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_trac[e]|qat[.]py' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU busy, abort before the eval"; exit 1; fi
echo "=== speculative eval, one request, k=4, p 0.5, two passes $(date) ==="
uv run python experiments/drafter/evaluate.py results/drafter/eval-onpolicy-halo.json plain,stock-4-p0.5,v19k-4-p0.5,v135k-4-p0.5,onq4s-4-p0.5,onq4k-4-p0.5,stock-4-p0.4,v135k-4-p0.4,onq4s-4-p0.4,onq4k-4-p0.4,stock-4-p0.3,v135k-4-p0.3,onq4s-4-p0.3,onq4k-4-p0.3
echo "=== TRACE ON-POLICY PILOT DONE $(date) ==="
