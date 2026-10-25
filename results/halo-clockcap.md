# Clock cap on Strix Halo: capping the shader clock cuts 7B decode energy 37 to 42% at 4 to 8% less speed

**Verdict on the pre-registered prediction (`docs/predictions.md`, 12:20 PT):** direction held on decode,
magnitude underestimated; prefill missed. Predicted a 10 to 25% decode saving at a 1,200 to 1,800 MHz cap with
under 20% speed loss: measured **37 to 42% less energy per token at 4 to 8% less speed**. Predicted prefill
energy within 10% of auto: measured **33 to 38% less**. Predicted `force=low` would cost more energy per token
than auto: measured flat on the mean (+8% in pass 1, -7% in pass 2, spread flagged), at a fifth of the speed.

Strix Halo (gfx1151, shared GPU memory 90%), llama.cpp 620d2225c Vulkan, Qwen2.5 7B Q4_0, `phase` with
prefill 512, decode 128, 20 s timed windows, warm-up on, 10 s idle baseline inside every run. Two passes, the
second in reverse order. One model alone on the GPU, machine otherwise quiet; it ran 13:47 to 14:06 PDT,
between the Lattice D runs (PR #17, measured on auto before this) and the Trace harvest. The clock was
restored to auto and the OD table reset at the end; readback in `results/halo-clockcap-readback.txt`.
No Lattice number was measured under a cap.

## Which controls cap the clock (verified under a decode load before measuring)

| control | active max MHz under load | capped? |
|---|---:|---|
| `power_dpm_force_performance_level=low` | 719 | yes |
| `=manual` + `pp_dpm_sclk` level mask | 2900 | no (write rejected: Invalid argument, as v1 found) |
| `=manual` + OD table `s 1 1200`, `c` | 1200 | yes |
| `=manual` + OD table `s 1 1800`, `c` | 1800 | yes |

The OD table is the control that works on gfx1151. The `pp_dpm_sclk` write after the OD commit also returned
Invalid argument and was not needed; the cap held from the OD table alone, and the active clock sampled during
every measurement stayed at the cap (`results/halo-clockcap-diag.txt`).

## Results, every pass

| cap | pass | idle W | decode tok/s | decode W | decode mJ/tok | prefill tok/s | prefill W | prefill mJ/tok |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| auto (2900) | 1 | 12.5 | 50.5 | 110.0 | 2176 | 1542 | 141.2 | 91.5 |
| auto (2900) | 2 | 11.1 | 50.7 | 114.6 | 2261 | 1550 | 140.1 | 90.4 |
| OD 1800 | 1 | 12.2 | 48.8 | 67.6 | 1386 | 1039 | 58.8 | 56.6 |
| OD 1800 | 2 | 12.4 | 48.8 | 67.8 | 1390 | 1043 | 58.7 | 56.3 |
| OD 1200 | 1 | 11.2 | 46.3 | 59.0 | 1272 | 724 | 44.2 | 61.1 |
| OD 1200 | 2 | 11.8 | 46.4 | 59.8 | 1289 | 724 | 44.5 | 61.4 |
| force low (~700) | 1 | 11.0 | 10.7 | 25.1 | 2344 | 351 | 26.8 | 76.4 |
| force low (~700) | 2 | 13.5 | 10.7 | 22.7 | 2112 | 351 | 26.0 | 74.2 |

## Two-pass means against auto

| cap | decode mJ/tok | vs auto | decode tok/s | vs auto | prefill mJ/tok | vs auto | prefill tok/s | vs auto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| auto | 2219 | | 50.6 | | 91.0 | | 1546 | |
| OD 1800 | 1388 | **-37%** | 48.8 | -4% | 56.4 | -38% | 1041 | -33% |
| OD 1200 | 1281 | **-42%** | 46.4 | -8% | 61.2 | -33% | 724 | -53% |
| force low | 2228 | +0% | 10.7 | -79% | 75.3 | -17% | 351 | -77% |

Spread flagged (over 3% pass to pass): auto decode mJ/tok **3.8%** (110.0 vs 114.6 W at the same speed);
force-low decode mJ/tok **10.4%** (25.1 vs 22.7 W; at 23 W the idle floor of 11 to 13 W is half the reading,
so a 2 W drift is 10%). The capped cells repeat to within 1.3% on everything.

## What to take from this

1. **The 7B decode is memory-bound, and the clock pays for nothing it does not need.** At 1,800 MHz the
   package draws 68 W instead of 112 W for 96% of the tokens per second: 37% less energy per token. At
   1,200 MHz, 42% less at 92% of the speed. The prediction had the direction and badly underestimated the
   size.
2. **Prefill also gets cheaper, which was not predicted.** Energy per token falls 33 to 38% while speed falls
   with the clock (-33% at 1,800, -53% at 1,200). Power falls faster than the clock: 141 W at 2,900 MHz, 59 W
   at 1,800, 44 W at 1,200. The top of the voltage-frequency curve is expensive on this package.
3. **600 to 700 MHz is too low.** Decode drops to 10.7 tok/s and energy per token returns to auto's level,
   because at 23 W the package's floor dominates. The predicted "rises above auto" did not show on the mean.
4. For Foundry on this class of machine, an 1,800 MHz cap is close to free on decode speed and cuts chip
   energy by over a third. The joules-per-correct-answer bar (`experiments/quality.py`) has not been run
   under a cap yet; that is the next measurement, with the same two-pass rule.

## Limits

One model, one machine, chip (package) energy, batch 1, 20 s windows. The cap needs root to set; on a
laptop the equivalent is the firmware's power mode, which was not measured. Whether the saving holds at
8 slots, on the 32B, and on the quality harness is untested here.

Raw: `results/halo-clockcap-{auto,od_1800,od_1200,force_low}-pass{1,2}.json`, `results/halo-clockcap-diag.txt`,
`results/halo-clockcap-readback.txt`, `results/halo-clockcap-original.json` (sysfs before the sweep).
Script: `experiments/halo_clockcap.sh`.
