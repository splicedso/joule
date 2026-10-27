# Thinking on a budget

**Prediction verdict:** missed on all four clauses, three of them in the budget's favour. Letting a 4B think for at most 2,048 tokens on code, and asking again without thinking when it runs out, raised HumanEval from 78.0% to 89.6%. It cost 2.9 times the tokens and 1.7 times the energy per correct answer, against a predicted 3 to 7.

Spliced research note 30, 26 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew). Qwen3.5 4B Instruct (Apache-2.0), quantized to Q4_0 here, as in note 29.

Note 29 found that thinking lost a 4B its accuracy by running out of room, not by reasoning badly. Replaying its recorded replies suggested a policy: think up to a budget, and if no answer has come, ask again with thinking off. The replay covered 40 code problems. This note runs the policy live on all 164.

**Prediction** (`docs/predictions.md`, 26 October 20:08, before the run): the budget raises accuracy by 2 to 8 points over thinking off, at 3 to 6 times the tokens and 3 to 7 times the energy per correct answer, and 4 to 15% of problems fall back. Set at the same time: Foundry offers the budget only if the gain is at least 3 points.

## Method

`experiments/general_eval.py` with `THINK_BUDGET=2048`: each problem is asked with thinking on and at most 2,048 tokens. A reply stopped by that limit is discarded and the problem is asked again with thinking off, up to 16,384 tokens. Both replies' tokens and energy count. HumanEval, all 164 problems, the model's code run against the tests in a sandbox with no network and no access to the home directory. Eight requests at once. Two passes per condition in mirrored order (off, budget, budget, off), started after the Mac idled under 2 W twice in a row (`experiments/budget_mac.sh`).

## Results

| condition | accuracy | tokens per problem | chip J per correct | fell back |
|---|---:|---:|---:|---:|
| thinking off | 78.0% | 442 | 120.0 | |
| budget 2,048 | 89.6% | 1,282 | 201.9 | 16% |
| budget against off | +11.6 points | x2.9 | x1.68 | |

Accuracy was identical in both passes of each condition. Energy differed by 6.9% and 8.0% between passes, both times with the second pass costlier and the machine warmer at rest.

**The gain is real, and not from the 40 problems already seen.** The budget fixed 20 problems and broke 1. On problems 1 to 40 it scored 37 against 34, exactly what note 29's replay said. On problems 41 to 164, which had never been run with thinking, it scored 110 against 94, a gain of 12.9 points. On the 138 problems where thinking finished inside the budget, it got 133 right against 114 without thinking. On the 26 that fell back, the answer is the plain answer, so the score is the same.

**Why it cost less energy than predicted.** Two problems made the model loop without thinking: it reasoned in comments inside its code block until it hit 16,384 tokens, wrong both times. Those two replies were 45% of all thinking-off tokens. They ran at the end of the batch, nearly alone, and note 24 showed one request at a time costs several times more per token than eight. So thinking off paid 205 mJ per token and the budget 136. The budget pays for the same two loops after falling back, but its other tokens are decoded eight at a time.

## What this means for the box

On a small model, on code, a short thinking budget with a fallback is worth having: twelve points for under twice the energy per correct answer. Unlimited thinking was the worst setting in note 29, and thinking off is still best on maths and knowledge questions. So the box should set thinking per task, with a budget, never unlimited. The decision rule is met, so Foundry gets a "think on code" setting built on this.

The loops point to a second, cheaper fix: no plain reply that passed was longer than 1,374 tokens, so a cap near 2,048 tokens on plain code replies would have cut nearly half of thinking off's tokens, and lost nothing. That is a prediction for a later run, not a result.

## Limits

- One small model, one machine, one task. Maths and knowledge were not re-run: note 29's replay found no gain there.
- Chip energy, not the wall. The pass-to-pass energy gap is over 3% in both conditions.
- The budget of 2,048 was chosen from note 29's replay of problems 1 to 40, which are part of this run. Problems 41 to 164 are the clean test, and the gain held there.
