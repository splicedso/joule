# What thinking costs

**Prediction verdict:** missed on accuracy, unresolved on energy. Thinking made a 4B model less accurate on maths and knowledge questions, not more, and cost about seven to eight times the energy per correct answer. Almost every answer it lost was a reply that ran out of room mid-thought. On the questions where it finished thinking, it tied or won on all three tasks.

Spliced research note 29, 26 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew). Qwen3.5 4B Instruct (Apache-2.0), converted from the official weights and quantized to Q4_0 here.

The open models released in 2026 reason before they answer. They write a chain of thought, then the answer. The strongest bases for our flagship all do it, and so does this 4B, behind a switch in its chat template. Thinking is paid for in tokens, and a token is what 28 notes have measured the energy of. This note asks what thinking costs per correct answer, and what it buys.

**Prediction** (`docs/predictions.md`, 26 October 12:47, before the weights finished downloading): thinking multiplies tokens per answer by 4 to 10 on maths and knowledge and 3 to 8 on code. It raises accuracy by 3 to 10 points on GSM8K, 5 to 15 on MMLU-Pro and 0 to 10 on HumanEval. It costs 3 to 8 times more energy per correct answer overall and is not cheaper on any task. Fewer than 5% of replies hit the limit.

## Method

`experiments/general_eval.py`: GSM8K (50 problems), MMLU-Pro (4 per subject, 56 questions, ten options) and HumanEval (40 problems, the model's code run against the tests in a sandbox with no network and no access to the home directory). Eight requests at once. Thinking off and on through the template's `enable_thinking`. Chip energy sampled over each task. Joules per correct answer is that energy over the number answered correctly, so a wrong answer costs energy and buys nothing. Two passes per condition in mirrored order (off, on, on, off), started only after the Mac idled under 2 W twice in a row.

**The design changed once, on the record, before the measured run.** Two smoke tests came first. With a 4,096-token limit per reply, 7 of 19 thinking replies were cut off mid-thought and returned no answer. At 16,384 tokens, 3 of 18 still ran out. So the run allows 16,384 tokens per reply, and the samples were cut so a thinking pass takes about an hour. The change was committed before the run started. The smoke tests had shown the token and cut-off figures, so those two clauses are reported but not counted.

**One pass has untrusted energy.** Decoding was repeatable: both passes of each condition produced the same tokens and the same answers. The first thinking pass overlapped other work on this Mac, testing the box server and committing drawings. Its idle reading was 2.97 W against under 1.8 W for the others, and it drew 35.8 W on MMLU-Pro against 28.2 W at a similar speed. Energy below comes from the second passes, which ran on a quiet machine. The busy pass is in the results files.

## Results

Accuracy and tokens (identical in both passes):

| task | accuracy, off | accuracy, on | tokens per answer, off | on | cut off at 16,384, on |
|---|---:|---:|---:|---:|---:|
| GSM8K | 98.0% | 92.0% | 366 | 3,228 | 6% |
| MMLU-Pro | 64.3% | 57.1% | 870 | 7,183 | 30% |
| HumanEval | 85.0% | 87.5% | 182 | 2,250 | 10% |

Chip energy per correct answer, second passes:

| task | off, J | on, J | on against off |
|---|---:|---:|---:|
| GSM8K | 43 | 417 | x9.6 |
| MMLU-Pro | 261 | 1,623 | x6.2 |
| HumanEval | 35 | 435 | x12.6 |
| all three | 107 | 764 | x7.2 |

With the busy pass averaged in, the overall figure is x8.1.

**Thinking lost by running out of room.** Every question thinking got wrong that the plain model got right ended in a cut-off reply, except one MMLU-Pro question. A cut-off reply has no answer, so it scores wrong. On the questions where thinking finished, the comparison is fair, since both modes answered the same questions:

| task | questions thinking finished | right, off | right, on |
|---|---:|---:|---:|
| GSM8K | 47 of 50 | 46 | 46 |
| MMLU-Pro | 39 of 56 | 31 | 32 |
| HumanEval | 36 of 40 | 32 | 35 |

The cut-off replies are also where most of the tokens went: 31% of thinking's tokens on GSM8K, 69% on MMLU-Pro and 73% on HumanEval were spent on replies that never answered.

**A budget with a fallback.** That suggests a policy: think up to a budget, and if no answer has come, ask again with thinking off. Because decoding was repeatable, the recorded replies show what that policy would have returned (`experiments/think_fallback.py`). This is a replay, not a measurement. The fallback is charged the full budget plus the plain reply.

| thinking budget | GSM8K | MMLU-Pro | HumanEval | all three | tokens against thinking off |
|---:|---:|---:|---:|---:|---:|
| none (thinking off) | 98.0% | 64.3% | 85.0% | 81.5% | x1.0 |
| 1,024 | 98.0% | 64.3% | 85.0% | 81.5% | x2.6 |
| 2,048 | 98.0% | 64.3% | 92.5% | 83.6% | x3.4 |
| 4,096 | 98.0% | 64.3% | 92.5% | 83.6% | x4.7 |
| 16,384 | 98.0% | 66.1% | 92.5% | 84.2% | x9.2 |

On this model, thinking bought nothing on GSM8K at any budget, and one MMLU-Pro question at 8,192 tokens and above. On code it bought three HumanEval problems, all inside 2,048 tokens.

## What this means for the box

A small model on a small machine should not think by default. Thinking off answered best per joule on every task. Where thinking helps, here on code, a short budget with a fallback got all of its gain for about a third of the tokens of unlimited thinking. Letting a 4B think without a limit was the worst setting measured: more energy and a lower score.

That is a setting the box's software controls, and it is cheap to change. The next step is to measure the policy rather than replay it, on a larger HumanEval sample, before Foundry offers it.

## Limits

- One small model, one machine, small samples (50, 56 and 40). Three HumanEval problems is within noise at this size, and so is the MMLU-Pro gap on finished questions.
- The fallback figures are a replay of recorded replies, not a measured run.
- Chip energy, not the wall. One of four passes had a busy machine; its energy is excluded and reported here.
- Larger models may use thinking better than a 4B does. Nothing here measured them, so nothing here says thinking does not pay on the flagship bases.
