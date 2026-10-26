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
