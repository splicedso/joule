# Per correct answer, how a model is served matters as much as its size

Spliced research note 19, 25 October 2026. Two machines: an Apple M5 Pro (24 GB, macOS 27, Metal) and an AMD Ryzen AI Max+ 395 (Strix Halo, Radeon 8060S, 125 GB, Linux, Vulkan). llama.cpp build 11669 (620d2225c) on both, llama-server, Qwen2.5 1.5B and 7B Instruct Q4_0, all layers on the GPU.

Our earlier notes measured energy per token. That rewards a model that answers quickly and wrongly. This note measures what a user pays for: **joules per correct answer**, the chip energy of a whole evaluation divided by the questions it got right.

**Prediction.** The Mac ran first and found that the 7B serving eight requests at once costs less per correct answer than the 1.5B serving one at a time. Before the second machine ran, we predicted the same ordering would hold there. It did.

## Method

`experiments/quality.py`: the first 250 GSM8K test questions (grade-school maths, MIT licence), greedy, through llama-server's chat endpoint, with 1 or 8 requests in flight (slots). The answer is read from `\boxed{}`, else the last "The answer is", else the last number. Chip power is sampled through the whole evaluation. Two passes per cell, the second in reverse order.

The chip figure is the M5 Pro's SoC and the Strix Halo's whole APU package. On the Halo, idle power wandered between 7 and 15 W from run to run, so the gross figure is the headline and the net one, idle subtracted, is shown beside it. The two passes agreed within 2% on the Mac and within 6% on the Halo.

## Results

Accuracy was the same on both machines: 66% for the 1.5B and 88% for the 7B, give or take one question.

| machine | model | slots | accuracy | J per correct answer | net | tok/s |
|---|---|---:|---:|---:|---:|---:|
| M5 Pro | 1.5B | 1 | 66.0% | 40.2 | 39.0 | 197 |
| M5 Pro | 1.5B | 8 | 65.6% | 13.7 | 13.4 | 866 |
| M5 Pro | 7B | 1 | 88.4% | 101.9 | 99.5 | 60 |
| M5 Pro | 7B | 8 | 88.0% | 35.1 | 34.6 | 279 |
| Strix Halo | 1.5B | 1 | 66.0% | 230.9 | 208.9 | 178 |
| Strix Halo | 1.5B | 8 | 66.6% | 65.2 | 60.9 | 648 |
| Strix Halo | 7B | 1 | 88.8% | 609.0 | 568.1 | 48 |
| Strix Halo | 7B | 8 | 88.4% | 156.6 | 147.0 | 210 |

## 1. A bigger model, batched, beats a smaller one alone

On both machines the 7B serving eight requests costs less per correct answer than the 1.5B serving one: 35 against 40 J on the Mac (0.87 times), and 157 against 231 J on the Halo (0.68 times). It also answers 22 points more questions correctly.

At equal serving the small model is still cheaper: at eight slots the 1.5B costs about 40% of the 7B per correct answer on both machines. So the choice isn't simply small or large. Batching cut the cost per correct answer 2.9 times on the Mac and 3.5 to 3.9 times on the Halo, which is about as much as changing model size. A deployment that serves one request at a time on a small model can pay more per right answer than one that batches a model five times larger.

## 2. The same accuracy costs four and a half to six times more on the Halo

The two machines scored the same, and the Halo spent 4.5 to 6 times the chip energy on them. The Halo's package draws 109 to 126 W during these runs, against 21 to 37 W for the M5 Pro's SoC, at similar or lower speed.

One measurement points at why. During 7B decode, which waits on memory, the Halo's shader clock sits at its 2,900 MHz ceiling, the same as during compute-bound prefill, and the package draws 105 W. At idle the clock falls to 785 MHz and the package to about 14 W (`results/halo-gpuclock.json`). The GPU runs flat out while it waits. We haven't tested whether capping the clock during decode keeps the speed and cuts the energy, because that needs a system setting changed.

The two machines' chip figures are not the same boundary: the Halo's is the whole APU package and the Mac's is the SoC. Neither includes the rest of the machine.

## What to take from this

1. Measure cost per correct answer, not per token. It changes which configuration looks cheapest.
2. Serving many requests at once can make a model five times larger cheaper per right answer than a small model served alone. Batching and model size are levers of the same order.
3. On the Strix Halo, the GPU clock stays at its maximum through memory-bound decode. A decode-time clock cap is the obvious next test.

## Limits

One task (GSM8K) and its first 250 questions, greedy, one answer format. Two models from one family, one quantization. Chip energy only, with different boundaries on the two machines. Accuracy is the model's on this prompt format, not its best possible.

## Reproduce

```
uv run python experiments/quality.py models/quant/<size>-Q4_0.gguf results/quality-<machine>-<size>-s<slots>-run<pass>.json 250 <slots>
```

Raw results: `results/quality-mac-*.json`, `results/quality-halo-*.json`, `results/halo-gpuclock.json`, `results/halo-quality.md`.
