# Does 2-bit pay on large models?

Spliced research note 22, 25 October 2026. AMD Ryzen AI Max+ 395 (Strix Halo, Radeon 8060S, 128 GB, shared GPU memory 90%), Linux, llama.cpp 620d2225c, Vulkan. Qwen2.5 7B and 32B Instruct.

Note 20 found that on the M5 Pro a calibrated 2-bit 1.5B doubles the accuracy of a plain one but still costs more per correct answer than Q4_0, because a 2-bit token costs more energy there. The reason given was that fewer bits only save energy where moving bytes dominates. Larger models are where they should: the weights read per token grow with the model.

**Prediction** (`docs/predictions.md`, committed before the runs): on the 7B, Q4_0 is still cheaper per correct answer. On the 32B, calibrated Q2_K loses fewer accuracy points than the 1.5B did and costs less energy per token than Q4_0; it wins per correct answer, by less than 15%.

## Method

For each model, an importance matrix from 1,500 GSM8K training problems with their worked answers (note 20's recipe), used to quantize the F16 model to Q2_K; standard Q4_0 for comparison. `experiments/quality.py`, the first 250 GSM8K test questions, 8 requests at once, two passes with the second reversed, chip (APU package) energy with Phase's warm-up, nothing else on the GPU.

## Results

7B, pass 1 (pass 2 confirming):

| format | correct | J per correct | net of idle | tok/s | mJ per token |
|---|---:|---:|---:|---:|---:|
| Q4_0 | 88.0% (220/250) | 161.6 | 141.8 | 226 | 617 |
| Q2_K, calibrated | 84.8% (212/250) | 200.3 | 166.3 | 189 | 717 |

32B: PENDING.

## What to take from this

1. On the 7B, Q4_0 wins on every axis: 3.2 points more accurate, 19% less energy per correct answer, 20% faster. The 7B half of the prediction held.
2. Calibration keeps the 7B's 2-bit model close to its 4-bit one (84.8% against 88.0%), far closer than the 1.5B managed (42% against 66%). Larger models quantize more gracefully, as predicted.
3. The 2-bit token still costs 16% more chip energy than the 4-bit one. On this machine, fewer bits read do not pay for the extra work of unpacking them at 7B. Whether the 32B, which reads four times the bytes per token, flips this is the open question.

## Limits

One task, one machine, chip (package) energy. Calibration on GSM8K's training split matches the test's domain; note 20 measured how much that adds on the 1.5B.
