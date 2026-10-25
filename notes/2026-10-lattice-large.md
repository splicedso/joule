# Does 2-bit pay on large models?

**Prediction verdict:** held in direction at both sizes; the 32B margin (16.0%) is outside the "less than 15%" pre-registered.

Spliced research note 22, 25 October 2026. AMD Ryzen AI Max+ 395 (Strix Halo, Radeon 8060S, 128 GB, shared GPU memory 90%), Linux, llama.cpp 620d2225c, Vulkan. Qwen2.5 7B and 32B Instruct.

Note 20 found that on the M5 Pro a calibrated 2-bit 1.5B doubles the accuracy of a plain one but still costs more per correct answer than Q4_0, because a 2-bit token costs more energy there. The reason given was that fewer bits only save energy where moving bytes dominates. Larger models are where they should: the weights read per token grow with the model.

**Prediction** (`docs/predictions.md`, committed before the runs): on the 7B, Q4_0 is still cheaper per correct answer. On the 32B, calibrated Q2_K loses fewer accuracy points than the 1.5B did and costs less energy per token than Q4_0; it wins per correct answer, by less than 15%.

## Method

For each model, an importance matrix from 1,500 GSM8K training problems with their worked answers (note 20's recipe), used to quantize the F16 model to Q2_K; standard Q4_0 for comparison. `experiments/quality.py`, the first 250 GSM8K test questions, 8 requests at once, two passes with the second reversed, chip (APU package) energy with Phase's warm-up, nothing else on the GPU.

## Results

Two passes each, the second in reverse order, means below; every pass and both idle readings are in
`results/lattice-halo.md`, raw JSON in `results/lattice-halo-*-pass{1,2}.json`.

32B:

| format | correct | J per correct | net of idle | tok/s | mJ per token |
|---|---:|---:|---:|---:|---:|
| Q4_0 | 94.8% (237, 237) | 563.6 | 467.7 | 56.3 | 2224 |
| Q2_K, calibrated | 95.6% (240, 238) | 473.7 | 393.6 | 61.2 | 1992 |

7B:

| format | correct | J per correct | net of idle | tok/s | mJ per token |
|---|---:|---:|---:|---:|---:|
| Q4_0 | 88.6% (220, 223) | 153.8 | 131.2 | 225.9 | 589 |
| Q2_K, calibrated | 84.2% (212, 209) | 195.9 | 160.7 | 187.3 | 695 |

Spread: the 32B cells repeat to within 2.8% on J per correct (Q4_0's mJ per token differs by 3.3%
between passes, flagged). The 7B cells do not: pass 1 ran in the previous session and drew 10% more
power than pass 2 at the same speed, so Q4_0's J per correct differs by 10.2% between passes and
Q2_K's by 4.5%, both flagged. The 7B ranking is far outside that gap. Idle drifted 16.6 to 25.9 W
over the afternoon; the chip totals do not depend on it. Each 32B run took 15 to 18 minutes.

## What to take from this

1. **On the 32B, calibrated 2-bit pays.** 473.7 against 563.6 J per correct answer, 16.0% less, at
   equal accuracy (95.6% against 94.8%, two problems apart) and 9% more tokens per second. The 2-bit
   token costs 10% less energy than the 4-bit one here (1992 against 2224 mJ). The prediction's
   direction held; its margin did not: 16.0% on the two-pass mean (17.9% and 14.0% per pass) is outside
   the "less than 15%" written down beforehand.
2. **On the 7B, Q4_0 still wins on every axis:** 4.4 points more accurate, 27% less energy per correct
   answer, 21% faster. The 7B half of the prediction held, as it did on the 1.5B (note 20).
3. The crossover is between 7B and 32B on this machine. At 7B a 2-bit token costs 18% more chip energy
   than a 4-bit one; at 32B, which reads four times the bytes per token, it costs 10% less. Fewer bits
   pay once memory traffic dominates the token, and not before.
4. Calibration holds accuracy at both sizes: 84.2% against 88.6% at 7B, and no loss at 32B. The 1.5B
   lost 24 points (note 20). Larger models quantize more gracefully, as predicted.

## Limits

One task, one machine, chip (package) energy. Calibration on GSM8K's training split matches the test's domain; note 20 measured how much that adds on the 1.5B.
