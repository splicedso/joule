# The memory-bound regime: when a long context caps the batch

Spliced research note 16 (Windows half), 24 October 2026. Windows 11 laptop: Intel Core Ultra 9 285H, NVIDIA GeForce RTX 5070 Ti Laptop GPU (12 GB, Blackwell), 32 GB RAM, on AC. llama.cpp build 11851 (prebuilt CUDA 13.4 x64), CUDA backend, all layers on the GPU. Qwen2.5 7B Q4_0.

Note 14 found that a 4096-token context barely dents the batching saving, and said why: the cache still fit, so batching was never forced down, and note 8's lost-batching effect needs memory to be the binding constraint. This note forces that constraint. At 8192 and 16384 tokens of context on a 12 GB card, how large a batch still fits, what does the forced-smaller batch cost, and can an 8-bit KV cache, which note 13 found costs more energy per token, win it back by letting a bigger batch fit?

## Method

7B Q4_0, `experiments/batching.py` with 512 generated tokens per sequence, three passes. Each batch size was run in its own invocation, so its key-value cache is sized to that batch alone: `batching.py` allocates the context for the largest batch in a run, which would spill every batch in a shared run, so a per-batch invocation is the only way to find the true fit boundary. Context lengths 8192 and 16384. Three cache settings: the default f16 cache, the f16 cache with flash attention (`-fa on`), and an 8-bit cache (`-ctk q8_0 -ctv q8_0 -fa on`). GPU (chip) energy only.

This card does not hard-fail when a run exceeds VRAM: the NVIDIA driver spills to shared system memory and the run crawls. So a spill shows as peak dedicated memory pegged near the 12 GB cap with throughput collapsing, not as an out-of-memory error. Fit and spill were judged by peak `nvidia-smi` memory and completion, not by a timeout, because a large batch at a long context has a slow prefill that is not itself a spill. `batching.py` was given a minimal optional passthrough so trailing flags reach llama-batched-bench (noted in the PR); nothing else in it changed.

Per-cell spread (max over min of three passes) was under 2% at batch 4 and above, where the comparisons below are made. Batch 1 and 2 at these lengths, with few short decode windows, spread up to 15% and are the least precise cells.

## What fits

Largest batch that fit in 12 GB, with peak dedicated VRAM:

| context | f16 cache | q8_0 cache |
|---|---|---|
| 8192 | batch 8 (8.4 GB); batch 16 spills (11.9 GB, pegged) | batch 16 (8.6 GB); batch 32 spills |
| 16384 | batch 8 (11.9 GB); batch 16 spills | batch 8 (8.4 GB); batch 16 spills (11.9 GB, pegged) |

The 4.4 GB of weights plus the cache decide this. At 8192 the f16 cache for 16 sequences is about 7.8 GB and with the weights does not fit; at 16384 it is about 15 GB and does not fit for 16 at either precision.

## Energy, at equal flash attention

Chip energy per token (mJ) and decode speed (tok/s), mean of three passes. The f16 cache with and without flash attention agreed within about 1% (for example batch 8 at 8192: 313.3 against 315.7 mJ), so the q8 comparison below is not a flash-attention artifact.

| context | setting | batch | mJ/tok | tok/s |
|---|---|---:|---:|---:|
| 8192 | f16 (fa) | 8 (its max) | 313.3 | 310.9 |
| 8192 | q8_0 | 8 | 463.8 | 210.6 |
| 8192 | q8_0 | 16 (its max) | 333.1 | 286.4 |
| 16384 | f16 (fa) | 8 (its max) | 420.1 | 230.3 |
| 16384 | q8_0 | 8 (its max) | 689.6 | 141.1 |

## 1. A long context caps the batch, and that is the whole cost

On this card the f16 cache fits only 8 sequences at 8192 or 16384 tokens; batch 16 spills at both. Batching is the lever that makes a token cheap (note 8), and here memory caps it at 8 exactly because the context is long. This is note 8's lost-batching effect made concrete on one machine: not that a long context makes each token's compute dearer (note 13 found that direct cost small), but that it takes away the batch headroom that would have made the token cheap.

## 2. The 8-bit cache does not win the batch back

Note 13 found an 8-bit cache costs more energy per token than f16 when the f16 cache already fits. The hope was that by halving the cache it could let a larger batch fit and so pay for itself. It does not, in either length tested.

- At 16384 it cannot fit a larger batch than f16 does: q8 batch 16 spills just as f16 batch 16 does, because sixteen sequences' 8-bit cache, about 7.5 GB, plus 4.4 GB of weights and the compute buffers still exceeds 12 GB. So the 8-bit cache buys no extra batch and is a pure loss, 689.6 against 420.1 mJ per token at batch 8, 1.64 times the energy, and slower (141 against 230 tok/s).
- At 8192 it does let batch 16 fit, where f16 is stuck at 8. The extra batching recovers most of its own penalty: q8 at batch 16 costs 333.1 mJ per token against q8 at batch 8's 463.8, a 28% drop. But that still does not beat the f16 cache at its own largest batch: f16 batch 8 is 313.3 mJ per token, so q8 batch 16 costs 6% more, and runs slower (286.4 against 310.9 tok/s).

So even in the one case where the 8-bit cache buys a bigger batch, the bigger batch only draws level with, and stays just behind, what the f16 cache already did at batch 8.

## 3. Why halving the cache was not enough

Halving the cache can at most double the batch that fits, and here it did less than that or exactly that: no extra step at 16384, one step from 8 to 16 at 8192. So the 8-bit cache wins only where one batch doubling saves more than its own per-token penalty, about 1.5 times here. At these batch sizes it does not. Going from batch 8 to 16 with the 8-bit cache saved 28%, a factor of 1.39, short of the 1.48 times the 8-bit cache costs at batch 8 and 8192 tokens.

The doubling saves most when the batch is small: in this note, batch 1 to 2 saved 40 to 43% with the f16 cache. So the 8-bit cache has its best chance when the long context leaves room for only one or two sequences in f16, and halving the cache lets a second fit. That is the regime of a larger model or a smaller card, not tested here.

Update: note 17 tested this at 65536 tokens, where f16 fits two sequences and the 8-bit cache three. It does not hold on this card: the context long enough to force the batch that low also shrinks the batching saving and raises the 8-bit penalty.

## What to take from this

1. A long context's real cost on a memory-limited device is the batch it forbids. Memory caps the batch at 8 for a 7B model at 8192 to 16384 tokens on a 12 GB card, which caps how cheap a token can get.
2. An 8-bit KV cache does not undo that here. At 16384 it fits no larger batch and costs 1.64 times the energy; at 8192 it fits one step larger and still lands 6% above the f16 cache's best.
3. Halving the cache can at most double the batch, so the 8-bit cache pays only where one doubling saves more than its roughly 1.5 times penalty. That means very small batches, where memory leaves room for one or two sequences; at batch 8 to 16 it does not.

## Limits

GPU (chip) energy only; no whole-system figure on AC. One model (7B Q4_0), two context lengths, one card. Spill was judged by peak VRAM and a throughput collapse, not a hard error, because the driver spills to shared memory. Each batch was measured in its own invocation, so these are single-stream batch runs, not a server scheduler packing mixed-length sequences. The spilled runs were stopped and not saved, so the fit boundaries rest on the peak-memory readings in this note, not on committed result files. `batching.py` gained a minimal flag passthrough. Build 11851 (CUDA).

## Reproduce

Windows, no admin, plugged in. With a clone and a prebuilt llama.cpp CUDA build on `PATH`:

```powershell
.\.venv\Scripts\python -m pip install -e .
# f16 cache, one batch per invocation so the cache is sized to that batch:
.\.venv\Scripts\python experiments/batching.py models/quant/7b-Q4_0.gguf results/membound-7b-p16384-b8-f16.json 8 16384
# 8-bit cache at the length where f16 first fails to fit a larger batch:
.\.venv\Scripts\python experiments/batching.py models/quant/7b-Q4_0.gguf results/membound-7b-p8192-b16-q8.json 16 8192 -ctk q8_0 -ctv q8_0 -fa on
```

Watch `nvidia-smi` memory.used: a batch that pegs it near 12 GB and then crawls has spilled to shared memory. Raw results: `results/membound-7b-p{8192,16384}-b*-{f16,f16fa,q8}.json`, `results/summary-memory-bound-windows.json`.
