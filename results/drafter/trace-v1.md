# Trace v1: training a 0.5B to trace Qwen2.5 7B

Prediction before the runs: with ~10x v0's prompts and the teacher's top-20 distribution,
held-out top-1 agreement with the 7B would clear the stock draft by at least 3 points (>= 0.79),
and on-policy distillation (DistillSpec, Zhou et al. 2023) would do better still. Neither held.

Stock Qwen2.5 0.5B agreement with the 7B on the 180 held-out prompts: **0.7616**.

## Attempts (all on the Linux machine, gfx1151, ~9-10k teacher prompts, shared 90%)

| run | method | best held-out agreement | vs stock |
|---|---|---:|---:|
| off-policy, ALPHA=2, LR 1e-5 | top-20 CE, stock-wrong positions weighted | 0.7616 (step 0) | +0.00 |
| off-policy, ALPHA=2, LR 3e-6 | same, lower LR | **0.7685** | +0.69 |
| on-policy, TVD, LR 3e-6, 300 steps | student rolls out, bf16 7B grades its tokens | 0.7616 (step 0) | +0.00 (declined) |

Curves:
- off-policy LR 1e-5: 0.7564, 0.7549, 0.7545, 0.7560, 0.7557 (steps 200..1000). Below stock the whole epoch, matching the Mac's MLX runs.
- off-policy LR 3e-6: 0.7660, 0.7673, 0.7665, 0.7683, 0.7685 (steps 200..1000). Above stock, flattening at +0.7.
- on-policy TVD: 0.7600, 0.7606, 0.7592, 0.7582, 0.7574, 0.7574 (steps 50..300). Slight monotonic decline.

## Why on-policy declined (hypothesis)

The on-policy teacher is the **bf16** 7B (transformers), but held-out agreement is scored against
the **Q4_0** 7B's own answers (the acceptance target, from teacher.py). Matching the bf16
distribution on the student's rollouts can move the student away from the Q4_0 target it is judged
on. Pulling the teacher logits from the Q4_0 7B through llama.cpp instead would remove the mismatch,
but that is a larger change (llama.cpp, not transformers). Secondary: only 300 steps / 1,200
rollouts against ~10k prompts, so it is also underfit.

## Standing result

No method cleared the +3 bar. The best Trace v1 so far is **off-policy, LR 3e-6, 0.7685 (+0.7)**;
its acceptance, speed and chip energy against the stock draft are measured in
`results/drafter/eval-v1-halo.json`. The most promising untried lever is scale: the off-policy
LR 3e-6 run was still inching up at the end of one epoch on ~9k prompts, so retraining on the full
35k (once the teacher run finishes) is the next step.
