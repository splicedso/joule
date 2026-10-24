# One flag fixes speculative decoding's energy problem

Spliced research note 9, 24 October 2026. Apple M5 Pro, 24 GB, llama.cpp build 11669. Target Qwen2.5 7B Q4_0, draft Qwen2.5 0.5B Q4_0.

Note 7 found that speculative decoding can make decoding faster and more expensive at once, and that long drafts on unpredictable text are an energy disaster: drafting 16 tokens on prose cost 3.95 times the energy of plain decoding. The cause is wasted guesses. llama.cpp already has a control for that: `--spec-draft-p-min`, a confidence threshold. The draft model stops guessing as soon as its confidence in its next token falls below the threshold, so it drafts long runs where text is predictable and short ones where it is not. This note asks whether that one setting removes the penalty, and what value to use.

## Method

As in note 7 (`experiments/speculative.py`), with the conditions given on the command line: plain decoding; drafts of up to 8 tokens with no threshold and with thresholds of 0.5, 0.8 and 0.95; drafts of up to 16 with no threshold and with 0.8. Code, prose and edit prompts, 384 generated tokens, greedy, three runs each in a shuffled order. Chip energy only, for the reason note 7 gives.

Plain decoding cost 394 to 404 mJ per token in this run, 9% to 11% more than in note 7. Since both notes were run on the same machine with the same settings, the difference is a property of the session (temperature, background load), and so every comparison here is against plain decoding **within this run**. Most conditions repeated within 10%; a few threshold conditions varied by up to 23%, and those spreads are reported.

## Results

Chip energy per generated token relative to plain decoding (below 1 saves energy), with the speed-up:

| prompt | strategy | accepted | speed | energy vs plain | spread |
|---|---|---:|---:|---:|---:|
| code | draft-8 | 51% | 1.32x | 1.03 | 1% |
| code | draft-8, p 0.5 | 71% | 1.57x | **0.84** | 6% |
| code | draft-8, p 0.8 | 95% | 1.52x | 0.85 | 3% |
| code | draft-8, p 0.95 | 100% | 1.25x | 1.03 | 13% |
| code | draft-16 | 31% | 0.74x | 2.05 | 1% |
| code | draft-16, p 0.8 | 93% | 1.50x | 0.88 | 17% |
| prose | draft-8 | 28% | 0.86x | 1.59 | 1% |
| prose | draft-8, p 0.5 | 68% | 1.30x | **0.99** | 6% |
| prose | draft-8, p 0.8 | 92% | 1.08x | 1.11 | 16% |
| prose | draft-8, p 0.95 | 98% | 0.95x | 1.20 | 23% |
| prose | draft-16 | 14% | 0.40x | 3.69 | 8% |
| prose | draft-16, p 0.8 | 92% | 1.08x | 1.09 | 19% |
| edit | draft-8 | 97% | 2.24x | 0.60 | 2% |
| edit | draft-8, p 0.5 | 97% | 2.24x | **0.61** | 10% |
| edit | draft-8, p 0.8 | 98% | 2.24x | 0.60 | 6% |
| edit | draft-8, p 0.95 | 98% | 2.15x | 0.62 | 14% |
| edit | draft-16 | 94% | 1.90x | 0.82 | 20% |
| edit | draft-16, p 0.8 | 95% | 2.01x | 0.73 | 3% |

<!-- chart:pmin -->

## 1. The threshold removes the penalty

Without a threshold, drafting 16 tokens cost 2.05 times plain decoding's energy on code and 3.69 times on prose. With a threshold of 0.8 the same drafts cost 0.88 and 1.09 times, and ran 1.5 and 1.08 times faster instead of slower. The draft model stops when it is unsure, so the large model no longer wastes work verifying guesses that were never likely to survive. Acceptance rises from 14% to 92% on prose for the same reason.

## 2. A low threshold is the best one tested

A threshold of 0.5 gave the best result on every prompt, or tied for it:

- **code**: 16% less energy at 1.57 times the speed (against 3% more energy with no threshold).
- **prose**: the same energy as plain decoding at 1.30 times the speed. Speculation on prose, which cost 59% more energy with no threshold, becomes a free speed-up.
- **edit**: 39% less energy at 2.24 times the speed, the same as with no threshold. Where the text is predictable the threshold rarely stops a draft, so it costs nothing.

## 3. Too strict a threshold gives the savings back

At 0.95 the draft model stops almost immediately, so drafts are short and nearly always right (98% to 100% accepted), but each round of drafting and verifying now produces few tokens, and its fixed cost is spread thin. Code returned to 3% more energy than plain decoding and prose to 20% more, at 0.95 to 1.25 times the speed. Acceptance rate alone is the wrong target: what matters is accepted tokens per round.

## What to take from this

1. If you run speculative decoding, set a draft confidence threshold. In llama.cpp that is `--spec-draft-p-min`; around 0.5 was best here. Without it, a draft length tuned on predictable text costs up to 3.7 times the energy on unpredictable text.
2. With the threshold, speculation stopped costing energy on every task measured, and became a pure speed-up on prose.
3. Optimize accepted tokens per draft round, not acceptance rate. A very confident drafter is right almost every time and still wastes energy.

## Limits

One machine, one model pair, greedy decoding, three prompts, three thresholds. 0.5 was the lowest threshold in the first run; the addendum tries lower ones. Some threshold conditions varied by up to 23% between runs, more than the untreated conditions; the conclusions above hold within those spreads, but the exact percentages should be read as approximate. Chip energy only.

## Addendum: thresholds below 0.5

0.5 was the lowest threshold in the first run, so a lower one might have done better. A second run (`results/speculative-pmin-low-7b.json`) tried 0.1, 0.2 and 0.3, with 0.5 repeated in the same session for comparison.

| prompt | strategy | accepted | speed | energy vs plain |
|---|---|---:|---:|---:|
| prose | draft-8, p 0.1 | 28% | 0.86x | 1.63 |
| prose | draft-8, p 0.2 | 30% | 0.90x | 1.65 |
| prose | draft-8, p 0.3 | 39% | 1.07x | 1.35 |
| prose | draft-8, p 0.5 | 68% | 1.30x | **1.01** |
| prose | draft-16, p 0.5 | 62% | 1.26x | 1.09 |
| edit | draft-8, p 0.1 to 0.5 | 97% | 2.25x to 2.29x | 0.59 to 0.61 |
| edit | draft-16, p 0.5 | 94% | 1.90x | 0.80 |

**Lower is worse.** Below 0.5 the threshold stops too few bad drafts, and on prose the energy penalty returns: 1.35 times plain decoding at 0.3, 1.65 at 0.2. At 0.5 prose is again energy-neutral at 1.3 times the speed, matching the first run (0.99 there, 1.01 here). On the edit task the threshold barely matters, since almost every draft is right. Together with the first run, the best value on this machine lies between 0.5 and 0.8, and 0.5 remains the recommendation. Even with a threshold, drafts of 8 beat drafts of 16 on every prompt.

The code prompt was noisy in this session: plain decoding itself varied by 27% between its three runs, and the code conditions by up to 29%, so code is left out of the table. Prose and edit repeated within 5% to 24% and agree with the first run.

## Reproduce

```bash
uv run python experiments/speculative.py results/speculative-pmin-7b.json \
  plain,draft-8,draft-8-p0.5,draft-8-p0.8,draft-8-p0.95,draft-16,draft-16-p0.8
```

Raw results: `results/speculative-pmin-7b.json`, `results/summary-speculative-pmin.json`, `results/speculative-pmin-low-7b.json`, `results/summary-speculative-pmin-low.json`.
