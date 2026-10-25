# Our first model: a distilled draft model, and what it did not fix

Spliced research note 15, 24 October 2026. Apple M5 Pro, 24 GB, macOS 27, on AC. llama.cpp build 11669 (Metal), llama-server. Target Qwen2.5 7B Instruct Q4_0. Drafts: Qwen2.5 0.5B Instruct, stock and distilled, both Q4_0 through the same conversion.

Notes 7, 9 and 11 used the stock Qwen2.5 0.5B as a draft model for speculative decoding. A draft is only useful when the big model accepts its guesses, so we built one trained to guess the 7B: the Spliced drafter. Primer 7 explains distillation; this note is the measurement.

## How it was built

1. 3,600 prompts, chat and code, from UltraChat (MIT) and CodeAlpaca (CC-BY-4.0); 80 more held out, never trained on.
2. The 7B answered every prompt greedily, up to 384 tokens: 1.14 million tokens of the teacher's own output.
3. The 0.5B was fully fine-tuned on those answers with the prompt masked out (MLX, AdamW, learning rate 1e-5, batch 8, two epochs). 5% of the answers were held back as a validation set.
4. Both the stock and the tuned 0.5B were converted and quantized to Q4_0 by the same script, so their training is the only difference.

The whole pipeline, data to quantized model, ran on one laptop. Code: `experiments/drafter/`.

## Did training work?

Yes, on its own terms. On the held-out validation answers (56,815 tokens the model never trained on), the distilled model predicts the 7B better: mean loss 0.848 against 0.904 for the stock model, perplexity 2.33 against 2.47. That is a 6% lower loss.

## Did it make a better draft?

Barely. Twenty chat and twenty code held-out prompts, 256 greedy tokens each, two passes with the second in reverse order. Every condition's two passes agreed within 1.6% on chip energy. Energy and speed are relative to plain decoding of the same prompts (chip 363 mJ, system 826 mJ per token, 61.5 tok/s). "Drafted" and "accepted" count draft tokens per generated token.

Chat:

| draft | chip energy | system energy | speed | drafted | accepted |
|---|---:|---:|---:|---:|---:|
| stock, 4, p0.5 | 1.081 | 0.796 | 1.23x | 0.77 | 0.54 |
| Spliced, 4, p0.5 | 1.090 | 0.778 | 1.26x | 0.93 | 0.57 |
| Spliced, 4, p0.7 | 1.088 | 0.830 | 1.18x | 0.63 | 0.50 |
| stock, 8, p0.7 | 1.084 | 0.879 | 1.13x | 0.53 | 0.45 |
| Spliced, 8, p0.7 | 1.077 | 0.823 | 1.19x | 0.70 | 0.52 |

Code:

| draft | chip energy | system energy | speed | drafted | accepted |
|---|---:|---:|---:|---:|---:|
| stock, 4, p0.5 | 0.905 | 0.590 | 1.53x | 0.90 | 0.65 |
| Spliced, 4, p0.5 | 0.905 | 0.590 | 1.55x | 0.97 | 0.67 |
| Spliced, 4, p0.7 | 0.925 | 0.627 | 1.45x | 0.78 | 0.62 |
| stock, 8, p0.7 | 0.925 | 0.653 | 1.41x | 0.78 | 0.63 |
| Spliced, 8, p0.7 | 0.944 | 0.652 | 1.41x | 0.93 | 0.66 |

Thresholds 0.6 and 0.8 sit on the same lines and are in `results/drafter/eval-thresholds-mac.json`.

## 1. The gain is real and small

At the best setting for both, four tokens at a 0.5 threshold, the Spliced drafter gets 0.03 more accepted tokens per generated token on chat and 0.02 more on code. That is 2 to 3% more speed, and on chat 2% less whole-system energy. On code the two drafters cost the same. At eight tokens and a 0.7 threshold the gap is wider on chat: 1.19 times plain speed against 1.13, and 0.823 against 0.879 of plain system energy.

A 6% lower loss bought about 3% more acceptance. Loss averages how well the model predicts every token; acceptance only asks whether its top guess matches the 7B's top guess, and the stock 0.5B, from the same family and trained on similar data, already agreed with the 7B on most of the easy tokens. Distillation mostly improved tokens the draft was already getting right.

## 2. Our hypothesis about the threshold was wrong

The first evaluation found the Spliced drafter proposing more tokens per accepted one, and we guessed it was overconfident and needed a higher threshold. It does propose more: at p0.5 it drafts 0.93 tokens per generated token on chat against 0.77. But raising its threshold made it worse at every step, for both drafters, on both kinds of prompt. A rejected draft token is cheap on this machine, and a confident draft that is right half the time still wins. 0.5 is the best threshold we tested for either model, as note 9 found for the stock one.

## 3. On this machine, speculation saves time more than chip energy

On chat, every speculative setup used 8 to 11% more chip energy per token than plain decoding, while finishing 13 to 26% sooner. On code, where drafts are accepted more often, it saved 5 to 10%. The whole system saves far more, 12 to 41%, because the rest of the machine draws power for as long as generation runs, and speculation shortens that time. Which number matters depends on what you pay for: a phone or laptop on battery pays the system figure, while a datacenter accelerator's bill is closer to the chip figure. This agrees with note 7.

## What to take from this

1. A 0.5B drafter distilled from 1.14 million tokens of 7B output lowers held-out loss 6% and raises acceptance about 3%. Real, small, and on a laptop's budget.
2. The draft's confidence threshold was not the problem. 0.5 stays best for both drafters.
3. Lower loss is the wrong target for a draft model. What matters is top-1 agreement with the target on the tokens the stock draft gets wrong. The next version should train on those directly: distil the 7B's full output distribution rather than its sampled text, and weight the tokens where the stock draft disagrees.

## Limits

One target and one draft family, which already agree often; a draft from a different family would have more to gain. 3,600 training prompts, two epochs, no hyperparameter search. 40 evaluation prompts, chat and code only, 256 tokens. Greedy decoding. One machine; Windows cannot run llama-server under Smart App Control (note 11). The model is not yet published as a download.

## Reproduce

```
uv run --extra mlx python experiments/drafter/prepare.py
uv run python experiments/drafter/generate.py
sh experiments/drafter/pipeline.sh
uv run --extra mlx python experiments/drafter/loss.py results/drafter/loss-mac.json
uv run python experiments/drafter/evaluate.py results/drafter/eval-thresholds-mac.json plain,stock-4-p0.5,stock-4-p0.7,spliced-4-p0.5,spliced-4-p0.6,spliced-4-p0.7,spliced-4-p0.8,stock-8-p0.7,spliced-8-p0.7,spliced-8-p0.8
```

Raw results: `results/drafter/loss-mac.json`, `results/drafter/eval-mac.json`, `results/drafter/eval-thresholds-mac.json`.
