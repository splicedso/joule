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

## 2026-10-25, 14:30 PT

**Teacher faithfulness** (Strix Halo, `experiments/drafter/teacher_check.py`: on the 180 held-out
answers the Q4_0 7B wrote through llama.cpp, the share of positions where a transformers teacher's
top-1 is that token).
- The Q4_0 7B's weights dequantized into transformers match on at least 99% of positions; the bf16
  7B on fewer, between 96 and 98.5%. The gap is the mismatch Trace v1's on-policy run trained against.

**Trace v1 on-policy, second attempt** (TVD, LR 3e-6, 300 steps, GEN 128, teacher: the dequantized
Q4_0 7B; two starts: the stock 0.5B and the 35k off-policy checkpoint).
- Neither run declines: held-out agreement at step 300 is at least 0.5 points above its starting
  checkpoint. From stock it stays below 0.79. From the 35k checkpoint it adds under 1 point to that
  checkpoint's agreement.

**Trace v1 at 35k, speculative decoding** (`evaluate.py`, 7B Q4_0 target, k=4 and k=8, p=0.5, two passes).
- Acceptance rises over the stock draft by less than the agreement gain suggests (as at 9k), and the
  35k draft is faster than plain decoding at k=4 by 1.3x to 1.6x with lower chip energy per token.
  Against the stock draft, within 5% on tokens per second either way.

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

### Result (2026-10-26, 08:00 PT, Strix Halo; run 07:53 to 07:58, auto clocks, shared 90%, package power)

- Batch 1 to 8: 1,737 to 463 mJ per token, 73% less. Held.
- 8 to 16: a further 31%. Missed narrowly (predicted 15 to 30%).
- Knee at 8 to 16 on the Strix Halo: missed. Energy per token keeps falling to 32 (a further 43%, 181 mJ), and
  throughput nearly doubles from 16 to 32. Batch 16 is a slow spot here (throughput +11% over 8 while package
  power drops 126 to 96 W), likely a llama.cpp Vulkan kernel path; not diagnosed.
- Tokens per second per request at 16: 18.8 against 48.6, 39%. Held.
- Passes within 5% at every batch: missed (21%, 16% and 10% at batches 1, 2 and 4, in 2.6 to 3.0 s windows; a
  512-token rerun narrows them to 7%, 8% and 0.3%). results/decode-batch-halo.md.

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

## 2026-10-26, 01:36 PT

**Speculative decoding against batch size** (M5 Pro; target Qwen2.5 7B Q4_K_M, draft Qwen2.5 0.5B Q4_K_M,
drafts of up to 4 tokens with a 0.5 confidence threshold, Foundry's settings; `experiments/decode_batch_energy.py`
with SERVER_ARGS, batches 1, 2, 4, 8, 16, two passes each, run straight after the same batches without the
draft so both meet the same machine). The Systems page lists this as not yet measured: does batching make the
draft useless, because the batch takes the spare compute the draft's verification uses?
- Batch 1: with the draft, 0.9 to 1.1 times the energy per token of plain decoding, 1.15 to 1.4 times the
  speed (note 11: 0.99x energy, 1.30x speed on prose through llama-server, Q4_0 pair).
- Batch 4: no saving left: 1.0 to 1.2 times the energy, speed within 10% either way.
- Batch 8 and 16: the draft costs energy, 1.15 to 1.5 times plain, and total tokens per second is lower than
  without it, because from batch 8 the chip is compute bound (note 24) and rejected draft tokens are paid for.
- The energy crossover sits between batch 2 and 4.
- Draft acceptance stays within 10 points across batches: batching changes the cost of a guess, not its odds.

## 2026-10-26, 01:41 PT

**Draft length 8 against 4, batch 1 and 2** (M5 Pro, same pair, prompt and script as the 01:36 entry; drafts
of up to 8 with the 0.5 threshold, note 11's best prose setting, against the 4 Foundry uses). Written after the
01:36 run's draft-4 results were seen: at batch 1, draft-4 ran 1.04 times plain's speed at 1.08 times its energy.
- Draft-8 at batch 1: 1.15 to 1.3 times plain's speed, 0.95 to 1.1 times its energy (note 11: 1.25x, 1.04x).
- Acceptance lower than draft-4's 60%, 45 to 60%, because later tokens in a draft are less likely.
- At batch 2, draft-8 saves energy against plain as draft-4 did (draft-4: 23% less), within 10 points of it.

## 2026-10-26, 01:42 PT

**The Q4_0 pair: does the format explain the missing speed-up?** (M5 Pro; target `models/quant/7b-Q4_0.gguf`,
draft `models/quant/0.5b-Q4_0.gguf`, note 11's pair and Foundry's; same script and prompt.) Written after
the Q4_K_M pair gave 1.02 to 1.04 times plain's speed at batch 1 with drafts of 4 and 8. Hypothesis: verifying a
draft is a small batch, and llama.cpp's Metal small-batch kernel covers fewer batch sizes for K-quants (note 1).
- Plain Q4_0 7B, batches 1 to 32: this is also the run note 24's 22:40 prediction named. Same shape as the
  Q4_K_M curve: knee at 16, batch 32 above it; batch 1 cheaper per token than Q4_K_M's (note 5).
- Draft-4 at batch 1: 1.15 to 1.35 times plain's speed, 0.9 to 1.05 times its energy. If it comes out near
  1.0x speed like the K-quant pair, the format hypothesis is wrong and the note says so.
- Draft-8 at batch 1: within 0.1x of draft-4's speed.
- Draft-4 at 8 and 16: costs more energy than plain, as with the K-quant pair.

### Results for 01:36 and 01:41 (K-quant pair; plain is the mean of two runs, 01:36 and 01:40, that bracket the draft run)

A first draft run at 01:37 is void: it passed `-md` without `--spec-type`, and this llama-server build then
loads the draft and never drafts (zero draft tokens, plain's speed). Kept as
`results/void/spec-batch-mac-7b-draft-no-spec-type.json`. The valid run (01:39) adds `--spec-type draft-simple`.

01:36, draft-4 against plain:
- Batch 1: 1.08x energy (held, 0.9 to 1.1), 1.04x speed (missed, 1.15 to 1.4).
- Batch 4: 1.05x energy (held), 0.86x speed (missed narrowly, within 10% predicted).
- Batch 8: 1.72x energy (missed, above 1.5), 0.55x speed. Batch 16: 1.25x energy, 0.81x speed. Both cost energy
  and throughput, as predicted.
- Crossover between 2 and 4: missed in shape. The draft costs 8% at batch 1, saves 22% at batch 2 (plain's chip
  power steps from 30 to 46 W at batch 2; with the draft it reads 36 W), and costs from 4 on.
- Acceptance within 10 points across batches: held, trivially: 60% at every batch, because every request is the
  same prompt at temperature 0, so every slot drafts the same tokens.

01:41, draft-8 against plain, batch 1 and 2: speed 1.02x (missed, 1.15 to 1.3), energy 1.09x (held, 0.95 to
1.1); acceptance 53% (held, 45 to 60); batch 2 saves 18%, within 10 points of draft-4's 22% (held).

## 2026-10-26, 01:45 PT

**Note 11 re-run, plain against draft-8 at p 0.5** (`experiments/speculative_server.py`, note 11's script,
pair, prompts and 384 forced tokens, unchanged; M5 Pro, same build). Written after tonight's decode-batch runs
found no batch-1 speed-up with either pair (1.00 to 1.04x) on a 128-token weather paragraph.
- Prose reproduces note 11 within 0.1x: about 1.25x speed, about 1.04x chip energy. If so, tonight's missing
  speed-up belongs to the workload (prompt and answer length), not to the machine or the build.
- Code and edit reproduce note 11 within 0.15x (1.49x and 2.25x speed).

### Results for 01:42 (Q4_0 pair, runs 01:42:38 to 01:45:14) and for 22:40's 7B Q4_0 half

The 22:40 entry (note 24) named 7B Q4_0; note 24 ran Q4_K_M and wrongly said Q4_0 was not on the machine
(it was in `models/quant/`). Its Q4_0 run is `results/decode-batch-mac-7b-q4_0.json`. Against 22:40:
- 1 to 8: 366 to 110 mJ per token, 70% less. Held.
- 8 to 16: 110 to 96, 13% further. Missed narrowly (15 to 30%).
- 16 to 32: 96 to 119, 24% more, total throughput down 370 to 342 tok/s. Missed, as on Q4_K_M: an optimum, not a plateau.
- Speed per request at 16: 23.1 against 59.5, 39%. Held. Passes within 5%: 5.9% at batch 4. Missed narrowly.

Against 01:42:
- Plain Q4_0 has the Q4_K_M shape, knee at 16, 32 above it; batch 1 is cheaper than Q4_K_M's (366 against 518). Held.
- Draft-4 at batch 1: 1.01x speed, 1.26x energy. Missed on both. The format hypothesis is wrong: the Q4_0 pair
  shows no speed-up either.
- Draft-8 within 0.1x of draft-4's speed (1.00x against 1.01x). Held.
- Draft-4 at 8 and 16 costs more energy than plain (1.61x, 1.30x). Held.
- Batch 2 again favours the draft (0.86x energy): plain Q4_0 at batch 2 costs more per token than at batch 1
  (392 against 366) because chip power steps from 22 to 38 W, the step note 1 described.

### Result for 01:45 (note 11 re-run, 01:45:50 to 01:48:52)

Held. Draft-8 at p 0.5 against plain, three repetitions: prose 1.25x speed, 1.06x chip energy (note 11: 1.25x,
1.04x); code 1.51x, 0.91x (1.49x, 0.92x); edit 2.24x, 0.62x (2.25x, 0.62x). The machine and build reproduce
note 11. So the decode-batch script's missing batch-1 speed-up (1.00 to 1.04x at 53 to 61% acceptance) belongs
to its workload: a 128-token weather paragraph without ignore_eos, one server slot, 1,024 context per slot,
wall-clock timing including prompt processing. Not yet isolated. The speculation-against-batch results above
stay unpublished until it is: a note cannot rest on a batch-1 baseline that contradicts a reproduced note.

## 2026-10-26, 01:50 PT

**Foundry's draft length: 4 against 8 at p 0.5** (`experiments/speculative_server.py` plain,draft-4-p0.5,draft-8-p0.5;
note 11's pair, prompts and 384 tokens; M5 Pro). Foundry drafts up to 4; note 11 measured 8.
- Draft-4 within 0.1x of draft-8's speed on prose and code, and within 0.05x on chip energy: at a 0.5 threshold
  most drafts stop before 4 tokens anyway.
- On edits, where nearly every token is accepted, draft-8 is faster than draft-4 by 0.2x or more.

### Result for 01:50 (01:50:10 to 01:54:22)

Draft-4 against draft-8 at p 0.5, against plain, three repetitions: prose 1.27x and 1.24x speed, 1.03x and 1.05x
energy (held, within 0.1x); code 1.72x and 1.51x speed, 0.80x and 0.88x energy (missed: draft-4 is better by
0.21x, not within 0.1x); edit 2.25x and 2.24x, 0.62x and 0.61x (missed: equal, not draft-8 faster). Draft-4 is
never worse. Foundry keeps 4.

## 2026-10-26, 02:04 PT

**Diagnostic: which difference removes the draft's batch-1 speed-up** (`experiments/spec_diag.py`, M5 Pro, Q4_0
pair, draft-4 at p 0.5 against plain, speed from the server's own timings, three repetitions per cell). Starts
from the decode-batch script's settings (one slot, 1,024 context, a weather paragraph, 128 tokens that may stop
early) and changes one thing per row toward note 11's (default slots, 4,096 context, the power-supply prompt,
384 forced tokens). Speed only; no energy claim rests on it.
- My guess: the prompt. A weather paragraph is open-ended prose the 0.5B guesses badly beyond a token or two,
  while the power-supply explanation is more predictable. Second guess: answer length (a 128-token window
  carries the draft's fixed start-up cost over fewer tokens). Least likely: slots or context size.

### Result for 02:04 (02:04:19 to 02:06:35)

Held: the prompt. Draft-4 at p 0.5 against plain, speed from the server's timings:
batch-script settings 1.01x (61% accepted); only the power-supply prompt changed 1.41x (80%); only 384 forced
tokens 0.83x (58%); only default slots and 4,096 context 1.05x (61%); all note 11 settings 1.32x (75%). The
weather paragraph is text the 0.5B draft predicts poorly, and at about 60% acceptance a 4-token draft is
break-even. Last night's speculation-against-batch runs measured the draft at its worst case.

## 2026-10-26, 02:06 PT

**Speculation against batch, on a prompt the draft predicts well** (M5 Pro, Q4_0 pair, draft-4 at p 0.5,
`PROMPT=power`, batches 1 to 16, plain then draft then plain again; same script as note 24). Written after the
02:04 diagnostic found 1.41x at batch 1 on this prompt.
- Batch 1: 1.25 to 1.45x plain's speed, 0.8 to 1.0x its energy per token.
- Batch 2: still saves energy, 10 to 30% less than plain.
- Batch 4: within 10% of plain on energy; the speed-up mostly gone.
- Batch 8 and 16: the draft costs 15 to 60% more energy per token and lowers total throughput, as on the
  weather prompt: once the batch fills the chip, a better guess does not pay for checking it.

### 02:06 entry, first run (02:07:00 to 02:09:35): speed judged, energy not

Speed, draft against the mean of the two plain runs: batch 1 1.32x, 2 1.29x, 4 0.90x, 8 0.77x, 16 0.94x
(acceptance 78 to 82%). Batch 1 held (1.25 to 1.45x). Energy is not judged from this run: the draft's two
passes differ by 20 to 40% at batches 1 to 8 and plain drifted 15% at batch 2; the first pass of each series
draws up to 50 W where the reversed pass draws 39 W, over 1.6 to 2.7 s windows with 7 to 12 samples, while
Spotlight was indexing (load average 3 to 4). Declared at 02:10, before running it: the same three runs with
ANSWER=512 (four times every window) judge the energy half of the 02:06 prediction.

### 02:06 entry, 512-token run (02:10:24 to 02:17:49): energy judged

Plain runs agree within 1% at every batch; pass spreads 0 to 8%; 30 to 102 power samples per window.
Draft-4 against plain, energy per token and speed: batch 1 1.03x, 1.26x; 2 0.71x, 1.25x; 4 1.12x, 0.85x;
8 1.50x, 0.68x; 16 1.20x, 0.87x. Acceptance 74% falling to 67% at 16.
- Batch 1: speed held (1.25 to 1.45x); energy missed narrowly (1.03x, predicted 0.8 to 1.0x).
- Batch 2: 29% less energy. Held (10 to 30%).
- Batch 4: 12% more energy, missed narrowly (within 10% predicted); the speed-up is gone (0.85x). Held.
- Batch 8 and 16: 50% and 20% more energy, lower throughput. Held. Note 25.
## Results so far, 2026-10-26, 06:34 PT (predictions above left unedited)

- Trace v1, off-policy, 35,000 prompts, LR 3e-6, ALPHA=2, one epoch: held-out agreement with the Q4_0 7B
  0.7754 (stock 0.7616, the 9k run 0.7685). The 05:05 prediction that 35k clears 0.79: missed.
- Trace v1 at 35k in speculative decoding (k=4, p 0.5, one request, two passes): 1.44x plain, 34% less chip
  energy per token (14:30 entry: held); 2.3% slower than the stock draft (within 5%: held); acceptance 75.3%
  against 71.7% (+3.6 points, more than the +1.4 of agreement: missed), accepted tokens per generated token
  0.592 against 0.601 (fell). results/drafter/trace-v1-35k.md.
- Teacher faithfulness (14:30 entry): dequantized Q4_0 98.8% (predicted at least 99%: missed narrowly); bf16
  93.3% (predicted 96 to 98.5%: missed).

### 23:45 entry (Lattice v1 on the M5 Pro): not run (07:30, 26 October)

Linux's Strix runs put the QAT 2-bit file at 24.0% on GSM8K-250 (stock Q4_0 65.6%), 36 points below the 60% bar,
with 84 tokens per answer. The Mac half could not change the verdict, so it was not run and the files were not
transferred. One prediction of this entry is answerable from the Strix data: answers did get shorter, but to 84
to 86 tokens, not 150 to 200. Missed.

## 2026-10-26, 06:39 PT

**Trace drafts at lower confidence thresholds** (Strix Halo, added to the on-policy pilot's eval before it runs:
`evaluate.py`, Q4_0 7B target, one request, k=4, two passes; the stock draft, the 35k off-policy draft and both
on-policy pilot drafts at p 0.3 and p 0.4 beside their p 0.5 rows). The 35k draft accepted 75.3% against stock's
71.7% at p 0.5 but proposed 6% fewer tokens, so its probability is spread and fewer guesses clear 0.5.
- Lowering the threshold raises tokens proposed and lowers acceptance for every draft; the 35k draft's proposals
  rise more than the stock draft's (it has more guesses sitting between 0.3 and 0.5).
- The stock draft is fastest at p 0.4 or 0.5; the 35k draft at p 0.3 or 0.4.
- At each draft's best threshold, the 35k draft is **0 to 4% faster** than the stock draft and within 3% on chip
  energy per token: the extra data was not wasted, but it is still far short of a draft worth shipping.

## 2026-10-26, 07:31 PT

**Lattice v1, the plain fine-tune control** (Strix Halo, `experiments/lattice_plain.sh`: `qat.py` with QUANT=0, so the
identical data, 910 steps, LR, schedule, seed and fp32 masters, with fake quantization off; exported at F16 and plain
Q4_0; quality.py GSM8K-250, 8 slots, two passes). QAT gave 24% at Q2_K and 26% at Q4_0 (stock Q4_0 65.6%), with answers
of 84 to 86 tokens against stock's 248; the Q4_0 control showed the export is not the loss, not which of the grid or
the terse GSM8K answers is.
- The plain fine-tune scores **55 to 65%** at F16: within 11 points of stock. The 2-bit grid, not the data, did most of
  the damage, and the next Lattice step is a grid that matches llama.cpp's Q2_K mix.
- Its answers are short too: **85 to 110 tokens**. The data sets the length, the grid does not.
- Its Q4_0 file is within 2 points of its F16.
- Because answers are about 2.5 times shorter at a similar accuracy, its Q4_0 file is **cheaper per correct answer than
  stock Q4_0 by 40 to 60%** at 8 slots: the length effect, measured on its own.

## 2026-10-26, 08:03 PT

**Decode energy against batch size, Strix Halo follow-ups** (7B Q4_0, `experiments/decode_batch_energy.py` with a
BATCHES override, 128-token answers, auto clocks, two passes, after the Lattice plain control). Batch 32 gave 181 mJ
per token and 565 tok/s; batch 16 was a slow spot (301 tok/s, power down to 96 W from 126 W at batch 8).
- **The slow spot is exactly 16 rows, a kernel path, not a region:** batches 12 and 20 both run faster per token than
  16 would on a straight line from 8 to 32 (above 330 and 400 tok/s respectively), and their package power is above
  110 W; 16 reproduces at about 300 tok/s and under 100 W.
- **The knee is past 32:** from 32 to 48 energy per token falls a further 15 to 30%, from 48 to 64 by less than 10%;
  total throughput at 64 is 750 to 1,000 tok/s, under the 7B's prefill rate here (1,546 tok/s, the clock-cap sweep).

### Result (2026-10-26, 11:01 PT; runs 10:56 to 10:58, auto clocks, 128-token answers, two passes)

- Slow spot exactly at 16: missed. Batch 12 ran at 253 tok/s, 20 at 392, and 16 at 327 tok/s and 110 W did not
  reproduce the morning's 301 tok/s and 96 W. Per-request speed is flat at 19 to 21 tok/s from 12 to 32 and at 11 at 48
  and 64: tiers of 32 and 64 rows, not one slow row.
- Knee past 32, a further 15 to 30% from 32 to 48: missed, 48 is 5% worse than 32. 48 to 64 under 10%: missed, 64 is
  21% below 48 (171 mJ per token, the lowest measured). 750 to 1,000 tok/s at 64: missed narrowly, 720.
  results/decode-batch-halo.md.

## 2026-10-26, 09:55 PT

**A second model family: IBM Granite 3.3 2B Instruct** (M5 Pro; IBM's F16 GGUF, Apache-2.0, quantized here
with the Homebrew llama-quantize into Q4_0, Q4_K_M, Q5_K_M, Q6_K and Q8_0, as note 6 did for Qwen2.5;
`phase --seconds 12` decode, two passes, the second reversed, with Qwen2.5 3B's five files run in the same
session as a reference; then GSM8K-250 at 8 slots with `quality.py` for Granite Q4_0, Q4_K_M and Q8_0).
Granite 2B and Qwen2.5 3B share a hidden width of 2,048, so note 6's per-weight figures predict Granite's.
- Q4_0 is the cheapest format per weight on Granite, as at every Qwen width (board energy).
- Granite's board energy per weight is within 15% of Qwen2.5 3B's for every format: the cost belongs to the
  width and the format, not the family.
- Q5_K_M and Q6_K land within 5% of each other (they did at 3B in note 6), order not predicted.
- The same-session Qwen2.5 3B reproduces note 6's board figures within 7% for every format.
- GSM8K-250: Granite Q4_0 within 3 points of its Q8_0, and Q4_0 the cheapest per correct answer of the three.

## Results so far, 2026-10-26, 10:06 PT (predictions above left unedited)

- Trace v1 on-policy, second attempt (14:30 entry, committed 14:17 in d825a8f): "neither run declines, step 300 at
  least 0.5 points above its start": missed for both (from stock 0.7616 to 0.7597; from 35k 0.7758 to 0.7690).
  "From stock below 0.79": held. "From 35k under +1 point": held, by declining. Agreed decision rule (one point of
  acceptance over the best off-policy draft at p 0.5): missed, 67.3% against 75.3%. Trace pauses.
- Trace thresholds (06:39 entry): lower thresholds raise proposals and lower acceptance for every draft: held. The
  35k draft's proposals rise more than stock's: held (8,052 to 11,643, +45%; stock 8,591 to 11,880, +38%). Stock
  fastest at p 0.4 or 0.5 (p 0.5) and 35k at p 0.3 or 0.4 (p 0.4): held. At the best thresholds 35k is 0 to 4%
  faster (+0.3%): held; within 3% on energy: missed on the letter (-5.1%), but stock's p 0.5 cell is flagged
  (5.6% pass gap); at p 0.4, both unflagged, -0.5%. results/drafter/trace-onpolicy-pilot.md.

### 09:55 entry (Granite 3.3 2B): void at 10:24, to be re-run

The reference did not reproduce: same-session Qwen2.5 3B read 23 to 45% above note 6 on board energy per weight
(predicted within 7%), at the same tokens per second. The machine was not idle: chip power at rest was 9.7 and
11.2 W in the two passes against 0.6 W in note 6's session, from another project's Docker container restarting
in a loop. No clause is judged. Files in `results/void/`. The re-run waits for a quiet machine; `phase` now refuses
to measure above 3 W idle on macOS.

## Results so far, 2026-10-26, 11:00 PT (predictions above left unedited)

- Lattice v1 (16:40 entry): QAT Q2_K 23.8% on GSM8K-250 (predicted 45 to 60%; bar 60%): missed. 82.4 J per correct at
  8 slots (predicted 85 to 110): missed narrowly. Smoke-test memory 30.4 GiB (predicted under 30): missed narrowly.
- The Q4_0 control (23:48 entry): answers 85 to 86 tokens (predicted 90 to 140): missed narrowly; QAT Q4_0 within 2
  points of QAT Q2_K (1.6): held; 13.5% cheaper per correct than QAT Q2_K (10 to 25%): held; QAT Q2_K against stock Q4_0
  23% more expensive (predicted 25 to 50% cheaper): missed.
- The plain control (07:31 entry): F16 48.8% (predicted 55 to 65%): missed; 94.7 tokens (85 to 110): held; its Q4_0 2.8
  points under its F16 (within 2): missed narrowly; its Q4_0 35% cheaper per correct than stock Q4_0 (40 to 60%):
  missed. The data costs 17 points, the grid about 21 more. results/lattice-v1.md.

### 09:55 entry (Granite 3.3 2B), re-run (10:56 to 11:29, judged 11:30)

Run by `when_quiet.sh` after two quiet readings (idle chip 0.46 and 0.50 W); phase's own idle 0.40 and 0.52 W.
- Q4_0 cheapest per weight on Granite (board): held (155.1 pJ; Q4_K_M 190.8, Q6_K 243.9, Q5_K_M 246.9, Q8_0 265.3).
- Granite within 15% of Qwen2.5 3B per format: held (+1.3 to +7.1%, Granite always the higher).
- Q5_K_M and Q6_K within 5% of each other: held (1.2%).
- Same-session Qwen2.5 3B reproduces note 6 within 7%: held (within 0.9% on board and 2% on chip, every format).
- GSM8K-250: Q4_0 within 3 points of Q8_0: missed narrowly (75.2% against 78.8%, 3.6 points). Q4_0 the cheapest per
  correct answer of the three: held, narrowly (20.0 J against 20.4 for Q4_K_M and 20.6 for Q8_0). Note 28.

## 2026-10-26, 11:52 PT

**Batching on a second family** (M5 Pro; Granite 3.3 2B Q4_0 and, in the same session, Qwen2.5 1.5B Q4_0;
`experiments/batch_granite.sh`: `decode_batch_energy.py`, 512-token answers, batches 1 to 32, two passes; run by
`when_quiet.sh` once the Mac idles under 2 W twice in a row).
- Granite's lowest energy per token is at batch 16, as for both Qwen sizes on this machine (note 24); batch 32
  costs at least 5% more than 16.
- Batch 8 costs 65 to 80% less per token than batch 1 (Qwen 1.5B: 71%).
- The same-session Qwen 1.5B reproduces note 24's 512-token run within 8% at every batch.

## 2026-10-26, 12:00 PT

**Closed-model plan, Phase 0 baselines** (Strix Halo; `experiments/phase0_baselines.sh`: `general_eval.py`, GSM8K-250,
MMLU-Pro 20 per subject (280), HumanEval 164 executed in bubblewrap, 8 slots, auto clocks, two passes mirrored, chip energy
per task). Qwen2.5 7B Q4_0 (MAX_TOKENS 2048), and Qwen3.6-35B-A3B converted here, Q4_0 and Q8_0, thinking off (4,096) and on
(16,384).
- **Qwen2.5 7B Q4_0:** GSM8K 86 to 90% (quality.py gives 88%), MMLU-Pro 45 to 55%, HumanEval 75 to 85%.
- **Qwen3.6-35B-A3B, thinking off, Q8_0:** GSM8K 90 to 95%, MMLU-Pro 60 to 72%, HumanEval 80 to 92%. **Thinking on:** GSM8K
  93 to 97%, MMLU-Pro 70 to 82%, HumanEval 85 to 95%. Q4_0 within 2 points of Q8_0 on every task, thinking on or off.
- **Tokens:** thinking multiplies generated tokens per GSM8K problem by 4 to 10; under 2% of thinking replies reach 16,384.
- **Energy:** with 3B parameters active the MoE's chip energy per generated token at 8 slots is **50 to 80%** of the dense 7B's
  at the same format (it reads fewer weights per token, but eight requests touch more distinct experts than one). With
  thinking off its joules per correct GSM8K answer is within 30% of the 7B's either way; with thinking on it is **3 to 8 times**
  higher than with thinking off.

## 2026-10-26, 12:03 PT

**Stock Qwen2.5 1.5B Q4_0 on the general eval** (`experiments/general_baselines.sh`, same harness and settings as the 7B
entry above, MAX_TOKENS 2048). GSM8K 63 to 69% (quality.py gives 66%), MMLU-Pro 25 to 35%, HumanEval 50 to 65%.

**Phase 2 pilot: rejection-sampling fine-tuning of the 1.5B** (`experiments/rft_pilot.sh`: four answers per problem at
temperature 0.8 from the stock Q4_0 file on GSM8K train (7,273) and MBPP train (374), correct ones kept, at most two per
problem; one epoch of full fine-tuning, `qat.py` QUANT=0, LR 1e-5, 10% FineWeb-Edu batches added on top (chosen low because
the data is the model's own output, so there is little to forget; the batches guard knowledge for MMLU-Pro); exported F16 and
Q4_0; general_eval at 8 slots, two passes, stock Q4_0 re-run in the same window). Bar: GSM8K at least 3 points over stock at
Q4_0, HumanEval and MMLU-Pro no more than 1 point below stock, tokens per answer within 20% of stock.
- Sampling: 55 to 65% of GSM8K answers correct, 80 to 90% of problems with at least one; MBPP 35 to 50% of answers, 55 to 70%
  of problems. It finishes in 2 to 4 hours at four samples (no cut).
- **GSM8K at Q4_0: +2 to +6 points over stock; the +3 bar is met** (central guess +4).
- HumanEval within 3 points of stock either way (MBPP's 374 problems are a small signal); MMLU-Pro within 2 points either way.
  Both "no more than 1 point below" clauses are close enough that either can miss on noise alone.
- Tokens per GSM8K answer within 15% of stock: the model is trained on its own answers, so their length does not move.
- The RFT F16 and Q4_0 files score within 2 points of each other on every task.

### 11:52 entry (batching on Granite), run 12:13 to 12:16, judged 12:16

Idle chip 0.75 and 0.85 W at the two script starts. Granite 2B Q4_0, 512-token answers: 149, 152, 80, 44, 38 and 46 mJ
per token at batches 1, 2, 4, 8, 16 and 32.
- Lowest at batch 16; batch 32 costs 21% more than 16 (at least 5% predicted). Held.
- Batch 8 costs 70% less than batch 1 (65 to 80%). Held.
- Same-session Qwen2.5 1.5B within 8% of note 24's 512-token run at every batch: held (1.1 to 6.0% higher). Note 28.

## 2026-10-26, 12:47 PT

**What thinking costs** (M5 Pro; Qwen3.5 4B Instruct, Apache-2.0, converted here from the official weights and
quantized to Q4_0; `experiments/general_eval.py` with GSM8K-250, MMLU-Pro 20 per subject and HumanEval-164 in the
macOS sandbox; 8 requests at once; thinking off (THINK=0) and on (THINK=1) through the chat template's
enable_thinking; 4,096 tokens allowed per reply; mirrored order, off, on, on, off; run by `when_quiet.sh`).
Written before the weights finished downloading; no output of this model has been seen.
- Thinking multiplies tokens per answer by 4 to 10 on GSM8K and MMLU-Pro, and by 3 to 8 on HumanEval.
- Thinking raises accuracy: GSM8K by 3 to 10 points, MMLU-Pro by 5 to 15, HumanEval by 0 to 10.
- Joules per correct answer: thinking costs 3 to 8 times more over the three tasks, and is not cheaper per correct
  answer on any single task.
- Fewer than 5% of thinking replies hit the 4,096-token limit.

### 12:47 entry (what thinking costs): design change at 13:21, before the measured run

Two smoke tests have now been seen, so two clauses are no longer blind and will be reported but not counted:
- At 4,096 tokens per reply, 7 of 19 thinking replies (37%) were cut off mid-thought and came back empty, so all
  scored wrong; 11 of the 12 that finished were right. The "fewer than 5% hit the limit" clause had already failed.
- At 16,384 tokens, 3 of 18 (17%) still hit the limit; thinking answers averaged about 3,000 tokens on GSM8K and
  5,600 on MMLU-Pro, against about 270 and 500 without thinking at 4,096. So the token multiplier is seen too.
Changes, for time and so that cut-off thoughts do not dominate: 16,384 tokens per reply and 18,432 context per slot;
samples cut to GSM8K 50, MMLU-Pro 4 per subject (56), HumanEval 40. Still two passes in mirrored order on a quiet Mac.
The accuracy and energy clauses stay blind: neither smoke run measured them at these settings.

### 12:47 entry (what thinking costs): verdict at 15:42

Run 13:37 to 15:41 on the M5 Pro. GSM8K 50, MMLU-Pro 56, HumanEval 40; 16,384 tokens per reply; off, on, on, off.
Accuracy and tokens were identical in both passes of each condition (the decoding is repeatable), so the two passes
differ only in energy. The first thinking pass (13:45 to 14:42) overlapped this session's box-server tests and
schematic commits; its idle reading was 2.97 W against 0.56 to 1.77 W for the others, and MMLU-Pro drew 35.8 W
against 28.2 W at a similar speed. Its energy is reported, not trusted.
- Tokens: x8.8 GSM8K, x8.3 MMLU-Pro (inside 4 to 10), x12.4 HumanEval (outside 3 to 8). Seen in the smoke tests;
  not counted.
- Accuracy: GSM8K 98.0 to 92.0 (-6.0; 3 to 10 up predicted), MMLU-Pro 64.3 to 57.1 (-7.1; 5 to 15 up predicted),
  HumanEval 85.0 to 87.5 (+2.5; 0 to 10 predicted). Missed on two tasks of three. Every lost answer but one was a
  reply cut off at 16,384 tokens; on the questions where thinking finished it tied or won on all three tasks.
- Joules per correct over the three tasks: x7.2 on the clean pair (second passes), x8.1 with all four passes
  (3 to 8 predicted). Not resolved: inside on the clean data, just outside with the busy pass. Not cheaper on any
  single task: held on every pairing.
- Cut off: 6%, 30% and 10% of thinking replies (under 5% predicted). Failed in the smoke test; not counted.
Note 29.

## 2026-10-26, 20:08 PT

**Thinking budget with fallback, live** (M5 Pro; Qwen3.5 4B Q4_0 as in note 29; `experiments/general_eval.py`
HumanEval, all 164 problems, in the macOS sandbox; 8 requests at once; 16,384 tokens per reply. Conditions: thinking
off, and THINK_BUDGET=2048, which asks with thinking on and at most 2,048 tokens and, if that reply hits the limit,
asks again with thinking off. Both replies' tokens and energy count. Mirrored order, off, budget, budget, off;
`experiments/budget_mac.sh` under `when_quiet.sh`.)
What has been seen: note 29's replay of the first 40 problems (+7.5 points at 4.6x tokens), and two smoke tests of
the new mode on problems 1 to 4 (budget 256 and 4,096), which only checked that both paths work. Problems 41 to 164
have never been run with thinking.
- The budget raises HumanEval accuracy over thinking off by 2 to 8 points.
- Tokens per problem: 3 to 6 times thinking off.
- Chip joules per correct answer: 3 to 7 times thinking off.
- 4 to 15% of problems fall back.
Decision rule, set now: Foundry offers the budget as a "think on code" setting only if the gain is at least 3 points;
under that, thinking stays off on this model and the setting is not built.

## Results so far, 2026-10-26, 20:59 PT (predictions above left unedited)

- **12:00 entry, Qwen2.5 7B Q4_0 on the general eval** (`results/general-halo-baselines.md`): GSM8K 86 to 90%: missed,
  91.4% (91.6, 91.2). MMLU-Pro 45 to 55%: held, 50.4%. HumanEval 75 to 85%: held, 79.0%. The Qwen3.6 clauses of that entry
  are still to run.
- **12:03 entry, stock 1.5B Q4_0**: GSM8K 63 to 69%: held, 68.6% (67.2, 70.0). MMLU-Pro 25 to 35%: held, 27.1%. HumanEval
  50 to 65%: held, 56.1%. Energy spreads over 3% on every 1.5B task (4.0, 25.7, 11.0%) and on the 7B's GSM8K (7.1%) and
  MMLU-Pro (9.0%), flagged on the page. The RFT clauses of that entry are still to run.

## 2026-10-26, 21:03 PT

**Lattice v2 at 32B, rerun of the void cells** (Strix Halo; `experiments/lattice32_rerun.sh`, the same files as the 11:04 entry,
SHA256 checked, same protocol: quality.py GSM8K-250, 8 slots, auto clocks, two mirrored passes; new output names). The 11:04
search ran to completion, but from 12:51 to 14:42 another job shared the GPU (the power log shows it at 100% between runs, 108
to 121 W in three "idle" windows, CPU load 2.3 to 2.5), so IQ3_XXS pass 1, Q3_K_M passes 1 and 2, the end of IQ2_XS pass 1 and
the start of IQ3_XXS pass 2 are void for energy. The rerun takes Q4_0 as the anchor, then IQ2_XS, IQ3_XXS, Q3_K_M (pass 2
reversed), each run behind a gate (no compute client in /sys/class/kfd, GPU busy under 5% for 60 s; an idle reading over 15 W
re-gates three times, then aborts), with the shader, fabric and SoC clocks sampled every 2 s during each run. Clean cells so
far: Q4_0 558.3 / 553.1 J per correct at 95.6%, 55.5 / 55.6 tok/s; calibrated Q2_K 476.9 / 491.2 J at 95.6 / 96.4%;
IQ2_M 859.9 / 990.9 J at 90.4 / 89.2%, 35.6 / 29.2 tok/s; IQ2_XS pass 2 717.9 J at 91.6%, 38.9 tok/s.
- Q4_0 reproduces its clean cells: both passes within 3% of 555.7 J per correct, 95 to 97%.
- Accuracy is unchanged by the disturbance, so these are replications: IQ2_XS 90 to 94%, IQ3_XXS 89 to 93%, Q3_K_M 95 to 97%.
- **All three formats cost more per token than Q2_K's 2,050 mJ and lose to it per correct answer:** IQ2_XS 2,500 to 3,300
  mJ per token at 38 to 48 tok/s; IQ3_XXS 3,100 to 4,500 at 27 to 39 tok/s; Q3_K_M 2,800 to 4,200 at 29 to 44 tok/s. None
  lands under 560 J per correct, so the 11:04 entry's "Q3_K_M between Q2_K and Q4_0" stays missed.
- **The fabric-clock lead:** the earlier passes disagreed by 15 to 18% on IQ2_M and IQ2_XS with the marked fabric level lower in
  the slower pass. Prediction: for the three formats here, pass 2 (later, warmer) is slower than pass 1 by 5 to 25% on tokens
  per second, Q4_0 within 3%, and where the clock log has marked fabric levels the slower pass shows the lower one.

**Qwen3.6-35B-A3B with a 2,048-token thinking budget** (Strix Halo; `experiments/phase0_baselines.sh`, STAGE=eval, changed before
any eval ran: the "thinking on at 16,384" condition of the 12:00 entry is replaced by THINK_BUDGET=2048 with fallback to thinking
off at 4,096, on the Mac lead's direction after note 29; THINK=0 at 4,096 stays the baseline, Q4_0 and Q8_0, mirrored passes, each
run behind the GPU gate). The 12:00 entry's thinking-off clauses stand. For the budget condition:
- Fell back (thinking cut at 2,048, re-asked with thinking off): GSM8K 10 to 30% of problems, MMLU-Pro 30 to 60%, HumanEval 15
  to 40%.
- Accuracy against thinking off at the same format: GSM8K within 2 points either way; MMLU-Pro +2 to +8; HumanEval +3 to +10.
- Tokens per answer 2.5 to 4 times thinking off; joules per correct answer 2.5 to 5 times, so the budget does not pay on GSM8K
  and pays on MMLU-Pro and HumanEval only if a point is worth more than double the energy.
- Q4_0 within 2 points of Q8_0 on every task under the budget, as predicted for thinking off.

### 20:08 entry (thinking budget with fallback, live): verdict at 21:10

Run 20:13 to 21:09 on the M5 Pro, idle 0.48 to 1.62 W before each pass. Accuracy identical in both passes of each
condition (162 and 163 of 164 replies byte-identical). Thinking off 78.0% (128/164); budget 2,048 89.6% (147/164).
- Accuracy +11.6 points (2 to 8 predicted). Missed, above the range: 20 problems fixed, 1 broken. On problems 41 to
  164, never run with thinking before, +12.9 points. On problems 1 to 40, 34 against 37, exactly as the replay said.
- Tokens per problem x2.90 (3 to 6 predicted). Missed narrowly.
- Joules per correct x1.68 (3 to 7 predicted). Missed, below the range: two thinking-off replies (problems 132 and
  134) ran to 16,384 tokens, 45% of thinking-off's tokens, decoded at the end of the run nearly alone, so thinking
  off paid 205 mJ per token against 136 for the budget.
- Fell back on 26 of 164 (16%; 4 to 15% predicted). Missed narrowly.
All four clauses missed; three in the budget's favour. The decision rule (gain at least 3 points) is met. Energy
pass gaps 6.9% and 8.0%, both over 3%, both with the second pass costlier and its idle reading higher (1.6 W).
Note 30.

## 2026-10-26, 21:21 PT

**Three answer modes on code** (M5 Pro; Qwen3.5 4B Q4_0; HumanEval 164 in the macOS sandbox; 8 requests at once;
`experiments/modes_mac.sh`, mirrored A B C C B A under `when_quiet.sh`). A: thinking off, replies capped at 2,048
tokens. B: note 30's budget (think up to 2,048, else ask again without thinking), every reply capped at 2,048. C:
llama.cpp's own `--reasoning-budget 2048`, which ends the thought at 2,048 tokens and lets the model answer, 4,096
tokens per reply in all. Reference: note 30's uncapped runs, same day and machine: thinking off 78.0%, 442 tokens,
120.0 J per correct; budget 89.6%, 1,282 tokens, 201.9 J.
Seen before writing: decoding repeats, so note 30's replies fix A and B's answers. Replayed: A 78.0% at 267 tokens per
problem, B 89.6% at 1,107; no passing reply was longer than 2,048 tokens. Those are reported, not counted. C was
smoke-tested on problems 1 to 3 at a 40-token budget, only to check that it works.
- A costs 40 to 65 J per correct answer: the runaway replies were most of thinking-off's energy.
- B costs 150 to 185 J per correct answer.
- C scores 86 to 92% at 900 to 1,200 tokens per problem.
- C costs 5 to 20% less than B per correct answer.
Decision rule, set now: Foundry's Think switch moves from B's policy to C's if C is within 1 point of B (or better)
and at least 5% cheaper per correct answer. A cap on plain replies is not adopted in Foundry whatever A measures: in a
chat, a long answer is often the right one, and HumanEval does not test that.

### 21:21 entry (three answer modes on code): verdict at 22:29

Run 21:36 to 22:28 on the M5 Pro. Every reply byte-identical between the two passes of each condition (492 of 492).
A (off, capped) 78.0% at 267 tokens; B (fallback, capped) 89.6% at 1,107; C (built-in budget) 92.1% (151/164) at
1,076. On the 138 problems whose thought finished inside 2,048 tokens, B and C wrote the same reply; on the 26 that
did not, B's fresh answer scored 14 (the same as A) and C's answer from the cut thought 18.
- A costs 40 to 65 J per correct answer: 43.6. Held.
- B costs 150 to 185 J: 141.8. Missed, below the range.
- C scores 86 to 92% at 900 to 1,200 tokens: 92.1% at 1,076. Missed by 0.1 point, above the range.
- C costs 5 to 20% less than B: 4.7% more on the mean of its two passes. Missed. Its first pass drew 36.2 W against
  31 to 33 W for every other pass, at the same token count, with no cause found; its second pass alone is 5.7%
  cheaper, and the token count says about 3% cheaper. None of the three reaches 5%.
One clause held. The decision rule is not met: Foundry's Think switch keeps B's policy. Note 31.

## 2026-10-26, 22:29 PT

**The built-in budget on maths and knowledge** (M5 Pro; Qwen3.5 4B Q4_0; GSM8K first 100, MMLU-Pro first 8 per
subject (112); 8 requests at once; `experiments/modes_mac_qa.sh`, mirrored A B C C B A under `when_quiet.sh`). A, B
and C exactly as in the 21:21 entry: off capped at 2,048; fallback with every reply capped at 2,048; llama.cpp's
`--reasoning-budget 2048` with 4,096 per reply.
Seen before writing: note 29 ran GSM8K 1 to 50 and MMLU-Pro 4 per subject with unlimited thinking; its replay of B at
2,048 matched thinking off exactly on both (98.0% and 64.3%), and its thoughts ran a median 3,228 tokens on GSM8K
and 7,183 on MMLU-Pro. C has never been run on either task.
- B is within 1 point of A on both tasks.
- B falls back on 20 to 50% of GSM8K and 60 to 90% of MMLU-Pro.
- C is within 2 points of A on GSM8K.
- C beats B on MMLU-Pro by 0 to 6 points.
- C uses 5 to 15% fewer tokens than B on MMLU-Pro.
Decision rule, set now: Foundry's Think switch moves from B's policy to C's if, across note 31's HumanEval and these
two tasks, C is no less accurate than B on any, at least 2 points better on one of these two, and no more than 10%
costlier per correct answer on any.

## 2026-10-26, 23:57 PT

**Qwen3.6-35B-A3B with llama-server's own reasoning budget** (Strix Halo; `experiments/phase0_baselines.sh`, STAGE=eval, a
third mode added before any Qwen3.6 eval ran, on the Mac lead's ask after note 31: THINK=1, `--reasoning-budget 2048`, 4,096
per reply, 6,144 per slot, as `experiments/modes_mac_qa.sh`'s C; results named `-native-`; Q4_0 and Q8_0; runs after the
thinking-off and THINK_BUDGET=2048 (fallback) conditions in pass 1, before them in pass 2; each run behind the GPU gate).
Seen before writing: note 31 (Qwen3.5 4B, HumanEval-164): C 92.1% against the fallback's 89.6%, identical replies on the 138
problems whose thought finished, 18 against 14 on the 26 that ran long, tokens 1,076 against 1,107, energy per correct 4.7%
more on the mean of C's passes with one pass 36.2 W against 31 to 33 W. The Mac's GSM8K/MMLU-Pro comparison (22:29 entry)
has not reported. Qwen3.6 has never run here in any mode; the 12:00 and 21:03 entries' clauses for the other two modes stand.
- C is within 2 points of the fallback on GSM8K at the same format (both near thinking off; the problems are easy for a 35B).
- C beats the fallback on MMLU-Pro by 0 to 6 points and on HumanEval by 0 to 5 points, at the same format; it loses on
  neither by more than 1 point.
- C uses fewer tokens per answer than the fallback: 0 to 15% fewer on MMLU-Pro and HumanEval (no re-ask), within 5% on GSM8K.
- C's joules per correct answer are within 10% of the fallback's on every task, in either direction.
- Q4_0 is within 2 points of Q8_0 under C on every task.
- Replies cut by the budget (reply tokens over 2,048) are 10 to 30% of GSM8K, 30 to 60% of MMLU-Pro, 15 to 40% of
  HumanEval, the same shares as the fallback condition's.
Decision rule for the Halo: the 22:29 entry's rule applies here too, scored on the Qwen3.6 cells (C no less accurate than
the fallback on any task, at least 2 points better on one, no more than 10% costlier per correct answer on any).
