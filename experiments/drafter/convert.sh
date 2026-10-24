#!/bin/sh
# Hugging Face model directory -> GGUF F16 -> Q4_0, with llama.cpp's own converter at the
# build every note uses (vendor/llama.cpp, 620d2225c). Used for both drafters, so the stock
# and the fine-tuned model go through an identical pipeline.
#
#   sh experiments/drafter/convert.sh models/hf-0.5b models/quant/drafter-stock
set -e
src="$1"; out="$2"
uv run --with "numpy<3" --with sentencepiece --with "transformers>=4.45" --with torch --with safetensors \
  --with ./vendor/llama.cpp/gguf-py \
  python vendor/llama.cpp/convert_hf_to_gguf.py "$src" --outtype f16 --outfile "$out-F16.gguf"
llama-quantize "$out-F16.gguf" "$out-Q4_0.gguf" Q4_0
ls -la "$out-F16.gguf" "$out-Q4_0.gguf"
