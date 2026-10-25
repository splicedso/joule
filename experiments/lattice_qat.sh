#!/bin/sh
# Lattice v1 pipeline after experiments/lattice/qat.py has saved models/lattice-1.5b-qat:
# convert to GGUF through the same converter as every other model, quantize to Q2_K with the GSM8K
# imatrix (the artefact), then measure it with quality.py on auto, GSM8K-250, two passes (second
# reversed), at 8 slots and at 1 slot (the laptop bar). The quality runs are ENERGY runs: one model alone
# on the GPU, machine quiet, idle sampled before each. Stock Q2_K and calibrated Q2_K references for the
# 1.5B are note 20's (Mac); the Halo references are quality-halo-1.5b-s{1,8}-pass{1,2}.json (Q4_0).
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
echo "=== QUANTIZE Q2_K with GSM8K imatrix $(date) ==="
llama-quantize --imatrix results/lattice/imatrix-1.5b-gsm8k.gguf "models/quant/1.5b-$TAG-F16.gguf" "models/quant/1.5b-$TAG-Q2_K-imat.gguf" Q2_K
ls -la "models/quant/1.5b-$TAG-Q2_K-imat.gguf" models/quant/1.5b-Q4_0.gguf
if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_trac[e]' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU busy, stop before the energy runs"; exit 1; fi
idle_pre() { sleep 5; s=0; n=0; for i in $(seq 1 10); do s=$((s + $(cat $HW))); n=$((n+1)); sleep 1; done
  w=$(awk -v s=$s -v n=$n 'BEGIN{printf "%.2f", s/n/1e6}'); echo "$(date -Is),1.5b,$1,$2,$w" >> "$IDLE"; echo "idle before 1.5b $1 pass$2: ${w} W"; }
run() { idle_pre "$1-s$3" "$2"; echo "=== quality 1.5b $1 slots $3 pass$2 $(date) ==="; uv run python experiments/quality.py "models/quant/1.5b-$1.gguf" "results/lattice-halo-1.5b-$1-s$3-pass$2.json" 250 "$3"; }
run "$TAG-Q2_K-imat" 1 8
run "$TAG-Q2_K-imat" 1 1
run "$TAG-Q2_K-imat" 2 1    # pass 2 reversed
run "$TAG-Q2_K-imat" 2 8
echo "=== LATTICE QAT QUALITY DONE $(date) ==="
