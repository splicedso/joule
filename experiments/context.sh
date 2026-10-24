#!/bin/sh
# Note 13: decode energy against context depth, with the default f16 KV cache and an 8-bit one.
# llama-bench's -d decodes with D tokens already in the context. Two passes, the second in
# reverse order. Same models, depths and settings on every machine.
#
#   sh experiments/context.sh <machine-tag>      e.g. mac
set -e
tag="$1"
cd "$(dirname "$0")/.."
run() {  # size depth kv pass
  extra="-d $2 -fa on"
  suffix=""
  [ "$3" = q8 ] && { extra="$extra -ctk q8_0 -ctv q8_0"; suffix="-kvq8"; }
  [ "$4" = 2 ] && suffix="$suffix-run2"
  uv run phase "models/quant/$1-Q4_0.gguf" --seconds 12 --out "results/depth-$tag-$1-d$2$suffix.json" -- $extra
}
for pass in 1 2; do
  depths="0 1024 4096 8192 16384"
  [ "$pass" = 2 ] && depths="16384 8192 4096 1024 0"
  for size in 1.5b 7b; do
    for d in $depths; do
      run "$size" "$d" f16 "$pass"
      run "$size" "$d" q8 "$pass"
    done
  done
done
