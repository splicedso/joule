#!/bin/sh
# Export a fine-tuned Hugging Face checkpoint to GGUF in the stock file's tensor layout, then check it tensor by tensor.
#   sh experiments/rft/export.sh HF_DIR OUT_PREFIX [EXISTING_F16]
# writes OUT_PREFIX-F16.gguf (a separate output.weight, stock tensor order) and OUT_PREFIX-Q4_0.gguf (output Q6_K, embedding
# Q4_0, as in models/quant/1.5b-Q4_0.gguf), and results/rft/layout-<name>.txt: the gguf_dump tensor tables of the Q4_0 and of
# the stock file side by side and their diff. With EXISTING_F16 (a tied F16 already converted from HF_DIR) the conversion is
# skipped and that file is untied instead. CPU only, about a minute of all cores for the quantize: not during an energy run.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
HF=$1; OUT=$2; TIED=${3:-}; STOCK=${STOCK-models/quant/1.5b-Q4_0.gguf}; NAME=$(basename "$OUT")   # STOCK= (empty): no reference order, no layout check (other model sizes)
GG="uv run --with ./vendor/llama.cpp/gguf-py"
mkdir -p results/rft
if [ -z "$TIED" ]; then
  TIED=$OUT-tied-F16.gguf
  echo "=== convert $HF -> $TIED $(date) ==="
  uv run --with "numpy<3" --with sentencepiece --with "transformers>=4.45" --with torch --with safetensors \
    --with ./vendor/llama.cpp/gguf-py python vendor/llama.cpp/convert_hf_to_gguf.py "$HF" --outtype f16 --outfile "$TIED"
fi
echo "=== untie $TIED -> $OUT-F16.gguf (order of $STOCK) $(date) ==="
$GG python experiments/rft/untie_export.py "$TIED" "$OUT-F16.gguf" $STOCK
echo "=== quantize Q4_0, output Q6_K, embedding Q4_0 $(date) ==="
llama-quantize --output-tensor-type Q6_K --token-embedding-type Q4_0 "$OUT-F16.gguf" "$OUT-Q4_0.gguf" Q4_0 > "results/rft/quantize-$NAME.log" 2>&1
table() { $GG python vendor/llama.cpp/gguf-py/gguf/scripts/gguf_dump.py "$1" 2>/dev/null | sed -n '/Dumping .* tensor/,$p' | awk -F'|' 'NF>=4{gsub(/^ *[0-9]+: */,"",$1); print $2 "|" $3 "|" $4}' | sed 's/  */ /g'; }
if [ -n "$STOCK" ]; then
table "$STOCK" > "results/rft/layout-stock.txt"; table "$OUT-Q4_0.gguf" > "results/rft/layout-$NAME.txt"
{ echo "# tensor tables (dims | type | name) of $OUT-Q4_0.gguf against $STOCK, $(date)"
  echo "stock: $(wc -l < results/rft/layout-stock.txt) tensors, $(du -h "$STOCK" | cut -f1); $NAME: $(wc -l < "results/rft/layout-$NAME.txt") tensors, $(du -h "$OUT-Q4_0.gguf" | cut -f1)"
  if diff "results/rft/layout-stock.txt" "results/rft/layout-$NAME.txt" > "results/rft/layout-$NAME.diff"; then echo "LAYOUT MATCHES STOCK tensor by tensor (name, dims, type, order)"; else echo "LAYOUT DIFFERS:"; cat "results/rft/layout-$NAME.diff"; fi
} | tee "results/rft/layout-$NAME.check"
fi
echo "=== export done: $OUT-F16.gguf $OUT-Q4_0.gguf $(date) ==="
