#!/bin/sh
# Closed-model plan, Phase 2 pilot (docs/concepts/closed-model.md): rejection-sampling fine-tuning of Qwen2.5 1.5B Instruct on
# its own correct answers. STAGE=train: sample (4 per problem at T 0.8 from the stock Q4_0 file, 32 slots; cut to 2 if the
# projection passes 6 h), keep correct ones (at most 2 per problem), one epoch of full fine-tuning through qat.py's plain path
# (QUANT=0) with 10% FineWeb-Edu batches on top, export F16 and Q4_0. STAGE=eval: general_eval.py, stock Q4_0, RFT Q4_0, RFT F16,
# then reversed, 8 slots, MAX_TOKENS 2048 (ENERGY runs: GPU-exclusive, machine quiet).
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
mkdir -p data/rft results/rft
if [ "${STAGE:-train}" = train ]; then
  echo "=== sample $(date) ==="
  uv run --with pyarrow python experiments/rft/sample.py models/quant/1.5b-Q4_0.gguf data/rft/samples-1.5b.jsonl
  cp data/rft/samples-1.5b.summary.json results/rft/sampling-1.5b.json
  echo "=== build $(date) ==="
  python3 experiments/rft/build.py data/rft/samples-1.5b.jsonl data/rft/rft-1.5b.jsonl | tee results/rft/dataset-1.5b.json
  echo "=== train (QUANT=0, DATA, GENERAL_FRAC 0.1) $(date) ==="
  QUANT=0 DATA=data/rft/rft-1.5b.jsonl GENERAL_FRAC=0.1 LR=1e-5 .venv-torch/bin/python experiments/lattice/qat.py models/hf-1.5b models/rft-1.5b
  cp models/rft-1.5b/train_log.json results/rft/train-log-1.5b.json
  echo "=== export $(date) ==="
  uv run --with "numpy<3" --with sentencepiece --with "transformers>=4.45" --with torch --with safetensors \
    --with ./vendor/llama.cpp/gguf-py python vendor/llama.cpp/convert_hf_to_gguf.py models/rft-1.5b --outtype f16 --outfile models/quant/1.5b-rft-F16.gguf
  llama-quantize models/quant/1.5b-rft-F16.gguf models/quant/1.5b-rft-Q4_0.gguf Q4_0
  echo "=== RFT TRAIN STAGE DONE $(date) ==="
else
  if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_[a-z]*[.]py|qat[.]py|curl -sL -C' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU or network busy, abort"; exit 1; fi
  [ "$(cat /sys/class/drm/card0/device/power_dpm_force_performance_level)" = auto ] || { echo "clock not auto, abort"; exit 1; }
  ev() { echo "=== $1 pass$3 $(date) ==="; MAX_TOKENS=2048 CTX_PER_SLOT=6144 EXEC_OK=1 uv run --with pyarrow python experiments/general_eval.py \
    "$2" "results/general-halo-$1-pass$3.json" gsm8k,mmlu_pro,humaneval 8; }
  ev 1.5b-Q4_0-rftwindow models/quant/1.5b-Q4_0.gguf 1; ev 1.5b-rft-Q4_0 models/quant/1.5b-rft-Q4_0.gguf 1; ev 1.5b-rft-F16 models/quant/1.5b-rft-F16.gguf 1
  ev 1.5b-rft-F16 models/quant/1.5b-rft-F16.gguf 2; ev 1.5b-rft-Q4_0 models/quant/1.5b-rft-Q4_0.gguf 2; ev 1.5b-Q4_0-rftwindow models/quant/1.5b-Q4_0.gguf 2
  echo "=== RFT EVAL STAGE DONE $(date) ==="
fi
