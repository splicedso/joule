# PyTorch on gfx1151 (Strix Halo): can we train here?

Item 3 of the program: confirm PyTorch with ROCm runs on this APU, so Trace v1
can be trained on this machine rather than the Mac.

## Install

A separate venv (`.venv-torch`) so it cannot clash with the project env. torch
and its matching triton installed by direct URL from AMD's ROCm 7.2 index
(repo.radeon.com/rocm/manylinux/rocm-rel-7.2), which carries cp313 wheels for
gfx1151; no CUDA libraries are pulled. Plus transformers 5.20.2, safetensors,
accelerate from PyPI.

- torch 2.10.0+rocm7.2.0, HIP 7.2.26015, Python 3.13.
- The default `pip install torch` resolves to the CUDA/PyPI build, which is the
  wrong backend; the version must be pinned to the `+rocm` wheel.

## It runs real kernels, not just `is_available()`

`torch.cuda.is_available()` can return True on gfx1151 and still fault on the
first tensor, so these are measured with real work (`results/halo-torch-rocm.json`):

| test | result |
|---|---|
| device | AMD Radeon 8060S Graphics |
| bf16 matmul, 8192^3 | 31.8 to 33.5 TFLOPS |
| memory bandwidth, bf16 read+write | ~230 GB/s |

~230 GB/s is the unified LPDDR5X; 32 TFLOPS bf16 is modest but ample for a 0.5B.

## End to end: the Trace trainer runs

`train_trace.py` (load Qwen2.5 0.5B, forward, backward, AdamW, save) runs on the
GPU with no code change. On a partial teacher file (180 validation + 154 training
records) the stock 0.5B's held-out top-1 agreement with the 7B is **0.7616**,
matching the Mac's 0.7606 (the small difference is this machine regenerating the
validation answers). transformers 5.x works, with a `torch_dtype` deprecation
warning and an experimental-attention note, both harmless.

Conclusion: Trace v1 can be trained on this machine.

Ran under shared GPU memory 90% (113 GiB), after the 2026-10-25 reboot.
