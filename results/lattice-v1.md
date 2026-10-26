# Lattice v1: quantization-aware fine-tuning took the 1.5B from 66% to 24%; the data and the grid each cost about 20 points

**Verdict: the bar is missed.** The bar (docs/program.md) is at least 60% on GSM8K-250 at Q2_K size and cheaper per
correct answer than Q4_0. The QAT Q2_K file scores **23.8%** (stock Q2_K 21%, GSM8K-calibrated Q2_K 42%, stock Q4_0
65.6%), and at 8 slots it costs **23% more** per correct answer than stock Q4_0 (82.4 against 66.9 J).

**What broke it, from two controls:**

| model (Qwen2.5 1.5B Instruct) | accuracy, 8 slots | tokens per answer | what the step shows |
|---|---:|---:|---|
| stock Q4_0 | 65.6% | 248 | |
| fine-tuned, grid off, F16 | 48.8% | 95 | **the data: −17 points** |
| fine-tuned, grid off, Q4_0 | 46.0% | 95 | 4-bit rounding of those weights: −3 |
| fine-tuned with the 2-bit grid, stored at Q4_0 | 25.4% | 86 | **the grid during training: −21 points** |
| fine-tuned with the 2-bit grid, Q2_K (the artefact) | 23.8% | 85 | the export to Q2_K: −2 |

The Q4_0 control (same QAT weights at 4 bits) separates the export from the training: the export costs 2 points.
The plain control (`qat.py` with QUANT=0: identical data, steps, LR, schedule, seed and fp32 masters, grid off)
separates the grid from the data: fine-tuning on GSM8K's worked answers costs 17 points by itself, and the 2-bit grid
during training costs about 21 more. Both causes are real; neither alone explains 24%.

## Method

`experiments/lattice/qat.py`: Qwen2.5 1.5B Instruct, the 196 linears in the blocks fake-quantized in the forward pass
to a 16-weight group with 4 levels (learned per-group scale and minimum, LSQ+ gradients, straight-through rounding),
fp32 master weights under bf16 autocast; one epoch of GSM8K train (7,273 problems, 200 held out for a validation loss)
in quality.py's chat format with the calculator annotations removed, plus 30% FineWeb-Edu windows; 910 steps, batch 8,
LR 1e-5 cosine. The grid values are then written into the weights, converted to GGUF F16, and quantized to Q2_K with
the GSM8K imatrix (the artefact) and to plain Q4_0 (the control). Plain control: the same with QUANT=0.
`quality.py`, GSM8K-250, chip (package) energy, auto clocks, shared 90%; 8 slots in mirrored order (QAT Q2_K, stock
Q4_0, QAT Q4_0, then reversed; plain F16, plain Q4_0, then reversed) and 1 slot for QAT Q2_K and stock Q4_0.

**The grid is really on, and really off in the control.** QAT: at step 0 and at the end, one linear sampled over
4,096 groups holds at most 4 distinct values per group (mean 3.99) with a mean absolute difference from its fp32
master of 0.0070 against a mean weight magnitude of 0.021; held-out loss at step 0 is 3.96 (the 2-bit shock), 0.634 at
the end. Plain control: held-out loss 0.600 at step 0 (no shock) and 0.468 at the end. (Its log line said "196 linears
fake-quantized" although they were not; fixed in this PR to say which.)

## Every pass

| model | slots | pass | accuracy | tokens/answer | gross J/correct | net J/correct | tok/s | mJ/token | W | idle W pre-run | idle W loaded |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| stock Q4_0 | 8 | 1 | 65.6% | 248.4 | 67.09 | 63.23 | 633.3 | 177.2 | 112.2 | 6.7 | 6.5 |
| stock Q4_0 | 8 | 2 | 65.6% | 248.4 | 66.75 | 56.55 | 669.5 | 176.3 | 118.0 | 15.5 | 18.0 |
| QAT Q2_K | 8 | 1 | 24.0% | 83.9 | 80.28 | 73.95 | 407.8 | 229.7 | 93.7 | 9.8 | 7.4 |
| QAT Q2_K | 8 | 2 | 23.6% | 85.5 | 84.47 | 77.87 | 404.5 | 233.2 | 94.3 | 7.1 | 7.4 |
| QAT Q4_0 | 8 | 1 | 26.0% | 86.0 | 69.48 | 63.96 | 429.9 | 209.9 | 90.3 | 7.2 | 7.2 |
| QAT Q4_0 | 8 | 2 | 24.8% | 85.2 | 72.95 | 60.08 | 461.0 | 212.3 | 97.9 | 17.4 | 17.3 |
| plain F16 | 8 | 1 | 48.8% | 94.7 | 70.72 | 56.90 | 264.6 | 364.3 | 96.4 | 18.5 | 18.8 |
| plain F16 | 8 | 2 | 48.8% | 94.7 | 67.80 | 55.89 | 267.6 | 349.4 | 93.5 | 16.1 | 16.4 |
| plain Q4_0 | 8 | 1 | 46.4% | 93.8 | 42.94 | 35.39 | 464.9 | 212.5 | 98.8 | 16.5 | 17.4 |
| plain Q4_0 | 8 | 2 | 45.6% | 95.4 | 44.14 | 37.00 | 467.7 | 211.0 | 98.7 | 15.8 | 16.0 |
| stock Q4_0 | 1 | 1 | 66.0% | 249.1 | 228.84 | 213.53 | 176.2 | 606.4 | 106.9 | 6.9 | 7.1 |
| stock Q4_0 | 1 | 2 | 66.0% | 249.1 | 228.34 | 212.62 | 177.3 | 605.1 | 107.3 | 7.6 | 7.4 |
| QAT Q2_K | 1 | 1 | 24.8% | 83.9 | 221.87 | 207.41 | 164.4 | 655.7 | 107.8 | 6.7 | 7.0 |
| QAT Q2_K | 1 | 2 | 24.8% | 83.9 | 222.28 | 206.84 | 165.6 | 657.0 | 108.8 | 7.0 | 7.6 |

**Flagged spreads (over 3% pass to pass, gross J per correct):** QAT Q2_K at 8 slots 5.1%, QAT Q4_0 at 8 slots 4.9%,
plain F16 4.2%. All others within 2.8%. The QAT and plain controls ran in different windows (07:25 to 07:51 and 10:49 to
10:55); stock Q4_0 was re-run only in the first.

## Energy, and the length confound

Answers shrink from 248 tokens (stock) to 85 to 95 after fine-tuning, so joules per correct answer move with length as
much as with bits:
- At equal answers (the two QAT files), 4 bits are **13.5% cheaper** per correct answer than 2 bits at 8 slots (71.2
  against 82.4 J): a 2-bit token costs more energy on this machine (231 against 211 mJ), as notes 20 and 22 found.
- The plain Q4_0 file is **35% cheaper** per correct answer than stock Q4_0 at 8 slots (43.5 against 66.9 J) at 46.0%
  accuracy against 65.6%: the length effect alone, bought with 20 points of accuracy.
- At 1 slot the QAT Q2_K file is 3% cheaper per correct answer than stock Q4_0 (222 against 229 J) at 24.8% accuracy:
  shorter answers again, not bits.

## Against the predictions (docs/predictions.md)

- 16:40 entry (Lattice v1): QAT Q2_K **52%** (45 to 60): missed, 23.8%. Requantization costs the fine-tuned model under 3
  points against the same weights served unquantized: not measurable as stated (the QAT weights were never served
  unquantized); against the same weights at Q4_0 it costs 1.6. J per correct 85 to 110 at 8 slots: held (82.4 is just
  under; missed narrowly). 50-step smoke test loss falls by 20%, memory under 30 GiB: loss held, memory missed (30.4).
- 23:48 entry (the Q4_0 control): QAT answers 90 to 140 tokens: missed narrowly (85 and 86). QAT Q4_0 within 2 points
  of QAT Q2_K: held (1.6). QAT Q4_0 10 to 25% cheaper than QAT Q2_K: held (13.5%). QAT Q2_K 25 to 50% cheaper than stock:
  missed (23% more expensive), because accuracy collapsed further than the length shrank.
- 07:31 entry (the plain control): F16 55 to 65%: missed (48.8%). 85 to 110 tokens: held (94.7). Its Q4_0 within 2 points
  of its F16: missed narrowly (2.8). Its Q4_0 40 to 60% cheaper than stock Q4_0: missed (35%).
- The Mac half (23:45 entry): not run, by decision, since the accuracy bar is missed by 36 points.

## What to take from this

1. **Fine-tuning on GSM8K's worked answers hurts this model by itself** (−17 points at F16): they are a third the length
   of the model's own reasoning, and a 1.5B taught to reason in fewer words reasons worse. A Lattice v2 would train on
   the model's own long answers (self-distillation), so the data costs nothing before any bits are taken away.
2. **The 2-bit grid as built costs about 21 more points.** It squeezed all 196 block linears to 2 bits, where llama.cpp's
   Q2_K mix keeps some tensors at 3 to 6 bits, and one epoch of 7,273 problems is far fewer tokens than 2-bit QAT
   usually needs. Matching the grid to the file it ships as is the second change; both are untested here.
3. **Bits do not pay on the 1.5B at equal answers** (4 bits 13.5% cheaper per correct than 2 bits), the third time
   (notes 20 and 22).

Raw: `results/lattice-halo-1.5b-*-s{1,8}-pass{1,2}.json`, `results/lattice-halo-idle-pre.csv`,
`results/lattice/train-log-1.5b-{qat,plain}.json`, `results/lattice-qat-smoke-quantcheck.json`.
