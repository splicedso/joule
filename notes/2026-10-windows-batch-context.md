# A long context does not spend the batching saving, where the cache still fits

Spliced research note 14 (Windows half), 24 October 2026. Windows 11 laptop: Intel Core Ultra 9 285H, NVIDIA GeForce RTX 5070 Ti Laptop GPU (12 GB, Blackwell), 32 GB RAM, on AC. llama.cpp build 11851 (prebuilt CUDA 13.4 x64), CUDA backend, all layers on the GPU. Qwen2.5 1.5B and 7B, Q4_0.

Note 8 found a 405B datacenter result costing 60 times the energy per token of a 70B one, concluded that long prefill alone could not explain it, and named two effects of a long context on decode: a larger key-value cache to read each step, and fewer sequences fitting in memory, so less batching. Note 13 measured the first at batch 1 and found it small, about 1.3 times at 16k, too small on its own. It named the batching loss as the untested remainder. This note tests that: does a long context erode the energy saving from batching?

## Method

`experiments/batching.py` (llama-batched-bench), batch sizes 1, 2, 4 and 8, 512 generated tokens per sequence, three passes. Two context lengths per sequence: 64 and 4096 prompt tokens. Two models, 1.5B and 7B Q4_0. Flash attention left at the script's default. GPU (chip) energy only, as in note 4; there is no whole-system reading on AC here. Batch 8 at 4096 tokens fit in the 12 GB of VRAM for both models, so nothing was dropped. The three passes agreed within 5% on chip energy per token at batch 2 and above; batch 1, with the shortest decode windows, varied up to 14%, and those cells are the least precise.

## Results

Chip energy per token (mJ) and decode speed (tok/s), mean of three passes:

1.5B Q4_0:

| batch | p64 mJ/tok | p64 tok/s | p4096 mJ/tok | p4096 tok/s |
|---:|---:|---:|---:|---:|
| 1 | 283.0 | 350.9 | 345.5 | 297.0 |
| 2 | 157.0 | 607.5 | 186.4 | 528.7 |
| 4 | 109.3 | 929.2 | 130.6 | 760.5 |
| 8 | 72.1 | 1383.5 | 95.7 | 1033.0 |

7B Q4_0:

| batch | p64 mJ/tok | p64 tok/s | p4096 mJ/tok | p4096 tok/s |
|---:|---:|---:|---:|---:|
| 1 | 1041.2 | 95.4 | 1130.2 | 87.7 |
| 2 | 566.4 | 175.4 | 601.2 | 165.6 |
| 4 | 322.9 | 309.1 | 368.3 | 268.5 |
| 8 | 222.1 | 446.1 | 269.1 | 366.8 |

Batch-8 saving, 1 minus mJ at batch 8 over mJ at batch 1:

| model | p64 | p4096 |
|---|---:|---:|
| 1.5B | 75% | 72% |
| 7B | 79% | 76% |

## 1. The saving survives at 4096 tokens

Batching still pays almost as well with a 4096-token context as with a 64-token one. Batch 8 cuts per-token energy by 72% at 4096 against 75% at 64 on the 1.5B, and by 76% against 79% on the 7B: a loss of 3 percentage points in both cases. Whatever ends batching's benefit at datacenter scale, a 4096-token context on this card is not enough to do it.

## 2. The context raises the floor, and dilutes the saving a little

A long context is not free: it makes every batch cost more, and more so at high batch. At batch 1 the 4096 context costs 1.22 times the 64-token one on the 1.5B and 1.09 times on the 7B; at batch 8 it costs 1.33 and 1.21 times. The batch-8 speed-up also falls, from 3.9 to 3.5 times on the 1.5B and from 4.7 to 4.2 times on the 7B.

The reason the saving dilutes is what batching does and does not amortise. Batching shares the weight read across the sequences in the batch, which is where its saving comes from. It does not share the key-value cache: each sequence has its own, it grows with the context, and it is read every decode step. So the per-step cache read is a cost that the batch cannot spread, and as the context grows it is a larger share of each token, which is why batch 8 saves 3 points less at 4096. At 4096 that share is still small.

## 3. What this says about note 8

This does not reproduce note 8's 60 times gap, and it is not meant to. Note 8's batching-loss effect is that at long contexts fewer sequences fit in memory, so a server is forced to a smaller batch. That requires memory to be the binding constraint. Here it was not: batch 8 at 4096 fit in 12 GB for both models, so batching was never forced down, and the saving held. Note 8's regime is batches near 58 at about 9,400 tokens, where the cache for a full batch would not fit and the batch must shrink. This note shows that context alone, within what fits, does not spend the batching saving; the datacenter effect needs the memory-bound regime that a 12 GB card at these sizes does not reach.

## What to take from this

1. A 4096-token context keeps 72 to 76% of the batch-8 energy saving on this card, against 75 to 79% at 64 tokens. Batching is robust to context length while the cache fits.
2. The small erosion that does happen is the per-sequence cache read, which batching cannot amortise. It grows with context and would matter more at datacenter depths.
3. Note 8's lost-batching effect is a memory-fit effect, not a context effect as such. It appears when the batch is forced down, which did not happen here.

## Limits

GPU (chip) energy only; no whole-system figure on AC. A 12 GB card, so the memory-bound regime where a long context forces the batch down, which is note 8's actual mechanism, is exactly what is not tested here. Batches to 8, contexts to 4096, two models, one quantization, greedy decode through llama-batched-bench. Build 11851 (CUDA) differs from the Mac's 11669 (Metal).

## Reproduce

Windows, no admin, plugged in. With a clone and a prebuilt llama.cpp CUDA build on `PATH`:

```powershell
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\python experiments/batching.py models/quant/1.5b-Q4_0.gguf results/batch-context-windows-1.5b-p64.json 1,2,4,8 64
.\.venv\Scripts\python experiments/batching.py models/quant/1.5b-Q4_0.gguf results/batch-context-windows-1.5b-p4096.json 1,2,4,8 4096
.\.venv\Scripts\python experiments/batching.py models/quant/7b-Q4_0.gguf results/batch-context-windows-7b-p64.json 1,2,4,8 64
.\.venv\Scripts\python experiments/batching.py models/quant/7b-Q4_0.gguf results/batch-context-windows-7b-p4096.json 1,2,4,8 4096
```

Raw results: `results/batch-context-windows-{1.5b,7b}-p{64,4096}.json`, `results/summary-batch-context-windows.json`.
