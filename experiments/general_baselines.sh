#!/bin/sh
# The bars the closed-model training is judged against: stock Qwen2.5 1.5B and 7B Instruct at Q4_0 through general_eval.py
# (GSM8K-250, MMLU-Pro 20 per subject, HumanEval 164 executed in bubblewrap), 8 slots, MAX_TOKENS 2048, auto clocks, two
# passes in mirrored order. ENERGY runs: GPU-exclusive, machine quiet.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_[a-z]*[.]py|qat[.]py' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU busy, abort"; exit 1; fi
[ "$(cat /sys/class/drm/card0/device/power_dpm_force_performance_level)" = auto ] || { echo "clock not auto, abort"; exit 1; }
ev() { echo "=== $1 pass$3 $(date) ==="; MAX_TOKENS=2048 CTX_PER_SLOT=6144 EXEC_OK=1 uv run --with pyarrow python experiments/general_eval.py \
  "$2" "results/general-halo-$1-pass$3.json" gsm8k,mmlu_pro,humaneval 8; }
ev 1.5b-Q4_0 models/quant/1.5b-Q4_0.gguf 1; ev 7b-Q4_0 models/quant/7b-Q4_0.gguf 1
ev 7b-Q4_0 models/quant/7b-Q4_0.gguf 2; ev 1.5b-Q4_0 models/quant/1.5b-Q4_0.gguf 2
echo "=== GENERAL BASELINES DONE $(date) ==="
