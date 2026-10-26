# Trace v1 at 35,000 prompts: agreement +1.4 points, the 0.79 bar missed, no faster than the stock draft

**Verdicts on the pre-registered predictions.** 05:05 entry: "clears the +3 point bar (0.79) on the full
35,000 prompts": **missed**, 0.7754. 14:30 entry (committed 14:17, d825a8f): the 35k draft is 1.3x to 1.6x
faster than plain decoding at k=4 with lower chip energy (**held**, 1.44x, 34% less) and within 5% of the
stock draft's speed (**held**, 2.3% slower); acceptance rises over stock by less than the agreement gain
suggests (**missed on the acceptance rate**, +3.6 points against +1.4 of agreement; **held on accepted tokens
per generated token**, which fell 0.9 points, see below). Teacher faithfulness (14:30 entry): the dequantized
Q4_0 teacher matches at least 99% (**missed narrowly**, 98.8%), bf16 between 96 and 98.5% (**missed**, 93.3%).

What every number here is measured against: the **Q4_0 7B as served by llama.cpp**. `teacher.py` harvests
from `models/quant/7b-Q4_0.gguf` through llama-server (greedy, `n_probs` 20); the held-out set is the 180
validation prompts' answers harvested the same way (56,600 answer positions), and `train_trace.py`'s
held-out agreement compares the draft's top-1 with that model's top-1 at each position (the chosen token
equals llama.cpp's top-1 at all 56,600). The speculative eval runs the same Q4_0 7B as target. So the
0.79 bar is agreement with the model the draft serves.

## Training (Strix Halo, shared 90%, PyTorch 2.10 on ROCm 7.2)

Harvest resumed from 10,005 to all 35,000 training prompts plus the 180 held out (`data/drafter/teacher.jsonl`,
35,180 records), interrupted once for the capped quality run (note 23) and resumed. Then
`ALPHA=2 EPOCHS=1 LR=3e-6 train_trace.py`: one epoch, 4,200 steps, 121 min; early stopping never fired.

Held-out top-1 agreement with the Q4_0 7B, every 200 steps (`results/drafter/train-log-v1-35k.json`):

| step | 0 (stock) | 200 | 1000 | 2000 | 3000 | 3600 | 4000 | 4200 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| agreement | 0.7616 | 0.7663 | 0.7683 | 0.7707 | 0.7724 | 0.7739 | 0.7753 | **0.7754** |

The same recipe on the first 9,000 prompts reached 0.7685. Four times the data bought about 0.7 points
more. The curve was still rising at the end of the epoch, by about 0.5 points over the last 2,000 steps
and slowing.

## Speculative decoding (evaluate.py, Q4_0 7B target, 40 held-out prompts, 256 tokens, one request, two passes)

`--spec-type draft-simple` is set for every draft condition; every speculative row drafted tokens.
Idle 8.4 W. Chip (package) energy.

| condition | tok/s | vs plain | acceptance | accepted per generated token | chip mJ/token | vs plain |
|---|---:|---:|---:|---:|---:|---:|
| plain | 49.6 | 1.00x | | | 2096 | |
| stock draft, k=4 | 73.3 | 1.48x | 71.7% | 0.601 | 1400 | -33% |
| 9k v1, k=4 | 70.1 | 1.41x | 73.6% | 0.581 | 1423 | -32% |
| **35k v1, k=4** | 71.7 | 1.44x | **75.3%** | 0.592 | **1385** | **-34%** |
| stock draft, k=8 | 66.5 | 1.34x | 63.6% | 0.641 | 1450 | -31% |
| 35k v1, k=8 | 67.6 | 1.36x | 67.2% | 0.631 | 1437 | -31% |

Per pass (both passes, second reversed) and the drafted and accepted counts are in
`results/drafter/eval-v135k-halo.json`. **Flagged spreads (over 3%):** stock k=4 tokens per second 4.0% and
mJ per token 3.5% (pass 1 74.8, pass 2 71.9 tok/s); plain mJ per token 3.2%. Every trained draft repeats
within 1.1%.

**Why higher acceptance does not buy speed.** The 35k draft is right more often when it drafts, but it drafts
less: 8,052 tokens proposed against the stock draft's 8,591 per pass at the same 0.5 confidence threshold, so it
lands 6,061 accepted tokens against 6,158. Accepted tokens per generated token, the number speed depends on,
fall from 0.601 to 0.592. Training on the 7B's renormalized top-20 spreads the draft's probability mass, and
fewer tokens clear p 0.5. Against the stock draft at k=4 the 35k draft is 2.3% slower and 1.1% cheaper per
token, both inside the stock draft's own pass-to-pass gap. Split by prompt kind: chat acceptance 70.0% to
72.8%, code 73.1% to 77.4%; code speed is unchanged (79.8 against 79.7 tok/s), chat 4% slower.

## What to take from this

1. **The off-policy method has run out at this size.** 35,000 prompts give +1.4 points of held-out agreement
   and nothing at serving time. More epochs on the same data would land near 0.78 by the curve's slope.
2. **Speculation itself pays on this machine at one request:** any of these drafts makes the 7B 1.4x to 1.5x
   faster and a third cheaper per token (note 21). The trained drafts do not improve on the stock one.
3. **Next and last pilot (agreed with the Mac lead):** on-policy distillation with a teacher faithful to the
   served model, the Q4_0 7B dequantized into transformers (98.8% top-1 agreement with its llama.cpp tokens;
   the bf16 teacher of the failed on-policy run agreed 93.3%). Pre-registered in the 14:30 entry,
   committed 14:17 (d825a8f) before every run. If it does not beat the best off-policy draft by at least one
   point of acceptance at one request, Trace pauses for a write-up. The 72B Trace stays parked.

Raw: `results/drafter/eval-v135k-halo.json`, `results/drafter/train-log-v1-35k.json`,
`results/drafter/teacher-check-halo.json`. Model: `models/trace-0.5b-v1-35k` (not committed; GGUF
`models/quant/drafter-v135k-Q4_0.gguf`).
