# Faster is not cheaper: the energy of speculative decoding

Spliced research note 7, 24 October 2026. Apple M5 Pro, 24 GB, llama.cpp build 11669. Target Qwen2.5 7B Q4_0, draft Qwen2.5 0.5B Q4_0.

Speculative decoding is in every serious serving stack. A small draft model guesses the next k tokens; the large model checks all k in one forward pass and keeps the ones it agrees with. Decode is memory bound (note 2), so checking k tokens costs about as many weight reads as generating one, and every accepted guess is a token the large model did not have to produce alone. It is sold, and measured, as a latency win. Whether it saves energy is a separate question: the draft model's work costs energy, and so does the large model's work on every guess it throws away.

## Method

`experiments/speculative.py`. Greedy decoding, a fixed 384 generated tokens, 7B Q4_0 target. Six strategies:

- **plain**: no speculation (`llama-completion`).
- **draft-k**: the 0.5B model drafts k = 2, 4, 8 or 16 tokens per step (`llama-speculative-simple`).
- **ngram**: no draft model. Guesses are copied from n-grams already in the context.

Three prompts: write new code, write prose, and edit code given in the prompt (rewrite an 831-token Python file with type hints, so most of the output repeats the input). Each strategy and prompt ran three times, in a shuffled order each time. Every condition repeated within 5% on chip energy.

**What we did not use, and why.** The board reading is smoothed by about a second. The faster strategies finish in 1.5 to 4 seconds, so their windows include more of the sensor's lag from idle, and they read low. The bias grows with exactly the thing being compared, so it would flatter speculation. The fastest run reads the same board energy as chip energy, which is impossible. This note uses chip energy only. A slow sensor on a short window is a confound, not noise.

## Results

Chip millijoules per generated token, mean of three runs, and the ratio to plain decoding:

| prompt | strategy | tokens/s | accepted | chip mJ/tok | vs plain |
|---|---|---:|---:|---:|---:|
| code | plain | 62.0 | | 362.5 | 1.00 |
| code | draft-2 | 90.9 | 78% | 383.5 | 1.06 |
| code | draft-4 | 107.0 | 68% | 302.0 | 0.83 |
| code | draft-8 | 81.8 | 51% | 379.9 | 1.05 |
| code | draft-16 | 45.3 | 31% | 778.8 | 2.15 |
| code | ngram | 59.7 | 4% | 390.4 | 1.08 |
| prose | plain | 62.1 | | 360.4 | 1.00 |
| prose | draft-2 | 78.8 | 60% | 447.5 | 1.24 |
| prose | draft-4 | 81.4 | 45% | 397.7 | 1.10 |
| prose | draft-8 | 52.1 | 28% | 611.1 | 1.70 |
| prose | draft-16 | 24.6 | 14% | 1422.1 | 3.95 |
| prose | ngram | 60.8 | | 366.9 | 1.02 |
| edit | plain | 61.0 | | 368.0 | 1.00 |
| edit | draft-2 | 102.7 | 98% | 339.3 | 0.92 |
| edit | draft-4 | 137.8 | 99% | 234.6 | 0.64 |
| edit | draft-8 | 137.0 | 97% | 228.3 | 0.62 |
| edit | draft-16 | 116.4 | 94% | 297.9 | 0.81 |
| edit | ngram | 290.2 | 100% | 119.5 | 0.32 |

<!-- chart:spec -->

## 1. Faster and cheaper are different questions

On code, drafting 2 tokens is 1.47 times faster than plain decoding and costs 6% more energy per token. On prose, drafting 2 is 1.27 times faster and costs 24% more. A benchmark that reports only tokens per second would call both a win.

The reason is in what each guess costs. A rejected guess still cost a draft-model forward pass and a slot in the large model's verification batch. Verification of k tokens is cheap in memory traffic but not free in arithmetic, and on this hardware (note 5) arithmetic shows up as power, not time. So speculation can hide its extra work behind the memory wait and finish sooner while drawing more power the whole time.

## 2. It saves energy only when guesses are good

Every strategy that saved energy had high acceptance: 68% for draft-4 on code (17% saved), 97% to 99% for drafts of 4 and 8 on the edit task (36% to 38% saved). Every strategy below about 60% acceptance cost more energy than plain decoding, however much faster it ran.

High acceptance is necessary but not enough. Draft-2 on code was accepted 78% of the time and still cost 6% more than plain decoding. With only two tokens per step, the fixed cost of each draft-and-verify round, a draft forward pass and a verification pass, is spread over at most three tokens. Draft-4 on the same prompt, with lower acceptance, spread it over more and saved 17%.

## 3. Draft length has an optimum, and long drafts are dangerous

The number of tokens to draft is a bet on how predictable the text is. On the edit task acceptance stays near 100% and drafts of 4 to 8 are best. On prose, acceptance falls from 60% at 2 tokens to 14% at 16, and drafting 16 costs 3.95 times the energy of plain decoding while running at less than half its speed. A fixed draft length tuned on predictable text is a large energy penalty on unpredictable text.

## 4. Copying beats a draft model when the answer is in the prompt

The n-gram strategy has no draft model: it guesses by copying what already appears in the context. On new code and prose there is nothing to copy (4% acceptance or none) and it costs within 8% of plain decoding. On the edit task it is accepted 100% of the time and runs at 290 tokens per second, 4.7 times plain, at **32% of plain's energy**: the best result here by a wide margin, for no extra model. Edits, refactors, retrieval answers that quote their sources and structured rewrites all have this shape.

## What to take from this

1. Report energy and speed separately. Speculative decoding can make decode faster and more expensive at once.
2. Acceptance rate decides the energy outcome. Below about 60% on this hardware, speculation cost energy in every case measured.
3. The best strategy depends on the task: copy-based drafting for edits, a short draft model for code, little or no speculation for open-ended prose.
4. Sensor lag is a confound when the conditions you compare run for different lengths of time. Check that the measurement's error is not correlated with the variable you are studying.

## Limits

One machine, one target and draft pair, greedy decoding, three prompts. Chip energy only, for the reason above; whole-machine energy will favour the faster strategies more, since the rest of the board draws power for as long as a token takes, and needs a faster sensor to measure honestly. Acceptance with sampling at higher temperature will be lower than with greedy decoding.

## Reproduce

```bash
uv run python experiments/speculative.py results/speculative-7b.json
```

Raw results: `results/speculative-7b.json`, `results/summary-speculative.json`. The edit input is `experiments/speculative_edit_input.py`.
