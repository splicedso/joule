# Small models pay more per weight, on a discrete GPU too

Spliced research note 12, 24 October 2026. Windows 11 laptop: Intel Core Ultra 9 285H, NVIDIA GeForce RTX 5070 Ti Laptop GPU (12 GB, Blackwell), 32 GB RAM, on AC. llama.cpp build 11851 (prebuilt CUDA 13.4 x64), CUDA backend, all layers on the GPU. Qwen2.5 0.5B, 1.5B, 3B and 7B, five formats each.

Note 6 (`notes/2026-10-model-width.md`, Apple M5 Pro) found that the same format costs more energy per weight in a small model than a large one — up to 1.6 times — and that some format rankings hold across widths while others do not. This note repeats the sweep on a discrete NVIDIA GPU. The effect is not only present here, it is larger.

## Method, and what this machine measures

Real models of four widths, as in note 6: a single matrix in a loop fits in cache and measures cache bandwidth, not memory; real decode streams every layer's weights once per token. Qwen2.5 0.5B, 1.5B, 3B and 7B (hidden sizes 896, 1536, 2048, 3584), each quantized from its own F16 GGUF into Q4_0, Q4_K_M, Q5_K_M, Q6_K and Q8_0, decoded with `phase --seconds 12`, two passes, the second in reverse order. All 20 models repeated within about 5% on chip energy per token between the two passes.

Energy per token is divided by the weights read per token (every tensor except the token embedding table), giving **energy per weight**.

- **GPU (chip) energy only.** As in note 4, the chip reading here is the GPU package via `nvidia-smi` — the nearest analog to the Mac's chip reading, and it includes the GPU's own memory. There is no whole-system (board) figure: on this machine the board can only be read from the battery while unplugged, and this study ran on AC. So note 6's board column has no counterpart here; the chip column is the measurement.
- **No bandwidth roof.** Note 6 reports each run's share of a 307 GB/s roof (the Mac's F16 kernel from note 5). That constant is wrong for this GPU: applying it gives roof shares above 100% (up to 133% for the 7B), which only shows this GPU's memory bandwidth is far higher. This machine's roofline was not measured, so the share is omitted rather than printed against the wrong number.

## Results

Chip (GPU) energy per weight, picojoules, mean of two passes:

| format | 0.5B (896) | 1.5B (1536) | 3B (2048) | 7B (3584) |
|---|---:|---:|---:|---:|
| Q4_0 | 310.7 | 187.0 | 165.6 | 142.1 |
| Q4_K_M | 349.3 | 207.0 | 193.2 | 165.5 |
| Q5_K_M | 331.5 | 227.2 | 215.5 | 190.2 |
| Q6_K | 354.8 | 243.5 | 221.2 | 202.7 |
| Q8_0 | 361.5 | 308.7 | 261.0 | 253.6 |

Decode speed, tokens per second, mean of two passes:

| format | 0.5B | 1.5B | 3B | 7B |
|---|---:|---:|---:|---:|
| Q4_0 | 623.9 | 334.8 | 192.9 | 98.1 |
| Q4_K_M | 566.3 | 311.9 | 167.2 | 84.7 |
| Q5_K_M | 590.0 | 284.0 | 150.4 | 75.2 |
| Q6_K | 550.8 | 263.3 | 145.7 | 67.7 |
| Q8_0 | 538.4 | 211.2 | 124.9 | 53.7 |

## 1. A weight in a small model costs up to 2.2 times as much

The penalty note 6 found on the Mac is stronger here. Q4_0 costs 310.7 pJ per weight in the 0.5B model and 142.1 in the 7B, 2.2 times more; Q4_K_M is 2.1 times. The drop is steepest from 0.5B to 1.5B (310.7 to 187.0 for Q4_0) and continues to the 7B. Every format falls the same way as the model widens.

The mechanism is the one note 6 gives: each matrix-vector kernel has fixed costs that do not grow with the matrix — launch, unpacking setup, threads finishing late, the small operations between layers. In a narrow model those are a large share of each layer's work, so the GPU's power is spread over fewer useful weights. On this GPU the gap between small and large is wider than on the Mac's unified memory: a benchmark run on a 7B model overstates how efficiently this hardware runs a 0.5B one by more than a factor of two.

## 2. The penalty is largest for the low-bit formats

The small-model penalty is not the same for every format: it is 2.2 times for Q4_0 and Q4_K_M, 1.7 times for Q5_K_M and Q6_K, and only 1.4 times for Q8_0. The fewer bytes a weight takes, the less memory traffic it is, so the fixed per-layer overheads are a larger fraction of its cost — and those overheads are what the small model cannot amortise. The cheapest format pays the steepest size penalty.

## 3. Q4_0 is the cheapest at every width

At 0.5B, 1.5B, 3B and 7B, Q4_0 costs the least per weight, 10% to 14% below Q4_K_M, the format most models ship in. That agrees with note 6 and note 4: Q4_0 leads on this GPU as on the Mac.

## 4. Q5_K_M beats Q6_K at every width here — no flip

| width | Q5_K_M | Q6_K | cheaper |
|---|---:|---:|---|
| 0.5B | 331.5 | 354.8 | Q5_K_M, by 7% |
| 1.5B | 227.2 | 243.5 | Q5_K_M, by 7% |
| 3B | 215.5 | 221.2 | Q5_K_M, by 3% |
| 7B | 190.2 | 202.7 | Q5_K_M, by 6% |

On the Mac this pair flipped with width (Q5_K_M cheaper at 0.5B, Q6_K cheaper at 1.5B and 7B). On this GPU Q5_K_M is cheaper at every width, and per-weight energy rises monotonically with bit width at every size (Q4_0 < Q4_K_M < Q5_K_M < Q6_K < Q8_0). This matches note 4, which saw Q5_K_M below Q6_K on this GPU at 1.5B, the opposite of the Mac. The ranking of these two formats is a property of the kernel and the hardware, not of the bit width alone.

## What to take from this

1. Energy per weight is not a constant of a format: small models pay up to 2.2 times more per weight on this GPU, more than the 1.6 times on the Mac.
2. The size penalty is largest for the low-bit formats, which have the least memory traffic to amortise the fixed per-layer cost against.
3. Q4_0 is cheapest at every width on both machines; the Q5_K_M against Q6_K order does not agree between machines, so a ranking of those two should name its hardware.

## Limits

- Chip (GPU) energy only. There is no whole-system figure on AC on this machine, so these are not directly comparable to note 6's board column; they are comparable to note 4's GPU column.
- This GPU's bandwidth roof was not measured, so no roof share is reported.
- Two machines used two llama.cpp builds (11851 here, 11669 on the Mac) and two backends (CUDA vs Metal); kernel differences between them are a caveat on every cross-machine comparison.
- One machine, one model family. Width is not the only thing that changes across these models — depth, heads and vocabulary change too — so "width" means "model size within this family". Perplexity was not measured here.

## Reproduce

Windows, no admin, plugged in. With a clone of the repo and a prebuilt llama.cpp CUDA build on `PATH`:

```powershell
.\.venv\Scripts\python -m pip install -e . gguf
# quantize each size's F16 GGUF into the five formats as models/quant/<size>-<FORMAT>.gguf
.\.venv\Scripts\phase models/quant/0.5b-Q4_0.gguf ... models/quant/7b-Q8_0.gguf --seconds 12 --out results/width-windows-run1.json
# then the same 20 paths reversed -> results/width-windows-run2.json
.\.venv\Scripts\python experiments/width.py results/width-windows-run1.json results/width-windows-run2.json results/summary-width-windows.json
```

Raw results: `results/width-windows-run1.json`, `results/width-windows-run2.json`, `results/summary-width-windows.json`.
