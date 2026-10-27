# A cap on the answer, too

**Prediction verdict:** all three clauses held. Letting the model answer from a cut thought, with the whole reply capped at 2,560 tokens, beat Foundry's fallback on every task at no extra energy per correct answer. The extra power of note 32 is gone. By the rule set before the run, Foundry's Think switch moves to it.

Spliced research note 33, 27 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew). Qwen3.5 4B Instruct (Apache-2.0), quantized to Q4_0 here, as in notes 29 to 32.

Notes 31 and 32 found that answering from a cut thought gets a few more questions right than starting over, but that the model sometimes keeps reasoning in its answer until the reply limit. That cost tokens, and those passes also drew 5 to 6 W more for reasons we could not pin down. This note caps the answer as well as the thought, and asks again without thinking when the cap is hit.

**Prediction** (`docs/predictions.md`, 27 October 01:02, before the run): the capped mode lands within a point of what a replay of notes 31 and 32's recorded replies gives it on every task; its chip power is within 1.5 W of the fallback's; and its energy per correct answer is within 8% of the fallback's. Set at the same time: Foundry moves to it if it is never less accurate than the fallback, at least 2 points better on one task, and no more than 10% costlier per correct answer on any.

## Method

`experiments/general_eval.py` on all 164 HumanEval problems, the first 100 GSM8K problems and the first 8 MMLU-Pro questions of each of its 14 subjects. Eight requests at once. Two conditions:

- **Fallback** (Foundry's Think until now): think up to 2,048 tokens; if no answer has come, ask again with thinking off. Every reply capped at 2,048.
- **Capped answer:** the server started with `--reasoning-budget 2048`, so the thought ends there and the model answers from it. The whole reply is capped at 2,560 tokens; a reply stopped by that cap is asked again with thinking off, capped at 2,048.

Two passes each in mirrored order, started after the Mac idled under 2 W twice in a row (`experiments/modes_mac_d.sh`). Three passes ran 01:07 to 03:06. Martin paused the work there, and the fallback's second pass ran alone from 11:38 to 12:14 under the same gate. It matched its first pass question for question.

## Results

| condition | HumanEval | GSM8K | MMLU-Pro | chip W | J per correct, HumanEval / GSM8K / MMLU-Pro |
|---|---:|---:|---:|---:|---:|
| fallback | 89.6% | 96.0% | 68.8% | 30.2 to 31.2 | 138.3 / 186.6 / 359.9 |
| capped answer | 92.1% | 97.0% | 71.4% | 30.4 to 30.5 | 128.9 / 179.2 / 358.6 |

**The replay was right to the question.** The capped mode scored exactly what the recorded replies predicted on all three tasks, with token counts within a few per question, and asked again on 3, 3 and 31 questions as predicted. No reply changed score between passes in either condition.

**More right, for the same energy.** The capped mode gained 2.4 points on code, 1.0 on maths and 2.7 on knowledge, and cost 7%, 4% and 0% less per correct answer. Every difference comes from the questions where the thought ran past 2,048 tokens: 26 on code (18 right against 14), about a third of maths (28 against 27) and 75 on knowledge (46 against 43). Question by question it won 12 and lost 4 across the three tasks. That is a real gain on this set, but a small one.

**The cap catches the runaways.** On knowledge, 31 of 112 answers reached 2,560 tokens and were asked again; 15 of those came out right, against 14 for the fallback on the same questions. They are expensive, 46% of the capped mode's knowledge tokens, which is why it used 4% more tokens there than the fallback. On code and maths it was 3 questions each. No reply in a chat now reasons on for thousands of tokens before an answer.

**The extra watts were the runaways.** With the server flag on and the replies capped, chip power was within a watt of the fallback's on every task: 0.8 and 0.3 W lower on code and maths, 0.3 W higher on knowledge. In note 32 the same flag with replies allowed to 4,096 tokens drew 36 to 37 W. So the flag costs nothing. The extra power came with the long replies, though this run does not show why a long reply draws more at the same speed.

## Verdicts

- The capped mode lands within a point of its replay on every task: **held** (exactly, on all three).
- Its chip power is within 1.5 W of the fallback's on every task: **held** (-0.8, -0.3 and +0.3 W).
- Its energy per correct answer is within 8% of the fallback's on every task: **held** (-6.8%, -4.0% and -0.4%).

## What this means for the box

The rule is met: never less accurate, 2.4 and 2.7 points better on code and knowledge, and no costlier per correct answer anywhere. Foundry's Think switch now starts the server with `--reasoning-budget 2048` and caps a Think reply at 2,560 tokens; a reply that hits the cap is still asked again without thinking.

Across notes 29 to 33, the answer for a 4B is: thinking off by default; with Think on, end the thought at 2,048 tokens, let the model answer from it, and cap the whole reply. The next question is whether the same holds for a larger model, which the Strix Halo's Qwen3.6 runs will answer.

## Limits

- One small model, one machine. The gain is 12 questions won against 4 lost, out of 376.
- Chip energy, not the wall.
- The fallback's second pass ran nine hours after the rest, after a pause. It matched its first pass on every question, and its chip power was within 0.6 W of it.
- The test sets overlap notes 29 to 32, and the prediction was made from a replay of their recorded replies. The replay is what was tested here, not a fresh sample.
