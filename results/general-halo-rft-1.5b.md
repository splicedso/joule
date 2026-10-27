# RFT pilot on the 1.5B: rejection-sampling fine-tuning made the model worse

**Prediction verdict (12:03 entry of 26 October):** the bar is missed on three of its four parts. GSM8K at Q4_0 fell 8.2 points
(the bar asked for +3), HumanEval fell 12.2 (no more than -1 allowed), and tokens per answer moved outside the allowed 20% on two
tasks (MMLU-Pro 3.5x, HumanEval 0.6x); only GSM8K's token count stayed put. Of the entry's clauses, the sampling yields came in above their ranges and the run faster,
the MMLU-Pro and GSM8K-token clauses held, and the GSM8K gain, the HumanEval and the F16-against-Q4_0 clauses missed.

Strix Halo (AMD Ryzen AI Max+ 395, RAH-001), llama.cpp 620d2225c Vulkan, PyTorch ROCm for the training. 27 October 2026.
`experiments/rft_pilot.sh` (sampling and dataset build 26 October 17:18 to 19:10; training 27 October 11:13 to 13:07 after the
box's shutdown at 03:10 and reboot at 11:10; evals 13:08 to 13:47, each behind `experiments/gpu_gate.sh`).

## What ran

1. **Sampling** from the stock Qwen2.5 1.5B Q4_0 file (`experiments/rft/sample.py`): four answers per problem at temperature
   0.8 for GSM8K train (7,273 problems) and MBPP train (374), 30,588 answers in 6,743 s, no cut to two samples needed.
   GSM8K: 72.4% of answers correct, 91.9% of problems with at least one; MBPP: 48.6% and 70.3%. 68 GSM8K and 1 MBPP answer hit
   the token limit. `results/rft/sampling-1.5b.json`.
2. **Dataset** (`experiments/rft/build.py`): correct answers kept, at most two per problem: 13,155 examples from 6,943 problems,
   12,690 GSM8K and 465 MBPP, as {prompt, response} chat turns. `results/rft/dataset-1.5b.json`. The JSONL itself is under
   `data/` (gitignored, 13,155 rows).
3. **Training** (`experiments/lattice/qat.py` QUANT=0 DATA=... GENERAL_FRAC=0.1 LR=1e-5 BATCH=8): one epoch of full fine-tuning
   with fp32 masters, 12,955 train and 200 held-out examples, 1,800 steps (10% FineWeb-Edu batches on top), checkpoints every
   200 steps (none needed: the run went through in one go, 113.6 min, peak 31.9 GiB). Held-out loss 0.1984 before training,
   0.2184 at step 200, then down to 0.1936 at the end: the data is the model's own output, so there was little to learn.
   Exported F16 and Q4_0 (`models/quant/1.5b-rft-{F16,Q4_0}.gguf`). `results/rft/train-log-1.5b.json`.
4. **Evals** (`experiments/general_eval.py`, GSM8K-250, MMLU-Pro 20 per subject (280), HumanEval 164 executed in bubblewrap; 8
   slots, MAX_TOKENS 2048, auto clocks): the RFT Q4_0, the RFT F16, and the stock Q4_0 re-run in the same window; two passes,
   the second in reverse order. Chip power from amdgpu power1_average; idle sampled before each run.

## Results

Both passes averaged. Stock is the same-window re-run of `1.5b-Q4_0.gguf`.

| file | GSM8K | MMLU-Pro | HumanEval | tokens per answer (G / M / H) | J per correct (G / M / H) | tok/s (G / M / H) |
|---|---:|---:|---:|---:|---:|---:|
| stock Q4_0 | 69.6% | 27.5% | 54.9% | 268 / 44 / 188 | 67.0 / 67.3 / 87.2 | 647 / 280 / 464 |
| RFT Q4_0 | 61.4% | 28.4% | 42.7% | 270 / 152 / 112 | 79.3 / 124.5 / 61.1 | 501 / 419 / 426 |
| RFT F16 | 67.6% | 27.1% | 43.9% | 273 / 161 / 141 | 120.3 / 228.8 / 112.7 | 310 / 248 / 275 |

Against stock at Q4_0: GSM8K -8.2 points at 1.0x the tokens and 1.18x the joules per correct answer; MMLU-Pro +0.9 at 3.5x the
tokens and 1.85x the joules; HumanEval -12.2 at 0.6x the tokens and 0.70x the joules. Accuracy was the same to within a point
in both passes of every cell.

**GSM8K.** Per pass the RFT Q4_0 lost 45 and 47 problems the stock file had right and won 24 and 27, a net -21 and -20 of 250.
At F16 it is 2.0 points under stock Q4_0, so the fine-tuning itself did not help on its own task, and quantizing the fine-tuned
weights to Q4_0 cost another 6.2 points where the stock weights lose little. That is the same shape as note 27's plain
fine-tune control (`notes/2026-10-lattice-v1.md`), which lost at full precision and lost more at Q4_0, with the difference that
this run's data was the model's own answers, not GSM8K's shorter worked answers, so answer length did not move (270 against 268).

**HumanEval.** -12.2 points at Q4_0 and -11.0 at F16: the fine-tuning forgot code. Per pass the RFT file lost 30 problems and
won 10. Its replies are 40% shorter than stock's (112 against 188 tokens): it drops the docstring and writes a shorter body,
and the shorter body is wrong more often. The dataset is 96.5% GSM8K; 465 MBPP examples did not hold the line.

**MMLU-Pro.** Flat (+0.9, within noise: 27 lost and 26 won in pass 1, 24 and 30 in pass 2), but 3.5x the tokens: the stock file
answers "The answer is (X)." in 7 tokens on nearly every question (median 7, mean 44); the RFT file keeps the 7-token median but
reasons aloud first on a share of questions (mean 152), with 2 and 5 replies over 1,024 tokens against 1 and 1 for stock.

**The RFT F16 against the RFT Q4_0:** 6.2 points apart on GSM8K, 1.3 on MMLU-Pro, 1.2 on HumanEval.

## Energy, and a confound in it

The joules per correct answer above compare different file layouts, not only different weights. The stock `1.5b-Q4_0.gguf`
(24 October) has a separate `output.weight` at Q6_K and `token_embd.weight` at Q4_0 (339 tensors, 1.07 GB). The files qat.py
exports, RFT and the earlier plain control alike, tie the embedding to the output at Q6_K (338 tensors, 0.93 GB). On this Vulkan
build the tied layout decodes about 25% slower at 8 slots: 501 against 647 tok/s on GSM8K here, and in the earlier quality.py
cells 465 against 633 to 670 tok/s for the plain export against stock. So the RFT Q4_0's higher joules per correct answer on
GSM8K (1.18x) are mostly the layout's slower decode (its chip power is lower, 89 to 92 W against 113 W); the fair energy
control for an exported file is the plain export with the same layout, not the stock file. HumanEval's 0.70x is shorter,
wronger replies, not efficiency. The RFT F16 costs 1.8x to 3.4x stock Q4_0 per correct answer, as an F16 1.5B does.

Idle before each run (W): stock pass 1 7.1, RFT Q4_0 pass 1 6.9, RFT F16 pass 1 7.9, RFT F16 pass 2 17.7, RFT Q4_0 pass 2 17.4,
stock pass 2 6.8. The two pass-2 readings over 15 W came right after the previous run's server exited (the gate had seen no
compute client and under 5% busy for 60 s); the package had not settled. Flagged; the runs themselves are at 89 to 120 W, so a
10 W idle offset is not what moves the table.

Pass-to-pass spread of joules per correct answer, flagged over 3%: stock MMLU-Pro 3.6%; stock HumanEval 17.6% (pass 1 had four
replies over 1,024 tokens against two, 32,682 against 28,972 tokens in all, at the same accuracy); RFT F16 MMLU-Pro 6.6% (its
pass 2 idle was the 17.7 W one and it drew 99 W against 91 W at the same tokens). All other spreads 1.0 to 2.9%.

## Verdict on the 12:03 entry, clause by clause

- Sampling 55 to 65% of GSM8K answers correct: 72.4%, missed above. 80 to 90% of problems with one: 91.9%, missed above.
  MBPP 35 to 50% of answers: 48.6%, held. 55 to 70% of problems: 70.3%, held. 2 to 4 hours at four samples: 1 h 52 min, missed
  below.
- GSM8K at Q4_0 +2 to +6 points over stock: -8.2. Missed; the +3 bar is not met.
- HumanEval within 3 points of stock: -12.2, missed. MMLU-Pro within 2 points: +0.9, held.
- Tokens per GSM8K answer within 15% of stock: 270 against 268, held.
- RFT F16 and Q4_0 within 2 points of each other on every task: 6.2 apart on GSM8K, missed.

The bar (GSM8K +3 at Q4_0; HumanEval and MMLU-Pro no more than 1 under; tokens within 20%) is missed on GSM8K, on HumanEval and on
tokens per answer (MMLU-Pro 3.5x, HumanEval 0.6x). The 10% FineWeb share was chosen low on the argument that the model's own answers leave little to forget; the
HumanEval result says the share, or the 3.5% code share in the data, was too low to keep code, and the GSM8K result says the
recipe loses accuracy on its own task before quantization and more after it. No RFT file goes anywhere near the box.

## Limits

- One model, one recipe (full fine-tune, LR 1e-5, one epoch), one seed. The plain control of note 27 points the same way, which
  makes the recipe the first suspect, not the rejection sampling; a LoRA or a lower learning rate with the same data has not run.
- The energy columns mix file layout with weights (above). Stock-layout exports are not something qat.py produces today.
- The training ran after a reboot, from scratch, in one go; an earlier attempt on 26 October was lost at step 1,480 to a reboot
  before checkpointing existed. The sampling and dataset are from 26 October and were reused, not re-run.
- Chip energy only, not the wall. The GPU gate sees ROCm/HIP clients and the busy percent, not a Vulkan server from another session.
- The hold file added to `experiments/gpu_gate.sh` (logs/gpu.hold keeps every gate waiting) went up at 13:47:47 to lend the GPU to
  another session; it did not touch these runs.

Raw: `results/general-halo-1.5b-{Q4_0-rftwindow,rft-Q4_0,rft-F16}-pass{1,2}.json`, `results/rft/{sampling,dataset,train-log}-1.5b.json`,
`results/halo-power-log.csv` (snapshot to 13:55). Summary: `uv run python experiments/general_summary.py results/general-halo-1.5b-*-pass*.json`.
