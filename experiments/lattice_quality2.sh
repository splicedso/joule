#!/bin/sh
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
run() { echo "=== quality $1 $2 pass$4 $(date) ==="; uv run python experiments/quality.py "$3" "results/lattice-halo-$1-$2-pass$4.json" 250 8; }
run 7b Q4_0 models/quant/7b-Q4_0.gguf 1
run 7b Q2_K-imat models/quant/7b-Q2_K-imat.gguf 1
run 7b Q2_K-imat models/quant/7b-Q2_K-imat.gguf 2
run 7b Q4_0 models/quant/7b-Q4_0.gguf 2
echo "=== 7B PAIR DONE $(date) ==="
run 32b Q4_0 models/quant/32b-Q4_0.gguf 1
run 32b Q2_K-imat models/quant/32b-Q2_K-imat.gguf 1
run 32b Q2_K-imat models/quant/32b-Q2_K-imat.gguf 2
run 32b Q4_0 models/quant/32b-Q4_0.gguf 2
echo "=== LATTICE QUALITY ALL DONE $(date) ==="
