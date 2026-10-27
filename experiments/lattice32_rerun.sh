#!/bin/sh
# Lattice v2 at 32B, rerun of the cells voided on 2026-10-26 (another job shared the GPU from 12:51 to 14:42): IQ2_XS, IQ3_XXS
# and Q3_K_M, with stock Q4_0 as the anchor again. Same files (SHA256 in results/lattice32-SHA256SUMS), same protocol as
# lattice32_formats.sh (quality.py GSM8K-250, 8 slots, auto clocks, two mirrored passes), new output names so the void cells
# stay on disk, marked. Before every run: the GPU gate (no compute client, busy under 5% for 60 s), then the idle sample;
# an idle reading over 15 W re-gates (three tries) and then aborts. A sampler logs the shader, fabric and SoC clocks, GPU
# busy and package power every 2 s during each run (results/lattice32r-halo-clocks.csv) to test the fabric-clock lead.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
D=/sys/class/drm/card0/device; HW=$D/hwmon/hwmon3/power1_average
IDLE=results/lattice32r-halo-idle-pre.csv; CLK=results/lattice32r-halo-clocks.csv
FORMATS="${FORMATS:-IQ2_XS IQ3_XXS Q3_K_M}"
[ -f "$IDLE" ] || echo "timestamp,format,pass,idle_pre_w,tries" > "$IDLE"
[ -f "$CLK" ] || echo "timestamp,format,pass,sclk_mhz,fclk_mhz,socclk_mhz,gpu_busy_pct,package_w" > "$CLK"
(cd models/quant && sha256sum -c --quiet ../../results/lattice32-SHA256SUMS) && echo "files match results/lattice32-SHA256SUMS"
[ "$(cat $D/power_dpm_force_performance_level)" = auto ] || { echo "clock not auto, abort"; exit 1; }
cur() { grep '\*' "$D/pp_dpm_$1" | grep -o '[0-9]*Mhz' | grep -o '[0-9]*' | head -1; }   # the marked level, blank when none is marked
idle_pre() {  # format pass: gate, then 10 one-second samples after 5 s of quiet; over 15 W re-gates, three tries
  for try in 1 2 3; do
    sh experiments/gpu_gate.sh 12 || exit 1
    sleep 5; s=0; n=0; for i in $(seq 1 10); do s=$((s + $(cat $HW))); n=$((n + 1)); sleep 1; done
    w=$(awk -v s=$s -v n=$n 'BEGIN{printf "%.2f", s/n/1e6}')
    echo "idle before $1 pass$2: ${w} W (try $try)"
    if awk -v w=$w 'BEGIN{exit !(w <= 15)}'; then echo "$(date -Is),$1,$2,$w,$try" >> "$IDLE"; return 0; fi
    echo "$(date -Is),$1,$2,$w,$try-high" >> "$IDLE"; sleep 60
  done
  echo "idle over 15 W three times before $1 pass$2, abort"; exit 1; }
run() {  # format pass
  m=models/quant/32b-$1.gguf; [ "$1" = Q4_0 ] || m=models/quant/32b-$1-imat.gguf
  idle_pre "$1" "$2"; echo "=== quality 32b $1 pass$2 $(date) ==="
  ( while :; do echo "$(date -Is),$1,$2,$(cur sclk),$(cur fclk),$(cur socclk),$(cat $D/gpu_busy_percent),$(awk '{printf "%.1f", $1/1e6}' $HW)" >> "$CLK"; sleep 2; done ) & S=$!
  uv run python experiments/quality.py "$m" "results/lattice32r-halo-$1-pass$2.json" 250 8 || { kill $S; exit 1; }
  kill $S; wait $S 2>/dev/null || true; }
ORDER="Q4_0 $FORMATS"
for f in $ORDER; do run "$f" 1; done
for f in $(echo $ORDER | tr ' ' '\n' | tac); do run "$f" 2; done     # pass 2 reversed
echo "=== LATTICE32 RERUN DONE $(date) ==="
