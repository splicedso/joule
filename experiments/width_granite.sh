#!/bin/sh
# A second family against note 6: Granite 3.3 2B and Qwen2.5 3B (both hidden 2048), five formats, two passes reversed.
set -e
cd "$(dirname "$0")/.."
M=""; for s in granite2b 3b; do for f in Q4_0 Q4_K_M Q5_K_M Q6_K Q8_0; do M="$M models/quant/$s-$f.gguf"; done; done
R=$(for m in $M; do echo $m; done | tail -r | tr '\n' ' ')
uv run phase $M --seconds 12 --out results/width-granite-run1.json
uv run phase $R --seconds 12 --out results/width-granite-run2.json
WIDTHS="granite2b:2048,3b:2048" uv run --with gguf python experiments/width.py results/width-granite-run1.json results/width-granite-run2.json results/summary-width-granite.json
# GSM8K-250 at 8 slots for three Granite formats (the prediction's accuracy clause), mirrored order
for f in Q4_0 Q4_K_M Q8_0; do uv run python experiments/quality.py models/quant/granite2b-$f.gguf results/quality-mac-granite2b-$f-pass1.json 250 8; done
for f in Q8_0 Q4_K_M Q4_0; do uv run python experiments/quality.py models/quant/granite2b-$f.gguf results/quality-mac-granite2b-$f-pass2.json 250 8; done
