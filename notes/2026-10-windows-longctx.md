# The 8-bit cache does not win even when it fits an extra sequence

Spliced research note 17 (Windows half), 24 October 2026. Windows 11 laptop: Intel Core Ultra 9 285H, NVIDIA GeForce RTX 5070 Ti Laptop GPU (12 GB, Blackwell), 32 GB RAM, on AC. llama.cpp build 11851 (prebuilt CUDA 13.4 x64), CUDA backend, all layers on the GPU. Qwen2.5 7B Q4_0, context 65536.

Note 16 found that an 8-bit KV cache did not win in the memory-bound regime it tested, and reasoned that it would win where the f16 cache fits only one or two sequences and the 8-bit cache lets another fit, because at small batch a single doubling saves more than the cache's roughly 1.5 times per-token penalty costs. This note tests that prediction directly. It does not hold on this card, and the reason is that the two conditions it needs do not occur together here.

## Finding the regime

At 32768 tokens the f16 cache still fit 4 sequences (batch 6 spilled), so it is not the one-or-two regime. Pushing the context to 65536, twice the model's 32768 native length (llama.cpp extrapolates RoPE beyond the trained length; output quality is not scored here, this is an energy and memory measurement), brings the f16 cache down to 2 sequences. That is the regime the prediction is about.

## Method

7B Q4_0, `experiments/batching.py` with 512 generated tokens, three passes, each batch in its own invocation so its cache is sized to that batch. f16 cache with flash attention against an 8-bit cache (`-ctk q8_0 -ctv q8_0 -fa on`), batches 1, 2, 3, 4, 6 until each spills. GPU (chip) energy only. A spill is peak dedicated VRAM pegged near the 12 GB cap with throughput collapsing, this driver spilling to shared memory rather than erroring; each spilled attempt is recorded (batch, peak VRAM) in `results/longctx-spills.jsonl`. The 65536 cells below repeated within 2% across the three passes. The 32768 cells used only to locate the regime were noisier, 10 to 16%, and are not used for the comparison.

## Results at 65536

| cache | batch | mJ/tok | tok/s | peak VRAM | fit |
|---|---:|---:|---:|---:|---|
| f16 (fa) | 1 | 1933.6 | 49.4 | 8116 MiB | yes |
| f16 (fa) | 2 | 1440.3 | 66.8 | 11742 MiB | yes (its max) |
| f16 (fa) | 3 | - | - | 11876 MiB | spill |
| q8_0 | 1 | 2872.0 | 34.0 | 6418 MiB | yes |
| q8_0 | 2 | 2432.2 | 39.8 | 8344 MiB | yes |
| q8_0 | 3 | 2281.7 | 42.4 | 10370 MiB | yes (its max) |
| q8_0 | 4 | - | - | 11890 MiB | spill |

The 8-bit cache does let a third sequence fit, where the f16 cache stops at two. So the structural part of the prediction holds. The energy part does not: the 8-bit cache at its largest batch (3) costs 2281.7 mJ per token, against the f16 cache's 1440.3 at its largest batch (2). That is 1.58 times the energy, and slower (42.4 against 66.8 tok/s). The extra sequence does not pay for the cache.

## Why the prediction fails here

The prediction rests on two things being true at once: a batch doubling must save a lot, and the 8-bit cache's per-token penalty must be small. Both fail at the context needed to force the f16 cache down to two sequences.

- **The batch saving shrinks as the context grows.** The f16 batch 1 to 2 saving was 42% at 16384 (note 16), 30% at 32768, and 26% at 65536. A longer context makes decode attention-bound: each step must read the whole cache, which batching does not amortise because every sequence has its own cache, so the weight read that batching does share is a smaller part of the step.
- **The 8-bit penalty grows as the context grows.** The q8 against f16 cost at batch 1 was 1.23 times at 16384 (note 16) and 1.49 times at 65536. A larger cache is more key-value data to dequantize every step.

So the one extra sequence the 8-bit cache buys at 65536 saves only about 6% (batch 2 to 3, 2432.2 to 2281.7 mJ), against a penalty near 1.5 times. The conditions the prediction needs hold at short contexts, where the batch doubling is cheap and the penalty small, but at short contexts the f16 cache already fits many sequences and is never forced to one or two. The regime where f16 is forced low is exactly the regime where batching stops paying and the cache penalty is largest.

## What to take from this

1. The prediction from note 16 does not hold on this card. At 65536 the 8-bit cache fits a third sequence but still costs 1.58 times the f16 cache's best, because the context that forces f16 to two sequences also makes decode attention-bound.
2. An 8-bit KV cache lets you fit a longer context or one more sequence than you otherwise could. It does not make the resulting token cheaper than the f16 cache at its own limit, at any context tested here.
3. The lever that would make the 8-bit cache win, a cheap batch doubling, lives at short contexts, which do not need it. The two do not meet on a 7B model and a 12 GB card.

## Limits

GPU (chip) energy only; no whole-system figure on AC. One model (7B Q4_0), one card. 65536 is twice the model's native context, reached by RoPE extrapolation, so the attention pattern is outside training; the energy and memory behaviour is what is measured, not output quality. The f16 cache was forced to two sequences at 65536; a context that forces it to exactly one (longer still) would be more attention-bound, not less, so it was not expected to rescue the 8-bit cache and was not run. Shorter contexts that still leave f16 at two (around 49152) were not measured, but both governing trends run against the 8-bit cache as the context lengthens. Spill judged by peak VRAM and a throughput collapse, not a hard error. Build 11851 (CUDA).

## Reproduce

Windows, no admin, plugged in. With a clone and a prebuilt llama.cpp CUDA build on `PATH`:

```powershell
.\.venv\Scripts\python -m pip install -e .
# f16 cache, one batch per invocation, at a context that leaves f16 at two sequences:
.\.venv\Scripts\python experiments/batching.py models/quant/7b-Q4_0.gguf results/longctx-7b-p65536-b2-f16fa.json 2 65536 -fa on
# 8-bit cache, which fits one more sequence:
.\.venv\Scripts\python experiments/batching.py models/quant/7b-Q4_0.gguf results/longctx-7b-p65536-b3-q8.json 3 65536 -ctk q8_0 -ctv q8_0 -fa on
```

Watch `nvidia-smi` memory.used: a batch that pegs it near 12 GB and then crawls has spilled. Raw results: `results/longctx-7b-p{32768,65536}-b*-{f16fa,q8}.json`, `results/longctx-spills.jsonl`, `results/summary-longctx-windows.json`.
