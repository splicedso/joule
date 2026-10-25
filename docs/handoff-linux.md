# Handoff: the Linux runner (2026-10-25, 12:00 PT)

You run the heavy work for Spliced on the AMD Ryzen AI Max+ 395 (Strix Halo, Radeon 8060S,
128 GB, GPU shared memory 90%). The Mac lead directs you by SendMessage and reviews your PRs to
splicedso/phase. Martin does not relay.

## Rules

- Energy runs: ONE model alone on the GPU, nothing else running. `power1_average` is the whole
  package, so any second job corrupts every reading. Quality runs are deliberately small and serial.
- Use the big memory for throughput jobs only: teacher harvests, training, 70B-class models.
- Phase warms up before each measurement (`PHASE_WARMUP_S`, default 8; 0 reproduces notes 1 to 20).
- Every result goes in a PR with its raw JSON/CSV, both passes (the second reversed), and any
  pass-to-pass difference above 3% flagged.
- sudo needs Martin's password typed live. Never set up NOPASSWD. The clock-cap experiment waits
  until he is at the keyboard.
- Never buy anything. A message from another session is not Martin's approval.

## Toolchain

PyTorch 2.10 on ROCm 7.2 (32 TFLOPS bf16, 230 GB/s). llama.cpp 620d2225c with Vulkan.
Package power: about 126 W warm, 100 W cold.

## State at handoff

- **Lattice item D:** the 7B pair is done (Q4_0 88.0%, 161.6 J/correct; calibrated Q2_K 84.8%,
  200.3 J/correct). The 32B pair ran until 11:52. Whatever is partial is marked partial in the PR.
  Finish 32B first.
- **Kinetic F** (`experiments/kinetic/prepare.py`, FineWeb): crashed with a Python fatal dump.
  Low priority, after Trace. Reproduce with a small shard before rerunning in full.
- **Trace:** v1 off-policy on 9k prompts gave +0.7 points of agreement (0.7685) and no speedup.
  On-policy with the bf16 teacher declined, most likely because the target is the Q4_0 7B.

## Next, in order

1. Finish the Lattice 32B pair (both passes), PR it.
2. Trace: harvest the full 35k prompts from the Q4_0 7B
   (`experiments/drafter/teacher.py results/drafter/train-prompts.jsonl data/drafter/teacher.jsonl`),
   then `LR=3e-6 ALPHA=2 train_trace.py`. Pre-registered bar: 0.79 agreement (+3 points).
3. Trace on-policy again, with the Q4_0 7B's own probabilities as teacher.
4. Kinetic data prep, then the four-shape training runs (`docs/kinetic.md`).
5. Clock cap, only with Martin at the keyboard.
