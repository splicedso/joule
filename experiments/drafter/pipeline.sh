#!/bin/sh
# The rest of the drafter pipeline, run after the training answers exist: train, fuse the
# trained weights into a standalone model directory, convert it through the same pipeline as
# the stock model, then evaluate both drafters against plain decoding.
#
#   sh experiments/drafter/pipeline.sh
set -e
cd "$(dirname "$0")/../.."
uv run --extra mlx python experiments/drafter/train.py results/drafter/train-answers.jsonl models/drafter-0.5b
uv run --extra mlx python -m mlx_lm fuse --model models/hf-0.5b --adapter-path models/drafter-0.5b \
  --save-path models/hf-drafter-0.5b
sh experiments/drafter/convert.sh models/hf-drafter-0.5b models/quant/drafter-spliced
uv run python experiments/drafter/evaluate.py results/drafter/eval-mac.json
