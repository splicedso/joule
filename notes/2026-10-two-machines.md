# Two machines, one token

Spliced research note 4, 24 October 2026. Qwen2.5 1.5B on two laptops: an Apple M5 Pro (24 GB, unified memory) and a Windows laptop with an Intel Core Ultra 9 285H, 32 GB, and an NVIDIA GeForce RTX 5070 Ti Laptop GPU, run on battery.

Notes 1 to 3 measured one machine. A finding from one machine might be physics, or it might be Apple. This note repeats the format study on hardware that shares nothing with the Mac: a different CPU vendor, a discrete GPU with its own memory, a different GPU backend (CUDA instead of Metal), a different operating system.

## Method

The Windows study used joule with a new power backend, written for this note (`joule/power_windows.py`), that needs no admin rights:

- **GPU** power from `nvidia-smi`, every 200 ms. This is the nearest thing to the Mac's chip reading, with one difference that matters below: it includes the GPU's own memory.
- **System** power from the battery's discharge rate (WMI `BatteryStatus`), the whole laptop, readable only while unplugged. The machine ran on battery throughout; both result files record `on_ac: false`.
- **CPU** package power is not read: on Windows it needs a kernel driver. It is left out, not estimated.

Same model, same eight formats quantized from F16, same perplexity settings, same `joule --seconds 15`, two passes.

## Repeatability, and one figure we discard

GPU energy repeated within 3% for every format. System energy repeated within 1% to 9%: the battery reports discharge slowly, so it is noisier. The **idle baseline did not repeat**: system idle read 39 W before the first pass and 69 W before the second. A slow battery reading most likely carried the first pass's load into the second pass's idle window. Net, idle-subtracted figures are therefore not used in this note. Gross figures are.

## Perplexity agrees across machines

| format | M5 Pro (Metal) | RTX 5070 Ti (CUDA) |
|---|---:|---:|
| F16 | 9.63 | 9.65 |
| Q8_0 | 9.63 | 9.65 |
| Q6_K | 9.65 | 9.68 |
| Q5_K_M | 9.70 | 9.73 |
| Q4_K_M | 10.01 | 10.05 |
| Q4_0 | 10.09 | 10.11 |
| Q3_K_M | 10.76 | 10.87 |
| Q2_K | 15.90 | 16.02 |

Within 1% everywhere. Same weights, same scoring, two different GPU backends: this is the cross-check that the two measurement setups agree on what they are measuring.

## Energy

| format | Windows tok/s | Windows GPU mJ/tok | Windows system mJ/tok | Mac tok/s | Mac chip mJ/tok | Mac board mJ/tok |
|---|---:|---:|---:|---:|---:|---:|
| F16 | 94 | 614 | 740 | 84 | 135 | 547 |
| Q8_0 | 160 | 358 | 444 | 142 | 154 | 408 |
| Q6_K | 184 | 302 | 387 | 171 | 152 | 369 |
| Q5_K_M | 203 | 264 | 361 | 178 | 197 | 411 |
| Q4_K_M | 234 | 248 | 308 | 205 | 134 | 314 |
| Q4_0 | 261 | 222 | 269 | 213 | 99 | 258 |
| Q3_K_M | 193 | 302 | 372 | 204 | 161 | 332 |
| Q2_K | 255 | 225 | 285 | 228 | 133 | 279 |

Means of two passes per machine.

## What transfers

1. **Q4_0 is the cheapest useful format on both machines.** Lowest GPU and system energy on Windows, lowest board energy on the Mac, with perplexity within error of Q4_K_M on both. Q2_K costs about the same on both machines and is far worse.
2. **F16 is the most expensive on both**, 2.8 times Q4_0 for the whole Windows laptop and 2.1 times at the Mac's board.
3. **Q3_K_M loses to Q4_0 on both**: more energy, worse quality. Going below 4 bits buys nothing here.
4. **At 4 bits, a token costs the same whole-machine energy on both laptops.** Q4_0: 269 mJ on Windows, 258 on the Mac. Q4_K_M: 308 and 314. Q2_K: 285 and 279. Two architectures with nothing in common land within 5% of each other. Whether that is coincidence or a common limit is a question for a third machine.

## What does not transfer

1. **Q5_K_M against Q6_K reverses.** On the Mac, Q5_K_M costs more than Q6_K in both passes (411 against 369 mJ at the board). On Windows it costs less (264 against 302 mJ at the GPU, which repeats within 2%). So note 1's "Q5_K_M is worse than Q6_K on both counts" is a property of the Metal kernels, not of the format. The format names describe the bits; the energy depends on who wrote the kernel.
2. **F16 costs much more on Windows** (740 against 547 mJ for the whole machine), while the 4-bit formats cost the same. Full precision is where the two memory systems differ most.

<!-- chart:two -->

## Where you put the probe decides what you count

On the Mac, the board draws 2.1 to 4.1 times what the chip does. On Windows, the whole laptop draws only 1.2 to 1.4 times what the GPU does. The machines are not that different. The probes are:

- Apple's chip reading covers the CPU, GPU and Neural Engine but not the memory. Memory energy appears only at the board, which is why note 1 found that chip-only figures misrank F16.
- NVIDIA's GPU reading covers the GPU package **and its own memory** on the same card. Most of the memory energy is already inside it.

So "GPU power" on a discrete card and "chip power" on Apple Silicon are not the same quantity, and comparing them directly is wrong. Comparing whole-machine figures is the fair test, and that is the comparison in "What transfers".

## A power cap turns energy into speed

On battery the RTX GPU drew 55 to 60 W on every format. Its power was effectively constant, so energy per token on Windows is that power divided by speed, and the energy ranking is the speed ranking. Q3_K_M costs more than Q4_0 here only because its kernel is slower (193 against 261 tokens per second) at the same power.

On the Mac, power varied by format (note 1: 11 to 34 W at the chip), so energy and speed rank differently. Which regime a machine is in depends on its power limits, and a laptop on battery is usually capped. That is worth knowing before reading any energy benchmark: under a cap, energy per token tells you nothing that tokens per second did not.

## Limits

- No wall meter on either machine. The Mac ran on its adapter, the Windows laptop on battery, so the two system figures are measured at different points (DC input against battery discharge).
- The Windows GPU was likely running at its battery power limit. Plugged in, it would draw more and run faster, and the energy ranking could change.
- The Windows idle baseline is unusable for this run, so only gross figures are compared. The battery's actual update interval was not recorded; the next Windows run should log it (`Sampler.battery_update_s`).
- Two machines are enough to show that some findings transfer and one does not. They are not enough to say why the 4-bit whole-machine figures match.

## Reproduce

```bash
# Windows, on battery, NVIDIA driver installed
uv run joule models\quant\1.5b-*.gguf --seconds 15 --out results\run.json
```

Raw results: `results/quant-energy-windows-battery-run1.json`, `results/quant-energy-windows-battery-run2.json`, `results/quant-ppl-windows.txt`, `results/summary-two-machines.json`.
