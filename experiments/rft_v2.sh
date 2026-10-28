#!/bin/sh
# RFT v2 on the 1.5B (docs/predictions.md, the "RFT v2 on the 1.5B: two arms, one change each" entry): the pilot's recipe
# (experiments/rft_pilot.sh: the same data/rft/rft-1.5b.jsonl, qat.py QUANT=0, batch 8, one epoch plus 10% general text)
# with one named change per arm.  ARM=lr: LR 2e-6 instead of 1e-5.  ARM=lora: a rank-16 LoRA (alpha 32) on the same 196
# block linears with everything else frozen, LR 1e-4, merged at export.  Export in the stock tensor layout
# (experiments/rft/export.sh).  STAGE=train (the GPU gate first: training is not an energy run but must not land on an eval),
# STAGE=eval (ENERGY runs: stock Q4_0 re-run in the window, the arm's Q4_0 and F16, and for ARM=lr the pilot's untied
# re-export; two passes, the second reversed, each behind the gate).  Resumable: qat.py picks up its checkpoint.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
ARM=${ARM:?set ARM=lr or ARM=lora}
case $ARM in
  lr)   TR="LR=2e-6";;
  lora) TR="LR=1e-4 LORA_R=16 LORA_ALPHA=32";;
  *) echo "ARM must be lr or lora"; exit 1;;
esac
mkdir -p results/rft
if [ "${STAGE:-train}" = train ]; then
  [ -f data/rft/rft-1.5b.jsonl ] || { echo "data/rft/rft-1.5b.jsonl missing (the pilot's dataset is reused, not rebuilt)"; exit 1; }
  sh experiments/gpu_gate.sh 24 || exit 1
  echo "=== train $ARM ($TR; QUANT=0 DATA=data/rft/rft-1.5b.jsonl GENERAL_FRAC=0.1) $(date) ==="
  env QUANT=0 DATA=data/rft/rft-1.5b.jsonl GENERAL_FRAC=0.1 $TR .venv-torch/bin/python experiments/lattice/qat.py models/hf-1.5b models/rft2-$ARM
  cp models/rft2-$ARM/train_log.json results/rft/train-log-rft2-$ARM.json
  sh experiments/rft/export.sh models/rft2-$ARM models/quant/1.5b-rft2-$ARM
  echo "=== RFT V2 $ARM TRAIN STAGE DONE $(date) ==="
else
  if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_[a-z]*[.]py|qat[.]py|curl -sL -C' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU or network busy, abort"; exit 1; fi
  [ "$(cat /sys/class/drm/card0/device/power_dpm_force_performance_level)" = auto ] || { echo "clock not auto, abort"; exit 1; }
  ev() { sh experiments/gpu_gate.sh 12 || exit 1; echo "=== $1 pass$3 $(date) ==="; MAX_TOKENS=2048 CTX_PER_SLOT=6144 EXEC_OK=1 uv run --with pyarrow python experiments/general_eval.py \
    "$2" "results/general-halo-$1-pass$3.json" gsm8k,mmlu_pro,humaneval 8; }
  FILES="1.5b-Q4_0-rft2window-$ARM:models/quant/1.5b-Q4_0.gguf"
  [ "$ARM" = lr ] && FILES="$FILES 1.5b-rft-untied-Q4_0:models/quant/1.5b-rft-untied-Q4_0.gguf"
  FILES="$FILES 1.5b-rft2-$ARM-Q4_0:models/quant/1.5b-rft2-$ARM-Q4_0.gguf 1.5b-rft2-$ARM-F16:models/quant/1.5b-rft2-$ARM-F16.gguf"
  for f in $FILES; do ev "${f%%:*}" "${f#*:}" 1; done
  for f in $(echo $FILES | tr ' ' '\n' | tac); do ev "${f%%:*}" "${f#*:}" 2; done
  echo "=== RFT V2 $ARM EVAL STAGE DONE $(date) ==="
fi
