#!/bin/sh
# Lattice v1 pipeline after experiments/lattice/qat.py has saved models/lattice-1.5b-qat:
#  1. convert to GGUF F16 through the same converter as every other model;
#  2. quantize to Q2_K with the GSM8K imatrix (the artefact) and to plain Q4_0 with no imatrix (the
#     control: the same fine-tuned weights at 4 bits, like the stock Q4_0 reference, so a gain from
#     shorter answers can be told apart from a gain from fewer bits);
#  3. SHA256SUMS for the Mac's eval; writes logs/lattice_qat_quantized.done;
#  4. quality.py, GSM8K-250, on auto. 8 slots: QAT Q2_K, stock Q4_0, QAT Q4_0, then the reverse (pass 2).
#     1 slot (the laptop bar): QAT Q2_K, stock Q4_0, then the reverse.
# The quality runs are ENERGY runs: one model alone on the GPU, machine quiet, idle sampled before each.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
SRC=${SRC:-models/lattice-1.5b-qat}
TAG=${TAG:-qat}
HW=/sys/class/drm/card0/device/hwmon/hwmon3/power1_average
IDLE=results/lattice-halo-idle-pre.csv
echo "=== CONVERT $(date) ==="
uv run --with "numpy<3" --with sentencepiece --with "transformers>=4.45" --with torch --with safetensors \
  --with ./vendor/llama.cpp/gguf-py python vendor/llama.cpp/convert_hf_to_gguf.py "$SRC" --outtype f16 --outfile "models/quant/1.5b-$TAG-F16.gguf"
echo "=== QUANTIZE Q2_K with GSM8K imatrix, and plain Q4_0 (control) $(date) ==="
llama-quantize --imatrix results/lattice/imatrix-1.5b-gsm8k.gguf "models/quant/1.5b-$TAG-F16.gguf" "models/quant/1.5b-$TAG-Q2_K-imat.gguf" Q2_K
llama-quantize "models/quant/1.5b-$TAG-F16.gguf" "models/quant/1.5b-$TAG-Q4_0.gguf" Q4_0
(cd models/quant && sha256sum "1.5b-$TAG-Q2_K-imat.gguf" "1.5b-$TAG-Q4_0.gguf" > "1.5b-$TAG-SHA256SUMS")
cat "models/quant/1.5b-$TAG-SHA256SUMS"; ls -la "models/quant/1.5b-$TAG-Q2_K-imat.gguf" "models/quant/1.5b-$TAG-Q4_0.gguf" models/quant/1.5b-Q4_0.gguf
date > "logs/lattice_${TAG}_quantized.done"
if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_trac[e]|qat[.]py' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU busy, stop before the energy runs"; exit 1; fi
idle_pre() { sleep 5; s=0; n=0; for i in $(seq 1 10); do s=$((s + $(cat $HW))); n=$((n+1)); sleep 1; done
  w=$(awk -v s=$s -v n=$n 'BEGIN{printf "%.2f", s/n/1e6}'); echo "$(date -Is),1.5b,$1,$2,$w" >> "$IDLE"; echo "idle before 1.5b $1 pass$2: ${w} W"; }
run() {  # name pass slots  (name: the GGUF under models/quant/1.5b-NAME.gguf)
  idle_pre "$1-s$3" "$2"; echo "=== quality 1.5b $1 slots $3 pass$2 $(date) ==="
  uv run python experiments/quality.py "models/quant/1.5b-$1.gguf" "results/lattice-halo-1.5b-$1-s$3-pass$2.json" 250 "$3"; }
Q2="$TAG-Q2_K-imat"; Q4="$TAG-Q4_0"; STOCK="Q4_0"
for m in "$Q2" "$STOCK" "$Q4"; do run "$m" 1 8; done
for m in "$Q4" "$STOCK" "$Q2"; do run "$m" 2 8; done      # pass 2 reversed
for m in "$Q2" "$STOCK"; do run "$m" 1 1; done
for m in "$STOCK" "$Q2"; do run "$m" 2 1; done            # pass 2 reversed
echo "=== LATTICE QAT QUALITY DONE $(date) ==="
