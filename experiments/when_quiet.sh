#!/bin/sh
# Run a measurement script only once the Mac is quiet: idle chip power under LIMIT watts in two checks in a row,
# five minutes apart, each a 10 s macmon sample. Gives up after HOURS.   sh experiments/when_quiet.sh SCRIPT
LIMIT=${LIMIT:-2}; HOURS=${HOURS:-8}; ok=0; end=$(( $(date +%s) + HOURS * 3600 ))
while [ "$(date +%s)" -lt "$end" ]; do
  w=$(macmon pipe -i 1000 -s 10 2>/dev/null | python3 -c "import json,sys; v=[json.loads(l)['all_power'] for l in sys.stdin if l.strip()]; print(f'{sum(v)/len(v):.2f}')")
  echo "$(date +%H:%M) idle chip ${w} W"
  if python3 -c "import sys; sys.exit(0 if float('$w') < $LIMIT else 1)"; then ok=$((ok + 1)); else ok=0; fi
  if [ "$ok" -ge 2 ]; then echo "$(date +%H:%M) quiet; running $1"; sh "$1"; exit $?; fi
  sleep 300
done
echo "$(date +%H:%M) never quiet in ${HOURS} h; not run"; exit 3
