#!/bin/sh
# Wait until the GPU is free for an energy run: no compute (KFD) client in /sys/class/kfd/kfd/proc and gpu_busy_percent
# under 5 for 60 s running (12 samples 5 s apart). Exit 0 when it passes, 1 after MAX_HOURS (default 24). Prints what it
# is waiting for every 10 min. Written 2026-10-26 after another session's ROCm job shared the GPU with the 32B cells.
#   sh experiments/gpu_gate.sh [max_hours]
D=/sys/class/drm/card0/device; MAXH=${1:-24}; t0=$(date +%s); ok=0; last=0
while :; do
  k=$(ls /sys/class/kfd/kfd/proc/ 2>/dev/null | wc -l); b=$(cat $D/gpu_busy_percent)
  if [ "$k" -eq 0 ] && [ "$b" -lt 5 ]; then ok=$((ok+1)); else ok=0; fi
  [ $ok -ge 12 ] && { echo "gpu gate passed $(date): no compute client, busy ${b}% for 60 s"; exit 0; }
  now=$(date +%s)
  [ $((now - t0)) -gt $((MAXH * 3600)) ] && { echo "gpu gate timed out after $MAXH h $(date)"; exit 1; }
  if [ $((now - last)) -ge 600 ]; then
    who=$(for p in $(ls /sys/class/kfd/kfd/proc/ 2>/dev/null); do ps -o comm= -p $p 2>/dev/null; done | tr '\n' ' ')
    echo "gpu gate waiting $(date): $k compute client(s) ${who:+($who)}, busy ${b}%"; last=$now
  fi
  sleep 5
done
