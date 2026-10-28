# Lattice v2 at 32B: the format search, with the void cells rerun

**Verdicts (`docs/predictions.md`, 11:04 and 21:03 entries of 26 October, judged 18:12 on 27 October):** the format search's
central claim held, calibrated Q2_K is still the cheapest per correct answer, by 12.9% over Q4_0 and with no format beating
note 22's figure; seven of its twelve clauses missed, mostly on how far the IQ formats fall (accuracy and energy both). The
rerun's clauses held except the fabric-clock lead, which is dead: the second pass was faster, not slower, and the clocks the
kernel shows do not explain the gap. Q3_K_M, whose only earlier cells were void, turns out to be Q4_0's equal at 85% of the bytes.

Strix Halo (AMD Ryzen AI Max+ 395, RAH-001, 128 GB, shared GPU memory 90%), llama.cpp 620d2225c Vulkan. Qwen2.5 32B Instruct:
stock Q4_0 against five formats quantized from the same F16 with note 22's GSM8K imatrix (`results/lattice/imatrix-32b-gsm8k.gguf`).
quality.py GSM8K-250, 8 slots, auto clocks, two passes with the second in reverse order, one model alone on the GPU, package
`power1_average` for energy. `experiments/lattice32_formats.sh` (26 October 11:30 to 16:45) and `experiments/lattice32_rerun.sh`
(27 October 15:02 to 18:07). File hashes in `results/lattice32-SHA256SUMS`, checked before the rerun.

## The clean table (two-pass means; cells from the run that was clean)

| format | bytes | accuracy | tokens per answer | tok/s | W | mJ per token | J per correct | against Q4_0 | run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Q4_0 (stock) | 18.6 GB | 95.6% | 240 | 55.6 | 122.8 | 2,211 | **555.7** | | 26 Oct |
| Q2_K, calibrated | 12.3 GB | 96.0% | 227 | 60.0 | 122.8 | 2,048 | **484.1** | -12.9% | 26 Oct |
| Q3_K_M, calibrated | 15.9 GB | 96.0% | 238 | 54.4 | 123.5 | 2,270 | 563.8 | +1.5% | 27 Oct |
| IQ2_XS, calibrated | 10.0 GB | 92.8% | 210 | 44.6 | 123.4 | 2,774 | 628.3 | +13.1% | 27 Oct |
| IQ2_M, calibrated | 11.3 GB | 89.8% | 227 | 32.4 | 117.9 | 3,662 | 925.4 | +66.5% | 26 Oct |
| IQ3_XXS, calibrated | 12.8 GB | 90.0% | 229 | 32.8 | 119.7 | 3,658 | 931.6 | +67.7% | 27 Oct |

The order is set by tokens per second. All six formats draw 118 to 124 W while decoding, so the cost per token is the inverse
of the speed, and the speed is the unpacking cost of the format on this Vulkan path, not the bytes read: the smallest file,
IQ2_XS, decodes at 80% of Q4_0's rate, and IQ2_M and IQ3_XXS at 58 to 59%. Q2_K is the one format that is both smaller and
faster than Q4_0. Q3_K_M matches Q4_0 on every column (96.0 against 95.6%, 238 against 240 tokens, 2% slower) at 85% of the
bytes, so it is the format to take when Q4_0 does not fit and a 2-bit loss is not wanted. The 3-bit IQ3_XXS scores below the
2-bit IQ2_XS (90.0 against 92.8%) and costs 48% more per correct answer: on this model and imatrix, bigger IQ is not better IQ.

Tokens per answer against Q4_0's 240: Q3_K_M 238 (-0.8%), IQ3_XXS 229 (-4.6%), Q2_K 227 (-5.4%), IQ2_M 227 (-5.4%), IQ2_XS 210
(-12.5%). The 2-bit formats answer shorter, IQ2_XS by an eighth; the prediction's "within 5%" held for two formats of five.

## Every cell, both runs

The 26 October run (`results/lattice32-halo-*-pass{1,2}.json`, idle in `results/lattice32-halo-idle-pre.csv`) ran all six
formats, but from 12:51 to 14:42 another job shared the GPU (the power log shows it at 100% busy between runs, 108 to 121 W in
three "idle" windows, CPU load 2.3 to 2.5). The cells it touched are **void for energy** and kept here marked; their accuracy is
unaffected (the model's answers do not depend on who else is on the GPU) and agrees with the rerun to within 2 points. The
27 October rerun (`results/lattice32r-halo-*-pass{1,2}.json`, `results/lattice32r-halo-idle-pre.csv`,
`results/lattice32r-halo-clocks.csv`) redid IQ2_XS, IQ3_XXS and Q3_K_M with Q4_0 as the anchor, each run behind the GPU gate
(no compute client in `/sys/class/kfd`, GPU busy under 5% for 60 s, then a 10 s idle sample that must read 15 W or less).

| format | pass | run | accuracy | tokens per answer | tok/s | W | idle before, W | mJ per token | J per correct | state |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Q4_0 | 1 | 26 Oct | 95.6% (239) | 240 | 55.5 | 123.6 | 12.6 | 2,228 | 558.3 | clean |
| Q4_0 | 2 | 26 Oct | 95.6% (239) | 241 | 55.6 | 122.0 | 5.2 | 2,194 | 553.1 | clean |
| Q4_0 | 1 | 27 Oct | 95.6% (239) | 238 | 57.0 | 125.9 | 6.8 | 2,208 | 550.7 | clean, anchor |
| Q4_0 | 2 | 27 Oct | 95.2% (238) | 241 | 56.6 | 125.1 | 6.6 | 2,208 | 558.3 | clean, anchor |
| Q2_K | 1 | 26 Oct | 95.6% (239) | 227 | 61.0 | 122.4 | 6.8 | 2,007 | 476.9 | clean |
| Q2_K | 2 | 26 Oct | 96.4% (241) | 227 | 58.9 | 123.1 | 5.2 | 2,088 | 491.2 | clean |
| IQ2_M | 1 | 26 Oct | 90.4% (226) | 227 | 35.6 | 121.6 | 21.2 | 3,421 | 859.9 | clean, idle high |
| IQ2_M | 2 | 26 Oct | 89.2% (223) | 226 | 29.2 | 114.1 | 5.4 | 3,904 | 990.9 | clean |
| IQ2_XS | 1 | 26 Oct | 93.2% (233) | 210 | 46.6 | 122.0 | 6.6 | 2,620 | 589.4 | **void** (end shared) |
| IQ2_XS | 2 | 26 Oct | 91.6% (229) | 209 | 38.9 | 122.4 | 5.3 | 3,147 | 717.9 | clean |
| IQ2_XS | 1 | 27 Oct | 92.8% (232) | 210 | 42.0 | 123.3 | 6.6 | 2,936 | 664.5 | clean |
| IQ2_XS | 2 | 27 Oct | 92.8% (232) | 210 | 47.3 | 123.5 | 6.1 | 2,611 | 592.1 | clean |
| IQ3_XXS | 1 | 26 Oct | 91.2% (228) | 228 | 34.7 | 120.9 | 29.5 | 3,489 | 872.5 | **void** |
| IQ3_XXS | 2 | 26 Oct | 90.8% (227) | 229 | 26.5 | 110.5 | 113.6 | 4,173 | 1,053.5 | **void** (start shared) |
| IQ3_XXS | 1 | 27 Oct | 89.2% (223) | 230 | 31.5 | 119.6 | 5.7 | 3,799 | 979.5 | clean |
| IQ3_XXS | 2 | 27 Oct | 90.8% (227) | 228 | 34.0 | 119.7 | 6.0 | 3,518 | 883.7 | clean |
| Q3_K_M | 1 | 26 Oct | 95.6% (239) | 239 | 31.6 | 120.3 | 115.4 | 3,804 | 950.2 | **void** |
| Q3_K_M | 2 | 26 Oct | 96.0% (240) | 238 | 21.3 | 119.9 | 117.5 | 5,641 | 1,398.2 | **void** |
| Q3_K_M | 1 | 27 Oct | 96.0% (240) | 238 | 54.5 | 123.5 | 5.6 | 2,268 | 562.4 | clean |
| Q3_K_M | 2 | 27 Oct | 96.0% (240) | 239 | 54.3 | 123.5 | 5.6 | 2,273 | 565.3 | clean |

"Idle before" is the 10 s package sample with nothing loaded right before the run; the JSONs also carry quality.py's own
8 s baseline with the model loaded (8.9 to 9.8 W in the rerun). The 26 October IQ2_XS pass 2, read on its own in the 21:03
entry as a clean 717.9 J cell, is 14% dearer than the rerun's mean (8% over its dearer pass); it is kept as clean (nothing shared the GPU during it) but
the rerun's two passes are the figures used. The void Q3_K_M cells read 1.7 to 2.5 times the clean ones: the whole of the
first run's "Q3_K_M is dear" was the other job.

**Pass-to-pass gaps on J per correct, flagged over 3%:** rerun IQ2_XS 11.5% and IQ3_XXS 10.3% (both with the later pass
cheaper and faster); Q4_0 1.4%, Q3_K_M 0.5%. 26 October: Q4_0 0.9%, Q2_K 3.0% (14.3 J on 484, at the line, flagged), IQ2_M 14.2% (flagged). Accuracy agrees
between passes to within 1.6 points everywhere.

## The fabric-clock lead, tested and dropped

The 21:03 entry predicted, from the 26 October passes disagreeing by 15 to 18% on IQ2_M and IQ2_XS with a lower marked
fabric level in the slower pass, that the rerun's second pass would be 5 to 25% slower and show the lower fabric level. The
rerun sampled `pp_dpm_sclk`, `pp_dpm_fclk`, `pp_dpm_socclk`, `gpu_busy_percent` and package power every 2 s during each run
(5,112 samples). What it shows:

- The second pass was **faster**: IQ2_XS by 12.7%, IQ3_XXS by 8.1%; Q3_K_M and Q4_0 within 0.7%.
- The fabric clock is sparsely marked: the kernel marks a current level in 3 to 56 of 529 to 915 samples per run (0.3 to
  10%), the rest of the time no level carries the asterisk. Where marked, IQ2_XS's slower pass 1 shows 1,850 MHz (3 of 5
  samples) and its faster pass 2 shows 1,600 (54 of 56): the opposite of the lead, on too few samples to be more than that.
- The shader clock is marked on every sample and was **higher in the slower pass** (busy at 80% or more: IQ2_XS 2,640
  against 2,523 MHz, IQ3_XXS 2,810 against 2,756; Q4_0 and Q3_K_M within 20 MHz between passes), at package power equal to
  0.3 W. Faster at a lower shader clock and the same power means the gap is not in the GPU core.
- The SoC clock, marked in 1 to 15 samples per run, reads higher in the faster pass (IQ2_XS 1,104 against 883 MHz; IQ3_XXS
  1,104 against 981 on one sample; Q4_0 1,261 in both). A lead for the memory side, not a result: it needs a sampler that
  reads the clocks the kernel actually reports (amdgpu_pm_info or the SMU metrics table) rather than the DPM level tables.

The IQ formats' speed varies 8 to 13% between passes at identical accuracy, power and shader clock, in the direction that
disagrees with "later is warmer is slower". Until the memory-side clocks are logged, treat any IQ cell as ±10% on speed and
energy, and the Q-format cells (gaps under 1.5%) as firm.

## Verdicts in full

Given per clause in `docs/predictions.md` under the 11:04 and 21:03 entries (verdict sections dated 18:12, 27 October). In
one line each: the 11:04 search held five clauses (Q3_K_M, Q2_K and IQ2_XS accuracy; Q2_K cheapest; nothing beats 473.7 J;
ranking by speed) and missed seven (IQ3_XXS and IQ2_M accuracy, 5.6 and 5.8 points below Q4_0; the IQ formats' per-token
band, 35 to 79% dearer than Q2_K rather than within 5%; Q3_K_M between Q2_K and Q4_0, it is 3% over Q4_0; answer length
within 5%; Q2_K within 5% of second, it is 12.9% under). The 21:03 rerun held three (Q4_0 reproduces within 1%; the three
accuracies replicate; all three dearer than Q2_K per token and per correct, none under 560 J), held its bold claim with both
Q3_K_M ranges missed (2,270 mJ at 54 tok/s against a predicted 2,800 to 4,200 at 29 to 44, ranges seeded by the void cells),
and missed the fabric-clock lead.

## Limits

- **The 26 October contamination window** (12:51 to 14:42): another session's job on the GPU, found from the power log after
  the fact, not by the runner, which had no gate then. Void cells are kept and marked above; nothing from them is used for
  energy. The gate (`experiments/gpu_gate.sh`) came from this.
- **The gate's compute-client check sees only ROCm/HIP clients** (`/sys/class/kfd/proc`); a Vulkan or display client shows
  only as GPU busy. The busy threshold (under 5% for 60 s) covers that, and it is what caught the two held cases below.
- **The reboot:** the box shut down at 03:10 on 27 October (3 minutes after a hold) and came back at 11:10; the rerun ran
  after it, on the same files (SHA256 checked at the start of the script), the same llama.cpp build, same settings. The 26
  October clean cells and the rerun's Q4_0 anchor agree to within 1% on J per correct, so the reboot moved nothing we measure.
- **Desktop compositing holds the gate:** the first gate of the rerun waited from 14:58 to 15:02 at 4 to 5% GPU busy with no
  compute client, which was the desktop compositor repainting this session's own terminal output, and passed within a minute
  once the polling stopped. Q4_0 pass 2's idle sample read 34.2 W for the same reason and re-gated once (2.5 minutes). A
  runner that polls its own log while gating delays its own runs.
- **Before the rerun** the GPU was held for the Illusion session's job from 13:48 to 14:57 (`logs/gpu.hold`); the rerun's first
  cell started at 15:02:55, after the gate and a 6.8 W idle.
- **The fabric clock log is sparse** (above): the DPM level files mark a current level only part of the time on this kernel
  (7.2.7). The sampler's fclk and socclk columns are mostly empty; sclk, busy and power are complete.
- One task (GSM8K-250), one model, one imatrix. The IQ formats' ranking is an artefact of this Vulkan build's unpacking
  kernels; a ROCm build or a later llama.cpp may order them differently.
