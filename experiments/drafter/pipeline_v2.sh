#!/bin/sh
# Drafter v2 after teacher.py: train on the 7B's probabilities, convert, then measure top-1
# agreement and speculative decoding against the stock draft and v1.
#
#   sh experiments/drafter/pipeline_v2.sh
set -e
cd "$(dirname "$0")/../.."
uv run --extra mlx python experiments/drafter/train_kd.py data/drafter/teacher.jsonl models/hf-drafter2-0.5b
sh experiments/drafter/convert.sh models/hf-drafter2-0.5b models/quant/drafter-v2
uv run --extra mlx python experiments/drafter/agree.py data/drafter/teacher.jsonl results/drafter/agree-mac.json
uv run python experiments/drafter/evaluate.py results/drafter/eval-v2-mac.json plain,stock-4-p0.5,spliced-4-p0.5,v2-4-p0.5,stock-8-p0.5,v2-8-p0.5
