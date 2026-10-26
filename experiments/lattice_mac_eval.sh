#!/bin/sh
# Lattice v1 on the M5 Pro: the half of the bar the Strix pipeline (lattice_qat.sh) cannot judge.
# The bar (docs/program.md): at least 60% on GSM8K-250 at Q2_K size, and cheaper per correct answer than
# Q4_0 on this machine. Three models in one session, mirrored so each meets the same warm-up: QAT 2-bit,
# stock Q4_0, the QAT weights at Q4_0 (the control), then the same three reversed; each quality.py at
# note 20's settings (250 questions, 8 slots). Energy runs: nothing else on the machine.
# The control separates the two things fine-tuning changes: if the QAT 2-bit beats stock Q4_0 only because
# its answers got shorter, the QAT Q4_0 will beat it too, and the note must say the win is length, not bits.
#
#   sh experiments/lattice_mac_eval.sh [QAT_Q2_K.gguf] [QAT_Q4_0.gguf]
#
# Missing files are fetched from the draft release lattice-v1-qat (drafts are visible only to repo writers,
# so this is a transfer, not a publication) and checked against the release's SHA256SUMS.
set -e
cd "$(dirname "$0")/.."
QAT=${1:-models/quant/1.5b-qat-Q2_K-imat.gguf}
CTL=${2:-models/quant/1.5b-qat-Q4_0.gguf}
REF=models/quant/1.5b-Q4_0.gguf
for f in "$QAT" "$CTL"; do
  [ -f "$f" ] && continue
  echo "fetching $f from the draft release lattice-v1-qat"
  gh release download lattice-v1-qat --pattern "$(basename "$f")" --pattern SHA256SUMS --dir models/quant --clobber
  (cd models/quant && grep " $(basename "$f")\$" SHA256SUMS | shasum -a 256 -c -) || { echo "checksum mismatch on $f; not measuring"; exit 1; }
done
if pgrep -f "Blender|Google Chrome|Safari|firefox|llama-server|quality[.]py" >/dev/null; then
  echo "something else is running (a browser, Blender or a server); close it first"; exit 1
fi
run() { uv run python experiments/quality.py "$1" "results/lattice-mac-v1-$2-pass$3.json" 250 8; }
run "$QAT" qat 1
run "$REF" q4_0 1
run "$CTL" qat_q4_0 1
run "$CTL" qat_q4_0 2
run "$REF" q4_0 2
run "$QAT" qat 2
uv run python - <<'PY'
import json
s = {(m, p): json.load(open(f"results/lattice-mac-v1-{m}-pass{p}.json"))["summary"] for m in ("qat", "q4_0", "qat_q4_0") for p in (1, 2)}
mean = lambda m, k: (s[(m, 1)][k] + s[(m, 2)][k]) / 2
print("| model | accuracy | J per correct | mJ per token | tokens per answer | tok/s | pass spread (J/correct) |")
print("|---|---:|---:|---:|---:|---:|---:|")
for m in ("qat", "q4_0", "qat_q4_0"):
    a, b = s[(m, 1)]["chip_j_per_correct"], s[(m, 2)]["chip_j_per_correct"]
    print(f"| {m} | {100 * mean(m, 'accuracy'):.1f}% | {mean(m, 'chip_j_per_correct'):.1f} | {mean(m, 'chip_mj_per_token'):.1f} | {mean(m, 'tokens') / 250:.0f} | {mean(m, 'tok_s'):.0f} | {100 * abs(a - b) / ((a + b) / 2):.1f}% |")
acc, jq, jr = mean("qat", "accuracy"), mean("qat", "chip_j_per_correct"), mean("q4_0", "chip_j_per_correct")
print(f"\nbar, accuracy at least 60%: {'met' if acc >= 0.60 else 'missed'} ({100 * acc:.1f}%)")
print(f"bar, cheaper per correct answer than Q4_0 on the M5 Pro: {'met' if jq < jr else 'missed'} ({jq:.1f} against {jr:.1f} J, {100 * (jq / jr - 1):+.0f}%)")
jc = mean("qat_q4_0", "chip_j_per_correct")
print(f"control, the QAT weights at Q4_0: {jc:.1f} J per correct; 2-bit {'beats' if jq < jc else 'does not beat'} 4-bit on the same weights")
print("note 20's Q4_0 reference, same settings, earlier session: 65.8%, 14.8 J per correct")
PY
