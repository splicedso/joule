#!/bin/sh
# Trace v1 on the full 35k prompts: resume the Q4_0 7B teacher harvest (resumable, skips prompts
# already in data/drafter/teacher.jsonl), then retrain the 0.5B at LR 3e-6, ALPHA=2, one epoch.
# Throughput job, not an energy run. Never run alongside a Lattice/Phase measurement.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
PROMPTS=data/drafter/train-prompts-35k.jsonl   # the 35,000-prompt set from experiments/drafter/prepare.py 35000
if pgrep -f 'quality.py|lattice_halo_finish|phase/measure' | grep -vx -e $$ -e $PPID >/dev/null; then
  echo "energy run in progress, abort"; exit 1
fi
echo "=== HARVEST START $(date) ==="
uv run python experiments/drafter/teacher.py "$PROMPTS" data/drafter/teacher.jsonl
echo "=== HARVEST DONE $(date) ==="
echo "=== TRAIN START $(date) ==="
ALPHA=2 EPOCHS=1 LR=3e-6 .venv-torch/bin/python experiments/drafter/train_trace.py data/drafter/teacher.jsonl models/trace-0.5b-v1-35k
echo "=== TRAIN DONE $(date) ==="
