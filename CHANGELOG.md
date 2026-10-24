# Changelog

## 0.2.0

- Windows backend: NVIDIA GPU power from `nvidia-smi` and whole-system power from the battery's discharge rate, unplugged; drops spurious `nvidia-smi` power spikes.
- Experiments: batch sweeps, MLX formats, memory bandwidth, roofline, energy model, per-kernel energy (with a patch to llama.cpp's `test-backend-ops`), model width, speculative decoding with draft thresholds.
- Research notes 1 to 10, every result file behind them, and the combined dataset `results/spliced-decode-energy.csv`.
- Continuous integration: tests, and a check that every result file a note names exists.

## 0.1.0

- `joule`: energy per token for llama.cpp on Apple silicon, chip and board, prefill and decode apart, no sudo.
