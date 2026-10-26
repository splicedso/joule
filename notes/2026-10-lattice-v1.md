# Two-bit training took a model from 66% to 24%, and two controls say why

**Prediction verdict:** missed. Lattice v1 was predicted to reach 52% on the maths test at 2-bit size; it reached 23.8%, against a bar of 60%. Two controls, each committed before it ran, split the loss between the training data and the 2-bit grid.

Spliced research note 27, 26 October 2026. AMD Ryzen AI Max+ 395 (Strix Halo, Radeon 8060S, 128 GB, shared GPU memory 90%), Linux, llama.cpp 620d2225c, Vulkan; training in PyTorch 2.10 on ROCm 7.2. Qwen2.5 1.5B Instruct.

Note 20 found that calibrating a 2-bit model on maths problems doubles its accuracy, from 21% to 42%, while Q4_0 scores 66%. Lattice v1 asked whether training the model to live on a 2-bit grid closes the rest of the gap. The method is quantization-aware fine-tuning. Every linear layer in the model's blocks is rounded to 4 levels per group of 16 weights in each forward pass, and the model learns around the rounding. The training was one epoch of GSM8K's training problems with their worked answers, plus 30% general text.

## Results

GSM8K, 250 test problems, 8 requests at once, two passes:

| model | accuracy | tokens per answer | what the step shows |
|---|---:|---:|---|
| stock, Q4_0 | 65.6% | 248 | |
| fine-tuned, no grid, full precision | 48.8% | 95 | the training data: 17 points |
| the same, Q4_0 | 46.0% | 95 | 4-bit rounding: 3 points |
| fine-tuned on the 2-bit grid, stored at Q4_0 | 25.4% | 86 | the grid during training: 21 points |
| the same, stored as Q2_K | 23.8% | 85 | the export: 2 points |

## 1. The data cost 17 points before any bits were removed

The plain control is the same run with the grid switched off: same data, steps, learning rate, schedule and seed. It lost 17 points at full precision. GSM8K's worked answers are a third the length of the model's own reasoning, 95 tokens against 248, and a 1.5B model taught to reason in fewer words reasons worse. A first control, the 2-bit weights stored at 4 bits, could not show this. It separated the export from the training, not the grid from the data.

## 2. The grid cost 21 more

The grid squeezed every linear layer to 2 bits. llama.cpp's Q2_K, the file the model ships as, keeps some tensors at 3 to 6 bits. And one epoch of 7,273 problems is far less text than 2-bit training usually needs. Either may explain the 21 points; neither was tested.

## 3. On a 1.5B, fewer bits do not pay even at equal accuracy

The two files trained on the grid write answers of the same length. At 8 requests at once, the 4-bit one costs 13.5% less per correct answer than the 2-bit one: 71.2 against 82.4 joules. A 2-bit token costs more chip energy than a 4-bit one on this machine, 231 against 211 millijoules, because unpacking it takes more work than the bytes it saves. Notes 20 and 22 found the same at this size on both machines. Two-bit paid only at 32B (note 22), where reading the weights dominates the cost of a token.

So Lattice's energy bar, cheaper per correct answer than Q4_0, cannot be met by a 1.5B model on these machines at any accuracy.

## 4. Shorter answers are a bigger lever than bits

The plain fine-tuned model at Q4_0 costs 35% less per correct answer than the stock one, 43.5 against 66.9 joules, because its answers are 2.6 times shorter. It is also 20 points less accurate, so it is not a better model. But no format change measured so far has moved joules per correct answer by a third.

## What this changes

- Lattice moves to where fewer bits pay: models of 32B and up, where note 22 found a calibrated 2-bit file 16% cheaper per correct answer than Q4_0 at equal accuracy. The next step needs no training. It compares 2-bit and 3-bit recipes at 32B.
- Training a small model on short reference answers is a trap. A future fine-tune should train on the model's own answers, keeping the ones that are right.

## Limits

- One model, one task, one epoch, one learning rate. The 21 points the grid cost are an upper bound for this recipe, not for 2-bit training in general.
- The two controls ran in separate windows three hours apart; stock Q4_0 was re-run only in the first.
- Chip (package) energy, not the wall.

## Reproduce

On the Strix Halo, with the environment in `docs/handoff-linux.md`:

```bash
sh experiments/lattice_qat.sh     # train on the grid, export Q2_K and Q4_0, quality runs
sh experiments/lattice_plain.sh   # the same with QUANT=0, export F16 and Q4_0, quality runs
```

Raw: `results/lattice-halo-1.5b-*-s{1,8}-pass{1,2}.json`, `results/lattice/train-log-1.5b-{qat,plain}.json`, `results/lattice-qat-smoke-quantcheck.json`, and the full write-up with every pass, `results/lattice-v1.md`.
