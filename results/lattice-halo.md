# Lattice on Strix Halo: does calibrated 2-bit pay on larger models?

**Verdict on the pre-registered prediction (`docs/predictions.md`, 05:05 PT):** held in direction at both
sizes, missed in margin at 32B. On the 7B, Q4_0 is cheaper per correct answer (as predicted). On the 32B,
GSM8K-calibrated Q2_K wins per correct answer, as predicted, but by **16.0%** on the two-pass mean
(17.9% in pass 1, 14.0% in pass 2), not "less than 15%".

GSM8K-250, slots 8, chip (package) energy, GSM8K-calibrated Q2_K (imatrix from 1,500 train problems,
200 chunks, `results/lattice/imatrix-{7b,32b}-gsm8k.gguf`) against Q4_0. Shared GPU memory 90%
(113 GiB), llama.cpp 620d2225c, Vulkan, Phase warm-up on. Two passes, the second in reverse order,
one model alone on the GPU, machine otherwise quiet. All times PDT, this machine's NTP-synced clock.

Two idle figures per run, side by side: **idle, no server** is package `power1_average` sampled for 10 s
right before the run with nothing loaded (`results/lattice-halo-idle-pre.csv`); **idle, model loaded** is
quality.py's own 8 s baseline with llama-server up and the model in memory (`idle_soc_w` in each JSON).
Gross J/correct uses the whole package draw; net subtracts the loaded idle. Gross is the headline: idle
drifted 16.6 to 25.9 W across the afternoon, so net is soft.

## 32B (both passes)

| format | pass | accuracy | gross J/correct | net J/correct | tok/s | mJ/token | W during run | idle W, no server | idle W, model loaded |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Q4_0 | 1 | 94.8% (237/250) | 571.5 | 488.1 | 57.0 | 2260 | 128.9 | 16.6 | 18.8 |
| Q4_0 | 2 | 94.8% (237/250) | 555.7 | 447.3 | 55.5 | 2187 | 121.5 | 24.9 | 23.7 |
| Q2_K, GSM8K-calibrated | 1 | 96.0% (240/250) | 469.2 | 404.2 | 61.6 | 1981 | 122.0 | 19.9 | 16.9 |
| Q2_K, GSM8K-calibrated | 2 | 95.2% (238/250) | 478.1 | 382.9 | 60.9 | 2004 | 122.0 | 22.4 | 24.3 |

Two-pass means: Q4_0 94.8%, **563.6 J/correct**, 56.3 tok/s, 2224 mJ/token. Calibrated Q2_K 95.6%,
**473.7 J/correct**, 61.2 tok/s, 1992 mJ/token. Q2_K is 16.0% cheaper per correct answer, 10.4% cheaper per
token and 8.7% faster; its accuracy is 2 problems higher, which is within the noise of 250 questions.

Pass-to-pass spread: Q4_0 gross J/correct 2.8%, **mJ/token 3.3% (flagged, over 3%)**, tok/s 2.6%;
Q2_K gross J/correct 1.9%, mJ/token 1.2%, tok/s 1.2%, accuracy 0.8 points. The Q4_0 gap is power, not
speed: pass 1 drew 128.9 W and pass 2 121.5 W at tokens per second within 3%.

Each 32B run took 15 to 18 minutes (Q4_0 17.5 and 18.1 min, Q2_K 15.4 and 15.6 min), not the 10 to 14 of
the previous handoff.

## 7B (both passes)

| format | pass | accuracy | gross J/correct | net J/correct | tok/s | mJ/token | W during run | idle W, no server | idle W, model loaded |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Q4_0 | 1 | 88.0% (220/250) | 161.6 | 141.8 | 226.2 | 617 | 139.6 | not recorded | 17.1 |
| Q4_0 | 2 | 89.2% (223/250) | 145.9 | 120.5 | 225.5 | 561 | 126.5 | 20.9 | 22.0 |
| Q2_K, GSM8K-calibrated | 1 | 84.8% (212/250) | 200.3 | 166.3 | 188.5 | 717 | 135.1 | not recorded | 22.9 |
| Q2_K, GSM8K-calibrated | 2 | 83.6% (209/250) | 191.4 | 155.0 | 186.0 | 673 | 125.2 | 25.9 | 23.8 |
| Q4_0 | 1 re-run (16:00, not averaged) | 88.4% (221/250) | 160.5 | 139.4 | 227.4 | 615 | 139.8 | 16.9 | 18.3 |
| Q2_K, GSM8K-calibrated | 1 re-run (16:02, not averaged) | 82.4% (206/250) | 213.7 | 178.8 | 178.1 | 741 | 132.0 | 21.1 | 21.6 |

Two-pass means: Q4_0 88.6%, **153.8 J/correct**, 225.9 tok/s, 589 mJ/token. Calibrated Q2_K 84.2%,
**195.9 J/correct**, 187.3 tok/s, 695 mJ/token. Q4_0 is cheaper per correct answer by 21% (Q2_K costs 27% more).

**Flagged spreads:** Q4_0 gross J/correct **10.2%** and mJ/token **9.6%**; Q2_K gross J/correct **4.5%** and
mJ/token **6.4%**. Both are power gaps at equal speed (tok/s within 1.3%): pass 1 of each 7B run drew
135 to 140 W where pass 2 drew 125 to 127 W. Pass 1 came from the previous session (11:xx), pass 2 from this
one (13:12 to 13:23). To test whether that was the session, both pass-1 cells were re-run on auto in this
session at 16:00, right after the capped run (note 23) and before the harvest resumed; the re-run rows above
are kept apart and not averaged in. The re-run reproduced pass 1: Q4_0 within 1% (139.8 against
139.6 W, 160.5 against 161.6 J/correct), Q2_K within 3% on power and energy per token
(132.0 against 135.1 W, 741 against 717 mJ/token) with six fewer problems right (206 against
212), which puts its J/correct 6.7% off. So the 10% gap is run order, not the session: pass 2 followed four
32B runs and drew 10% less power at the same speed, and a first 7B run after a change of state (a session
start, or 95 minutes under a clock cap) draws the higher figure. The flag stays. The 7B energy numbers carry
that 10%; the ranking (Q4_0 cheaper by 21%) is far outside it. `results/halo-power-log.csv` logs the
clocks and display state to find which platform state moves.

Raw: `results/lattice-halo-{7b,32b}-{Q4_0,Q2_K-imat}-pass{1,2}.json`, `results/lattice-halo-7b-*-pass1-rerun.json`, `results/lattice-halo-idle-pre.csv`.
Script: `experiments/lattice_halo_finish.sh`. Dataset rows (note 22): `results/spliced-quality.csv`.
