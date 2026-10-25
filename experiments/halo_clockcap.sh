#!/usr/bin/env bash
# GPU shader-clock cap sweep v3 for 7B Q4_0 on Strix Halo (gfx1151, Vulkan).
# v1 found the pp_dpm_sclk mask alone did not pin the clock (GPU hit 2900 regardless).
# v2 (never run) tried several amdgpu controls and verified each under load.
# v3 is v2 plus the program's rules: every mechanism that really caps the clock is measured in two
# passes (the second in reverse order), each phase run records its own idle baseline, and the
# active clock is sampled during every measurement so a cap that slips is visible in the diag log.
# sudo is entered once (sudo -v) and refreshed from inside the script for its duration; nothing
# is made passwordless. The trap restores auto and resets the OD table on any exit.
set -u
cd /home/martin/spliced/phase
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
DEV=/sys/class/drm/card0/device
M7=models/quant/7b-Q4_0.gguf
BENCH="$PWD/vendor/llama.cpp/build-vulkan/bin/llama-bench"
LOG=results/halo-clockcap-diag.txt
mkdir -p results logs

if pgrep -f 'llama-server|quality.py|teacher.py|train_trace|prepare.py' | grep -vx -e $$ -e $PPID >/dev/null; then
  echo "another GPU/CPU job is running, abort"; exit 1
fi
: > "$LOG"
log() { echo "$(date +%H:%M:%S) $*" | tee -a "$LOG"; }

sudo -v || exit 1
( while sudo -n -v 2>/dev/null; do sleep 60; done ) &
KEEP=$!
restore() { echo auto | sudo -n tee $DEV/power_dpm_force_performance_level >/dev/null 2>&1 || true
            echo "r 1" | sudo -n tee $DEV/pp_od_clk_voltage >/dev/null 2>&1 || true; }
trap 'restore; kill $KEEP 2>/dev/null' EXIT

w() { echo "$2" | sudo -n tee "$DEV/$1" >/dev/null; }
cur_mhz() { grep '\*' $DEV/pp_dpm_sclk | grep -o '[0-9]*Mhz' | grep -o '[0-9]*' | head -1; }

apply() {  # label
  case $1 in
    auto)         restore;;
    force_low)    w power_dpm_force_performance_level low;;
    manual_sclk0) w power_dpm_force_performance_level manual; w pp_dpm_sclk 0;;
    od_1200)      w power_dpm_force_performance_level manual; w pp_od_clk_voltage "s 1 1200"; w pp_od_clk_voltage c; w pp_dpm_sclk 2;;
    od_1800)      w power_dpm_force_performance_level manual; w pp_od_clk_voltage "s 1 1800"; w pp_od_clk_voltage c; w pp_dpm_sclk 2;;
  esac
}

# max active shader clock (MHz) sampled for as long as a command runs
max_mhz_during() {
  "$@" >&2 & local bp=$! mx=0 c   # child's stdout to stderr, so only the MHz is captured
  while kill -0 $bp 2>/dev/null; do c=$(cur_mhz); [ -n "$c" ] && [ "$c" -gt "$mx" ] && mx=$c; sleep 0.2; done
  wait $bp; echo $mx
}
active_under_load() { max_mhz_during $BENCH -m $M7 -p 0 -n 400 -r 2 -ngl 99 >/dev/null 2>&1; }
bench_quiet() { "$BENCH" -m $M7 -p 0 -n 400 -r 2 -ngl 99 >/dev/null 2>&1; }

log "force levels: $(cat $DEV/power_dpm_force_performance_level)"
log "pp_dpm_sclk: $(tr '\n' ' ' < $DEV/pp_dpm_sclk)"
log "OD table: $(tr '\n' ' ' < $DEV/pp_od_clk_voltage)"

# --- try each mechanism, verify it caps the clock under a decode load ---
CAPPED=()
for label in force_low manual_sclk0 od_1200 od_1800; do
  restore; sleep 1; apply $label; sleep 2
  fl=$(cat $DEV/power_dpm_force_performance_level)
  mx=$(max_mhz_during bench_quiet)
  log "TRY $label -> force=$fl active_max=${mx}MHz"
  if [ -n "$mx" ] && [ "$mx" -gt 0 ] && [ "$mx" -lt 2800 ]; then CAPPED+=($label); fi
done
log "=== CAPPED MECHANISMS: ${CAPPED[*]:-none} ==="

measure() {  # label pass
  restore; sleep 1; apply $1; sleep 2
  log "MEASURE $1 pass$2 force=$(cat $DEV/power_dpm_force_performance_level) sclk_now=$(cur_mhz)MHz"
  mx=$(max_mhz_during uv run phase $M7 --seconds 20 --idle 10 --out results/halo-clockcap-$1-pass$2.json -- -ngl 99)
  log "MEASURE $1 pass$2 done, active_max_during=${mx}MHz"
}
ORDER=(auto "${CAPPED[@]}")
for label in "${ORDER[@]}"; do measure $label 1; done
for ((i=${#ORDER[@]}-1; i>=0; i--)); do measure "${ORDER[$i]}" 2; done   # pass 2 reversed

restore; sleep 1
{ echo "power_dpm_force_performance_level:"; cat $DEV/power_dpm_force_performance_level;
  echo "pp_dpm_sclk:"; cat $DEV/pp_dpm_sclk;
  echo "pp_od_clk_voltage:"; cat $DEV/pp_od_clk_voltage; } > results/halo-clockcap-readback.txt
log "=== READBACK ==="; cat results/halo-clockcap-readback.txt | tee -a "$LOG"
log "=== CLOCKCAP V3 DONE ==="
