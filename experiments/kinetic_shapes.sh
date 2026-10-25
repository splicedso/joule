#!/bin/sh
# Kinetic: train the four shapes (docs/kinetic.md) one after another on the same 1B-token stream.
# Throughput job on the GPU; about 9 h per shape. Never alongside an energy measurement.
set -e
cd /home/martin/spliced/phase
for shape in deep base wide widest; do
  echo "=== kinetic $shape START $(date) ==="
  .venv-torch/bin/python experiments/kinetic/train.py $shape data/kinetic/train.bin data/kinetic/valid.bin models/kinetic-$shape
  echo "=== kinetic $shape DONE $(date) ==="
done
echo "=== KINETIC SHAPES DONE $(date) ==="
