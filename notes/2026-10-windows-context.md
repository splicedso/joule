# What a long context costs, and what an 8-bit KV cache does not save

Spliced research note 13 (Windows half), 24 October 2026. Windows 11 laptop: Intel Core Ultra 9 285H, NVIDIA GeForce RTX 5070 Ti Laptop GPU (12 GB, Blackwell), 32 GB RAM, on AC. llama.cpp build 11851 (prebuilt CUDA 13.4 x64), CUDA backend, all layers on the GPU. Qwen2.5 1.5B and 7B, Q4_0.

Note 8 found that a 405B model's measured energy per token was far above what its weights alone predict, on a benchmark whose prompts average about 9,400 tokens. It concluded that long prefill alone could not explain the gap, and that the larger effect was likely what long contexts do to decode: more key-value cache to read per step, and fewer sequences fitting in memory at once, so less batching. This note measures the first of those directly, at batch 1, on one machine: how much more does a token cost when the context is already deep, and does quantizing the KV cache to 8 bits, the usual fix for a large cache, save that energy back?

## Method

`phase --seconds 12` with llama-bench's decode test at a given context depth (`-d`), flash attention on (`-fa on`). Depths 0, 1024, 4096, 8192, 16384 tokens already in the cache. Two configurations: the default f16 KV cache, and an 8-bit cache (`-ctk q8_0 -ctv q8_0`). Two models, 1.5B and 7B Q4_0. The whole set ran twice, the second pass in reverse order. GPU (chip) energy only, as in note 4: there is no whole-system reading on AC on this machine. Every depth fit in the 12 GB of VRAM for both models and both cache types, so nothing was skipped or spilled to the CPU. The two passes agreed within 6% on chip energy per token for every cell.

## Results

Chip energy per decoded token (mJ) and decode speed (tok/s), mean of two passes:

1.5B Q4_0:

| depth | f16 tok/s | f16 mJ/tok | q8 tok/s | q8 mJ/tok | q8 / f16 |
|---:|---:|---:|---:|---:|---:|
| 0 | 349.1 | 288.0 | 332.9 | 300.2 | 1.04 |
| 1024 | 328.7 | 304.2 | 309.0 | 322.4 | 1.06 |
| 4096 | 305.4 | 322.6 | 269.2 | 357.5 | 1.11 |
| 8192 | 297.1 | 331.8 | 235.9 | 420.3 | 1.27 |
| 16384 | 258.5 | 367.5 | 193.1 | 521.8 | 1.42 |

7B Q4_0:

| depth | f16 tok/s | f16 mJ/tok | q8 tok/s | q8 mJ/tok | q8 / f16 |
|---:|---:|---:|---:|---:|---:|
| 0 | 97.5 | 1027.0 | 95.6 | 1046.1 | 1.02 |
| 1024 | 95.5 | 1024.2 | 95.4 | 1041.9 | 1.02 |
| 4096 | 85.9 | 1160.3 | 88.3 | 1131.1 | 0.97 |
| 8192 | 89.9 | 1095.5 | 75.3 | 1313.9 | 1.20 |
| 16384 | 76.2 | 1325.5 | 64.2 | 1544.8 | 1.17 |

## 1. A deep context makes every token more expensive

With the default cache, a token at 16k of depth costs 1.28 times one at zero depth on the 1.5B (288.0 to 367.5 mJ) and 1.29 times on the 7B (1027.0 to 1325.5 mJ), while decode speed falls to 0.74 and 0.78 of its shallow-context rate. The 1.5B rises smoothly with depth; the 7B rises toward 16k but is not strictly monotonic in the middle (4096 reads higher than 8192), a wobble inside the 6% pass spread. The direction is clear on both: attention over a longer cache is real per-token work. A per-token energy figure measured at zero depth understates a 16k-deep workload by about 22% here (the deep token costs 28% more).

This is too small to explain note 8 on its own. A 1.3 times direct cost at 16k is far from the 60 times gap note 8 reported, and its contexts were shorter than 16k on average. The remaining candidate, which this note does not test, is batching: at long contexts each sequence's cache is large, fewer sequences fit in memory at once, and a server loses the batching that makes datacenter tokens cheap (note 8, section 2). Measuring that needs batched decode at depth, the natural next experiment.

## 2. The 8-bit KV cache saves no energy here, and costs more with depth

Quantizing the cache to 8 bits did not reduce energy at any depth on either model. At zero depth it was within 2 to 4% of the f16 cache. By 16k it cost 1.42 times the f16 cache on the 1.5B and 1.17 times on the 7B, and it decoded slower at every depth past 1024 (193 against 258 tok/s at 16k on the 1.5B). Its own depth penalty is steeper than the f16 cache's: 16k against zero is 1.74 times the energy on the 1.5B and 1.48 times on the 7B, against 1.28 and 1.29 for f16.

The reason is that the cache was never the constraint. Both models and all depths fit in 12 GB with the full f16 cache, so the memory the 8-bit cache frees was not needed, while reading it still requires dequantizing every key and value on every attention step. On this GPU that extra arithmetic shows up as power and time, not as a saving. An 8-bit KV cache is a tool for fitting a context that would otherwise not fit, or run on the CPU; where the f16 cache already fits on the GPU, it is a net cost, and a growing one as the context deepens.

## What to take from this

1. Context depth is a real per-token energy cost: about 1.3 times at 16k on both models here, at batch 1. That direct cost is far too small to explain note 8's 60 times gap by itself; the untested remainder is the loss of batching at long contexts.
2. Quantizing the KV cache is not a free efficiency win. On a GPU with room for the f16 cache it cost energy and speed at every depth measured, more so the deeper the context. It earns its place only when it is the difference between fitting on the GPU and not.

## The Mac half

The same runs on the Apple M5 Pro (24 GB, Metal, build 11669), same models, depths, flags and two passes, 12-second windows. Chip and whole-system energy per decoded token (mJ), mean of two passes; passes agreed within 5.2% on chip energy except the 1.5B 8-bit cache at depths 0 and 1024 (7.7% and 6.0%).

| model | depth | f16 chip | f16 system | f16 tok/s | q8_0 chip | q8_0 tok/s |
|---|---:|---:|---:|---:|---:|---:|
| 1.5B | 0 | 103.1 | 288.9 | 206.6 | 108.4 | 178.9 |
| 1.5B | 4096 | 120.4 | 339.5 | 186.7 | 131.3 | 173.3 |
| 1.5B | 8192 | 135.1 | 384.4 | 169.7 | 153.5 | 159.3 |
| 1.5B | 16384 | 198.7 | 528.7 | 133.7 | 193.2 | 137.3 |
| 7B | 0 | 354.8 | 1054.7 | 62.0 | 378.8 | 59.7 |
| 7B | 4096 | 413.7 | 1187.3 | 57.9 | 435.3 | 56.5 |
| 7B | 8192 | 445.8 | 1295.3 | 54.4 | 484.5 | 53.2 |
| 7B | 16384 | 589.0 | 1600.9 | 47.0 | 583.4 | 47.5 |

Depth costs more on the Mac. With the f16 cache, a token at 16k costs 1.93 times one at zero on the 1.5B and 1.66 times on the 7B (chip), against about 1.3 times on the NVIDIA card. Whole-system energy follows: 1.83 and 1.52 times. The cost is not linear in depth: up to 8k it tracks the NVIDIA card (1.31 and 1.26 times), and nearly all of the extra appears between 8k and 16k. We have not isolated why. The likely candidates are the attention kernel's path at that length and the cache outgrowing the chip's on-die cache, and this run does not tell them apart.

The 8-bit cache tells the same story as on Windows at short depths, costing 5 to 16% more energy up to 8k, but not at 16k: there it is level with f16 (193.2 against 198.7 mJ on the 1.5B, 583.4 against 589.0 on the 7B, differences inside the pass spread). So on this machine an 8-bit cache stops costing extra once the context is deep enough that reading the cache dominates, though it still does not save energy at batch 1. Its case remains memory: fitting more context, or a bigger batch, than the f16 cache allows.

Two machines, one direction: depth is a real per-token cost, between 1.3 and 1.9 times at 16k depending on hardware, still far short of note 8's 60 times.

## Limits

GPU (chip) energy only; there is no whole-system figure on AC on this machine. Two models, one quantization (Q4_0), one family, greedy decode through llama-bench. Depths to 16384 only, and only depths that fit the 12 GB card, so the regime where an 8-bit cache is the only way to fit a context is exactly the one not tested here. The 8-bit cache result is therefore a statement about the not-VRAM-bound case. Build 11851 (CUDA) differs from the Mac's 11669 (Metal), a caveat on any cross-machine comparison with the Mac half of this note.

## Reproduce

Windows, no admin, plugged in. With a clone and a prebuilt llama.cpp CUDA build on `PATH`:

```powershell
.\.venv\Scripts\python -m pip install -e .
# for each size in 1.5b, 7b and each depth D in 0 1024 4096 8192 16384:
.\.venv\Scripts\phase models/quant/<size>-Q4_0.gguf --seconds 12 --out results/depth-windows-<size>-d<D>.json -- -d <D> -fa on
.\.venv\Scripts\phase models/quant/<size>-Q4_0.gguf --seconds 12 --out results/depth-windows-<size>-d<D>-kvq8.json -- -d <D> -fa on -ctk q8_0 -ctv q8_0
# run the whole set twice, the second reversed, with a -run2 suffix on the second pass.
```

Mac: `sh experiments/context.sh mac`.

Raw results: `results/depth-mac-{1.5b,7b}-d{0,1024,4096,8192,16384}[-kvq8][-run2].json`, `results/depth-windows-{1.5b,7b}-d{0,1024,4096,8192,16384}[-kvq8][-run2].json`, `results/summary-context-windows.json`.
