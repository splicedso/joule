# Answering from a cut thought

**Prediction verdict:** one of four clauses held. llama.cpp's own reasoning budget, which ends the thought at 2,048 tokens and makes the model answer from it, scored 92.1% on HumanEval against 89.6% for note 30's policy of throwing the thought away and asking again. It was not cheaper, so by the rule set before the run, Foundry's Think switch stays as it is.

Spliced research note 31, 26 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew). Qwen3.5 4B Instruct (Apache-2.0), quantized to Q4_0 here, as in notes 29 and 30.

Note 30 gave a 4B a thinking budget on code: think for up to 2,048 tokens, and if no answer has come, discard the thought and ask again with thinking off. That added 11.6 points. llama.cpp has a second way to do it: `--reasoning-budget` closes the thought when the budget runs out and lets the model write its answer after it, in the same request. This note compares the two, and a cap on plain replies.

**Prediction** (`docs/predictions.md`, 26 October 21:21, before the run): thinking off with a 2,048-token cap costs 40 to 65 J per correct answer; the fallback policy with every reply capped costs 150 to 185 J; the built-in budget scores 86 to 92% at 900 to 1,200 tokens per problem, and costs 5 to 20% less than the fallback. Set at the same time: Foundry moves to the built-in budget if it is within a point of the fallback, or better, and at least 5% cheaper per correct answer.

## Method

`experiments/general_eval.py` on all 164 HumanEval problems, the model's code run against the tests in a sandbox with no network and no access to the home directory. Eight requests at once. Three conditions:

- **Off, capped:** thinking off, at most 2,048 tokens per reply.
- **Fallback, capped:** note 30's policy, but the second request is also capped at 2,048 tokens.
- **Built-in:** thinking on, the server started with `--reasoning-budget 2048`, at most 4,096 tokens per reply.

Two passes each in mirrored order (off, fallback, built-in, built-in, fallback, off), started after the Mac idled under 2 W twice in a row (`experiments/modes_mac.sh`). The run took 21:36 to 22:28.

## Results

| condition | accuracy | tokens per problem | chip J per correct | pass-to-pass energy |
|---|---:|---:|---:|---:|
| off, capped | 78.0% | 267 | 43.6 | 3.7% |
| fallback, capped | 89.6% | 1,107 | 141.8 | 0.8% |
| built-in | 92.1% | 1,076 | 148.5 | 19.9% |
| note 30: off, uncapped | 78.0% | 442 | 120.0 | 6.9% |
| note 30: fallback, uncapped | 89.6% | 1,282 | 201.9 | 8.0% |

Every reply was identical between the two passes of each condition, all 492 of them.

**The difference is all in 26 problems.** On the 138 problems where the thought finished inside 2,048 tokens, the fallback and the built-in budget wrote the same reply, token for token. They differ only on the 26 where it did not. There, the fallback's fresh answer got 14 right, exactly what thinking off gets on those 26. Answering from the cut thought got 18 right: six gained, two lost. It also used 8% fewer tokens on them, because the model does not start over.

**It was not cheaper, and one pass is why the figure is unsure.** By tokens, the built-in budget should cost about 3% less than the fallback. Its two passes decoded the same 176,410 tokens, but the first drew 36.2 W at 259 tokens a second and the second 31.5 W at 276. Every other pass in the run drew 31 to 33 W. I found no cause: nothing else was started on the Mac, and the idle reading before the pass was normal. Its mean is 4.7% more costly than the fallback; the second pass alone is 5.7% cheaper; the token count says 3%. None of the three reaches the 5% the rule asked for.

**The cap on plain replies did what note 30 said.** Problems 132 and 134 are the two that loop without thinking. A 2,048-token cap stopped both, cost no correct answers, and took thinking off from 120.0 to 43.6 J per correct answer. The same cap on the fallback's second reply took it from 201.9 to 141.8 J.

## Verdicts

- Off, capped, costs 40 to 65 J per correct answer: **held** (43.6).
- Fallback, capped, costs 150 to 185 J: **missed, low** (141.8). I credited the loops with less of its energy than they had.
- Built-in scores 86 to 92% at 900 to 1,200 tokens: **missed by 0.1 point, high** (92.1% at 1,076).
- Built-in costs 5 to 20% less than the fallback: **missed** (4.7% more on the mean).

## What this means for the box

The rule was about cost, and cost did not move. So Foundry's Think switch keeps note 30's policy. The finding the rule did not plan for is accuracy: when a small model's thought runs long, what it has thought is worth more than a fresh start without it. Four problems in 164 is too few to switch on, so the next run tests it where note 29 found thinking hurt most, on maths and knowledge questions, with the decision rule written for accuracy before it starts.

The plain-reply cap stays out of Foundry, as set before the run. HumanEval rewards short code; in a chat a long answer is often the right one.

## Limits

- One small model, one machine, one task. The 26 problems that separate the two policies are a small sample.
- Chip energy, not the wall. One pass drew 15% more power than its twin for no cause I could find, so this run cannot rank the two policies by energy closer than about 5%.
- Problems 1 to 40 informed note 30's budget of 2,048. Both policies use the same budget, so that favours neither.
