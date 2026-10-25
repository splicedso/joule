# Joules per correct answer under a 1,800 MHz shader-clock cap (Strix Halo)

**Verdict on the pre-registered prediction (`docs/predictions.md`, 14:50 PT entry, pushed 14:16 before the
first measurement):** the headline held: every cell costs 15 to 28% fewer joules per correct answer than on
auto, at accuracy within a point. Two misses: the 32B calibrated Q2_K slows by 22 to 24% under the cap, not
under 10%; and its lead over Q4_0 shrinks from 16% on auto to 5 to 10% under the cap, outside the predicted
11 to 21%. The 7B Q4_0 numbers (28% fewer joules, 15% slower) and the 32B Q4_0 numbers (24% fewer joules,
11% slower) are inside their predicted bands.

`experiments/halo_capped_quality.sh`, 14:21 to 15:56 PDT. OD table `s 1 1800`, `c`, verified under a decode
load before measuring (active max 1,800 MHz); the active clock sampled every 0.5 s during each run never
exceeded 1,800 MHz (`results/halo-capped-diag.txt`). `quality.py`, GSM8K-250, 8 slots, chip (package)
energy, Phase warm-up, two passes with the second reversed, one model alone on the GPU. Package idle sampled
for 10 s before each run with nothing loaded (`results/halo-capped-idle-pre.csv`); quality.py's loaded idle in
each JSON. Clock restored to auto and OD table reset at the end (`results/halo-capped-readback.txt`).
Auto cells are note 22's runs from earlier today (PR #17), same build and setting; the 7B pair was also re-run in
this session (below), kept apart.

## Every pass, capped at 1,800 MHz

| model, format | pass | accuracy | gross J/correct | net J/correct | tok/s | mJ/token | W during run | idle W, no server | idle W, model loaded |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 7B Q4_0 | 1 | 88.8% (222/250) | 110.2 | 87.2 | 192.7 | 424 | 81.8 | 18.2 | 17.1 |
| 7B Q4_0 | 2 | 87.6% (219/250) | 112.4 | 84.2 | 191.4 | 425 | 81.4 | 19.2 | 20.5 |
| 32B Q2_K, calibrated | 1 | 95.6% (239/250) | 403.4 | 334.7 | 47.8 | 1696 | 81.1 | 10.6 | 13.8 |
| 32B Q2_K, calibrated | 2 | 95.6% (239/250) | 365.9 | 316.6 | 45.2 | 1540 | 69.6 | 6.3 | 9.4 |
| 32B Q4_0 | 1 | 95.6% (239/250) | 436.4 | 344.5 | 49.9 | 1743 | 87.0 | 17.5 | 18.3 |
| 32B Q4_0 | 2 | 96.0% (240/250) | 415.9 | 320.8 | 49.9 | 1667 | 83.2 | 16.0 | 19.0 |

## Two-pass means, capped against auto

| model, format | accuracy cap / auto | J/correct cap | auto | delta | tok/s cap | auto | delta | mJ/token cap | auto | delta | W cap | auto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 7B Q4_0 | 88.2% / 88.6% | 111.3 | 153.8 | -28% | 192.1 | 225.9 | -15% | 425 | 589 | -28% | 81.6 | 133.1 |
| 32B Q2_K, calibrated | 95.6% / 95.6% | 384.7 | 473.7 | -19% | 46.5 | 61.2 | -24% | 1618 | 1992 | -19% | 75.4 | 122.0 |
| 32B Q4_0 | 95.8% / 94.8% | 426.2 | 563.6 | -24% | 49.9 | 56.3 | -11% | 1705 | 2224 | -23% | 85.1 | 125.2 |

Under the cap, calibrated Q2_K costs 384.7 against Q4_0's 426.2 J per correct answer on the two-pass means
(9.7% less), or 403.4 against 426.2 (5.3% less) if its flagged pass 2 is set aside (next section). On auto
it was 16.0% less. A 2-bit token is 5% cheaper than a 4-bit one under the cap (1618 against 1705 mJ) where
it was 10% cheaper on auto, and the 2-bit model loses more speed to the cap (24% against 11%): the unpacking
work that fewer bits add is the part a lower shader clock makes slower.

## Spreads, flagged over 3%

- Capped 32B Q2_K: J/correct **9.7%**, mJ/token **9.7%**, tok/s **5.6%**. The power log
  (`results/halo-power-log.csv`) shows the whole first 15 minutes of pass 2 (15:30 to 15:44) at 64 to 67 W
  at the same 1,785 MHz and 97 to 98% GPU busy as pass 1, then 75 to 87 W from 15:45. The pre-run idle
  before that pass was 6.3 W against 10.6 to 19.2 W before every other run. Something outside the GPU
  (the display, memory or fabric power state; the logger now records them) was in a lower state for that
  stretch. Pass 1 (403.4 J/correct) is the representative figure; the mean carries the artefact.
- Capped 32B Q4_0: J/correct **4.8%**, mJ/token **4.5%** (87.0 against 83.2 W at the same speed), tok/s 0.1%.
- Capped 7B Q4_0: J/correct 2.0%, mJ/token 0.2%, tok/s 0.7%, accuracy 1.2 points.
- Idle before each run drifted 6.3 to 19.2 W; gross J/correct is the headline, net is soft.

## 32B run time under the cap

Each 32B run took 20 minutes (Q2_K 20.1 and 21.3 min, Q4_0 20.3 and 20.3 min), against 15 to 18 on auto;
the 7B Q4_0 took 5.2 min against 4.3.

## 7B on auto, re-run in this session

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

Raw: `results/quality-halo-cap1800-{7b-Q4_0,32b-Q2_K-imat,32b-Q4_0}-pass{1,2}.json`,
`results/halo-capped-idle-pre.csv`, `results/halo-capped-diag.txt`, `results/halo-capped-readback.txt`.
Auto: `results/lattice-halo-*-pass{1,2}.json`; the 7B re-run: `results/lattice-halo-7b-*-pass1-rerun.json`.
