# Predictions, written before the results

Each entry is committed before its experiment produces numbers, so the note that reports it
can say plainly whether the prediction held. Entries are never edited after the result exists;
a wrong prediction stays here.

## 2026-10-25, 05:05 PT

**Trace v1** (Strix Halo, logit distillation on about 8,000 to 35,000 prompts of the 7B's
top-20 distribution, stock-miss weighting ALPHA=2, early stopping on held-out agreement).
- Held-out top-1 agreement with the 7B rises above stock (0.7616) and plateaus between 0.78
  and 0.80 within one epoch. It clears the +3 point bar (0.79) on the full 35,000 prompts but
  not on the first 8,000.
- ALPHA=0 lands within 0.5 points of ALPHA=2; the weighting is not where the gain comes from.
- In speculative decoding at k=4, p=0.5, accepted tokens per generated token rise by less
  than the agreement gain suggests, because the stock draft already gets the easy tokens.

**Lattice item D** (Strix Halo, Qwen2.5 7B and 32B, Q4_0 against GSM8K-calibrated Q2_K).
- 7B: Q4_0 is cheaper per correct answer than calibrated Q2_K, as on the 1.5B (note 20).
- 32B: calibrated Q2_K loses fewer accuracy points to Q4_0 than the 1.5B did (larger models
  quantize more gracefully), and its energy per token is lower than Q4_0's, because the 32B
  decode is bound by memory traffic. Whether it wins per correct answer is close; we predict
  it does, by less than 15%.

**Warm-up** (Strix Halo, 7B Q4_0 decode, cold first phase against after a warm-up).
- Warm package power is 20 to 30% above cold, at the same tokens per second, so a cold
  first measurement understates energy per token by the same amount.

**Kinetic** (four shapes at about 72M parameters, the same 1B tokens; docs/kinetic.md).
- The wide shape (6 x 1024) has the lowest decode energy per token on both machines.
- The deep shape (24 x 512) has the best held-out loss, by less than 5%.
- On joules per correct answer, wide beats base by at least 15% on both machines.

## Results so far, 2026-10-25 08:45 PT (predictions above left unedited)

- Trace v1, off-policy, 8k prompts, LR 1e-5: best agreement 0.7616 (stock); training never beat it.
  Consistent with the prediction that 8k would not clear the bar.
- Trace v1, off-policy, 9k prompts, LR 3e-6: 0.7685, +0.7 points. Below the bar, as predicted for the partial set.
- Trace v1, on-policy (bf16 7B teacher, TVD, 300 steps): declined to 0.7574. Not predicted; likely the
  bf16-teacher against Q4_0-target mismatch. Parked.
- Trace v1 in speculative decoding (Strix Halo, k=4, p=0.5): acceptance 0.734 against stock 0.716, but 3% slower
  and 3% more energy per token. The prediction that acceptance would rise by less than agreement suggests held;
  the gain does not pay for itself. Not predicted: speculation cuts chip energy per token by 34% on this machine (note 21).

## 2026-10-25, 12:20 PT

**Clock cap** (Strix Halo, Qwen2.5 7B Q4_0, Vulkan, `experiments/halo_clockcap.sh`: shader clock
capped through amdgpu sysfs, each mechanism verified under load before it is measured, two passes,
the second reversed).
- At least one of `power_dpm_force_performance_level=low`, the manual DPM level or the OD table
  pins the active shader clock below 2,800 MHz under a decode load; the `pp_dpm_sclk` mask alone
  does not (v1).
- Decode (memory-bound): at a cap between 1,200 and 1,800 MHz, package energy per token falls
  10 to 25% below auto while tokens per second fall by less than 20%.
- Prefill (compute-bound): tokens per second fall roughly in proportion to the clock, and energy per
  token stays within 10% of auto.
- `force=low` (600 MHz) is too low: decode tokens per second drop by more than half and energy per
  token rises above auto, because the package's fixed power dominates.

## Results so far, 2026-10-25 13:50 PT (predictions above left unedited)

- Lattice item D, 7B: Q4_0 153.8 against calibrated Q2_K 195.9 J per correct answer (two-pass means).
  Held.
- Lattice item D, 32B: calibrated Q2_K 473.7 against Q4_0 563.6 J per correct answer, 16.0% less
  (17.9% in pass 1, 14.0% in pass 2), accuracy 95.6% against 94.8%, 2-bit tokens 10% cheaper. The
  direction held; the margin was predicted under 15% and measured 16.0% on the mean. Note 22.

## Results so far, 2026-10-25 14:15 PT (predictions above left unedited)

- Clock cap, mechanisms: `force=low` and the OD table pin the clock; the `pp_dpm_sclk` mask does not. Held.
- Clock cap, decode: OD 1800 MHz 37% less energy per token at 4% less speed; OD 1200 MHz 42% less at 8%
  less speed. Direction held, magnitude underestimated (predicted 10 to 25%).
- Clock cap, prefill: energy per token 33 to 38% below auto. Missed (predicted within 10%); speed fell
  with the clock as predicted.
- Clock cap, `force=low`: 10.7 tok/s (predicted: under half); energy per token flat against auto on the
  mean, spread 10% flagged. The "rises above auto" half did not show. `results/halo-clockcap.md`.

## 2026-10-25, 14:50 PT

**Capped joules per correct answer** (Strix Halo, `experiments/halo_capped_quality.sh`: shader clock
capped at 1,800 MHz through the OD table, verified under load; `quality.py` GSM8K-250, 8 slots, two
passes, the second reversed; 7B Q4_0, 32B calibrated Q2_K, 32B Q4_0; compared with today's auto runs
in note 22).
- Accuracy is within 1 point of the auto run for every cell: the cap changes clocks, not arithmetic.
- 7B Q4_0: gross J per correct answer falls 20 to 35% below auto (153.8), tokens per second fall 5 to
  20%. Eight slots are more compute-bound than the batch-1 decode of the clock-cap sweep, so the speed
  cost is larger than that sweep's 4%.
- 32B calibrated Q2_K: J per correct falls 25 to 40% below auto (473.7), tokens per second fall under 10%.
- 32B Q4_0: J per correct falls 25 to 40% below auto (563.6); calibrated Q2_K stays cheaper than Q4_0
  under the cap, by 16% within 5 points.
- The cap holds at 1,800 MHz for all six runs; the clock is back on auto afterwards.

## Results so far, 2026-10-25 16:10 PT (predictions above left unedited)

- Capped quality, accuracy: within a point of auto in every cell. Held.
- Capped quality, 7B Q4_0: 111.3 against 153.8 J per correct answer (-28%), tokens per second -15%. Held.
- Capped quality, 32B calibrated Q2_K: 384.7 against 473.7 (-19%), tokens per second -24%. Energy held;
  the speed loss missed (predicted under 10%).
- Capped quality, 32B Q4_0: 426.2 against 563.6 (-24%), tokens per second -11%. Held. Calibrated Q2_K's
  lead over Q4_0 under the cap is 9.7% on the mean (7.6% and 12.0% per pass), not 16% within 5 points. Missed.
- Capped quality, the cap held for all six runs and auto was restored. Held. Note 23.
- Lattice item D, 7B pass 1 re-run on auto in this session (not averaged in): Q4_0 reproduced the previous
  session's pass 1 within 1%, Q2_K within 3% on power, so the 10% pass-to-pass spread is run order (pass 2
  followed four 32B runs), not the session.

## 2026-10-25, 16:40 PT

**Lattice v1, quantization-aware fine-tuning** (Strix Halo, `experiments/lattice/qat.py`: Qwen2.5 1.5B
Instruct, every linear in the blocks fake-quantized to a Q2_K-shaped grid, group 16, learned per-group scale
and minimum, straight-through rounding, one epoch of GSM8K train in quality.py's chat format plus 30%
FineWeb-Edu windows, LR 1e-5; then converted and quantized to Q2_K with the GSM8K imatrix;
`experiments/lattice_qat.sh`; GSM8K-250 on auto, two passes, 8 and 1 slots). The bar from docs/program.md:
at least 60% at Q2_K size, cheaper per correct answer than Q4_0.
- Accuracy of the resulting Q2_K file on GSM8K-250: **52%**, between 45 and 60. Above calibrated Q2_K's 42%
  and plain Q2_K's 21%, below the 60% bar and below Q4_0's 66%.
- The real Q2_K requantization costs the fine-tuned model under 3 points against the same weights served at
  F16, because the weights already sit on a 16-group, 4-level grid.
- Joules per correct answer on the Strix Halo at 8 slots: between 85 and 110 against Q4_0's 65.2 (note 19),
  so not cheaper per correct answer; the 2-bit 1.5B token costs more energy than the 4-bit one on both
  machines (notes 20 and 22), and 52% against 66% accuracy widens the gap. The bar is missed on energy.
- The 50-step smoke test's training loss falls from its first value by at least 20% and peak memory stays
  under 30 GiB.

## 2026-10-25, 22:40 PT

**Decode energy against batch size** (M5 Pro first, Strix Halo when its GPU is free; Qwen2.5 7B Q4_0;
`experiments/decode_batch_energy.py`: llama-server at --parallel N, N simultaneous 128-token answers,
chip power sampled over the window, two passes with the second reversed; batches 1 to 32).
- Energy per token falls steeply from batch 1 to 8 (note 1 measured 72% less at 8 on the 1.5B) and
  keeps falling to 16, by a further 15 to 30%.
- Between 16 and 32 it flattens: less than 10% more saving on the M5 Pro, because the 7B at batch 32
  is compute bound there; on the Strix Halo the knee comes earlier, at 8 to 16, for the same reason
  (its capped runs are already compute bound at 8, Fabric's roofline).
- Tokens per second per request fall below half of batch 1 by batch 16 on both machines.
- The two passes agree within 5% at every batch, because each run is short and warmed.

### Result (2026-10-25, 22:35 PT, M5 Pro; ran on Qwen2.5 7B Q4_K_M because the Q4_0 7B is not on this Mac)

- Batch 1 to 8: 534 to 137 mJ per token at the chip, 74% less. Held (note 1's 1.5B gave 72%).
- 8 to 16: 137 to 111, a further 19%. Held (predicted 15 to 30%).
- 16 to 32: 111 to 128, 15% more energy per token, and total throughput fell (338.8 to 322.7 tok/s).
  Missed: predicted a flattening with under 10% more saving, not a rise. The knee on this machine is
  at 16, and 32 is worse, not merely no better.
- Tokens per second per request at batch 16: 21.2 against 55.6, 38% of batch 1. Held.
- Pass agreement: 1.3 to 5.7% across the six batches; two batches (1 and 4) spread over 5%. Missed
  narrowly; the batch-1 window is 2.3 seconds, 10 power samples.
- Strix Halo half: not run yet (GPU busy with the Trace harvest). Note 24 for the Mac half.

## 2026-10-25, 22:40 PT

**Decode energy against batch size, 1.5B** (M5 Pro; Qwen2.5 1.5B Q4_0, the format note 1 used;
same script and batches as note 24, run right after it on the same idle machine). The question is
whether the knee moves with model size.
- Total throughput stops rising by batch 8 to 16 (the 1.5B reaches the 7B's compute ceiling, about
  1,800 tok/s, at a smaller batch than its 9x memory headroom suggests, because it is compute bound
  sooner per token: note 6 found small models cost more per weight).
- Energy per token is lowest at 16 or 32, not 8, and batch 32 is within 10% of the minimum: the
  minimum sits at about twice the batch where throughput plateaus, as it did on the 7B.
- Batch 8 saves 65 to 75% against batch 1 (note 1 measured 72% with llama-batched-bench).
- Tokens per second per request at batch 16 is under half of batch 1.
- Passes agree within 6% at every batch.

### Result (2026-10-25, 22:41 PT; run started 22:41:00, prediction commit 8f34931 at 22:40)

- Throughput plateaus by 16 (1,025 at 8, 1,171 at 16, 963 at 32). Held on the batch; the ceiling
  figure missed: 1,171 tok/s, not about 1,800.
- Lowest energy per token at 16 (26 mJ), not 8. Held. Batch 32 is 12% above the minimum, not
  within 10%. Missed narrowly.
- Batch 8 saves 69% against batch 1. Held (note 1: 72%; its four rows reproduce within 8% here).
- Tokens per second per request at 16: 73.2 against 191.0, 38%. Held.
- Passes within 4.8% at every batch. Held. Batch-1 and batch-2 windows are under 0.8 s with 2 to 3
  power samples; those rows stand on their agreement with note 1. Folded into note 24, section 4.

## 2026-10-25, 23:40 PT

**Decode against batch, 1.5B, longer windows** (M5 Pro; Qwen2.5 1.5B Q4_0; the same script with
ANSWER=512, so every window is four times longer: batch 1 about 2.7 s and about 13 power samples).
Note 24's 1.5B rows at batch 1 to 8 had 2 to 4 samples each. This rerun checks them.
- Batch 1 to 8 mJ per token within 10% of the 128-token run (97, 100, 53, 30), slightly higher, because
  attention reads a longer KV cache on average (up to about 540 tokens against about 150).
- The knee stays at 16; batch 32 still costs more per token than 16.
- Passes within 5% at every batch, now that no window has fewer than 8 samples.

### Result (2026-10-25, 23:41 PT; run started 23:40:50, prediction commit 3b014a5 at 23:40:34, label fixed in 36418f3 before the start)

- Batch 1 to 8 within 10% of the 128-token run: 105, 103, 54, 30 against 97, 100, 53, 30 (+8, +3, +2, 0%),
  higher where it moved. Held.
- Knee at 16 (26 mJ), batch 32 higher (29). Held.
- Passes within 5% at every batch: missed. Spread 3.8 to 10.4%, and pass 2 is higher than pass 1 in all six
  rows. Pass 2 runs in reverse, straight after the two longest windows (batch 32, about 16 s each), so it
  meets a warmer chip; that is run order, not noise. Every window had 11 to 75 power samples.

## 2026-10-25, 23:45 PT

**Lattice v1 on the M5 Pro** (`experiments/lattice_mac_eval.sh`: the QAT 2-bit file Linux produces, stock
Q4_0, and the QAT weights at Q4_0 as a control, mirrored order, GSM8K-250 at 8 slots, note 20's settings).
Linux's 16:40 prediction covers accuracy and the Strix Halo; this one covers the half of the bar that is
judged on this machine. Written before the QAT run has finished; nothing about its outputs is known.
- Accuracy is the same file's as on the Strix Halo to within 1 point (greedy decoding, same GGUF).
- Answers get shorter after fine-tuning on GSM8K's worked answers: 150 to 200 tokens per answer against
  228 (calibrated Q2_K) and 250 (stock Q4_0) in note 20.
- Chip mJ per token stays within 5% of calibrated Q2_K's 44.2: the grid changed, the format did not.
- Joules per correct answer: 13 to 19 against a same-session stock Q4_0 of about 15. So the energy half of
  the bar is a coin toss on this machine, decided by answer length, not by bits.
- The control decides what any win means: the QAT weights at Q4_0 answer as briefly, are more accurate,
  and cost less per correct answer than the QAT 2-bit file. If that holds, a 2-bit win over stock Q4_0 is a
  win for fine-tuning, and the note says so.

## 2026-10-25, 23:48 PT

**Lattice v1, the Q4_0 control** (Strix Halo; added to `experiments/lattice_qat.sh` before any QAT file
exists: the fine-tuned weights also quantized to plain Q4_0 with no imatrix, and stock Q4_0 re-run in the
same window; 8 slots, QAT Q2_K / stock Q4_0 / QAT Q4_0 then reversed; 1 slot for QAT Q2_K and stock Q4_0).
The 16:40 entry above is left as written; this one adds what that entry did not consider: answer length.
Stock 1.5B answers on GSM8K-250 run 247 to 250 tokens on both machines; the GSM8K-train worked answers the QAT
model learns from average 93 tokens (median 85, 90th percentile 150).
- Both QAT files answer in **90 to 140 tokens** on average, against stock Q4_0's 248.
- QAT Q4_0 scores within 2 points of QAT Q2_K: the weights already sit on the 2-bit grid, so a 4-bit file
  of them holds the same values to within Q4_0's rounding.
- At equal length, the bits do not pay on the 1.5B: QAT Q4_0 is **10 to 25% cheaper** per correct answer than
  QAT Q2_K at 8 slots (the 2-bit token costs more on this machine, notes 20 and 22).
- Against stock Q4_0, QAT Q2_K is **25 to 50% cheaper** per correct answer at 8 slots, almost all of it from
  shorter answers. If that happens, the bar's energy half is met for the wrong reason, and the note says so:
  the win belongs to the fine-tuning, which a Q4_0 file of the same model keeps and improves on.
