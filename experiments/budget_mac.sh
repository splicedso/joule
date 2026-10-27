#!/bin/sh
# Thinking budget with fallback, live: Qwen3.5 4B Q4_0, HumanEval 164 in the macOS sandbox, thinking off against
# THINK_BUDGET=2048 (think up to 2,048 tokens, else ask again with thinking off), mirrored order, on a quiet Mac.
# Prediction: docs/predictions.md, 26 October 20:08 entry.
set -e
cd "$(dirname "$0")/.."
export EXEC_OK=1 MAX_TOKENS=16384 CTX_PER_SLOT=18432 N_HUMANEVAL=164
M=models/quant/qwen35-4b-Q4_0.gguf
THINK=0 uv run --with pyarrow python experiments/general_eval.py $M results/budget-mac-qwen35-4b-off-pass1.json humaneval 8
THINK_BUDGET=2048 uv run --with pyarrow python experiments/general_eval.py $M results/budget-mac-qwen35-4b-b2048-pass1.json humaneval 8
THINK_BUDGET=2048 uv run --with pyarrow python experiments/general_eval.py $M results/budget-mac-qwen35-4b-b2048-pass2.json humaneval 8
THINK=0 uv run --with pyarrow python experiments/general_eval.py $M results/budget-mac-qwen35-4b-off-pass2.json humaneval 8
