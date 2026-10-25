# Predictions, written before the results

Each entry is committed before its experiment produces numbers, so the note that reports it
can say plainly whether the prediction held. Entries are never edited after the result exists;
a wrong prediction stays here.

## 2026-10-25, 05:05 PT

**Trace v1** (Strix Halo, logit distillation on about 8,000 to 35,000 prompts of the 7B's
top-20 distribution, stock-miss weighting ALPHA=2, early stopping on held-out agreement).
- Held-out top-1 agreement with the 7B rises above stock (0.7616) and plateaus between 0.78
  and 0.80 within one epoch. It clears the +3 point bar (0.79) on the full 35,000 prompts but
  not on the first 8,000.
- ALPHA=0 lands within 0.5 points of ALPHA=2; the weighting is not where the gain comes from.
- In speculative decoding at k=4, p=0.5, accepted tokens per generated token rise by less
  than the agreement gain suggests, because the stock draft already gets the easy tokens.

**Lattice item D** (Strix Halo, Qwen2.5 7B and 32B, Q4_0 against GSM8K-calibrated Q2_K).
- 7B: Q4_0 is cheaper per correct answer than calibrated Q2_K, as on the 1.5B (note 20).
- 32B: calibrated Q2_K loses fewer accuracy points to Q4_0 than the 1.5B did (larger models
  quantize more gracefully), and its energy per token is lower than Q4_0's, because the 32B
  decode is bound by memory traffic. Whether it wins per correct answer is close; we predict
  it does, by less than 15%.

**Warm-up** (Strix Halo, 7B Q4_0 decode, cold first phase against after a warm-up).
- Warm package power is 20 to 30% above cold, at the same tokens per second, so a cold
  first measurement understates energy per token by the same amount.

**Kinetic** (four shapes at about 72M parameters, the same 1B tokens; docs/kinetic.md).
- The wide shape (6 x 1024) has the lowest decode energy per token on both machines.
- The deep shape (24 x 512) has the best held-out loss, by less than 5%.
- On joules per correct answer, wide beats base by at least 15% on both machines.
