#!/bin/sh
# After the 35k retrain (experiments/trace_35k.sh): convert the new draft to GGUF through the same
# pipeline as the stock draft, then the speculative-decoding eval against the stock draft and v1.
# The eval is an ENERGY run (two passes, second reversed, idle recorded): GPU-exclusive, machine quiet.
# Then the four Kinetic shapes start (throughput job).
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
until grep -q 'TRAIN DONE' logs/trace_35k.log 2>/dev/null; do sleep 120; done
sleep 10
echo "=== CONVERT $(date) ==="
sh experiments/drafter/convert.sh models/trace-0.5b-v1-35k models/quant/drafter-v135k
echo "=== EVAL $(date) ==="
uv run python experiments/drafter/evaluate.py results/drafter/eval-v135k-halo.json plain,stock-4-p0.5,v1-4-p0.5,v135k-4-p0.5,stock-8-p0.5,v135k-8-p0.5
echo "=== TRACE EVAL DONE $(date) ==="
nohup sh experiments/kinetic_shapes.sh > logs/kinetic_shapes.log 2>&1 &
echo "kinetic pid $!"
