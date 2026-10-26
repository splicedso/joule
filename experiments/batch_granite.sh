#!/bin/sh
# Batching on a second family (note 28's Granite 3.3 2B, Q4_0) beside a same-session Qwen2.5 1.5B Q4_0 reference,
# 512-token answers (note 24: 128-token windows are too thin for a small model), batches 1 to 32, two passes each.
set -e
cd "$(dirname "$0")/.."
export ANSWER=512 BATCHES=1,2,4,8,16,32
uv run python experiments/decode_batch_energy.py models/quant/granite2b-Q4_0.gguf results/decode-batch-mac-granite2b-q4_0-a512.json
uv run python experiments/decode_batch_energy.py models/qwen2.5-1.5b-instruct-q4_0.gguf results/decode-batch-mac-1.5b-q4_0-a512-ref.json
