#!/bin/sh
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
echo "=== 32b Q4_0 $(date) ==="
uv run python experiments/quality.py models/quant/32b-Q4_0.gguf results/lattice-halo-32b-Q4_0-pass1.json 250 8
echo "=== 32b Q2_K-imat $(date) ==="
uv run python experiments/quality.py models/quant/32b-Q2_K-imat.gguf results/lattice-halo-32b-Q2_K-imat-pass1.json 250 8
echo "=== 32B PAIR DONE $(date) ==="
