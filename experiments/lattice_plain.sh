#!/bin/sh
# Lattice v1, the deciding control: qat.py's exact setup (data incl. the 30% FineWeb share, 910 steps, LR 1e-5,
# schedule, fp32 masters for the same linears, seed) with fake quantization OFF (QUANT=0). Separates the two
# causes the Q4_0 control could not: the 2-bit grid during training, or the terse GSM8K answers.
# Then F16 and plain Q4_0 (no imatrix) through quality.py, GSM8K-250, 8 slots, two passes, mirrored order.
# The quality runs are ENERGY runs: one model alone on the GPU, machine quiet, idle sampled before each.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
HW=/sys/class/drm/card0/device/hwmon/hwmon3/power1_average
IDLE=results/lattice-halo-idle-pre.csv
echo "=== plain fine-tune (QUANT=0) $(date) ==="
QUANT=0 .venv-torch/bin/python experiments/lattice/qat.py models/hf-1.5b models/lattice-1.5b-plain
echo "=== CONVERT and QUANTIZE $(date) ==="
uv run --with "numpy<3" --with sentencepiece --with "transformers>=4.45" --with torch --with safetensors \
  --with ./vendor/llama.cpp/gguf-py python vendor/llama.cpp/convert_hf_to_gguf.py models/lattice-1.5b-plain --outtype f16 --outfile models/quant/1.5b-plain-F16.gguf
llama-quantize models/quant/1.5b-plain-F16.gguf models/quant/1.5b-plain-Q4_0.gguf Q4_0
if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_trac[e]|qat[.]py|train_onpolic[y]' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU busy, stop before the energy runs"; exit 1; fi
idle_pre() { sleep 5; s=0; n=0; for i in $(seq 1 10); do s=$((s + $(cat $HW))); n=$((n+1)); sleep 1; done
  w=$(awk -v s=$s -v n=$n 'BEGIN{printf "%.2f", s/n/1e6}'); echo "$(date -Is),1.5b,$1,$2,$w" >> "$IDLE"; echo "idle before 1.5b $1 pass$2: ${w} W"; }
run() { idle_pre "$1-s8" "$2"; echo "=== quality 1.5b $1 slots 8 pass$2 $(date) ==="
  uv run python experiments/quality.py "models/quant/1.5b-$1.gguf" "results/lattice-halo-1.5b-$1-s8-pass$2.json" 250 8; }
run plain-F16 1; run plain-Q4_0 1
run plain-Q4_0 2; run plain-F16 2      # pass 2 reversed
echo "=== LATTICE PLAIN CONTROL DONE $(date) ==="
