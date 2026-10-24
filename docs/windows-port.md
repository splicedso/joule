# Porting Phase to Windows

Phase measures LLM energy per token at two points, the chip and the whole board, with prefill and decode reported apart. Today it only runs on macOS, where `macmon` reads both without sudo. This is the brief for a second machine.

## Goal

Run the study in `notes/2026-10-formats-and-batching.md` on a Windows laptop, so the format ranking and the batching step can be checked on different hardware.

## What to measure, and how, without admin rights where possible

1. Identify the hardware first: CPU, GPU (NVIDIA, Intel Arc, AMD, or a Snapdragon NPU), RAM, battery. Record it in the results.
2. Whole-system power, the equivalent of the Mac's board reading: battery `DischargeRate` from WMI (`root/wmi`, `BatteryStatus`) while unplugged. Measure and record its real sampling rate; on many laptops it updates every few seconds, so it is only usable as a mean over long windows.
3. GPU power, the nearest equivalent of the Mac's chip reading on a discrete GPU: `nvidia-smi --query-gpu=power.draw --format=csv -lms 100` on NVIDIA.
4. CPU package power only if it can be read without installing a driver. If it cannot, say so. Do not estimate it from TDP.

Add the backend beside `phase/power.py` behind the same `Sampler` interface, so `measure.py` and `experiments/batching.py` run unchanged.

## The study

- llama.cpp, Qwen2.5 1.5B Instruct, the same eight formats quantized from the F16 GGUF with `llama-quantize`, no importance matrix.
- Perplexity: WikiText-2 raw test, `-c 512 --chunks 60`.
- Energy: `phase --seconds 15`, two passes, the second in reverse order.
- Batching: `experiments/batching.py` at batch 1 to 8, three passes.

## Output

`notes/2026-10-windows-<machine>.md` in the same shape as note 1, raw JSON in `results/`, on a branch, as a pull request. Never state a number the results files do not hold, and list what this machine cannot measure.
