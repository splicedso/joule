# Smaller files, slower tokens

**Prediction verdict:** the central claim held. Calibrated Q2_K is still the cheapest format per correct answer for a 32B model, 12.9% under Q4_0. But seven of twelve clauses missed, mostly on how badly the IQ formats did. Calibrated Q3_K_M, which a disturbed first run made look expensive, matches Q4_0 at 85% of the bytes.

Spliced research note 34, 27 October 2026. AMD Ryzen AI Max+ 395 (Strix Halo, RAH-001), 128 GB, Linux, llama.cpp 620d2225c on Vulkan. Qwen2.5 32B Instruct (Apache-2.0).

Note 22 found that at 32B a calibrated 2-bit file (Q2_K) costs less per correct answer than Q4_0, the reverse of every smaller model. llama.cpp has other low-bit formats, the IQ family, that pack weights tighter still. This note asks whether any of them, or a 3-bit format, beats Q2_K.

**Prediction** (`docs/predictions.md`, 26 October 11:04, before any file was built): Q3_K_M and IQ3_XXS within a point of Q4_0, Q2_K and IQ2_M within 2, IQ2_XS 2 to 6 points below; the IQ formats no cheaper per token than Q2_K, because they cost more to unpack; Q3_K_M between Q2_K and Q4_0; answer length the same within 5%; Q2_K cheapest per correct answer, within 5% of second, and nothing beating note 22's 473.7 J by more than 5%.

## Method

Five formats quantized from the same F16 with note 22's GSM8K importance matrix, against stock Q4_0. GSM8K, 250 problems, eight requests at once, automatic clocks, two passes in mirrored order, package power for energy (`experiments/lattice32_formats.sh`, 26 October).

Part of that run was spoiled. From 12:51 to 14:42 another job shared the GPU, found afterwards in the power log. The cells it touched were void for energy, so they ran again on 27 October behind a gate that waits until no other job is on the GPU (`experiments/lattice32_rerun.sh`), with Q4_0 re-run as an anchor. The anchor reproduced to within 1%. The table uses only clean cells.

## Results

| format | file | accuracy | tokens per second | J per correct | against Q4_0 |
|---|---:|---:|---:|---:|---:|
| Q4_0, stock | 18.6 GB | 95.6% | 55.6 | 555.7 | |
| Q2_K, calibrated | 12.3 GB | 96.0% | 60.0 | 484.1 | -12.9% |
| Q3_K_M, calibrated | 15.9 GB | 96.0% | 54.4 | 563.8 | +1.5% |
| IQ2_XS, calibrated | 10.0 GB | 92.8% | 44.6 | 628.3 | +13.1% |
| IQ2_M, calibrated | 11.3 GB | 89.8% | 32.4 | 925.4 | +66.5% |
| IQ3_XXS, calibrated | 12.8 GB | 90.0% | 32.8 | 931.6 | +67.7% |

**Speed sets the order.** Every format drew 118 to 124 W while decoding, so energy per token is just the inverse of speed. Speed did not follow file size. The smallest file, IQ2_XS, decoded at 80% of Q4_0's rate, and IQ2_M and IQ3_XXS at 58 to 59%. The work of unpacking those formats on this GPU outweighs the bytes they save. Q2_K is the one format that is both smaller and faster than Q4_0.

**Q3_K_M is the safe middle.** It matched Q4_0 on accuracy, answer length and energy, 2% slower, in a file 3 GB smaller. In the spoiled run it had looked 1.7 to 2.5 times dearer; all of that was the other job. When Q4_0 does not fit and a 2-bit loss is not wanted, Q3_K_M is the format to take.

**The IQ formats lose accuracy too.** IQ2_M and IQ3_XXS scored 5.6 and 5.8 points below Q4_0, outside the predicted band, and the 3-bit IQ3_XXS scored below the 2-bit IQ2_XS. On this model and importance matrix, more bits in the IQ family did not mean better answers.

**The IQ speeds are not firm.** In the re-run, IQ2_XS and IQ3_XXS ran 13% and 8% faster in their later pass at the same accuracy, power and shader clock, and IQ2_M's two passes on 26 October differed by 14% in energy. A clock log during the re-run ruled out the GPU core and could not read the memory-side clocks well enough to say more. Treat each IQ figure as ±10%; the Q-format passes agree within 1.5%.

## Verdicts

- Accuracy: Q3_K_M, Q2_K and IQ2_XS **held**; IQ3_XXS and IQ2_M **missed** (5.6 and 5.8 points under Q4_0).
- The IQ formats no cheaper per token than Q2_K, within 5%: **missed**. They were 35 to 79% dearer, worse than predicted.
- Q3_K_M between Q2_K and Q4_0: **missed** (1.5% over Q4_0).
- Answer length within 5%: **missed** (IQ2_XS answered 12.5% shorter; two of five formats inside 5%).
- Q2_K cheapest per correct answer: **held**. Within 5% of second: **missed** (12.9% ahead). Nothing beats 473.7 J by 5%: **held**.
- The ranking is set by speed, not file size: **held**.

## What this means for the box

For a 32B model on this machine, use calibrated Q2_K, or Q3_K_M where a 2-bit file costs too much accuracy for the task. Avoid the IQ formats on this Vulkan build. The ranking belongs to this build's unpacking code: a ROCm build or a later llama.cpp could reorder the IQ formats, so the comparison is worth repeating when the box's software changes.

## Limits

- One task (GSM8K), one model, one importance matrix, one llama.cpp build.
- Package energy, not the wall.
- The spoiled cells were found after the fact. The gate that stops that from happening again (`experiments/gpu_gate.sh`) came from this run.
- Full per-cell table, both runs and the clock log: `results/lattice32-halo.md`.
