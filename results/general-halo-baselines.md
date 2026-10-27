# General-eval baselines on the Strix Halo: Qwen2.5 1.5B and 7B at Q4_0

**Prediction verdict:** 5 of 6 accuracy clauses held. The 7B scored above its GSM8K band (91.4% against 86 to 90%); the
other five bands held.

Spliced results page, 2026-10-26, 20:59 PT. AMD Ryzen AI Max+ 395 (Strix Halo, Radeon 8060S, 128 GB, shared GPU memory 90%),
Linux, llama.cpp 620d2225c, Vulkan. Qwen2.5 1.5B and 7B Instruct at Q4_0, the models Foundry ships today (`docs/program.md`,
the laptop bar). These are the reference rows every model we train is judged against on this machine.

**Prediction** (`docs/predictions.md`, 26 October 12:00 and 12:03 PT, committed before the runs): 7B GSM8K 86 to 90%,
MMLU-Pro 45 to 55%, HumanEval 75 to 85%; 1.5B GSM8K 63 to 69%, MMLU-Pro 25 to 35%, HumanEval 50 to 65%.

## Method

`experiments/general_baselines.sh`: `experiments/general_eval.py` with GSM8K (the first 250 test problems), MMLU-Pro (20 per
subject, 280 questions, ten options) and HumanEval (all 164, the model's code run against the tests inside bubblewrap: no
network, home and the repository hidden, a private /tmp). 8 requests at once, 2,048 tokens per reply, 6,144 tokens of
context per slot, auto clocks, chip (package) energy per task from `power1_average` with Phase's warm-up, idle sampled
before each run. Two passes in mirrored order (1.5B, 7B, 7B, 1.5B), 16:47 to 17:18 PT on 26 October, right after the 32B
format search. Nothing else ran: the power log shows the GPU idle before each run (4.9 to 6.4 W) and a 1-minute load of
0.4 to 0.6 throughout.

## Results

Means of the two passes, with each pass in brackets. Joules are chip energy per correct answer; W is the mean package power
during the task; "cut off" counts replies that hit 2,048 tokens (scored wrong); "same reply" is the share of problems whose
reply was identical in both passes.

| model | task | n | accuracy | tokens per answer | J per correct | spread | tok/s | W | cut off | same reply |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen2.5 7B Q4_0 | GSM8K | 250 | 91.4% (229, 228) | 235 (235, 235) | 155.0 (160.6, 149.5) | 7.1% **flagged** | 214 | 129.3 (135.1, 123.5) | 0, 0 | 66% |
| Qwen2.5 7B Q4_0 | MMLU-Pro | 280 | 50.4% (144, 138) | 125 (125, 126) | 190.4 (181.8, 199.0) | 9.0% **flagged** | 156 | 119.4 (119.3, 119.4) | 0, 0 | 75% |
| Qwen2.5 7B Q4_0 | HumanEval | 164 | 79.0% (130, 129) | 205 (205, 205) | 159.4 (159.0, 159.8) | 0.5% | 195 | 119.5 (119.6, 119.5) | 0, 0 | 87% |
| Qwen2.5 1.5B Q4_0 | GSM8K | 250 | 68.6% (168, 175) | 277 (281, 273) | 75.6 (77.1, 74.1) | 4.0% **flagged** | 615 | 115.2 (112.7, 117.7) | 4, 3 | 50% |
| Qwen2.5 1.5B Q4_0 | MMLU-Pro | 280 | 27.1% (76, 76) | 39 (34, 44) | 63.1 (55.0, 71.2) | 25.7% **flagged** | 279 | 123.7 (123.6, 123.8) | 0, 1 | 93% |
| Qwen2.5 1.5B Q4_0 | HumanEval | 164 | 56.1% (89, 95) | 175 (165, 185) | 79.1 (74.8, 83.5) | 11.0% **flagged** | 479 | 121.3 (122.2, 120.4) | 1, 3 | 71% |

Across all three tasks, joules per correct answer: 7B 166.3 and 166.0;
1.5B 71.5 and 76.1 (a 6.2% gap, flagged). Idle before each run: 1.5B 4.9 and
5.4 W, 7B 6.4 and 6.2 W. Raw files: `results/general-halo-{1.5b,7b}-Q4_0-pass{1,2}.json`
(every reply, its token count and whether it was correct); the day's power log in `results/halo-power-log.csv`.

## What to take from this

1. **The 7B buys 23 points on every task for 2 to 3 times the energy per correct answer:** 2.05x on GSM8K, 3.02x on
   MMLU-Pro, 2.01x on HumanEval. On MMLU-Pro it also writes 3.2 times the tokens (125 against 39): the 1.5B mostly
   answers with a letter, the 7B reasons first.
2. **GSM8K with 2,048 tokens per reply scores higher than quality.py's 384:** 7B 91.4% against 88.6% (note 22), 1.5B 68.6%
   against 66%. The two harnesses are not interchangeable; this page is the general-eval reference.
3. **The 1.5B's passes disagree more than the 7B's.** Decoding at 8 slots is not bit-exact between runs, and the small model
   diverges more: only 50% of its GSM8K replies were identical across passes (66% for the 7B), and on MMLU-Pro
   its pass-2 replies were 30% longer at the same accuracy, which is the whole 25.7% energy gap on that task. HumanEval:
   89 then 95 correct of 164, 12% more tokens in pass 2. These cells are flagged; the 1.5B needs more
   passes before a 3-point claim about it is safe.
4. **The 7B's GSM8K energy gap (7.1%) is power, not speed:** both passes decoded at 213 to 216 tok/s with the same tokens,
   but pass 1 drew 135.1 W against 123.5 W. Pass 1 was the first 7B run after the 1.5B and a four-hour 32B session; the
   power log shows the GPU edge at 92.7 C during it against 90.4 C in pass 2. Same work, warmer chip, more watts.

## Prediction verdict, clause by clause

- 7B GSM8K 86 to 90%: **missed**, 91.4% (91.6, 91.2), above the band.
- 7B MMLU-Pro 45 to 55%: held, 50.4%. 7B HumanEval 75 to 85%: held, 79.0%.
- 1.5B GSM8K 63 to 69%: held on the mean, 68.6% (67.2, 70.0; pass 2 alone is above the band).
- 1.5B MMLU-Pro 25 to 35%: held, 27.1%. 1.5B HumanEval 50 to 65%: held, 56.1%.

## Limits

One machine, chip energy, 8 slots. The 1.5B's energy spreads are over 3% on every task; the 7B's on two. Both models ran
in one window on a chip warm from the 32B search; a cold-start pass would read lower power. MMLU-Pro is 20 questions per
subject, so one question is 0.36 points. The HumanEval sandbox is bubblewrap on Linux (PR 30); the Mac's equivalent is
sandbox-exec, so cross-machine code scores compare the same test under two sandboxes.
