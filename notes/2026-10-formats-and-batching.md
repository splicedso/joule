# Fewer bits is not fewer joules

Spliced research note 1, 24 October 2026. Apple M5 Pro, 24 GB, macOS on AC, llama.cpp build 11669 (Homebrew), Metal, all layers on the GPU.

## Question

Does a lower-bit format cost less energy per decoded token on unified memory, and how much does serving several sequences at once save? Prior Apple Silicon energy work measures one format (Q4) with powermetrics, chip only, at about 2 s resolution, and names DRAM as the part it cannot see. Profiling work on Apple quantization reports latency, not energy. We measure both the chip (200 ms or faster) and the board's DC input, without sudo.

## Method

- One model, Qwen2.5 1.5B Instruct, quantized from the same F16 GGUF with `llama-quantize` (no importance matrix) into Q2_K, Q3_K_M, Q4_0, Q4_K_M, Q5_K_M, Q6_K, Q8_0, plus F16.
- Energy: `joule` (this repository). Decode is 128 generated tokens per repetition, about 15 timed seconds per format, first quarter of the window dropped, idle baseline taken first. Two full passes, the second in reverse order to expose drift and order effects.
- Quality: `llama-perplexity` on the WikiText-2 raw test set, 512-token context, 60 chunks.
- Batching: `experiments/batching.py` runs `llama-batched-bench` (64 prompt tokens, 512 generated per sequence) at batch 1 to 8, three passes, and aligns each decode window to the power samples. Chip power only, since the board reading is smoothed to about 1 Hz.

## Results: formats, batch 1

| format | perplexity | chip mJ/tok | board mJ/tok | tok/s |
|---|---:|---:|---:|---:|
| F16 | 9.63 | 134.6 | 546.5 | 84 |
| Q8_0 | 9.63 | 154.1 | 408.3 | 142 |
| Q6_K | 9.65 | 152.2 | 369.5 | 171 |
| Q5_K_M | 9.70 | 196.8 | 411.4 | 178 |
| Q4_K_M | 10.01 | 134.0 | 314.2 | 205 |
| Q4_0 | 10.09 | 98.7 | 257.9 | 214 |
| Q3_K_M | 10.76 | 160.8 | 332.1 | 205 |
| Q2_K | 15.90 | 133.2 | 279.3 | 228 |

Energy is the mean of two passes, which agreed within 4% for every format. Perplexity standard errors are about 0.21.

1. **Energy does not fall with bit width.** Chip energy ranges from 98.7 (Q4_0) to 196.8 mJ (Q5_K_M), in no order of bits.
2. **Chip-only measurement misranks F16.** On the chip F16 matches Q4_K_M, because the GPU draws only about 11 W while it waits on memory. At the board F16 is the most expensive format, 2.1 times Q4_0. The memory traffic is real energy that a package measurement does not see.
3. **Q4_0 is the efficient 4-bit format here.** Its perplexity is within error of Q4_K_M at 18% less board energy and 26% less chip energy, at the same speed. The formats nothing else beats on both quality and board energy are Q4_0, Q4_K_M, Q6_K and Q8_0. Q5_K_M, Q3_K_M and Q2_K are each beaten on both.

<!-- chart:fmt -->

## Results: batching

| batch | Q4_0 chip mJ/tok | Q4_0 GPU W | Q4_K_M chip mJ/tok | Q4_K_M GPU W |
|---:|---:|---:|---:|---:|
| 1 | 104.7 | 17.9 | 135.6 | 24.4 |
| 2 | 103.3 | 32.7 | 120.9 | 36.4 |
| 4 | 54.3 | 33.3 | 62.0 | 35.0 |
| 8 | 29.3 | 33.2 | 33.7 | 34.6 |

<!-- chart:bat -->

GPU power is a step, not a ramp. At batch 1 the GPU is memory-bound and draws 18 to 24 W. At batch 2 it reaches its ceiling and stays there through batch 8, while throughput keeps rising. So the second sequence pays for nearly the whole power step: batch 2 saves 1% per token on Q4_0. Batch 8 saves 72%.

We first suspected llama.cpp's Metal kernel selection: its small-batch matrix-vector kernel covers batch 2 to 8 for Q4_0 but only 4 to 8 for K-quants (`ggml-metal-ops.cpp`). Q4_0 shows the same flat step at batch 2 despite getting that kernel, so the selection does not explain it. The GPU clock read 1620 MHz throughout, so frequency scaling does not either.

## Limits

- One machine, one model size, one runtime. The format ranking may change with model size, with MLX, and on other chips.
- Board power is DC input reported by the SMC, not wall power, and is smoothed. It is only used over windows of 10 s or more.
- Perplexity on WikiText-2 is a proxy for quality, not a task score.
- The machine was a working laptop, not a thermally settled bench. Repeat runs agreed within 4%.

## Reproduce

```bash
brew install macmon llama.cpp
uv run joule models/quant/1.5b-*.gguf --seconds 15 --out results/run.json
uv run python experiments/batching.py model.gguf results/batch.json 1,2,3,4,5,6,7,8
```

Raw results: `results/quant-energy-1.5b*.json`, `results/quant-ppl-1.5b.txt`, `results/batching-gpu-1.5b-*.json`.
