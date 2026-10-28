#!/bin/sh
# Smoke test of qat.py's LoRA path and of export.sh, on the 0.5B: three steps on a 210-row toy dataset (200 of them are the
# held-out set), then the export in the stock layout. Checks that the LoRA moved the block linears and nothing else, and that
# the exported Q4_0 has output.weight at Q6_K and token_embd at Q4_0. A few minutes; uses the GPU, so not during an energy run.
set -e
cd /home/martin/spliced/phase
D=logs/lora_smoke; rm -rf "$D"; mkdir -p "$D"
python3 - "$D" <<'EOF'
import json, sys
d = sys.argv[1]
with open(f"{d}/toy.jsonl", "w") as f:
    for i in range(210):
        f.write(json.dumps({"prompt": f"What is {i} plus {i}?", "response": f"The answer is {2 * i}."}) + "\n")
EOF
echo "=== qat.py LoRA, 0.5B, 3 steps $(date) ==="
STEPS=3 BATCH=2 SEQ=64 QUANT=0 LORA_R=4 LORA_ALPHA=8 LR=1e-3 DATA=$D/toy.jsonl GENERAL_FRAC=0 CKPT_EVERY=0 EVAL_EVERY=100 \
  .venv-torch/bin/python experiments/lattice/qat.py models/hf-0.5b "$D/out"
.venv-torch/bin/python - "$D/out" <<'EOF'
import sys, torch
from safetensors.torch import load_file
a, b = load_file("models/hf-0.5b/model.safetensors"), load_file(sys.argv[1] + "/model.safetensors")
assert a.keys() == b.keys(), (set(a) ^ set(b))
moved = [k for k in a if not torch.equal(a[k], b[k])]
blocks = [k for k in moved if ".layers." in k and k.endswith("proj.weight")]
other = [k for k in moved if k not in blocks]
print(f"{len(moved)} tensors moved, {len(blocks)} block linears; unchanged outside them: {not other}")
assert blocks and not other, other[:5]
EOF
STOCK= sh experiments/rft/export.sh "$D/out" "$D/0.5b-smoke"
uv run --with ./vendor/llama.cpp/gguf-py python - "$D/0.5b-smoke-Q4_0.gguf" <<'EOF'
import sys, gguf
t = {x.name: x.tensor_type.name for x in gguf.GGUFReader(sys.argv[1]).tensors}
print("output.weight", t.get("output.weight"), "token_embd.weight", t.get("token_embd.weight"), "tensors", len(t))
assert t.get("output.weight") == "Q6_K" and t.get("token_embd.weight") == "Q4_0"
EOF
echo "=== LORA SMOKE OK $(date) ==="
