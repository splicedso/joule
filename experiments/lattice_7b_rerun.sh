#!/bin/sh
# Note 22's 7B pass 1 came from the previous session and drew 10% more power than pass 2 at the
# same speed. Re-run both 7B pass-1 cells on auto in this session so the pair shares conditions.
# Energy run: one model alone on the GPU, machine quiet, package idle sampled before each run.
# The previous session's pass-1 files are kept in results/superseded/.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
HW=/sys/class/drm/card0/device/hwmon/hwmon3/power1_average
IDLE=results/lattice-halo-idle-pre.csv
[ "$(cat /sys/class/drm/card0/device/power_dpm_force_performance_level)" = auto ] || { echo "clock not on auto, abort"; exit 1; }
if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_trac[e]' >/dev/null; then echo "GPU busy, abort"; exit 1; fi
idle_pre() { sleep 5; s=0; n=0; for i in $(seq 1 10); do s=$((s + $(cat $HW))); n=$((n+1)); sleep 1; done
  w=$(awk -v s=$s -v n=$n 'BEGIN{printf "%.2f", s/n/1e6}'); echo "$(date -Is),$1,$2,$3,$w" >> "$IDLE"; echo "idle before $1 $2 pass$3: ${w} W"; }
run() { idle_pre "$1" "$2" "$4"; echo "=== quality $1 $2 pass$4 $(date) ==="; uv run python experiments/quality.py "$3" "results/lattice-halo-$1-$2-pass$4.json" 250 8; }
run 7b Q4_0      models/quant/7b-Q4_0.gguf      1
run 7b Q2_K-imat models/quant/7b-Q2_K-imat.gguf 1
echo "=== 7B RERUN DONE $(date) ==="
