#!/bin/sh
# Lattice item D on Strix Halo: finish the 32B pair (both passes, second reversed) and the
# missing 7B pass 2. Energy run: one model alone on the GPU, machine quiet. Before each run,
# sample package idle power (power1_average, no server loaded) for 10 s and log it to
# results/lattice-halo-idle-pre.csv; quality.py records a second idle figure with the model loaded.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
HW=/sys/class/drm/card0/device/hwmon/hwmon3/power1_average
IDLE=results/lattice-halo-idle-pre.csv
[ -f "$IDLE" ] || echo "timestamp,size,format,pass,idle_pre_w" > "$IDLE"

# refuse to start while anything else sits on the GPU
BUSY=$(pgrep -f 'llama-server|llama-bench|teacher.py|train_trace|prepare.py' | grep -vx -e $$ -e $PPID || true)
if [ -n "$BUSY" ]; then
  echo "GPU/CPU job still running, abort"; ps -o pid,cmd -p $(echo $BUSY | tr ' ' ,) | cut -c1-120; exit 1
fi

idle_pre() {  # size format pass
  sleep 5; s=0; n=0
  for i in $(seq 1 10); do s=$((s + $(cat $HW))); n=$((n+1)); sleep 1; done
  w=$(awk -v s=$s -v n=$n 'BEGIN{printf "%.2f", s/n/1e6}')
  echo "$(date -Is),$1,$2,$3,$w" >> "$IDLE"
  echo "idle before $1 $2 pass$3: ${w} W"
}
run() {  # size format model pass
  idle_pre "$1" "$2" "$4"
  echo "=== quality $1 $2 pass$4 $(date) ==="
  uv run python experiments/quality.py "$3" "results/lattice-halo-$1-$2-pass$4.json" 250 8
}
run 32b Q4_0      models/quant/32b-Q4_0.gguf      1
run 32b Q2_K-imat models/quant/32b-Q2_K-imat.gguf 1
run 32b Q2_K-imat models/quant/32b-Q2_K-imat.gguf 2   # pass 2 reversed
run 32b Q4_0      models/quant/32b-Q4_0.gguf      2
echo "=== 32B PAIR DONE $(date) ==="
run 7b  Q2_K-imat models/quant/7b-Q2_K-imat.gguf  2   # 7B pass 2, reversed vs pass 1
run 7b  Q4_0      models/quant/7b-Q4_0.gguf       2
echo "=== LATTICE HALO FINISH DONE $(date) ==="
