# A second model family: the format findings hold

**Prediction verdict:** held on energy and on batching, missed narrowly on accuracy. On IBM's Granite 3.3 2B, Q4_0 is the cheapest format per weight and per correct answer, and every format's cost per weight lands within 7% of the Qwen2.5 model of the same width. Q4_0 scores 3.6 points below Q8_0, against a predicted 3.

Spliced research note 28, 26 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew). IBM Granite 3.3 2B Instruct (Apache-2.0) and Qwen2.5 3B Instruct.

Every format result in notes 1 to 27 was measured on one model family, Qwen2.5. A finding that holds on one family might belong to that family's shapes rather than to the formats. This note repeats note 6's format sweep on a second family. Granite 3.3 2B has the same hidden width as Qwen2.5 3B, 2,048, which note 6 measured, so the two can be compared weight for weight.

## Method

IBM's own F16 GGUF, its SHA-256 checked against the published hash, quantized here into Q4_0, Q4_K_M, Q5_K_M, Q6_K and Q8_0 with the Homebrew `llama-quantize`, as note 6 did for Qwen2.5. Each file decoded with `phase --seconds 12`, two passes, the second in reverse order, with Qwen2.5 3B's five files run in the same session as a reference. Energy per token is divided by the weights read per token, every tensor except the token embedding table, giving energy per weight. Then GSM8K, 250 problems, 8 requests at once, for Granite's Q4_0, Q4_K_M and Q8_0, two passes in mirrored order.

**A first attempt is void.** The first sweep came back 23 to 77% above note 6 on the same Qwen files at the same speed. The machine was not idle: another project's software container was holding the chip at 10 to 17 W at rest, against 0.6 W on a quiet machine. The `phase` tool now refuses to measure on macOS above 3 W at rest, and this run started only after two quiet readings in a row (0.46 and 0.50 W). The void files are kept in `results/void/`.

## Results

Board energy per weight, picojoules, mean of two passes:

| format | Granite 3.3 2B | Qwen2.5 3B, this session | Qwen2.5 3B, note 6 | Granite against Qwen |
|---|---:|---:|---:|---:|
| Q4_0 | 155.1 | 153.2 | 152.9 | +1.3% |
| Q4_K_M | 190.8 | 183.0 | 182.7 | +4.3% |
| Q5_K_M | 246.9 | 232.4 | 231.4 | +6.3% |
| Q6_K | 243.9 | 229.2 | 229.5 | +6.4% |
| Q8_0 | 265.3 | 247.8 | 250.1 | +7.1% |

GSM8K, 8 requests at once:

| Granite format | accuracy | chip J per correct answer | tokens per answer | chip mJ per token |
|---|---:|---:|---:|---:|
| Q4_0 | 75.2% | 20.0 | 260 | 57.8 |
| Q4_K_M | 74.4% | 20.4 | 219 | 69.3 |
| Q8_0 | 78.8% | 20.6 | 255 | 63.5 |

## 1. The cost of a weight belongs to the format and the width

At the same width, a Granite weight costs within 1.3 to 7.1% of a Qwen weight in every format. The order of the formats is the same: Q4_0 cheapest, then Q4_K_M, then Q5_K_M and Q6_K together, then Q8_0. Granite is always slightly the dearer. It has 40 layers to Qwen 3B's 36, with narrower feed-forward blocks (8,192 against 11,008), so each token passes through more, smaller matrices. The Qwen reference in this session matched note 6, two days earlier, within 0.9% in every format, so the comparison rests on a machine that measured the same thing twice.

## 2. Per correct answer the formats nearly tie

Per correct answer, Q4_0 is cheapest, but by 2 to 3%. Q8_0 answers 3.6 points more often, which nearly pays for its larger weights. At 8 requests at once Q8_0 also costs less per token than Q4_K_M, 63.5 against 69.3 millijoules: in a batch, the work of unpacking a K-quant shows, as note 5 found for a single matrix. Q4_K_M gives shorter answers, 219 tokens against 260, which is why it nearly matches Q4_0 per answer despite costing more per token.

## 3. Batching has the same shape

A third pre-registered run, 512-token answers, batches 1 to 32, with a same-session Qwen2.5 1.5B reference that matched note 24 within 6% at every batch:

| batch | 1 | 2 | 4 | 8 | 16 | 32 |
|---|---:|---:|---:|---:|---:|---:|
| Granite 2B Q4_0, mJ per token | 149 | 152 | 80 | 44 | 38 | 46 |
| Qwen2.5 1.5B Q4_0, mJ per token | 107 | 106 | 55 | 31 | 27 | 30 |

Granite follows note 24's curve on this machine: no saving at the second request, 70% less by batch 8, cheapest at 16, and 21% dearer at 32. The knee belongs to the machine, as note 24 concluded, on a second family too.

## What this changes

- The format recipe on the Systems page, Q4_0 below 32B, holds on a second family. On Granite the margin per correct answer is small, so a model that loses more accuracy at Q4_0 than Granite does could reverse it; check accuracy per model.
- Batching now holds on two families (section 3). Speculative decoding has been measured only on Qwen2.5.

## Limits

- One machine, one Granite size, one task. Two families now, not all families.
- Board energy for the format sweep, chip energy for GSM8K, as in notes 6 and 19.
- The token embedding table is left out of the weight count, as in note 6, though both models reuse it as the output layer.

## Reproduce

```bash
curl -L -o models/quant/granite2b-F16.gguf https://huggingface.co/ibm-granite/granite-3.3-2b-instruct-GGUF/resolve/main/granite-3.3-2b-instruct-f16.gguf
for f in Q4_0 Q4_K_M Q5_K_M Q6_K Q8_0; do llama-quantize models/quant/granite2b-F16.gguf models/quant/granite2b-$f.gguf $f; done
sh experiments/when_quiet.sh experiments/width_granite.sh   # waits for a quiet Mac, then the sweep and GSM8K
```

Raw: `results/decode-batch-mac-granite2b-q4_0-a512.json`, `results/decode-batch-mac-1.5b-q4_0-a512-ref.json` (section 3, `experiments/batch_granite.sh`), `results/width-granite-run1.json`, `results/width-granite-run2.json`, `results/summary-width-granite.json`, `results/quality-mac-granite2b-*-pass{1,2}.json`.
