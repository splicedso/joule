# Decode energy against batch size on the Strix Halo: no knee to batch 32, and a slow spot at 16

The Strix Halo half of note 24's question (`experiments/decode_batch_energy.py`, Qwen2.5 7B Q4_0, llama.cpp
620d2225c Vulkan, auto clocks, shared 90%, package power from the amdgpu hwmon, not wall; llama-server at
--parallel N, N simultaneous answers, two passes with the second reversed). Ran 07:53 to 07:58 PDT with nothing
else on the GPU, right after the QAT quality runs. A first run at 06:32 is void (the script read no power on
Linux; fixed in PR #24) and is not here.

Two runs: **as specified**, 128-token answers, comparable to note 24; and **ANSWER=512**, because a 128-token
answer at batch 1 is a 2.6 s window here (13 samples at 5 Hz), short for the package sensor. Summaries from
`experiments/decode_batch_summary.py`.

## 128-token answers (as specified)

| batch | tok/s | tok/s per request | W | mJ/token pass 1 | pass 2 | mean | vs batch 1 | spread |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 48.6 | 48.6 | 84.4 | 1551 | 1922 | 1737 | | **21.4%** |
| 2 | 92.5 | 46.3 | 102.5 | 1022 | 1195 | 1109 | 36% less | **15.6%** |
| 4 | 175.4 | 43.9 | 126.4 | 686 | 756 | 721 | 58% less | **9.7%** |
| 8 | 271.9 | 34.0 | 125.9 | 471 | 456 | 463 | 73% less | 3.2% |
| 16 | 300.7 | 18.8 | 95.7 | 317 | 319 | 318 | 82% less | 0.5% |
| 32 | 565.4 | 17.7 | 102.4 | 177 | 186 | 181 | 90% less | 4.8% |

## 512-token answers

| batch | tok/s | tok/s per request | W | mJ/token pass 1 | pass 2 | mean | vs batch 1 | spread |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 48.3 | 48.3 | 103.6 | 2069 | 2217 | 2143 | | **6.9%** |
| 2 | 92.8 | 46.4 | 124.6 | 1289 | 1396 | 1342 | 37% less | **8.0%** |
| 4 | 169.1 | 42.3 | 141.8 | 837 | 840 | 839 | 61% less | 0.3% |
| 8 | 263.7 | 33.0 | 141.9 | 536 | 540 | 538 | 75% less | 0.6% |
| 16 | 299.3 | 18.7 | 103.8 | 347 | 347 | 347 | 84% less | 0.1% |
| 32 | 573.1 | 17.9 | 111.5 | 190 | 199 | 195 | 91% less | 4.9% |

Spreads over 5% are bold. The batch 1 to 4 gaps in the 128-token run are power at equal speed (batch 1: 75.4
against 93.3 W) in windows of 2.6 to 3.0 s; the 512-token run's longer windows shrink them to 0.3 to 8%. Some
512-token answers end early (the model stops at about 368 tokens on this prompt), so from batch 8 up the
concurrency falls during the window; the 128-token run has no early stops and is the clean one for the shape.

## Against the prediction (docs/predictions.md, the decode-batch entry; Strix Halo clauses)

- Batch 1 to 8 falls steeply: 73% less (75% at 512). Held.
- 8 to 16 a further 15 to 30%: **31%** (36% at 512). Missed narrowly.
- **Knee at 8 to 16 on the Strix Halo: missed.** Energy per token keeps falling to 32, by a further 43% from 16
  (44% at 512), and total throughput nearly doubles from 16 to 32 (301 to 565 tok/s). On the M5 Pro batch 32
  was 15% worse than 16; here it is the best point measured.
- Tokens per second per request at 16 below half of batch 1: 18.8 against 48.6, 39%. Held.
- Passes within 5% at every batch: missed (batches 1, 2 and 4 in the 128-token run; 1 and 2 at 512).

## The slow spot at batch 16

Batch 16 is anomalous in both runs: throughput rises only 11% over batch 8 (272 to 301 tok/s, 264 to 299 at 512)
while package power **drops** from 126 to 96 W (142 to 104 W at 512), and at 512 tokens the batch-16 window
(27.1 s for 8,124 tokens) is longer than batch 32's (20.5 s for 11,776). The GPU is underused at exactly 16
concurrent sequences, and fully used again at 32. That looks like the llama.cpp Vulkan backend choosing a slower
matrix kernel path at 16 rows, not a hardware ceiling; it is not diagnosed here. The practical reading: on this
machine and build, serve at 8 or at 32, not at 16. Batch 16's low energy per token is real, but it comes from
low power at low throughput.

Raw: `results/decode-batch-halo-7b.json` (128), `results/decode-batch-halo-7b-a512.json` (512).
