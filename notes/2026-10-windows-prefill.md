# Reading the prompt: what prefill costs, and when it dominates

Spliced research note 18 (Windows half), 24 October 2026. Windows 11 laptop: Intel Core Ultra 9 285H, NVIDIA GeForce RTX 5070 Ti Laptop GPU (12 GB, Blackwell), 32 GB RAM, on AC. llama.cpp build 11851 (prebuilt CUDA 13.4 x64), CUDA backend, all layers on the GPU. Qwen2.5 1.5B and 7B, Q4_0.

Notes 13, 14, 16 and 17 measured decode, the tokens a model writes. A real request first reads a prompt, and that prefill costs energy too. This note measures prefill energy per prompt token across prompt lengths, then combines it with note 13's decode-at-depth figures for the same machine to answer a practical question: for a request with a short answer, what share of the energy is the prompt?

## Method

Prefill energy per prompt token from `phase` (llama-bench with `-p N -n 0`), batch 1, f16 cache with flash attention, prompt lengths 128, 512, 2048, 8192 and 16384 tokens. `--seconds 15` so even the fast short prefills fill a long enough window. Three passes per cell; all cells repeated within 2.3%. GPU (chip) energy only, as in note 4. The share calculation below combines these prefill figures with note 13's decode-at-depth figures (same machine, same build), decode interpolated to the prompt length; it is a calculation from two measured sources, not a single measurement.

## Prefill energy per prompt token

| prompt tokens | 1.5B mJ/tok | 7B mJ/tok |
|---:|---:|---:|
| 128 | 9.14 | 28.80 |
| 512 | 6.55 | 24.29 |
| 2048 | 7.04 | 24.88 |
| 8192 | 8.51 | 27.38 |
| 16384 | 10.37 | 31.68 |

Two things. First, a prompt token is cheap next to a generated one: at 512 tokens the 7B reads a token for 24.3 mJ and, from note 13, writes one for about 1030 mJ at low depth, roughly 42 times more. Reading is far cheaper than writing. Second, prefill per token is not flat. It falls to a minimum near 512 tokens, where the fixed cost of launching the pass is spread over enough tokens, then rises as the prompt grows and attention over the prompt becomes a larger part of each token. From 512 to 16384 tokens, a 32-fold increase, the per-token cost rose 58% on the 1.5B (6.55 to 10.37) and 30% on the 7B (24.29 to 31.68). Attention makes it grow, but slowly: even at 16384 tokens it is still a minority of the per-token cost.

## What share of a request is the prompt

Combining the prefill figures above with note 13's decode-at-depth, for a request with a 300-token answer:

| prompt tokens | 1.5B prefill share | 7B prefill share |
|---:|---:|---:|
| 500 | 3.6% | 3.8% |
| 2000 | 13.1% | 13.4% |
| 8000 | 40.6% | 39.9% |
| 8000, cached prefix | 0% | 0% |

The share is almost the same on both models, because both prefill and decode scale with model size in step, so their ratio does not. With a short answer, the prompt is a few percent of the energy for a chat-sized request, about an eighth for a 2000-token prompt, and about 40% once the prompt reaches 8000 tokens. A long-context request, a RAG prompt or a long chat history, spends nearly as much energy reading as writing, even though each prompt token is 40 times cheaper, because there are so many more of them against a fixed 300-token answer.

## The cached prefix

When the prompt is served from a cached prefix, its prefill is already done and costs about nothing. For the 8000-token request that turns the 40% prefill share into zero: on the 7B it cuts the request from about 549 J to about 330 J, a 40% saving, for the same output. This is the energy case for prompt caching in long-context serving: the saving is not a rounding error once prompts are long, it is the largest single lever on a long-prompt short-answer request.

## What to take from this

1. A prompt token costs about 40 times less energy than a generated token on this machine, so for short prompts the answer dominates and prefill is a few percent.
2. Prefill per token is lowest near 512 tokens and grows about 30 to 58% out to 16384 as attention builds, so a very long prompt is dearer per token as well as having more tokens.
3. By 8000 prompt tokens with a short answer, prefill is about 40% of the energy, and a cached prefix removes essentially all of it. Prompt caching is a large energy lever for long-context serving, not a small one.

## Limits

Batch 1 only; prefill and decode batch differently, so these shares are for single-stream serving. The share is a calculation combining this note's prefill with note 13's decode, measured in separate runs; decode was interpolated to the prompt length from note 13's depths, and the 500, 2000 and 8000 prompts used the prefill figures measured at 512, 2048 and 8192. GPU (chip) energy only; no whole-system figure on AC. Two models, one quantization, one card. Build 11851 (CUDA).

## Reproduce

Windows, no admin, plugged in. With a clone and a prebuilt llama.cpp CUDA build on `PATH`:

```powershell
.\.venv\Scripts\python -m pip install -e .
# prefill energy per token at a prompt length, batch 1, three passes:
.\.venv\Scripts\phase models/quant/7b-Q4_0.gguf --prefill 8192 --decode 16 --seconds 15 --out results/prefill-windows-7b-p8192-run1.json -- -fa on
```

Raw results: `results/prefill-windows-{1.5b,7b}-p{128,512,2048,8192,16384}-run{1,2,3}.json`, `results/summary-prefill-windows.json`. The share figures combine these with note 13's `results/depth-windows-*.json`.
