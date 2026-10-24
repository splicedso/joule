# Windows: the next run

Read notes 4 and 7 first (`notes/2026-10-two-machines.md`, `notes/2026-10-speculative-decoding.md`). Pull `main` before starting: `experiments/speculative.py` takes a list of conditions now.

## 1. Fix the two gaps from the first Windows run

- **Log the battery's real update interval.** Record `Sampler.battery_update_s()` into the result JSON (machine info is a good place). Note 4 could not say how often the system reading refreshes.
- **A clean idle baseline.** The first run's idle read 39 W and then 69 W, because the second pass started while the battery still reported the first pass's load. Wait until `DischargeRate` has settled (several identical readings in a row, or 60 s) before taking idle, and record the wait.

## 2. Speculative decoding on CUDA (the main task)

Does note 7's "faster can cost more energy" hold on a discrete NVIDIA GPU?

- Models: Qwen2.5 7B Q4_0 as the target, Qwen2.5 0.5B Q4_0 as the draft, both quantized from the official F16 GGUFs as in note 1.
- Run `experiments/speculative.py` with the default conditions, then again with `plain,draft-8,draft-8-p0.5,draft-8-p0.8,draft-8-p0.95,draft-16,draft-16-p0.8`.
- Use the GPU reading (nvidia-smi) as the energy figure, the equivalent of the Mac's chip reading. As note 7 explains, the slow system reading is biased on short runs and must not be used for speculative runs.
- Record whether the machine was on battery or AC, and run both if time allows. On battery the GPU is power-capped (note 4), which may change the result.

## 3. Output

`results/speculative-windows-*.json`, a short `notes/2026-10-windows-speculative.md` in the same shape as note 7, on a branch, as a pull request. Never state a number the results files do not hold.
