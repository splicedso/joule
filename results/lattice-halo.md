# Lattice on Strix Halo: does calibrated 2-bit pay on larger models? (partial)

Prediction (Mac note 20): a GSM8K-calibrated Q2_K recovers most of 2-bit's accuracy but still
costs more energy per correct answer than Q4_0, until the model is large and memory-bound enough
that saving bytes wins. This machine tests the size question on Qwen2.5 7B and 32B.

GSM8K-250, slots 8, chip energy, GSM8K-calibrated Q2_K (imatrix from 1,500 train problems, 200
chunks) against Q4_0. Shared GPU memory 90% (113 GiB). **Partial: the session stopped at noon PT
with only the 7B pair (pass 1) landed; the 32B comparison did not finish.**

## 7B (pass 1)

| format | accuracy | J / correct | tok/s | mJ / token |
|---|---:|---:|---:|---:|
| Q4_0 | 88.0% (220/250) | 161.6 | 226.2 | 617 |
| Q2_K, GSM8K-calibrated | 84.8% (212/250) | 200.3 | 188.5 | 717 |

At 7B, Q4_0 wins on every axis. Calibration does its job (84.8%, where an uncalibrated Q2_K would
be ~21%), but a 2-bit token still costs more energy than a 4-bit one here (717 vs 617 mJ/token) and
runs slower, so Q4_0 is cheaper per correct answer. Note 20's finding holds at 7B.

## 32B

Did not complete before the stop. This is the case that matters: the 32B is far more memory-bound,
so it is where fewer bits could finally start paying per correct answer. Running it is the first
task next session (`experiments/lattice_32b.sh`). imatrices are committed in `results/lattice/`.

Raw: `results/lattice-halo-7b-*.json`.
