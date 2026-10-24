# joule

Energy per token for local LLM inference, measured, with prefill and decode reported apart.

Published edge-LLM energy figures disagree because they measure different things: chip package only, a TDP estimate, or one device in one paper. `joule` measures two things on the machine in front of it and says which is which:

- **SoC**: the chip (CPU, GPU, ANE, memory interface), sampled every 200 ms.
- **sys**: the logic board's DC input as the SMC reports it. Close to wall power minus adapter loss, but smoothed to about 1 Hz, so it is only used as a mean over a long steady window.

Each is reported gross and **net** of an idle baseline taken at the start of the run.

## Use

```bash
brew install macmon llama.cpp
uv run joule model-a.gguf model-b.gguf --out results/run.json
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

## Known limits

- **Repeatability.** Prefill and 1.5B decode repeat within 3%. 0.5B decode drifted 58 to 74 mJ/tok across three runs while throughput held, so power rose, probably heat or other load on a working laptop. Results are not yet taken on an idle, thermally settled machine, and the table shows ranges, not a single number.
- **sys is not wall power.** It excludes the adapter's own loss. A wall meter is the next step.
- **One machine, one runtime.** Apple Silicon and llama.cpp only so far. MLX and other boards come next.
