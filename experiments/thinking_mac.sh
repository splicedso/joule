#!/bin/sh
# What thinking costs: Qwen3.5 4B Q4_0, thinking off and on, the general eval, mirrored order, on a quiet Mac.
set -e
cd "$(dirname "$0")/.."
export EXEC_OK=1 MAX_TOKENS=4096 CTX_PER_SLOT=6144
M=models/quant/qwen35-4b-Q4_0.gguf
T="gsm8k,mmlu_pro,humaneval"
THINK=0 uv run --with pyarrow python experiments/general_eval.py $M results/general-mac-qwen35-4b-think0-pass1.json $T 8
THINK=1 uv run --with pyarrow python experiments/general_eval.py $M results/general-mac-qwen35-4b-think1-pass1.json $T 8
THINK=1 uv run --with pyarrow python experiments/general_eval.py $M results/general-mac-qwen35-4b-think1-pass2.json $T 8
THINK=0 uv run --with pyarrow python experiments/general_eval.py $M results/general-mac-qwen35-4b-think0-pass2.json $T 8
