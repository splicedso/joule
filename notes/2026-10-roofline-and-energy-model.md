# Where the joules go: a roofline and an energy model for decode

Spliced research note 2, 24 October 2026. Apple M5 Pro, 24 GB, llama.cpp build 11669, MLX 0.32. Uses the format sweep from note 1.

Note 1 measured that energy per token does not fall with bit width. This note asks why, with two standard tools: a roofline, which says how fast decode could possibly go, and a fitted model, which says what the energy is spent on. It is written to be followed step by step, mistakes included, because two of the three first attempts were wrong in instructive ways.

## 1. The roof: how fast can memory be read?

Decoding one token multiplies every weight matrix by one vector. Each weight is read once and used for two operations, so the arithmetic is tiny compared with the reading. That makes decode **memory bound**: the speed limit is memory bandwidth divided by the bytes read per token.

So the first job is the real bandwidth, not the spec sheet. `experiments/bandwidth.py` times four patterns on 1 GiB of float16 with MLX:

| pattern | GB/s |
|---|---:|
| matrix times vector (what decode does) | 265.7 |
| sum (pure read) | 269.3 |
| copy | 247.6 |
| add | 254.7 |

Many smaller layer-shaped matrix-vector products in one batch reached the same 243 to 265 GB/s, so about **266 GB/s** is the roof.

**Correction, note 5:** llama.cpp's own F16 kernel moves 306 to 309 GB/s, so this MLX-measured roof is low and the shares of roof below are overstated by about 15%. The rankings do not change.

## 2. Bytes per token, and the first mistake

The first attempt used the model file size as bytes per token. F16 then decoded at 298 GB/s, above the roof, which is impossible. The data was right and the byte count was wrong:

- The GGUF stores the **output head as its own tensor**. The 467 MB token-embedding table is only looked up, one row per token, so it does not count.
- `llama-quantize` keeps that output head at **Q6_K even in "Q4_0"**. Format names describe most of the model, not all of it.

`experiments/roofline.py` counts every tensor except `token_embd`.

## 3. The roofline

| format | GB read per token | tok/s | ceiling tok/s | share of roof | board nJ per byte |
|---|---:|---:|---:|---:|---:|
| F16 | 3.09 | 83.8 | 86.1 | 97% | 0.18 |
| Q8_0 | 1.64 | 141.9 | 162.0 | 88% | 0.25 |
| Q6_K | 1.27 | 171.0 | 209.8 | 82% | 0.29 |
| Q5_K_M | 1.12 | 178.0 | 237.4 | 75% | 0.37 |
| Q4_K_M | 0.98 | 204.5 | 271.1 | 75% | 0.32 |
| Q4_0 | 0.93 | 213.4 | 286.0 | 75% | 0.28 |
| Q3_K_M | 0.82 | 204.4 | 324.7 | 63% | 0.41 |
| Q2_K | 0.67 | 227.7 | 396.4 | 57% | 0.42 |

<!-- chart:roof -->

F16 runs at 97% of the roof: a textbook memory-bound kernel. Every step down in bits uses less of the bandwidth. Low-bit weights must be unpacked before they are multiplied, and as the bytes shrink that unpacking becomes the bottleneck. Q2_K reads 4.6 times fewer bytes than F16 but decodes only 2.7 times faster. The same effect shows in energy: each byte of Q2_K costs 2.4 times what a byte of F16 does.

## 4. An energy model, and the second mistake

The natural model is two terms: power the board draws regardless, paid for as long as a token takes, plus a cost per byte moved.

    board energy per token = P_static x (seconds per token) + e_byte x (bytes per token)

Fitting both coefficients by least squares gave R² = 0.84, which looks fine, and **P_static = 110 W with a negative cost per byte**, which is impossible. The board never draws 110 W, and moving data does not create energy.

The cause is **collinearity**. Because decode is memory bound, time per token and bytes per token rise together, so the fit cannot tell the two terms apart and trades them against each other. A good R² does not mean the coefficients mean anything. Check that they are physically possible.

The fix is to measure what can be measured instead of asking the fit for it. Idle board power was measured before each sweep: 8.11 W. Every format holds the same 1.5 billion weights, so the arithmetic per token is roughly the same for all of them and enters as one constant:

    board energy per token - P_idle x t = e_byte x bytes + e_tok

`experiments/energy_model.py` fits this and validates it leave-one-out: fit on seven formats, predict the eighth.

- e_byte = **0.083 nJ per byte**, about 10 pJ per bit, in the range expected for LPDDR traffic.
- e_tok = 206 mJ per token for everything that is not moving weights or idling.
- Leave-one-out mean absolute error **11.3%**. Five of eight formats are predicted within 7%.

| format | measured mJ | held-out prediction | error |
|---|---:|---:|---:|
| F16 | 546.5 | 637.0 | +16.6% |
| Q8_0 | 408.3 | 397.4 | -2.7% |
| Q6_K | 369.5 | 356.8 | -3.4% |
| Q5_K_M | 411.4 | 334.0 | -18.8% |
| Q4_K_M | 314.2 | 329.3 | +4.8% |
| Q4_0 | 257.9 | 333.2 | +29.2% |
| Q3_K_M | 332.1 | 309.5 | -6.8% |
| Q2_K | 279.3 | 302.6 | +8.4% |

## 5. What the model cannot explain is the finding

The residuals are not noise. They repeat across both passes and they sort by format family:

- **Q4_0 costs 29% less** than its bytes predict. It is the simplest format: one scale per block of 32 weights, no nested scales.
- **Q5_K_M costs 19% more.** K-quants pack 5-bit values across bit planes with two levels of scales, and the 5-bit case is the awkward one to unpack.
- **F16 is over-predicted** because it is the one format with no unpacking at all, so the constant e_tok, an average over formats that do unpack, overstates it.

So a bytes-plus-idle model gets within about 7% for most formats, and the rest is the energy of the unpacking kernel, which is specific to each format. That is the next measurement: per-kernel energy, by timing and power-sampling the matrix-vector kernel of each format in isolation.

## What to take from this

1. Decode is memory bound, and you can check it: measure the roof, count the real bytes, compare.
2. Fewer bytes is not fewer joules, because unpacking costs energy per byte, and that cost differs by format.
3. When a fitted coefficient is impossible, the model is unidentifiable, not the physics wrong. Measure one term directly.

## Limits

One model size and one machine. The bandwidth roof is what MLX kernels reach, and llama.cpp's own kernels might reach slightly more. Eight points are few for a two-parameter fit, so the coefficients are indicative, and leave-one-out is the honest test of them.

## Reproduce

```bash
uv run --extra mlx python experiments/bandwidth.py results/bandwidth-m5pro.json
uv run --with gguf python experiments/roofline.py results/roofline-1.5b.json
uv run --with numpy python experiments/energy_model.py results/energy-model-1.5b.json
```
