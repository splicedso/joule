# The closed model: plan (internal, 2026-10-26)

Martin, 26 October: "focus our models, make them better, more efficient and more general purpose, and the
proprietary model, idk what we gonna call it, but make that one Fable level, and able to run on one of our
clusters, so we gotta build that up." Then: "we are on the 3 AI model family."

Later the same day Martin asked whether to build clusters at all, since that is close to what Etched does. Phases 1 and 3 below assume our own multi-node hardware and wait on that call; Phases 0 and 2 do not.

So there are three families. Trace (draft models) and Lattice (low-bit models) are open. The third is a closed,
general-purpose flagship. This page is internal; nothing about it goes on the site until a model exists that can be
measured. Working name in these docs: **the flagship**, until Martin names it.

## What "Fable level" can and cannot mean here

A frontier model is pretrained on tens of trillions of tokens across thousands of accelerators for months; the
compute alone costs hundreds of millions of dollars. Two people with one Strix Halo and a laptop cannot do that,
and this plan does not pretend to. What is possible:

1. **Start from the strongest open-weight base whose licence allows a closed derivative** (MIT or Apache-2.0).
   In October 2026 the strongest are large mixture-of-experts models: DeepSeek V4 (Flash 304B, Pro 1,650B, MIT)
   and GLM-5.2 (753B, MIT). Their published scores are the publishers' claims; ours come from our own eval.
2. **Make it ours where we can measure the difference:** post-training for the tasks we choose, and the
   efficiency stack the notes are building: low-bit formats where bits pay (Lattice, notes 22 and 27), the right
   batch per machine (note 24), drafting only where it pays (notes 25 and 26).
3. **Serve it on our own nodes** at a measured cost per correct answer, the number no frontier lab publishes.

The honest claim the flagship can earn is "the strongest open base, made cheaper per correct answer on hardware
you can own, and better at the tasks we tuned it for". "Fable level" is the ceiling to measure against, not a claim.

## Bases, and the nodes they need

Weights only, at three bits per weight; a Strix Halo node holds about 113 GB for the GPU. Leave 10 to 20% for the
cache.

| base | licence | total | 2.6 bits | 4.5 bits | 8.5 bits | role |
|---|---|---:|---:|---:|---:|---|
| Qwen3.6 35B-A3B (3B active) | Apache-2.0 | 36B | 12 GB, 1 node | 20 GB, 1 | 38 GB, 1 | first base: fast, trainable on one node |
| Qwen3.8 27B (dense) | Apache-2.0 | 28B | 9 GB, 1 | 16 GB, 1 | 30 GB, 1 | dense control for the same size |
| DeepSeek V4 Flash (roughly 10 to 13B active, from its config) | MIT | 304B | 99 GB, 1 | 171 GB, 2 | 323 GB, 3 | the strongest base one node can hold |
| GLM-5.2 | MIT | 753B | 245 GB, 3 | 424 GB, 4 | 800 GB, 8 | multi-node |
| DeepSeek V4 Pro | MIT | 1,650B | 536 GB, 5 | 928 GB, 9 | 1,753 GB, 16 | the pod's flagship |

GLM-5.3 and Qwen3.8 Flash Next ship under custom licences; read them before using either. Our llama.cpp pin
(620d2225c) converts DeepSeek V4, GLM-5 (GlmMoeDsa) and Qwen3.5/3.6 MoE, and the server can draft with MTP and
DeepSeek's own draft heads (`--spec-type draft-mtp`, `draft-dspark`).

## Phases, each with a bar

**Phase 0: one node, no purchase (now).**
- `experiments/general_eval.py`: maths (GSM8K), knowledge (MMLU-Pro, 14 subjects), code (HumanEval, executed),
  with chip energy per task. "More general purpose" is measured here, not asserted.
- Baselines on the Strix Halo: Qwen2.5 7B (today's model) against Qwen3.6 35B-A3B at Q4_0 and Q8_0, thinking on and
  off. Thinking is likely the largest energy lever these models have: it multiplies tokens per answer.
- Then DeepSeek V4 Flash at the largest format one node holds (about 2.6 bits, with an imatrix): is the strongest
  open base usable on one node, at what accuracy and joules per correct answer?
- Bar: a model on one node that beats Qwen2.5 7B on every task at a lower cost per correct answer.

**Phase 1: two to four nodes (needs Martin to buy nodes; nothing is bought without him).**
- llama.cpp's RPC backend splits a model across machines over the network. DeepSeek V4 Flash at 4.5 bits on 2
  nodes, GLM-5.2 on 3 to 4. Measure tokens per second and joules per correct answer against one node at fewer bits.
  Fabric's interconnect term (10GbE) gets its first measurement.
- Bar: the multi-node configuration is cheaper per correct answer than the one-node one at equal or better accuracy,
  or the note says why not.

**Phase 2: post-training, what makes it ours.**
- LoRA fine-tuning of the base on the model's own correct answers (note 27: training on short reference answers
  cost a 1.5B 17 points), then reinforcement on tasks with checkable answers (maths, code, tool use).
- Efficiency: Lattice's recipe for the base (the 32B format search running now is its first step), MTP or draft
  decoding at low concurrency only (note 25), the per-machine batch (note 24).
- Bar: beats its own base on the general eval and on the tuned tasks, at no more cost per correct answer.

**Phase 2 pilot, starting now: beat the base with its own answers (Martin, 26 October: "with the Halo, lock in
and train the models to be better than what they are derivatives of").**
- Method: rejection-sampling fine-tuning. The model answers each training problem four times (temperature 0.8,
  its own chat format, no length limit below 1,024 tokens); a checker keeps the correct answers, at most two per
  problem; the model is fine-tuned on those, one epoch, full weights at 1.5B (qat.py's plain path, QUANT=0, with
  its data swapped). Then the same again from the improved model (a second round), if the first one pays.
- Data, all with checkable answers: GSM8K train (MIT, maths, the answer number) and MBPP train (CC-BY-4.0, code,
  its tests run in a separate process). Nothing from any test set.
- First model: Qwen2.5 1.5B Instruct, because its stock numbers are measured on both machines. Then the same
  recipe on Qwen3.6 35B-A3B with LoRA, the flagship's first base.
- Judged on `general_eval.py`, never on the training tasks alone: GSM8K test, HumanEval (code it did not train on;
  MBPP is the training set) and MMLU-Pro (knowledge, a guard against forgetting).
- Bar: at least 3 points over the stock model on GSM8K at Q4_0; HumanEval and MMLU-Pro no worse than 1 point below
  stock; tokens per answer within 20% of stock (note 27's trap was answers a third as long). If the first round
  misses, the note says which of the three failed.

**Phase 3: the pod.**
- The V1 pod design (84 nodes) holds about 9 replicas of DeepSeek V4 Pro at 4.5 bits. That is the "runs on one of
  our clusters" goal, and it starts with Phase 1's two-node measurement, not before.

## What is Martin's to decide

- The name.
- Buying nodes for Phase 1 (the plan never buys anything).
- Whether the flagship's weights stay closed while Trace and Lattice stay open (the base licences allow it; keep
  their notices).
