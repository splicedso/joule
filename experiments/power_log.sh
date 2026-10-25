#!/bin/sh
# Package power logger: every 10 s, package power (W), active shader / memory / fabric / display
# clocks, GPU busy, the display's power state and the 1-min load average, appended to
# logs/halo-power-log.csv (snapshotted into results/halo-power-log.csv with each PR, so the tracked
# file never changes under git's feet). Runs all day, measurements included (one sysfs read per 10 s is far
# below the sampler's noise). Start: nohup sh experiments/power_log.sh &  (stop it by pid)
# Why the extra columns: on 2026-10-25 a 32B run sat at 65 W for 15 min at the same shader clock
# and GPU load, then jumped to 80 W; the shader clock alone could not say what changed.
cd /home/martin/spliced/phase
D=/sys/class/drm/card0/device
HW=$D/hwmon/hwmon3/power1_average
OUT=logs/halo-power-log.csv   # live file (gitignored); copied to results/halo-power-log.csv at each PR
[ -f "$OUT" ] || echo "timestamp,package_w,sclk_mhz,gpu_busy_pct,mclk_mhz,fclk_mhz,dcefclk_mhz,display_dpms,load1" > "$OUT"
cur() { grep '\*' "$D/pp_dpm_$1" 2>/dev/null | grep -o '[0-9]*Mhz' | grep -o '[0-9]*' | head -1; }
dpms() { for c in /sys/class/drm/card0-*; do [ "$(cat $c/status 2>/dev/null)" = connected ] && { cat $c/dpms; return; }; done; echo none; }
while true; do
  w=$(awk '{printf "%.2f", $1/1e6}' $HW)
  echo "$(date -Is),$w,$(cur sclk),$(cat $D/gpu_busy_percent),$(cur mclk),$(cur fclk),$(cur dcefclk),$(dpms),$(cut -d' ' -f1 /proc/loadavg)" >> "$OUT"
  sleep 10
done
