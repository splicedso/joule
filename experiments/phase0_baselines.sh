#!/bin/sh
# Closed-model plan, Phase 0 (docs/concepts/closed-model.md): general-purpose baselines on the Strix Halo.
# general_eval.py (GSM8K-250, MMLU-Pro 20 per subject, HumanEval 164 executed inside bubblewrap), 8 slots, auto clocks,
# two passes in mirrored order, chip energy per task. Models: Qwen2.5 7B Q4_0 (today's model), and Qwen3.6-35B-A3B
# (Apache-2.0) converted here from the official weights and quantized to Q4_0 and Q8_0, each with thinking off and on.
# Steps 1 and 2 load the network and disk; they run only when no energy measurement is in progress.
set -e
export PATH="$HOME/.local/bin:/home/martin/spliced/phase/vendor/llama.cpp/build-vulkan/bin:$PATH"
cd /home/martin/spliced/phase
SRC=models/hf-qwen3.6-35b-a3b
echo "=== disk before $(date) ==="; df -h /home | tail -1
echo "=== 1. download Qwen/Qwen3.6-35B-A3B (resumable) $(date) ==="
mkdir -p "$SRC"
curl -sL -m 60 "https://huggingface.co/api/models/Qwen/Qwen3.6-35B-A3B/tree/main" | python3 -I -c "import json,sys; [print(f['path']) for f in json.load(sys.stdin) if f['type']=='file']" > "$SRC/.files"
while read f; do
  [ -f "$SRC/$f" ] && continue
  curl -sL -C - --retry 20 --retry-delay 5 -o "$SRC/$f.part" "https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/main/$f" && mv "$SRC/$f.part" "$SRC/$f"
done < "$SRC/.files"
python3 -I -c "import json; idx=json.load(open('$SRC/model.safetensors.index.json')); import os; missing=[f for f in set(idx['weight_map'].values()) if not os.path.exists('$SRC/'+f)]; print('missing shards:', missing); assert not missing"
echo "=== 2. convert and quantize $(date) ==="
[ -f models/quant/qwen3.6-35b-a3b-BF16.gguf ] || uv run --with "numpy<3" --with sentencepiece --with "transformers>=4.45" --with torch --with safetensors \
  --with ./vendor/llama.cpp/gguf-py python vendor/llama.cpp/convert_hf_to_gguf.py "$SRC" --outtype bf16 --outfile models/quant/qwen3.6-35b-a3b-BF16.gguf
for q in Q4_0 Q8_0; do [ -f models/quant/qwen3.6-35b-a3b-$q.gguf ] || nice -n 10 llama-quantize models/quant/qwen3.6-35b-a3b-BF16.gguf models/quant/qwen3.6-35b-a3b-$q.gguf $q; done
ls -la models/quant/qwen3.6-35b-a3b-*.gguf
echo "=== disk after conversion $(date) ==="; df -h /home | tail -1
if pgrep -f 'llama-serve[r]|quality[.]py|teacher[.]py|train_[a-z]*[.]py|qat[.]py' | grep -vx -e $$ -e $PPID >/dev/null; then echo "GPU busy, abort"; exit 1; fi
[ "$(cat /sys/class/drm/card0/device/power_dpm_force_performance_level)" = auto ] || { echo "clock not auto, abort"; exit 1; }
echo "=== 3. evals $(date) ==="
ev() {  # tag model think max_tokens pass
  echo "=== $1 pass$5 $(date) ==="
  THINK=$3 MAX_TOKENS=$4 CTX_PER_SLOT=$(($4 + 4096)) EXEC_OK=1 uv run --with pyarrow python experiments/general_eval.py \
    "$2" "results/general-halo-$1-pass$5.json" gsm8k,mmlu_pro,humaneval 8; }
Q=models/quant/qwen3.6-35b-a3b
RUNS="7b-Q4_0:models/quant/7b-Q4_0.gguf::2048 q36-Q4_0-nothink:$Q-Q4_0.gguf:0:4096 q36-Q8_0-nothink:$Q-Q8_0.gguf:0:4096 q36-Q4_0-think:$Q-Q4_0.gguf:1:16384 q36-Q8_0-think:$Q-Q8_0.gguf:1:16384"
for r in $RUNS; do IFS=:; set -- $r; unset IFS; ev "$1" "$2" "$3" "$4" 1; done
for r in $(echo $RUNS | tr ' ' '\n' | tac); do IFS=:; set -- $r; unset IFS; ev "$1" "$2" "$3" "$4" 2; done   # pass 2 reversed
echo "=== PHASE 0 DONE $(date) ==="
