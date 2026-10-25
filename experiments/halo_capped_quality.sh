#!/usr/bin/env bash
# Joules per correct answer under a shader-clock cap (OD table, 1,800 MHz) on Strix Halo.
# quality.py, GSM8K-250, 8 slots, two passes (second reversed): 7B Q4_0, 32B Q2_K-imat, 32B Q4_0.
# Energy run: one model alone on the GPU, machine quiet. Package idle sampled before every run
# (results/halo-capped-idle-pre.csv); the active clock is sampled during every run and its max
# logged, so a cap that slips is visible. sudo once, refreshed in-script; trap restores auto.
# At the end the Trace harvest is resumed (it was stopped for this run).
set -u
cd /home/martin/spliced/phase
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
DEV=/sys/class/drm/card0/device
HW=$DEV/hwmon/hwmon3/power1_average
BENCH="$PWD/vendor/llama.cpp/build-vulkan/bin/llama-bench"
LOG=results/halo-capped-diag.txt
IDLE=results/halo-capped-idle-pre.csv
CAP=1800
mkdir -p results logs
[ -f "$IDLE" ] || echo "timestamp,size,format,pass,idle_pre_w" > "$IDLE"
log() { echo "$(date +%H:%M:%S) $*" | tee -a "$LOG"; }

sudo -v || exit 1
( while sudo -n -v 2>/dev/null; do sleep 60; done ) &
KEEP=$!
restore() { echo auto | sudo -n tee $DEV/power_dpm_force_performance_level >/dev/null 2>&1 || true
            echo "r 1" | sudo -n tee $DEV/pp_od_clk_voltage >/dev/null 2>&1 || true; }
trap 'restore; kill $KEEP 2>/dev/null' EXIT

# wait for anything else on the GPU (the teacher faithfulness check) to finish
while pgrep -f 'teacher_chec[k]|llama-serve[r]|quality[.]py' >/dev/null; do sleep 15; done
: > "$LOG"
log "start; sysfs: $(cat $DEV/power_dpm_force_performance_level) / $(tr '\n' ' ' < $DEV/pp_dpm_sclk)"

w() { echo "$2" | sudo -n tee "$DEV/$1" >/dev/null; }
cur_mhz() { grep '\*' $DEV/pp_dpm_sclk | grep -o '[0-9]*Mhz' | grep -o '[0-9]*' | head -1; }
apply_cap() { w power_dpm_force_performance_level manual; w pp_od_clk_voltage "s 1 $CAP"; w pp_od_clk_voltage c; }
max_mhz_during() {
  "$@" >&2 & local bp=$! mx=0 c
  while kill -0 $bp 2>/dev/null; do c=$(cur_mhz); [ -n "$c" ] && [ "$c" -gt "$mx" ] && mx=$c; sleep 0.5; done
  wait $bp; echo $mx
}

# verify the cap under a decode load before measuring anything
restore; sleep 1; apply_cap; sleep 2
mx=$(max_mhz_during "$BENCH" -m models/quant/7b-Q4_0.gguf -p 0 -n 400 -r 2 -ngl 99 >/dev/null 2>&1)
log "cap check: force=$(cat $DEV/power_dpm_force_performance_level) active_max=${mx}MHz"
if [ -z "$mx" ] || [ "$mx" -gt $((CAP + 50)) ]; then log "cap did not hold, abort"; exit 1; fi

idle_pre() {  # size format pass
  sleep 5; local s=0 n=0
  for i in $(seq 1 10); do s=$((s + $(cat $HW))); n=$((n+1)); sleep 1; done
  local wv; wv=$(awk -v s=$s -v n=$n 'BEGIN{printf "%.2f", s/n/1e6}')
  echo "$(date -Is),$1,$2,$3,$wv" >> "$IDLE"; log "idle before $1 $2 pass$3: ${wv} W (clock $(cur_mhz)MHz)"
}
run() {  # size format model pass
  idle_pre "$1" "$2" "$4"
  log "=== quality cap$CAP $1 $2 pass$4 ==="
  mx=$(max_mhz_during uv run python experiments/quality.py "$3" "results/quality-halo-cap$CAP-$1-$2-pass$4.json" 250 8)
  log "=== done $1 $2 pass$4, active_max_during=${mx}MHz ==="
}
run 7b  Q4_0      models/quant/7b-Q4_0.gguf       1
run 32b Q2_K-imat models/quant/32b-Q2_K-imat.gguf 1
run 32b Q4_0      models/quant/32b-Q4_0.gguf      1
run 32b Q4_0      models/quant/32b-Q4_0.gguf      2   # pass 2 reversed
run 32b Q2_K-imat models/quant/32b-Q2_K-imat.gguf 2
run 7b  Q4_0      models/quant/7b-Q4_0.gguf       2

restore; sleep 1
{ echo "power_dpm_force_performance_level:"; cat $DEV/power_dpm_force_performance_level;
  echo "pp_dpm_sclk:"; cat $DEV/pp_dpm_sclk; echo "pp_od_clk_voltage:"; cat $DEV/pp_od_clk_voltage; } > results/halo-capped-readback.txt
log "=== READBACK ==="; cat results/halo-capped-readback.txt | tee -a "$LOG"
log "=== CAPPED QUALITY DONE ==="
# resume the Trace harvest (resumable; appends to its log so the eval chain still sees TRAIN DONE later)
nohup sh experiments/trace_35k.sh >> logs/trace_35k.log 2>&1 &
log "harvest resumed, pid $!"
