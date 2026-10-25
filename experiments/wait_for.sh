#!/bin/sh
# Wait on a pid or a done-file, never on a command-line pattern (a pattern waiter matched its own
# command line twice today and never fired).
#   sh experiments/wait_for.sh pid 12345            exits when process 12345 is gone
#   sh experiments/wait_for.sh file LOG 'TRAIN DONE' exits when LOG contains the fixed string
# Optional third/fourth argument: poll interval in seconds (default 30).
mode=$1; target=$2
case $mode in
  pid)  every=${3:-30}; while [ -e "/proc/$target" ]; do sleep "$every"; done;;
  file) pat=$3; every=${4:-30}; until [ -f "$target" ] && grep -qF -- "$pat" "$target"; do sleep "$every"; done;;
  *) echo "usage: wait_for.sh pid PID [every] | file PATH 'STRING' [every]" >&2; exit 2;;
esac
