# Phase

Energy per token for local LLM inference, measured, with prefill and decode reported apart.

Published edge-LLM energy figures disagree because they measure different things: chip package only, a TDP estimate, or one device in one paper. `phase` measures two things on the machine in front of it and says which is which:

- **SoC**: the chip (CPU, GPU, ANE, memory interface), sampled every 200 ms.
- **sys**: the logic board's DC input as the SMC reports it. Close to wall power minus adapter loss, but smoothed to about 1 Hz, so it is only used as a mean over a long steady window.

Each is reported gross and **net** of an idle baseline taken at the start of the run.

## Use

```bash
brew install macmon llama.cpp
uv run phase model-a.gguf model-b.gguf --out results/run.json
```

Arguments after `--` go to `llama-bench` (for example `-- -fa on -t 8`).

## Method

For each model, prefill (512 prompt tokens) and decode (128 generated tokens) run as separate `llama-bench` tests. A three-repetition probe sizes the real run to about 20 timed seconds. The timed repetitions are the last thing `llama-bench` does, so the compute window is the final `sum(samples_ns)` before it exits. The first quarter of that window is dropped for clock ramp and sensor lag. Energy per token is mean power over the remaining window divided by `llama-bench`'s measured throughput.

## First results: Apple M5 Pro, 24 GB, macOS on AC, llama.cpp build 11669

Two consecutive runs, Q4_K_M, all layers on the GPU.

| model | phase | tok/s | SoC mJ/tok | sys mJ/tok | sys net mJ/tok |
|---|---|---:|---:|---:|---:|
| Qwen2.5 0.5B | prefill | 18,900 to 19,100 | 2.0 | 3.7 to 3.8 | 3.2 |
| Qwen2.5 0.5B | decode | 336 to 343 | 67 to 74 | 158 to 174 | 131 to 144 |
| Qwen2.5 1.5B | prefill | 6,430 to 6,450 | 6.5 to 6.7 | 12.2 to 12.6 | 10.8 to 11.0 |
| Qwen2.5 1.5B | decode | 196 to 198 | 142 to 145 | 340 to 345 | 294 |
| Qwen2.5 7B | prefill | 1,528 | 29 | 54 | 46 |
| Qwen2.5 7B | decode | 57.7 | 544 | 1,303 | 1,080 |

The 7B row is a single run.

What the numbers already say:
- Decode costs 20 to 35 times more energy per token than prefill. A benchmark that reports one blended figure hides the phase that matters for chat.
- The chip is well under half of what the machine draws. Package-only figures understate the real cost of a token by more than 2x on this laptop.

Raw JSON is in `results/`.

## Research notes

- [1. Fewer bits is not fewer joules](notes/2026-10-formats-and-batching.md): eight quantization formats and batch 1 to 8, chip and board energy, on Apple M5 Pro.
- [2. Where the joules go](notes/2026-10-roofline-and-energy-model.md): a decode roofline from measured bandwidth, and a validated energy model whose residuals isolate the cost of unpacking each format.
- [3. Does it hold?](notes/2026-10-scale-and-runtime.md): the format study at 7B, where it replicates, and in MLX, where repeat runs do not yet agree and only claims that survive both passes are made.
- [4. Two machines, one token](notes/2026-10-two-machines.md): the study on a Windows laptop with an RTX 5070 Ti, on battery. What transfers from the Mac, what does not, and why GPU power and chip power are not the same quantity.
- [5. The cost of unpacking](notes/2026-10-kernel-energy.md): each format's matrix-vector kernel measured alone. Q4_0 and Q4_K read identical bytes at identical speed, and Q4_K's unpacking costs 40% more chip energy.
- [6. Small models pay more per weight](notes/2026-10-model-width.md): five formats across 0.5B, 1.5B, 3B and 7B. A weight in a 0.5B model costs up to 1.6 times one in a 7B; Q4_0 is cheapest at every width; the Q5_K_M against Q6_K order flips with width.
- [7. Faster is not cheaper](notes/2026-10-speculative-decoding.md): speculative decoding with a draft model and with n-gram copying, three tasks. It can be faster and cost more energy at once; copy-based drafting on edits costs 32% of plain decoding.
- [8. Tokens per megawatt-hour](notes/2026-10-tokens-per-megawatt-hour.md): every MLPerf v5.0 and v5.1 LLM result with measured wall power (two servers). A B200 server buys 2.7 times the tokens per joule of an H100 NVL one; the roofline says it must batch 58 or more sequences per weight pass.
- [9. One flag fixes speculative decoding's energy problem](notes/2026-10-speculative-threshold.md): a draft confidence threshold (`--spec-draft-p-min`, about 0.5) removes the energy penalty on every task and makes speculation on prose a free 1.3x speed-up.
- [10. The same token, plugged in, and under batching](notes/2026-10-windows-ac-and-batching.md): the Windows laptop on AC power and a batch sweep on CUDA. Plugging in costs 23 to 33% more energy per token for 34 to 46% more speed, and the GPU is at its 100 W ceiling from batch 1, so the second request saves 43% where on the Mac it saved 1%.
- [11. Same result, second tool](notes/2026-10-speculative-second-tool.md): notes 7 and 9 repeated through llama-server. Every finding holds; the server is slightly more favourable to speculation; and why Windows Smart App Control blocked the Windows run.
- [12. Small models pay more per weight, on a discrete GPU too](notes/2026-10-windows-width.md): note 6's width sweep on the RTX 5070 Ti. Small models pay up to 2.2x per weight here, more than on the Mac for the 4-bit formats; Q4_0 is cheapest at every width; Q5_K_M beats Q6_K at every width, with no flip.
- [13. What a long context costs](notes/2026-10-windows-context.md): decode energy against context depth on the RTX 5070 Ti and the M5 Pro, with and without an 8-bit KV cache. A token at 16k costs about 1.3x one at zero depth; the 8-bit cache saves no energy where the f16 cache already fits, and costs more the deeper the context.
- [14. A long context does not spend the batching saving (Windows half)](notes/2026-10-windows-batch-context.md): batch 1 to 8 at 64 and 4096 tokens of context on the RTX 5070 Ti. Batch 8 keeps 72 to 76% of its energy saving at 4096 against 75 to 79% at 64; note 8's batching loss is a memory-fit effect, not a context effect, and did not appear where the cache still fit.
- [15. Our first model: a distilled draft model](notes/2026-10-spliced-drafter.md): a 0.5B draft distilled from 1.14M tokens of Qwen2.5 7B output. Held-out loss 6% lower, acceptance about 3% higher, 2 to 3% faster; raising its threshold did not help.
- [16. The memory-bound regime: when a long context caps the batch (Windows half)](notes/2026-10-windows-memory-bound.md): at 8192 and 16384 tokens the 7B's f16 cache fits only batch 8 on a 12 GB card, so memory caps the batching that makes a token cheap. An 8-bit cache does not win it back: at 16384 it fits no larger batch (1.64x the energy), and at 8192 it fits batch 16 but still costs 6% more than f16 at batch 8.
- [17. The 8-bit cache does not win even when it fits an extra sequence (Windows half)](notes/2026-10-windows-longctx.md): at 65536 tokens, where the 7B f16 cache fits only 2 sequences, the 8-bit cache fits a third but costs 1.58x f16's best. Forcing f16 that low needs a context so long that batching stops paying and the cache penalty is largest, so note 16's predicted win does not occur.

## Known limits

- **Repeatability.** Prefill and 1.5B decode repeat within 3%. 0.5B decode drifted 58 to 74 mJ/tok across three runs while throughput held, so power rose, probably heat or other load on a working laptop. Results are not yet taken on an idle, thermally settled machine, and the table shows ranges, not a single number.
- **sys is not wall power.** It excludes the adapter's own loss. A wall meter is the next step.
- **Two machines so far.** Apple Silicon (macmon) and Windows with an NVIDIA GPU (nvidia-smi plus battery discharge, unplugged only).

## License

Apache-2.0. Measurements in `results/` may be reused with attribution; see `CITATION.cff`.
