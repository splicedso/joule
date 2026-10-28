#!/bin/sh
# Lattice v2 at 32B: a post-training format search, no training. Every 2- and 3-bit file from the same F16 with
# note 22's GSM8K imatrix; stock Q4_0 (note 22's file) as the reference. quality.py GSM8K-250, 8 slots, auto clocks,
# two passes in mirrored order, idle sampled before each run. ENERGY runs: GPU-exclusive, machine quiet.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
F16=models/src32b/qwen2.5-32b-instruct-fp16-00001-of-00017.gguf
IMAT=results/lattice/imatrix-32b-gsm8k.gguf
HW=/sys/class/drm/card0/device/hwmon/hwmon3/power1_average
IDLE=results/lattice32-halo-idle-pre.csv
FORMATS="${FORMATS:-Q2_K IQ2_M IQ2_XS IQ3_XXS Q3_K_M}"
[ -f "$IDLE" ] || echo "timestamp,format,pass,idle_pre_w" > "$IDLE"
echo "=== quantize $(date) ==="
for f in $FORMATS; do
  out=models/quant/32b-$f-imat.gguf
  [ -f "$out" ] && { echo "$out exists (same F16 and imatrix), kept"; continue; }
  nice -n 10 llama-quantize --imatrix "$IMAT" "$F16" "$out" "$f" > "logs/quantize-32b-$f.log" 2>&1
  ls -la "$out"
done
(cd models/quant && sha256sum 32b-Q4_0.gguf $(for f in $FORMATS; do printf '32b-%s-imat.gguf ' $f; done)) | tee results/lattice32-SHA256SUMS
if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_[a-z]*[.]py|qat[.]py' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU busy, abort"; exit 1; fi
[ "$(cat /sys/class/drm/card0/device/power_dpm_force_performance_level)" = auto ] || { echo "clock not auto, abort"; exit 1; }
idle_pre() { sleep 5; s=0; n=0; for i in $(seq 1 10); do s=$((s + $(cat $HW))); n=$((n+1)); sleep 1; done
  w=$(awk -v s=$s -v n=$n 'BEGIN{printf "%.2f", s/n/1e6}'); echo "$(date -Is),$1,$2,$w" >> "$IDLE"; echo "idle before $1 pass$2: ${w} W"; }
run() {  # tag pass
  m=models/quant/32b-$1.gguf; [ "$1" = Q4_0 ] || m=models/quant/32b-$1-imat.gguf
  idle_pre "$1" "$2"; echo "=== quality 32b $1 pass$2 $(date) ==="
  uv run python experiments/quality.py "$m" "results/lattice32-halo-$1-pass$2.json" 250 8; }
ORDER="Q4_0 $FORMATS"
for f in $ORDER; do run "$f" 1; done
for f in $(echo $ORDER | tr ' ' '\n' | tac); do run "$f" 2; done     # pass 2 reversed
echo "=== LATTICE32 FORMATS DONE $(date) ==="
