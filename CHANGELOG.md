# Changelog

## 0.3.0

- Renamed from joule to Phase: the repository, the Python package and the `phase` command. Old GitHub links redirect. The tool's core idea is measuring each phase of inference, prefill and decode, apart.
- `experiments/speculative_server.py`: the speculative decoding experiment through llama-server, for machines whose llama.cpp build lacks `llama-speculative-simple`.

## 0.2.0

- Windows backend: NVIDIA GPU power from `nvidia-smi` and whole-system power from the battery's discharge rate, unplugged; drops spurious `nvidia-smi` power spikes.
- Experiments: batch sweeps, MLX formats, memory bandwidth, roofline, energy model, per-kernel energy (with a patch to llama.cpp's `test-backend-ops`), model width, speculative decoding with draft thresholds.
- Research notes 1 to 10, every result file behind them, and the combined dataset `results/spliced-decode-energy.csv`.
- Continuous integration: tests, and a check that every result file a note names exists.

## 0.1.0

- `phase`: energy per token for llama.cpp on Apple silicon, chip and board, prefill and decode apart, no sudo.
