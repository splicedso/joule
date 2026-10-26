# Where batching stops paying

**Prediction verdict, 7B:** held on the fall (74% less energy per token from batch 1 to 8, a further 19% to 16, speed per request at 38% of batch 1 by 16); missed on the top end, where energy per token rose 15% from batch 16 to 32 instead of flattening, and on pass agreement, which was 5.2 and 5.7% at two batches against a predicted 5%. **1.5B (second prediction, same evening):** held on the knee (lowest at 16, batch 8 saves 69%, speed per request 38% at 16, passes within 4.8%); missed on the ceiling (1,171 tok/s, not about 1,800) and narrowly on batch 32, which costs 12% more than 16 against a predicted 10%.

Spliced research note 24, 25 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew), llama-server. Qwen2.5 7B Instruct Q4_K_M (the Q4_0 the prediction names is not on this machine; Q4_K_M is the format every earlier Mac 7B figure used), then Qwen2.5 1.5B Instruct Q4_0 under a second prediction.

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

## 4. The knee does not move with model size

A second prediction, committed after the 7B result and before this run, asked whether a smaller model, with nine times the memory headroom per token, moves the knee later. Same script, Qwen2.5 1.5B Q4_0 (note 1's model and format), run on the same idle machine straight after.

| batch | tok/s | tok/s per request | W | mJ per token | vs batch 1 | pass spread |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 191.0 | 191.0 | 18.5 | 97 | | 4.8% |
| 2 | 326.5 | 163.3 | 32.7 | 100 | 3% more | 0.9% |
| 4 | 611.5 | 152.9 | 32.4 | 53 | 45% less | 0.1% |
| 8 | 1,025.5 | 128.2 | 30.3 | 30 | 69% less | 1.8% |
| 16 | 1,171.1 | 73.2 | 30.1 | 26 | 74% less | 3.6% |
| 32 | 963.0 | 30.1 | 27.6 | 29 | 70% less | 1.3% |

The same shape at a fifth of the size: lowest at 16, 12% more at 32, total throughput down from 1,171 to 963 tok/s. The prediction said the minimum would sit at 16 or 32 and that 32 would be within 10% of it; it is 12% off, so the top end missed narrowly in the same direction as the 7B. The predicted ceiling of about 1,800 tok/s was wrong too: the chip tops out at 1,171 on this model, which is 3.0 TFLOPS of useful work against 5.2 on the 7B, so the small model gets less of the chip, as note 6 found per weight.

Batch 1 to 8 reproduces note 1, which measured the same model and format with a different tool (llama-batched-bench, 512-token answers): 104.7, 103.3, 54.3 and 29.3 mJ per token there against 97, 100, 53 and 30 here, within 8% at every batch, including the finding that batch 2 saves nothing because chip power nearly doubles.

## What this changes

- Fabric's cost table carried note 1's 1.5B curve to batch 8 as its batch curve, labelled as transferred. It now carries the 7B curve to 32, still transferred to the Strix Halo until the same script runs there, with the knee at 16.
- The Systems page's per-module figure assumed 8 slots. Sixteen is 19% cheaper per token on this chip at 7B and 13% at 1.5B; the Strix Halo's knee is expected earlier (its capped runs are compute bound at 8), which the Linux run will settle.
- Two model sizes put the knee at the same batch on this chip. The place to look for it moving is the machine, not the model.

## Limits

- Chip energy only, not wall. Idle and board power are a fixed cost per second, so at the wall batching pays more than this table shows and the knee moves later, not earlier.
- Short windows. 7B: 2.3 seconds and 10 power samples at batch 1, 12.7 seconds at 32; two batches spread over 5% between passes. 1.5B: 0.7 seconds and 2 samples at batch 1, 3 to 4 samples through batch 8, 7 at 16 and 19 at 32, so its small-batch rows are thin on power and stand on their agreement with note 1; the knee rows have 7 and 19 samples.
- One prompt and one answer length. Longer contexts make the KV-cache read a larger share of each step and move the knee down (note 14 measured batching at 4,096-token contexts on the Windows laptop; this run did not vary context).
- The 7B is Q4_K_M, not the Q4_0 the prediction names. Note 5 found the two read the same bytes with Q4_K costing more to unpack; the shape of the curve should carry, the mJ figures are Q4_K_M's.
- Why batch 32 is slower in total than 16 was not isolated; the server was started fresh per batch and the context per slot was constant, so it is the batch, not memory pressure from a larger context.

## Reproduce

```bash
brew install macmon llama.cpp
uv run python experiments/decode_batch_energy.py models/Qwen2.5-7B-Instruct-Q4_K_M.gguf results/decode-batch-mac-7b-q4km.json
uv run python experiments/decode_batch_summary.py results/decode-batch-mac-7b-q4km.json
uv run python experiments/decode_batch_energy.py models/qwen2.5-1.5b-instruct-q4_0.gguf results/decode-batch-mac-1.5b-q4_0.json
uv run python experiments/decode_batch_summary.py results/decode-batch-mac-1.5b-q4_0.json
```

Nothing else running: no browser, no Blender. Raw results: `results/decode-batch-mac-7b-q4km.json`, `results/decode-batch-mac-1.5b-q4_0.json`.
