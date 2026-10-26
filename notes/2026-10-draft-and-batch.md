# A draft and a batch fill the same gap

**Prediction verdict:** held on the shape. A draft model pays at one or two requests at once and costs energy from four on. Missed narrowly at the edges: at one request the draft cost 3% more energy, not up to 20% less, and at four it cost 12% more, not within 10%. Two earlier predictions in the same series missed outright, and the reason they missed is part of this note (section 3).

Spliced research note 25, 26 October 2026. Apple M5 Pro, 24 GB, macOS 27.0.1 on AC, Metal. llama.cpp build 11669 (Homebrew), llama-server. Target Qwen2.5 7B Instruct Q4_0, draft Qwen2.5 0.5B Instruct Q4_0, drafts of up to 4 tokens with a 0.5 confidence threshold.

Notes 9 and 11 found that a draft model with a confidence threshold makes one request faster at no energy cost. Note 24 found that serving many requests at once cuts energy per token by up to 79%. Both work the same way: decoding one token reads every weight from memory, and the chip's arithmetic waits on that read. A draft fills the waiting arithmetic by checking several guessed tokens in one pass. A batch fills it with other people's requests. This note measures what happens when both compete for the same gap.

**Prediction** (`docs/predictions.md`, 26 October 02:06, committed before the run): at one request 1.25 to 1.45 times plain's speed at 0.8 to 1.0 times its energy; at two, 10 to 30% less energy; at four, within 10% of plain; at eight and sixteen, 15 to 60% more energy and less throughput.

## Method

`experiments/decode_batch_energy.py`, the script of note 24, with the draft passed to llama-server. For each batch of 1, 2, 4, 8 and 16, a fresh server, a short warm-up, then that many identical requests at once, each a 512-token answer to note 11's power-supply prompt at temperature 0. Chip power by macmon at 5 Hz over the whole window, two passes with the second reversed. Plain decoding ran before and after the draft run, and the two plain runs agree within 1% at every batch. Pass spreads are 0 to 8%, with 30 to 102 power samples per window.

## Results

| requests | plain tok/s | draft tok/s | speed | plain mJ/token | draft mJ/token | energy | plain W | draft W |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 61.9 | 78.3 | 1.26x | 370 | 381 | 1.03x | 22.9 | 29.8 |
| 2 | 100.2 | 125.5 | 1.25x | 391 | 279 | 0.71x | 39.1 | 35.0 |
| 4 | 192.3 | 163.4 | 0.85x | 203 | 227 | 1.12x | 39.0 | 37.1 |
| 8 | 339.2 | 229.8 | 0.68x | 109 | 163 | 1.50x | 36.9 | 37.6 |
| 16 | 377.0 | 329.1 | 0.87x | 95 | 114 | 1.20x | 35.9 | 37.5 |

Between 67% and 74% of drafted tokens were accepted at every batch.

## 1. One request: faster, not cheaper

At one request the draft gives 1.26 times the speed for 3% more energy per token, close to note 11's 1.25 times and 4%. Chip power rises from 23 to 30 W: checking a 4-token draft is a small batch, and the chip draws batch power to do it. The time saved almost exactly pays for the extra power.

## 2. Two requests: the draft's best case

At two requests the draft cuts energy per token by 29% and keeps its speed-up. Plain decoding pays a power step at the second request: 23 W at one, 39 W at two, the step note 1 described. With the draft the chip is already working at batch power, so the second request adds tokens without adding watts (35 W). Two is where the gap is widest and only the draft fills it.

## 3. Four and more: the batch has already filled the gap

From four requests the batch alone keeps the arithmetic busy, so checking guesses competes with real work. At eight requests the draft costs 50% more energy per token and serves 32% fewer tokens per second. Every rejected guess is now paid for in arithmetic the batch would have used.

The first runs of this series used a weather paragraph as the prompt. The draft's guesses on that text were accepted about 60% of the time, which is break-even for a 4-token draft. They showed no speed-up even at one request, contradicting note 11. A one-change-at-a-time diagnostic (`experiments/spec_diag.py`, `results/spec-diag-mac.json`) traced it to the prompt alone: on the power-supply prompt acceptance rose to 80% and the speed-up to 1.41 times. Answer length, slot count and context size did not explain it. The weather runs are kept and say the same thing about batching, at worse odds: on that text the draft costs energy at every batch except two. A draft's value depends on the text before it depends on anything else.

## 4. Two settings that decide whether there is a draft at all

- **Draft length.** At the 0.5 threshold, drafts of up to 4 matched drafts of up to 8 on prose (1.27 against 1.24 times plain's speed) and edits (2.25 against 2.24), and beat them on code (1.72 against 1.51; note 11's set, re-run 26 October, `results/speculative-server-mac-foundry-length.json`).
- **The speculative type.** In this llama.cpp build, `llama-server -md draft.gguf` loads the draft and never uses it unless `--spec-type draft-simple` is also given. Nothing warns. Our own app, Foundry, shipped Fast mode with that defect; it is fixed, and the app now says so if a Fast-mode answer drafted nothing. Any draft result whose timings show no drafted tokens is void. One run of this series was, and it is kept apart in `results/void/`.

## What this changes

- A draft model belongs on a machine serving one or two requests at once, which describes a person's own laptop. A server with four or more requests in flight should turn it off. The rule depends on the load, not on the model, so a scheduler can apply it per moment.
- The power at one request decides how much the draft saves. On the Strix Halo, whose package draws about 104 W decoding one request with or without the draft, the same kind of draft cuts energy per token by a third (note 26).
- Trace, our draft-model family, is for the first case. Its bar stays at one request, and its value is largest on text the stock draft guesses badly.

## Limits

- One machine, one model pair, one prompt for the main table. Every request in a batch is the same prompt, so every slot drafts the same tokens; a real batch mixes easy and hard text, and its acceptance would sit between this note's two prompts.
- Chip energy only, not the board or the wall. Idle and board power are a fixed cost per second, so at the wall the draft's speed-up at one request is worth more than this table shows.
- The power step at two requests belongs to this chip; on a GPU already at its power ceiling at one request (note 10) the batch-2 result will differ.

## Reproduce

```bash
export PROMPT=power BATCHES=1,2,4,8,16 ANSWER=512
uv run python experiments/decode_batch_energy.py models/quant/7b-Q4_0.gguf results/spec-batch-power-a512-plain1.json
SERVER_ARGS="-md models/quant/0.5b-Q4_0.gguf --spec-type draft-simple --spec-draft-n-max 4 --spec-draft-p-min 0.5 -ngld 99" \
  uv run python experiments/decode_batch_energy.py models/quant/7b-Q4_0.gguf results/spec-batch-power-a512-draft.json
uv run python experiments/decode_batch_energy.py models/quant/7b-Q4_0.gguf results/spec-batch-power-a512-plain2.json
uv run python experiments/spec_diag.py results/spec-diag-mac.json
```

Nothing else running. Raw results: `results/spec-batch-power-a512-*.json` (the table), `results/spec-batch-power-{plain1,draft,plain2}.json` (128-token windows, speed only, too noisy for energy), `results/spec-batch-mac-7b-*.json` and `results/spec-batch-mac-7b-q4_0-*.json` (the weather prompt), `results/spec-diag-mac.json`, `results/speculative-server-mac-rerun-2026-10-26.json`.
