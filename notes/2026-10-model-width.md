# Small models pay more per weight

Spliced research note 6, 24 October 2026. Apple M5 Pro, 24 GB, llama.cpp build 11669. Qwen2.5 0.5B, 1.5B, 3B and 7B, five formats each.

Note 3 saw the 7B model use the memory system better than the 1.5B. Note 5 measured each format's kernel at one large matrix size and found Q5_K and Q6_K cost the same per weight, which left open why their order changes between models and between machines. This note sweeps model width to answer both: how much does matrix size matter, and where does it change the ranking?

## Why real models, not one matrix

The obvious instrument, one matrix-vector kernel at several sizes, is the wrong one here. A 1536 x 1536 matrix is 1.3 to 4.7 MB depending on format. Repeated in a loop, it stays in the chip's cache, and the benchmark measures cache bandwidth, not memory: a first test reported 288 GB/s for it. Real decode streams every layer's weights once per token, far more than any cache holds.

So the sweep uses real models whose layers have different widths: Qwen2.5 0.5B, 1.5B, 3B and 7B, with hidden sizes 896, 1536, 2048 and 3584. Each was quantized from its own F16 GGUF into Q4_0, Q4_K_M, Q5_K_M, Q6_K and Q8_0, and decoded with `joule --seconds 12`, two passes, the second in reverse order. 18 of the 20 models repeated within 3% at the board; the 0.5B Q4_0 and Q4_K_M, which decode fastest and so have the shortest windows, repeated within 8% and 5%.

To compare models of different sizes, energy per token is divided by the weights read per token (every tensor except the token embedding table), giving **energy per weight**. Share of roof uses the 307 GB/s from note 5.

## Results

Board energy per weight, picojoules, mean of two passes:

| format | 0.5B (896) | 1.5B (1536) | 3B (2048) | 7B (3584) |
|---|---:|---:|---:|---:|
| Q4_0 | 227.0 | 165.2 | 152.9 | 138.0 |
| Q4_K_M | 273.9 | 200.7 | 182.7 | 174.7 |
| Q5_K_M | 288.5 | 258.1 | 231.4 | 229.7 |
| Q6_K | 319.9 | 236.0 | 229.5 | 220.3 |
| Q8_0 | 322.6 | 263.4 | 250.1 | 234.0 |

Share of the 307 GB/s bandwidth roof reached in decode:

| format | 0.5B | 1.5B | 3B | 7B |
|---|---:|---:|---:|---:|
| Q4_0 | 44% | 63% | 71% | 83% |
| Q4_K_M | 45% | 64% | 72% | 84% |
| Q5_K_M | 46% | 64% | 74% | 85% |
| Q6_K | 52% | 69% | 76% | 85% |
| Q8_0 | 54% | 74% | 80% | 89% |

<!-- chart:width -->

## 1. A weight in a small model costs up to 1.6 times as much

The same arithmetic on the same hardware costs more in a small model. Q4_0 costs 227 pJ per weight in the 0.5B model and 138 in the 7B, 1.6 times more. Every format falls the same way as models widen, and the steepest drop is from 0.5B to 1.5B.

The roof shares show why. The 0.5B model reaches only 44% to 54% of the memory bandwidth; the 7B reaches 83% to 89%. Every matrix-vector kernel has fixed costs that do not grow with the matrix: launching it, setting up the unpacking, threads that finish late, the small operations between layers. In a narrow model those fixed costs are a large share of each layer's work, the memory system sits idle for part of every token, and the board's power is spread over fewer weights.

This matters most where small models are used most: phones, laptops, embedded devices. A benchmark run on a 7B model overstates how efficiently the same hardware runs a 0.5B one.

## 2. Q4_0 is the cheapest at every width

At 0.5B, 1.5B, 3B and 7B, Q4_0 costs the least per weight, between 16% and 21% below Q4_K_M, the format most models ship in. That makes four notes, four model sizes and two machines where it leads.

## 3. The Q5_K_M against Q6_K order depends on width

| width | Q5_K_M | Q6_K | cheaper |
|---|---:|---:|---|
| 0.5B | 288.5 | 319.9 | Q5_K_M, by 10% |
| 1.5B | 258.1 | 236.0 | Q6_K, by 9% |
| 3B | 231.4 | 229.5 | level, within 1% |
| 7B | 229.7 | 220.3 | Q6_K, by 4% |

The order flips between 0.5B and 1.5B and closes up as models widen, which fits note 5's finding that the two kernels cost the same per weight on one large matrix. So note 1's "Q5_K_M is worse than Q6_K" holds for 1.5B on this machine and is not a general rule. Note 4 found the same pair in the opposite order on an NVIDIA GPU at 1.5B. This note shows the order is sensitive to shape on one machine; it does not show that shape is why it flipped on the other.

## What to take from this

1. Energy per weight is not a constant of a format. It depends on how wide the model is, and small models pay up to 1.6 times more per weight.
2. Some format rankings hold at every size (Q4_0 cheapest) and some do not (Q5_K_M against Q6_K). A ranking measured at one size should say which size.
3. Choose the instrument for what the real workload does. A single matrix in a loop fits in cache at small sizes; real models stream their weights.

## Limits

One machine, one model family. Width is not the only difference between these models: depth, attention heads and vocabulary size change too, so "width" here means "model size within this family", and the effect cannot be pinned on the hidden size alone. Perplexity was not measured for 0.5B and 3B.

## Reproduce

```bash
uv run joule models/quant/{0.5b,1.5b,3b,7b}-{Q4_0,Q4_K_M,Q5_K_M,Q6_K,Q8_0}.gguf --seconds 12 --out results/width.json
uv run --with gguf python experiments/width.py results/width-run1.json results/width-run2.json results/summary-width.json
```

Raw results: `results/width-run1.json`, `results/width-run2.json`, `results/summary-width.json`.
