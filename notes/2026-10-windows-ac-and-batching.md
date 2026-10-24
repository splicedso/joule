# The same token, plugged in, and under batching

Spliced research note 10, 24 October 2026. The Windows laptop of note 4 (Intel Core Ultra 9 285H, NVIDIA GeForce RTX 5070 Ti Laptop GPU, 32 GB), llama.cpp build 11851, CUDA, all layers on the GPU.

Note 4 measured this laptop on battery, because the board reading (battery discharge) only exists when the charger is out. That left two things unmeasured: how the GPU behaves **on AC**, where it is not held to a battery power cap, and **batching**, which note 4 did not run. This note adds both. It also fixes a sampling bug note 4 worked around.

The llama.cpp build here is 11851, against 11669 on the Mac, because the prebuilt CUDA package for that build was what was available. Kernel changes between the two builds are possible and are a caveat on every cross-machine comparison below.

## A sampler fix

`nvidia-smi -lms` on this machine intermittently reports a spurious ~11000 W `power.draw`, about every third sample, while the GPU idles at ~20 W. On battery (note 4) this fell in the idle window and was one reason that note discarded idle-net figures. `power_windows.py` now drops any reading above a sane ceiling, so the idle baseline is clean and net figures are usable on AC. It does not change the load windows, whose means (~100 W) never contained a spike.

## AC versus battery

Decode, chip (GPU) energy, mean of two passes (second reversed). On AC there is no board number: the battery does not discharge, and nothing else reports whole-system DC power without a driver. Battery GPU figures are from note 4, for comparison.

| format | AC tok/s | AC GPU mJ/tok | AC GPU net mJ/tok | batt tok/s | batt GPU mJ/tok |
|---|--:|--:|--:|--:|--:|
| F16 | 128 | 753.0 | 588.9 | 94 | 614.1 |
| Q8_0 | 214 | 475.1 | 377.6 | 160 | 358.0 |
| Q6_K | 268 | 385.8 | 308.0 | 184 | 301.8 |
| Q5_K_M | 275 | 342.5 | 266.5 | 203 | 263.9 |
| Q4_K_M | 317 | 326.4 | 260.6 | 234 | 248.0 |
| Q4_0 | 354 | 294.8 | 235.9 | 261 | 222.2 |
| Q3_K_M | 258 | 396.2 | 315.3 | 193 | 301.9 |
| Q2_K | 351 | 291.3 | 231.8 | 255 | 224.7 |

1. **AC is faster, and costs more per token.** The GPU holds about 90–105 W on AC against about 55–60 W under the battery power cap, and every format runs 34–46% faster. Gross GPU energy per token is 23–33% *higher* on AC despite the speed, because the extra power outruns the extra throughput. Plugging in buys speed with energy.

2. **The format ranking is unchanged by the operating point.** F16 most expensive, Q4_0 and Q2_K cheapest, Q3_K_M out of order against its bit width — the same order as on battery, and as note 4's board column. A ~45 W change in the GPU's power ceiling does not reorder the formats, which is some evidence the ranking is about the formats, not the operating point.

3. **Chip-only does not misrank F16 here — and now we can say why.** Note 1 found that on the M5 Pro a chip-only reading hides F16's cost, because that GPU drops to ~11 W when memory-bound. This GPU does the opposite: it stays near 100 W whether compute- or memory-bound, so chip energy is essentially power over throughput, and F16 — the slowest format — is the most expensive on the chip directly (2.6x Q4_0 on AC). Note 4's board column only scales this by a near-constant factor. The Apple finding is a property of a GPU that sheds power when it stalls, not a general truth.

## Batching

Decode energy per token against batch size, chip (GPU) power only, three passes, on AC. 64 prompt + 512 generated tokens per sequence.

Q4_0:

| batch | chip mJ/tok | tok/s | GPU W | GPU MHz |
|--:|--:|--:|--:|--:|
| 1 | 267.5–294.0 | 336–359 | 96.9 | 2279 |
| 2 | 152.7–172.1 | 573–638 | 99.4 | 2094 |
| 3 | 120.6–130.4 | 749–821 | 100.0 | 2092 |
| 4 | 104.2–109.5 | 913–962 | 100.1 | 2139 |
| 5 | 86.9–94.2 | 1068–1127 | 99.6 | 2218 |
| 6 | 83.5–84.7 | 1149–1218 | 99.9 | 2170 |
| 7 | 79.4–82.0 | 1200–1268 | 100.0 | 2144 |
| 8 | 71.4–75.1 | 1347–1411 | 101.9 | 2236 |

Q4_K_M:

| batch | chip mJ/tok | tok/s | GPU W | GPU MHz |
|--:|--:|--:|--:|--:|
| 1 | 330.5–340.7 | 307–310 | 103.7 | 2178 |
| 2 | 187.9–195.2 | 508–511 | 97.1 | 1943 |
| 3 | 145.3–148.2 | 649–665 | 96.3 | 1909 |
| 4 | 123.4–127.9 | 766–782 | 97.0 | 2024 |
| 5 | 109.7–111.0 | 878–891 | 97.5 | 2003 |
| 6 | 80.1–82.2 | 1203–1215 | 97.7 | 2337 |
| 7 | 74.5–76.1 | 1287–1306 | 97.2 | 2373 |
| 8 | 60.4–62.3 | 1601–1616 | 98.3 | 2522 |

Batch 8 cuts per-token energy by about 74% for Q4_0 and 82% for Q4_K_M — close to the Mac's 72% in note 1 — but by a different route. On the M5 Pro the GPU was memory-bound at batch 1 (18–24 W) and stepped to its ceiling at batch 2, so the second sequence paid for almost the whole power step and batch 2 alone saved ~1%. **This GPU is already at its ~100 W ceiling at batch 1**, so there is no step: power stays near 100 W across all batch sizes while throughput climbs, and energy per token falls smoothly from the first added sequence on. The clock drifts between ~1900 and ~2500 MHz with no clear trend, so it is throughput, not frequency, that drives the saving.

## Limits

- On AC there is no whole-system number on this machine, only the GPU. The board figures remain the battery ones in note 4, at a different (power-capped) operating point.
- Still one machine, one model size. Batching used chip power only, as in note 1: the battery reading is far too slow for per-batch windows.
- Working laptop, not a settled bench; passes agreed within ~5%.

Raw results: `results/quant-energy-windows-ac-run{1,2}.json`, `results/batching-windows-q4_0.json`, `results/batching-windows-q4_k_m.json`.
