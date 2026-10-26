# Where batching stops paying

**Prediction verdict:** held on the fall (74% less energy per token from batch 1 to 8, a further 19% to 16, speed per request at 38% of batch 1 by 16); missed on the top end, where energy per token rose 15% from batch 16 to 32 instead of flattening, and on pass agreement, which was 5.2 and 5.7% at two batches against a predicted 5%.

Spliced research note 24, 25 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew), llama-server. Qwen2.5 7B Instruct Q4_K_M (the Q4_0 the prediction names is not on this machine; Q4_K_M is the format every earlier Mac 7B figure used).

Note 1 measured that serving eight requests at once cuts chip energy per token 72% on a 1.5B model, and stopped at eight. Note 8's roofline says a server has to batch tens of sequences per weight pass before the memory traffic is paid for. The cluster reading note ranks one question first: on the machines we own, where does energy per token stop falling as the batch grows? This note answers it on the Mac at a 7B.

**Prediction** (`docs/predictions.md`, committed before the run): steep fall from 1 to 8, a further 15 to 30% to 16, then flat from 16 to 32 with under 10% more saving because the 7B is compute bound there; speed per request under half of batch 1 by 16; passes within 5%.

## Method

`experiments/decode_batch_energy.py`. For each batch N in 1, 2, 4, 8, 16, 32, llama-server is started fresh with `--parallel N` and a context of 1,024 tokens per slot, warmed with one 16-token batch, then sent N identical requests at once, each a 128-token answer to the same short prompt at temperature 0. Chip power is sampled by macmon at 5 Hz over the whole window and tokens are read from the server's timings. Energy per token is mean watts times window seconds over tokens generated. Two passes, the second in reverse order; the table is the mean of both.

Chip power only (CPU, GPU, memory interface), not the board or the wall: the board reading is smoothed to about 1 Hz and the batch-1 window is 2.3 seconds. That matters for the direction of the result, below.

## Results

| batch | tok/s | tok/s per request | W | mJ per token | vs batch 1 | pass spread |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 55.6 | 55.6 | 29.7 | 534 | | 5.2% |
| 2 | 94.5 | 47.3 | 45.8 | 485 | 9% less | 3.4% |
| 4 | 163.6 | 40.9 | 41.6 | 255 | 52% less | 5.7% |
| 8 | 293.2 | 36.6 | 40.3 | 137 | 74% less | 3.4% |
| 16 | 338.8 | 21.2 | 37.5 | 111 | 79% less | 3.0% |
| 32 | 322.7 | 10.1 | 41.2 | 128 | 76% less | 1.3% |

The batch-1 row agrees with the README's 7B decode figure measured by llama-bench (544 mJ per token at 57.7 tok/s), a second tool giving the same number.

## 1. The fall is as steep at 7B as at 1.5B

Batch 8 costs 26% of batch 1 per token here; note 1 measured 28% on the 1.5B. The second request is nearly free in throughput (94.5 against 55.6 tok/s) but not in energy: chip power jumps from 29.7 to 45.8 W at batch 2 and then drifts down as the batch grows, so batch 2 saves only 9%. From 4 on, power is roughly flat at about 40 W while throughput keeps climbing, and that is where the saving comes from.

## 2. The knee is at 16, and 32 is worse

Energy per token bottoms at 111 mJ at batch 16 and rises to 128 at 32, with total throughput falling from 338.8 to 322.7 tok/s. The 7B is compute bound on this chip well before 16: note 5's measured roof is 307 GB/s, and the Q4_K_M weights are 4.68 GB, so a memory-bound chip would decode 66 tokens per weight pass and about 1,050 tok/s at batch 16. The chip delivers 339, a third of that, so the batch stopped buying throughput by around 8 and the saving from 8 to 16 came from spreading the same power over more tokens. Past 16, more slots add KV-cache reads and per-step scheduling without adding throughput, and this run shows that as a 15% energy penalty. The prediction expected a plateau; the measurement says there is an optimum, and on this machine for this model it is 16.

## 3. What each request gives up

Per request, batch 16 decodes at 21.2 tok/s, 38% of batch 1, and batch 32 at 10.1. A chat user notices the difference between 55 and 21 tok/s. This is the trade Fabric's scheduler has to make per module: on this machine a decode module should hold about 16 slots, and adding a 17th costs both energy and speed.

## What this changes

- Fabric's cost table carried note 1's 1.5B curve to batch 8 as its batch curve, labelled as transferred. It now carries this 7B curve to 32, still transferred to the Strix Halo until the same script runs there, with the knee at 16.
- The Systems page's per-module figure assumed 8 slots. Sixteen is 19% cheaper per token on this chip; the Strix Halo's knee is expected earlier (its capped runs are compute bound at 8), which the Linux run will settle.

## Limits

- Chip energy only, not wall. Idle and board power are a fixed cost per second, so at the wall batching pays more than this table shows and the knee moves later, not earlier.
- Short windows: 2.3 seconds and 10 power samples at batch 1, 12.7 seconds at 32. Two batches spread over 5% between passes.
- One prompt and one answer length. Longer contexts make the KV-cache read a larger share of each step and move the knee down (note 14 measured batching at 4,096-token contexts on the Windows laptop; this run did not vary context).
- Q4_K_M, not the Q4_0 the prediction names. Note 5 found the two read the same bytes with Q4_K costing more to unpack; the shape of the curve should carry, the mJ figures are Q4_K_M's.
- Why batch 32 is slower in total than 16 was not isolated; the server was started fresh per batch and the context per slot was constant, so it is the batch, not memory pressure from a larger context.

## Reproduce

```bash
brew install macmon llama.cpp
uv run python experiments/decode_batch_energy.py models/Qwen2.5-7B-Instruct-Q4_K_M.gguf results/decode-batch-mac-7b-q4km.json
uv run python experiments/decode_batch_summary.py results/decode-batch-mac-7b-q4km.json
```

Nothing else running: no browser, no Blender. Raw result: `results/decode-batch-mac-7b-q4km.json`.
