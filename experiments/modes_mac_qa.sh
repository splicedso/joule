#!/bin/sh
# Three answer modes for Qwen3.5 4B Q4_0 on GSM8K 100 and MMLU-Pro 8 per subject (8 requests at once), mirrored A B C C B A:
#   A  thinking off, replies capped at 2,048 tokens
#   B  THINK_BUDGET=2048 with fallback to thinking off, every reply capped at 2,048
#   C  llama.cpp's own reasoning budget: thinking on, the server ends the thought at 2,048 tokens, 4,096 per reply in all
# Note 31 is the same comparison on HumanEval. Prediction: docs/predictions.md, 26 October 22:29 entry.
set -e
cd "$(dirname "$0")/.."
export N_GSM8K=100 N_PER_SUBJECT=8
M=models/quant/qwen35-4b-Q4_0.gguf
a() { THINK=0 MAX_TOKENS=2048 CTX_PER_SLOT=4096 uv run --with pyarrow python experiments/general_eval.py $M results/modes-qa-mac-qwen35-4b-offcap-pass$1.json gsm8k,mmlu_pro 8; }
b() { THINK_BUDGET=2048 MAX_TOKENS=2048 CTX_PER_SLOT=4096 uv run --with pyarrow python experiments/general_eval.py $M results/modes-qa-mac-qwen35-4b-budgetcap-pass$1.json gsm8k,mmlu_pro 8; }
c() { THINK=1 MAX_TOKENS=4096 CTX_PER_SLOT=6144 SERVER_ARGS="--reasoning-budget 2048" uv run --with pyarrow python experiments/general_eval.py $M results/modes-qa-mac-qwen35-4b-native-pass$1.json gsm8k,mmlu_pro 8; }
a 1; b 1; c 1; c 2; b 2; a 2
