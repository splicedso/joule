# Calibration doubles 2-bit accuracy, and 4-bit is still cheaper per answer

Spliced research note 20, 25 October 2026. Apple M5 Pro, 24 GB, Metal. llama.cpp (Homebrew build) llama-imatrix, llama-quantize and llama-server. Qwen2.5 1.5B Instruct, from the F16 GGUF.

Lattice is our line of models that keep their answers at fewer bits. Its starting point (`docs/program.md`): standard 2-bit quantization (Q2_K) drops the 1.5B from 66% to 21% on GSM8K. Before training anything, the cheapest fix is an importance matrix: llama.cpp measures which weights matter on sample text and spends its bits there.

**Prediction.** A calibrated Q2_K recovers a large share of the lost accuracy at an unchanged file size, and costs less per correct answer than standard Q2_K, but not less than Q4_0.

## Method

Two importance matrices from the F16 model, 200 chunks each. One from 1,500 GSM8K training problems with their worked answers (the test set is separate), one from 1,500 general chat and code prompts with answers (the drafter set, note 15). Each was used to quantize the same F16 model to Q2_K; a plain Q2_K is the control. All three files are 753 MB. Then `experiments/quality.py` ran the first 250 GSM8K test questions, 8 at a time, two passes with the second reversed, with chip energy sampled over each run, against standard Q4_0 for reference. Passes agreed within 3.5% on joules per correct answer, except the maths-calibrated file at 5.5%, whose second pass overlapped other work on the machine.

## Results

| model | size | accuracy | J per correct answer | mJ per token |
|---|---:|---:|---:|---:|
| Q2_K, standard | 753 MB | 21.0% | 39.3 | 46.1 |
| Q2_K, calibrated on general text | 753 MB | 37.2% | 28.4 | 43.2 |
| Q2_K, calibrated on maths | 753 MB | 42.4% | 23.8 | 44.2 |
| Q4_0, standard | 1.07 GB | 65.8% | 14.8 | 39.1 |

The other imatrix formats near this size did worse on the same test: IQ2_M 20.0% and IQ3_XXS 33.2%, both calibrated on maths (one pass, accuracy only).

## 1. Calibration doubles 2-bit accuracy

At the same file size, a maths-calibrated Q2_K answers 42.4% of the questions against 21.0% for the standard one: twice as many. Most of that is calibration itself rather than the topic: calibrating on general chat and code reaches 37.2%. So 16 of the 21 points come from calibrating at all, and 5 from calibrating on the task.

## 2. 4-bit is still cheaper per correct answer

The calibrated 2-bit costs 40% less per correct answer than the standard one, because it gets more right. But Q4_0 is cheaper still, 14.8 J against 23.8, and the reason is in the last column: on this machine a 2-bit token costs more energy than a 4-bit one (44 against 39 mJ). Unpacking the 2-bit format costs more than the bytes it saves, as note 1 found for the formats generally. Fewer bits only saves energy where moving bytes dominates: larger models, memory-bound hardware.

## What to take from this

1. Calibrate any 2-bit model. It is free at quantization time and doubled accuracy here.
2. On a laptop-class GPU with a 1.5B model, 2-bit does not save energy per answer. Q4_0 wins on both accuracy and energy.
3. Lattice's energy case has to be made on larger models where memory is the bottleneck. That is the next test, on the 125 GB Strix Halo, along with quantization-aware training (Lattice v1).

## Limits

One model, one task (GSM8K, first 250 questions, greedy), one machine, chip energy only. The Homebrew llama.cpp build differs from the pinned build of earlier notes; all four files here were quantized and served by the same build. Calibration on the GSM8K training split matches the test's domain; the general-text control shows how much that matters.

## Reproduce

```
llama-imatrix -m models/quant/1.5b-F16.gguf -f data/lattice-calib.txt -o data/imatrix-1.5b-gsm8k.gguf --chunks 200 -ngl 99
llama-quantize --imatrix data/imatrix-1.5b-gsm8k.gguf models/quant/1.5b-F16.gguf models/lattice/1.5b-Q2_K-imat.gguf Q2_K
uv run python experiments/quality.py models/lattice/1.5b-Q2_K-imat.gguf results/lattice-v0-energy-1.5b-Q2_K-imat-run1.json 250 8
```

The calibration texts are the first 1,500 rows of GSM8K's train.jsonl (question and answer) and of `results/drafter/train-answers.jsonl` (prompt and answer). The two importance matrices are committed in `results/lattice/`, so anyone can quantize the same files. Raw results: `results/lattice-v0-*.json`, `results/lattice-mac-*.json`.
