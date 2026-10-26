# Trace on-policy pilot: no gain, and at their best thresholds every draft is within 1% of the stock one

**Verdict:** Trace pauses. The decision rule agreed before the pilot (at least one point of acceptance over the
best off-policy draft, at one request, k=4, p 0.5) is missed by eight points: the on-policy drafts accept 66.9% and
67.3% against the 35k off-policy draft's 75.3%. Judged at each draft's best confidence threshold, all four trained
and stock drafts serve within 1% of each other in speed, at about 1.48x plain decoding.

## What ran (pre-registered in d825a8f, committed 14:17, headed 14:30; thresholds in 3b6826b, 06:39)

On-policy distillation (`train_onpolicy.py`): the draft generates 128 tokens per prompt, the teacher scores the
draft's own tokens, the loss is total variation distance at those positions. Teacher: the Q4_0 7B's GGUF dequantized
into transformers, 98.8% top-1 agreement with its llama.cpp tokens (`teacher-check-halo.json`). LR 3e-6, 300 steps,
four prompts per step. Two starts: the stock 0.5B, and the 35k off-policy checkpoint. 16 to 17 min each.

## Held-out top-1 agreement with the Q4_0 7B (`score_drafts.py`, one script, the same 56,600 positions)

| draft | agreement |
|---|---:|
| stock | 0.7619 |
| 9k off-policy (LR 3e-6) | 0.7685 |
| 35k off-policy | **0.7758** |
| on-policy from stock (best step, 100) | 0.7627 |
| on-policy from 35k (no step beat its start; final weights) | 0.7692 |

From stock, the on-policy run peaked at +0.08 points at step 100 and ended below its start (0.7597 at step 300).
From the 35k checkpoint it declined at every evaluation, from 0.7758 to 0.7690. Training curves:
`train-log-onq4-stock.json`, `train-log-onq4-35k.json`. (score_drafts.py loads in bf16, train_trace.py scored
in its own dtype: the 35k draft reads 0.7758 here and 0.7754 in training; the 9k draft agrees to four places.)

## Speculative decoding (evaluate.py, Q4_0 7B target, one request, 40 held-out prompts, 256 tokens, two passes)

Tokens per second here are total tokens over total seconds per condition (evaluate.py prints the mean of
per-prompt rates, a little higher). `--spec-type draft-simple` on every draft row. Idle 9.2 W.

| condition | tok/s | acceptance | drafted per pass | accepted per generated token | chip mJ/token |
|---|---:|---:|---:|---:|---:|
| plain | 49.9 | | | | 2144 |
| stock, p 0.5 | 73.9 | 71.7% | 8,591 | 0.601 | 1423 |
| 9k off-policy, p 0.5 | 72.2 | 73.6% | 8,086 | 0.581 | 1476 |
| 35k off-policy, p 0.5 | 71.3 | 75.3% | 8,052 | 0.592 | 1407 |
| on-policy from stock, p 0.5 | 72.7 | 66.9% | 9,430 | 0.616 | 1382 |
| on-policy from 35k, p 0.5 | 73.3 | 67.3% | 9,450 | 0.621 | 1367 |
| stock, p 0.4 | 73.8 | 64.2% | 10,068 | 0.631 | 1357 |
| 35k off-policy, p 0.4 | 74.1 | 67.0% | 9,616 | 0.629 | 1350 |
| on-policy from stock, p 0.4 | 73.8 | 60.0% | 10,954 | 0.641 | 1356 |
| on-policy from 35k, p 0.4 | 73.5 | 58.8% | 11,145 | 0.640 | 1365 |
| stock, p 0.3 | 73.4 | 55.9% | 11,880 | 0.648 | 1362 |
| 35k off-policy, p 0.3 | 74.1 | 57.1% | 11,643 | 0.649 | 1346 |
| on-policy from stock, p 0.3 | 73.3 | 53.7% | 12,459 | 0.653 | 1358 |
| on-policy from 35k, p 0.3 | 74.6 | 54.0% | 12,488 | 0.658 | 1339 |

Best threshold per draft (by speed): stock p 0.5 (73.9), 35k p 0.4 (74.1), on-policy from stock p 0.4 (73.8),
on-policy from 35k p 0.3 (74.6). The spread between the best and the worst of these is 1.1%.

**Flagged spreads (over 3% pass to pass):** plain (tok/s 3.8%, mJ 8.6%), stock p 0.5 (6.1%, 5.6%), 9k p 0.5
(5.7%, 6.3%). These are the conditions at the two ends of the 90-minute run order (first in pass 1, last in
pass 2); every condition in the middle repeats within 1%. So stock at p 0.5 is the noisiest cell in the table,
and the like-for-like comparison is at p 0.4, where both are unflagged: 35k 74.1 against stock 73.8 tok/s
(+0.4%), 1350 against 1357 mJ/token (-0.5%).

## What to take from this

1. **Speed at serving time does not follow agreement here.** The 35k draft has the best agreement (+1.4 points)
   and the on-policy drafts the lowest acceptance, yet at each draft's best threshold all four land within 1.1%.
   On-policy training made the draft more confident (more tokens clear p 0.5, so acceptance falls and accepted
   per generated token rises), which a lower threshold also does for any draft.
2. **The ceiling is the draft's cost, not its accuracy.** About 1.48x over plain and a third less chip energy per
   token is what a 0.5B draft gives the Q4_0 7B on this machine at one request, trained or not.
3. **Trace pauses**, as agreed: the write-up of why goes in a note. Any return needs a different lever than
   training the 0.5B (a smaller or cheaper draft, or a larger target, where the draft is relatively cheaper). The
   72B harvest stays parked.

Raw: `results/drafter/eval-onpolicy-halo.json`, `score-onpolicy-halo.json`, `train-log-onq4-{stock,35k}.json`.
