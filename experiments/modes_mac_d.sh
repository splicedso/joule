#!/bin/sh
# Qwen3.5 4B Q4_0, HumanEval 164 + GSM8K 100 + MMLU-Pro 8 per subject (8 requests at once), mirrored B D D B:
#   B  THINK_BUDGET=2048 with fallback to thinking off, every reply capped at 2,048 (Foundry's Think today)
#   D  the server ends the thought at 2,048 (--reasoning-budget 2048), the reply may run to 2,560 in all, and a reply
#      stopped there is discarded and asked again with thinking off, capped at 2,048
# Notes 31 and 32 are the references. Prediction: docs/predictions.md, 27 October entry.
set -e
cd "$(dirname "$0")/.."
export EXEC_OK=1 N_HUMANEVAL=164 N_GSM8K=100 N_PER_SUBJECT=8 MAX_TOKENS=2048 CTX_PER_SLOT=4096
M=models/quant/qwen35-4b-Q4_0.gguf
T=humaneval,gsm8k,mmlu_pro
b() { THINK_BUDGET=2048 uv run --with pyarrow python experiments/general_eval.py $M results/modes-d-mac-qwen35-4b-budgetcap-pass$1.json $T 8; }
d() { THINK_BUDGET=2560 SERVER_ARGS="--reasoning-budget 2048" uv run --with pyarrow python experiments/general_eval.py $M results/modes-d-mac-qwen35-4b-capnative-pass$1.json $T 8; }
b 1; d 1; d 2; b 2
