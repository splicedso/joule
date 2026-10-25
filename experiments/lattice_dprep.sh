#!/bin/sh
# Lattice item D prep: GSM8K imatrix for 7B and 32B, then calibrated Q2_K. GPU (imatrix) + CPU (quantize).
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
BIN=vendor/llama.cpp/build-vulkan/bin
F16_7B=models/src/qwen2.5-7b-instruct-fp16-00001-of-00004.gguf
F16_32B=models/src32b/qwen2.5-32b-instruct-fp16-00001-of-00017.gguf
mkdir -p results/lattice models/quant

# wait for llama-imatrix to finish building
while [ ! -x "$BIN/llama-imatrix" ]; do sleep 10; done
sleep 2

echo "=== imatrix 7B $(date) ==="
"$BIN/llama-imatrix" -m "$F16_7B" -f data/lattice-calib.txt -o results/lattice/imatrix-7b-gsm8k.gguf --chunks 200 -ngl 99
echo "=== imatrix 32B $(date) ==="
"$BIN/llama-imatrix" -m "$F16_32B" -f data/lattice-calib.txt -o results/lattice/imatrix-32b-gsm8k.gguf --chunks 200 -ngl 99

echo "=== quantize 7B Q2_K-imat $(date) ==="
"$BIN/llama-quantize" --imatrix results/lattice/imatrix-7b-gsm8k.gguf "$F16_7B" models/quant/7b-Q2_K-imat.gguf Q2_K
echo "=== quantize 32B Q2_K-imat $(date) ==="
"$BIN/llama-quantize" --imatrix results/lattice/imatrix-32b-gsm8k.gguf "$F16_32B" models/quant/32b-Q2_K-imat.gguf Q2_K

echo "=== D-PREP DONE $(date) ==="
ls -la models/quant/7b-Q2_K-imat.gguf models/quant/32b-Q2_K-imat.gguf results/lattice/imatrix-7b-gsm8k.gguf results/lattice/imatrix-32b-gsm8k.gguf
