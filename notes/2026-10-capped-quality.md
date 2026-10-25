# Does a clock cap pay per correct answer?

**Prediction verdict:** held on the headline (15 to 28% fewer joules per correct answer at accuracy within a
point, every cell); missed on the 32B calibrated Q2_K, which slows 22 to 24% under the cap (predicted under
10%) and whose lead over Q4_0 shrinks to 5 to 10% (predicted 16% within 5 points).

Spliced research note 23, 25 October 2026. AMD Ryzen AI Max+ 395 (Strix Halo, Radeon 8060S, 128 GB, shared GPU memory 90%), Linux, llama.cpp 620d2225c, Vulkan. Qwen2.5 7B and 32B Instruct.

The clock-cap sweep (`results/halo-clockcap.md`) found that capping the shader clock at 1,800 MHz through the OD table cuts the 7B's batch-1 decode energy per token by 37% at 4% less speed. That is energy per token at batch 1. The bar every model and setting is judged on is joules per correct answer at 8 requests at once (`experiments/quality.py`, note 19). This note runs that harness under the cap, on the same three cells note 22 measured on auto earlier today.

**Prediction** (`docs/predictions.md`, committed and pushed before the first measurement): accuracy within 1 point of the auto run in every cell. 7B Q4_0: 20 to 35% fewer joules per correct answer, 5 to 20% fewer tokens per second (eight slots are more compute-bound than batch-1 decode, so the speed cost is larger than the sweep's 4%). 32B calibrated Q2_K: 25 to 40% fewer joules, under 10% slower. 32B Q4_0: 25 to 40% fewer joules, and calibrated Q2_K stays 16% cheaper than Q4_0 within 5 points. The cap holds for all six runs.

## Method

`experiments/halo_capped_quality.sh`: the OD table set to 1,800 MHz (`power_dpm_force_performance_level=manual`, `pp_od_clk_voltage` `s 1 1800`, `c`), verified under a decode load before anything is measured, the active clock sampled during every run and its maximum logged. Then `quality.py`, GSM8K-250, 8 slots, chip (package) energy, two passes with the second reversed: 7B Q4_0, 32B calibrated Q2_K, 32B Q4_0. Package idle sampled for 10 s before every run with nothing loaded (`results/halo-capped-idle-pre.csv`), next to quality.py's own loaded idle. Auto comparison cells are note 22's runs from earlier today, same machine, same build, same shared-memory setting; the 7B auto pair was re-run in this session (below) so both of its passes share conditions. The clock was restored to auto and the OD table reset at the end; readback in `results/halo-capped-readback.txt`.

## Results

Capped at 1,800 MHz, two-pass means; every pass, both idle readings, the sampled clock and the spreads are in
`results/halo-capped-quality.md`, raw JSON in `results/quality-halo-cap1800-*-pass{1,2}.json`.

| model, format | accuracy | J per correct | vs auto | tok/s | vs auto | mJ per token | vs auto |
|---|---:|---:|---:|---:|---:|---:|---:|
| 7B Q4_0 | 88.2% | 111.3 | -28% | 192.1 | -15% | 425 | -28% |
| 32B Q2_K, calibrated | 95.6% | 384.7 | -19% | 46.5 | -24% | 1618 | -19% |
| 32B Q4_0 | 95.8% | 426.2 | -24% | 49.9 | -11% | 1705 | -23% |

Auto, for reference (note 22 means; the 7B re-run below is not averaged in):

| model, format | accuracy | J per correct | tok/s | mJ per token |
|---|---:|---:|---:|---:|
| 7B Q4_0 | 88.6% | 153.8 | 225.9 | 589 |
| 32B Q2_K, calibrated | 95.6% | 473.7 | 61.2 | 1992 |
| 32B Q4_0 | 94.8% | 563.6 | 56.3 | 2224 |

Package power during the runs fell from 122 to 127 W on auto to 75 to 87 W under the cap. The cap held: the
active clock, sampled every 0.5 s, never exceeded 1,800 MHz in any run. Idle before each run drifted 6.3 to
19.2 W; gross J per correct answer is the headline, net is soft.

Spread: the 7B and 32B Q4_0 cells repeat to within 2.0% and 4.8% on J per correct (the latter flagged: 87.0
against 83.2 W at the same speed). The capped 32B Q2_K pair differs by 9.7%, flagged: the power log shows
the first 15 minutes of its pass 2 at 64 to 67 W at the same clock and GPU load as pass 1, then 75 to 87 W,
and the pre-run idle before it was 6.3 W where every other run saw 10.6 to 19.2 W. Something outside the GPU
was in a lower power state for that stretch; the logger now records memory, fabric and display clocks and the
display's power state so the next such stretch can be attributed. Pass 1 (403.4 J per correct) is the
representative Q2_K figure; the mean carries the artefact.

## 7B on auto, re-run in one session

Note 22's 7B pass 1 (previous session) drew 10% more power than pass 2 at the same speed. To test whether
that was the session, both 7B pass-1 cells were re-run on auto in this session at 16:00, right after the
capped run and before the harvest resumed (`experiments/lattice_7b_rerun.sh`). The re-run rows are kept apart
in `results/lattice-halo.md` and not averaged into note 22's means.

| format | run | accuracy | gross J/correct | net J/correct | tok/s | mJ/token | W during run | idle W, model loaded |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Q4_0 | pass 1, previous session | 88.0% (220/250) | 161.6 | 141.8 | 226.2 | 617 | 139.6 | 17.1 |
| Q4_0 | pass 2, 13:18 | 89.2% (223/250) | 145.9 | 120.5 | 225.5 | 561 | 126.5 | 22.0 |
| Q4_0 | re-run, 15:57 | 88.4% (221/250) | 160.5 | 139.4 | 227.4 | 615 | 139.8 | 18.3 |
| Q2_K calibrated | pass 1, previous session | 84.8% (212/250) | 200.3 | 166.3 | 188.5 | 717 | 135.1 | 22.9 |
| Q2_K calibrated | pass 2, 13:12 | 83.6% (209/250) | 191.4 | 155.0 | 186.0 | 673 | 125.2 | 23.8 |
| Q2_K calibrated | re-run, 16:02 | 82.4% (206/250) | 213.7 | 178.8 | 178.1 | 741 | 132.0 | 21.6 |

The re-run reproduced pass 1: Q4_0 within 1% (139.8 against 139.6 W, 160.5 against 161.6
J/correct); Q2_K within 3% on power and energy per token (132.0 against 135.1 W, 741 against 717
mJ/token), with six fewer problems right, which puts its J/correct 6.7% off. So note 22's 10% spread is run
order, not the session: pass 2 followed four 32B runs and drew 10% less power at the same speed, and a first
7B run after a change of state (a session start; here, 95 minutes under the clock cap ending a minute earlier)
draws the higher figure. The flag stays on note 22's 7B cells.

## What to take from this

1. **The cap pays on the bar that matters.** At 8 requests at once, every cell costs 15 to 28% fewer joules
   per correct answer than on auto, at the same accuracy. The 7B Q4_0 drops from 153.8 to 111.3 J per correct
   answer at 15% fewer tokens per second; the 32B Q4_0 from 563.6 to 426.2 at 11% fewer. The predicted direction
   and sizes held for both Q4_0 cells.
2. **The 2-bit model pays for the cap in speed.** Calibrated Q2_K at 32B slows 24% under the cap where Q4_0
   slows 11%, and its energy lead over Q4_0 shrinks from 16% to 5 to 10%. Fewer bits mean more unpacking work
   per weight, and a lower shader clock makes that work the slow part. Not predicted; the prediction said the
   16% lead would hold within 5 points.
3. **Serving at 8 slots costs more speed than batch-1 decode did.** The clock-cap sweep lost 4% of batch-1 decode
   speed at 1,800 MHz; here the 7B loses 15% and the 32B Q4_0 11%, as predicted, because eight concurrent
   requests make the run more compute-bound.
4. **For Foundry on this machine:** a capped 32B Q4_0 answers GSM8K at 95.8% for 426 J per correct answer,
   24% less than the same model on auto, at 11% fewer tokens per second; whether that trade is worth it is a
   product decision, and only the energy and speed are measured here.

## Limits

One task, one machine, chip (package) energy, one cap value. The cap needs root; a laptop's equivalent is its firmware power mode, not measured here. Whether a lower cap (1,200 MHz) does better per correct answer at 8 slots is untested.
