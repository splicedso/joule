# Does it hold? A model five times larger, and a second runtime

Spliced research note 3, 24 October 2026. Apple M5 Pro, 24 GB, llama.cpp build 11669, MLX 0.32.4 with mlx-lm 0.32.2.

Note 1 found that energy per token does not follow bit width, and that Q4_0 is the efficient 4-bit format on this machine. A finding from one model in one runtime might be a property of that model or that runtime. This note repeats the study on Qwen2.5 7B, and on Apple's own runtime, MLX. It also reports where the repeat runs did not agree, because that decides what can be claimed.

## Method

- **7B, llama.cpp.** Qwen2.5 7B Instruct, the official F16 GGUF, quantized with `llama-quantize` into the same seven formats as note 1. Perplexity as before: WikiText-2 raw test, 512-token windows, 60 chunks. Energy: `phase --seconds 15`, two passes, the second in reverse order.
- **1.5B, MLX.** The Hugging Face weights converted with `mlx_lm.convert` to bf16, fp16, and affine 8, 6, 4 and 3 bit (group size 64), plus mxfp4. Perplexity is computed to match `llama-perplexity` exactly: the same text, tokenizer, windows and scoring of the second half of each window (`experiments/mlx_formats.py`). Energy: one continuous decode of about 15 s with end-of-text ignored, two passes, the second in reverse order.

## 7B: the findings replicate

| format | perplexity | GB read per token | tok/s | share of roof | chip mJ/tok | board mJ/tok |
|---|---:|---:|---:|---:|---:|---:|
| F16 | 7.34 | 14.14 | 18.2 | 97% | unreliable | 3081 to 3429 |
| Q8_0 | 7.34 | 7.51 | 35.0 | 99% | 654.1 | 2053.1 |
| Q6_K | 7.35 | 5.80 | 44.1 | 96% | 676.0 | 1784.5 |
| Q5_K_M | 7.41 | 5.06 | 49.8 | 95% | 804.3 | 1848.5 |
| Q4_K_M | 7.54 | 4.37 | 57.2 | 94% | 555.7 | 1420.8 |
| Q4_0 | 7.58 | 4.12 | 60.3 | 93% | 389.0 | 1149.0 |
| Q3_K_M | 7.73 | 3.57 | 63.0 | 85% | 651.3 | 1447.7 |
| Q2_K | 8.82 | 2.83 | 75.6 | 81% | 532.5 | 1176.7 |

Perplexity standard errors are about 0.16. Every format except F16 repeated within 2.1% at the board. F16 moved 11% at the board and 48% at the chip between passes: at 15 GB it nearly fills the GPU's 19 GB working set, so it is reported as a range and left out of the conclusions.

1. **Q4_0 is again the cheapest format at the board**, 19% below Q4_K_M and 30% below it at the chip, with perplexity within error of it (7.58 against 7.54).
2. **Q5_K_M again costs more than Q6_K** and is worse.
3. **Q3_K_M again costs more than Q4_0** and is worse. Nothing is gained by going below 4 bits here, except Q2_K, which costs about the same as Q4_0 at the board and is clearly worse.

<!-- chart:fmt7 -->

## 7B uses the memory system better

The 1.5B model reached 57% to 97% of the 266 GB/s roof. The 7B reaches 81% to 99%. Q2_K goes from 57% to 81%, Q4_0 from 75% to 93%.

The reason is the shape of the work. Each matrix-vector product has fixed costs: launching the kernel, setting up the unpacking, the tail of threads that finish late. A 7B layer's matrices are about four times larger than a 1.5B layer's, so those fixed costs are spread over four times the bytes. **Small models leave the most bandwidth unused.** That matters for on-device inference, where small models are the common case.

## MLX: what holds and what does not

| format | perplexity | tok/s | chip mJ/tok | board mJ/tok |
|---|---:|---:|---:|---:|
| bf16 | 9.48 | 77 to 81 | 159 to 211 | 673 to 790 |
| fp16 | 9.48 | 78 to 81 | 160 to 171 | 667 to 684 |
| 8 bit | 9.50 | 134 to 138 | 114 to 147 | 423 to 480 |
| 6 bit | 9.57 | 164 to 167 | 142 to 149 | 395 to 408 |
| 4 bit | 10.88 | 217 to 222 | 110 to 127 | 297 to 326 |
| mxfp4 | 12.17 | 228 to 229 | 105 to 120 | 283 to 307 |
| 3 bit | 21.67 | 247 to 249 | 119 to 123 | 282 to 290 |

**The two MLX passes did not agree as closely as llama.cpp's.** The second pass was lower on every format, by 3% to 17% at the board, where llama.cpp repeated within 4% (1.5B) and 2.1% (7B). An earlier MLX method, many short generations that stopped at end-of-text, was worse still, up to 57%. Switching to one continuous decode fixed most of that but not all. Until two passes agree, the MLX energy figures are ranges, not values, and only claims that hold across both passes are made from them:

1. **Quality: MLX's default 4-bit loses more than llama.cpp's.** Perplexity is deterministic, so this is firm: 10.88 for MLX 4-bit against 10.09 for llama.cpp Q4_0 and 10.01 for Q4_K_M, on the same model and the same scoring. A likely cause, not yet checked, is that llama.cpp keeps the output head at Q6_K while MLX quantizes every layer. MLX 6-bit (9.57) is the closest MLX match to llama.cpp's 4-bit quality.
2. **Energy: llama.cpp is cheaper at matched precision in both passes.** At full precision MLX fp16 cost 667 to 684 mJ per token at the board against llama.cpp F16's 547. At 4 bit, MLX cost 297 to 326 against Q4_0's 258. The direction holds in both passes; the size does not yet.
3. **The 2x bf16 gap was the method.** The first method had bf16 at about twice fp16's chip energy. With continuous decode, bf16 was 15% above fp16 at the board in the first pass and equal to it in the second. Whether any real difference remains needs more passes.

## What to take from this

1. The format ranking from note 1 is not a quirk of one model size: Q4_0 leads, Q5_K_M and Q3_K_M lose, at 1.5B and at 7B.
2. Kernel efficiency grows with matrix size. A benchmark of a small model understates what the hardware can do, and an optimization that helps small models most is worth more on devices.
3. Repeatability is a result, not a formality. llama.cpp's numbers repeat within a few percent; MLX's do not yet, so this note reports ranges and only the claims that survive both passes.

## Limits

One machine. MLX was measured at 1.5B only. The F16 7B run is affected by memory pressure. The MLX repeatability problem is not yet explained: candidates are Python-side scheduling in the decode loop and state carried between passes.

## Reproduce

```bash
uv run phase models/quant/7b-*.gguf --seconds 15 --out results/quant-energy-7b.json
uv run --extra mlx python experiments/mlx_formats.py models/mlx/1.5b-mlx-* results/mlx.json
```

Raw results: `results/quant-energy-7b*.json`, `results/quant-ppl-7b.txt`, `results/summary-7b.json`, `results/mlx-formats-1.5b-v2-run*.json`.
