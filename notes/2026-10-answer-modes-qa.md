# When a stopped thought keeps talking

**Prediction verdict:** four of five clauses held. On knowledge questions, llama.cpp's built-in reasoning budget beat the fallback policy by 3.6 points. But one answer in six carried on reasoning in plain view until the reply limit, and it cost 16 to 17% more energy per correct answer. By the rule set before the run, Foundry's Think switch keeps the fallback.

Spliced research note 32, 27 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew). Qwen3.5 4B Instruct (Apache-2.0), quantized to Q4_0 here, as in notes 29 to 31.

Note 31 compared two ways to stop a small model that thinks too long. The fallback discards the thought and asks again with thinking off. The built-in budget ends the thought and has the model answer from it. On code, the built-in budget scored 92.1% against 89.6%, from 26 problems. This note runs the same comparison on maths and knowledge, where note 29 found thinking hurt most.

**Prediction** (`docs/predictions.md`, 26 October 22:29, before the run): the fallback lands within a point of thinking off on both tasks, falling back on 20 to 50% of maths and 60 to 90% of knowledge questions; the built-in budget lands within 2 points of thinking off on maths, beats the fallback on knowledge by 0 to 6 points, and uses 5 to 15% fewer tokens there. Set at the same time: Foundry moves to the built-in budget if, across note 31's code and these two tasks, it is never less accurate than the fallback, at least 2 points better on one of these two, and no more than 10% costlier per correct answer on any.

## Method

`experiments/general_eval.py` on the first 100 GSM8K problems and the first 8 MMLU-Pro questions of each of its 14 subjects (112, ten options each). Eight requests at once. The same three conditions as note 31:

- **Off, capped:** thinking off, at most 2,048 tokens per reply.
- **Fallback, capped:** think up to 2,048 tokens; if no answer has come, ask again with thinking off, also capped at 2,048.
- **Built-in:** thinking on, the server started with `--reasoning-budget 2048`, at most 4,096 tokens per reply.

Two passes each in mirrored order, started after the Mac idled under 2 W twice in a row (`experiments/modes_mac_qa.sh`). The run took 22:37 to 00:34.

## Results

| condition | GSM8K | MMLU-Pro | tokens per question, MMLU-Pro | chip J per correct, MMLU-Pro |
|---|---:|---:|---:|---:|
| off, capped | 96.0% | 69.6% | 548 | 99.5 |
| fallback, capped | 96.0% | 68.8% | 2,207 | 372.8 |
| built-in | 96.0% | 72.3% | 2,244 | 434.3 |

**Maths: nothing to choose.** All three scored 96 of 100, and the same 96. The thought ran past 2,048 tokens on 32 problems, and every way of handling that got the same 28 right. Thinking off did it for a quarter of the energy.

**Knowledge: the built-in budget is more accurate.** The thought ran long on 75 of 112 questions. There, the fallback got 43 right, thinking off 44, and the built-in budget 46 and 48 in its two passes. On the other 37, all three wrote the same 34 right answers. So, as on code, answering from the thought beats starting over, and the whole difference comes from the questions where the thought ran long.

**It was not fully repeatable.** Thinking off gave identical replies in both passes. The fallback differed on 3 of 112 knowledge replies and 1 of 100 maths replies, with the same score. The built-in budget differed on 5 knowledge replies, all long thoughts, and scored 80 then 82. Notes 30 and 31 found decoding on this Mac repeatable to within a reply or two; here it held for the score in every condition but this one.

**A stopped thought keeps talking.** On 18 of 112 knowledge questions, in both passes, the built-in budget's answer ran to the 4,096-token limit. When the thought is cut off, the model carries on reasoning in its answer ("Let's recall the rule...") and never stops. Only 4 of those 18 were right, and they were 29% of the condition's tokens. Law and psychology were 9 of the 18. On maths it happened twice. In a chat, that is two thousand tokens of visible reasoning before, or instead of, an answer.

**It cost more, and part of the cost is unexplained.** The built-in budget decoded 1.7% more knowledge tokens than the fallback, at the same speed as the fallback's second pass, but drew 36 to 37 W against 30 to 32 W for every other knowledge pass. Note 31 saw the same once on code. At the fallback's power it would have cost about the same per correct answer; as measured, it cost 16 to 17% more in both passes. My own sessions answered messages while both of its knowledge passes were finishing. But a fallback pass with the same overlap drew 30.4 W, so that is not a full explanation. The idle reading before the built-in budget's second pass was 14 W, against under 1 W for the others. Its maths energy is excluded; the knowledge figure is reported as measured.

## Verdicts

- The fallback lands within a point of thinking off on both tasks: **held** (0 and 0.9 points).
- The fallback falls back on 20 to 50% of maths and 60 to 90% of knowledge questions: **held** (32% and 67%).
- The built-in budget lands within 2 points of thinking off on maths: **held** (the same 96).
- The built-in budget beats the fallback on knowledge by 0 to 6 points: **held** (+2.7 and +4.5 in its two passes).
- The built-in budget uses 5 to 15% fewer tokens on knowledge: **missed** (1.7% more). The runaway answers outweighed the saving from not starting over.

## What this means for the box

The rule is not met: the built-in budget was 16 to 17% costlier per correct answer on knowledge questions, over the 10% allowed. Even had it passed, the runaway answers would count against it in a chat. Foundry's Think switch keeps the fallback.

Across notes 29 to 32, the modes question has a plain answer for a 4B. Thinking off is best per joule on maths and knowledge. On code, a 2,048-token budget is worth twelve points, and the fallback is the safe way to stop it. The built-in budget gets a few more right but sometimes cannot stop talking. A budget on the answer as well as the thought could fix that. That is the next thing to test, with a larger model as well as this one.

## Limits

- One small model, one machine. 112 knowledge questions; the gain is 4 to 5 questions.
- Chip energy, not the wall, and the built-in budget's extra 5 to 6 W is unexplained in two runs out of three.
- The first 50 GSM8K and first 4 per MMLU-Pro subject were seen in note 29, with unlimited thinking only.
