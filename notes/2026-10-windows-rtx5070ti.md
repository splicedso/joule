# Batching without a step: a discrete GPU on AC power

Spliced research note 10, 24 October 2026. Windows 11 laptop: Intel Core Ultra 9 285H, NVIDIA GeForce RTX 5070 Ti Laptop GPU (12 GB, Blackwell, compute 12.0), 32 GB RAM, on a battery. llama.cpp build 11851 (prebuilt CUDA 13.4 x64), CUDA backend, all layers on the GPU, no admin rights.

This repeats note 1 (`notes/2026-10-formats-and-batching.md`, Apple M5 Pro) on different hardware, to see whether the format ranking and the batching step hold. Note 4 (`notes/2026-10-two-machines.md`) compared the two machines on battery; this note adds the machine plugged in, where its GPU is not power-capped, and the batch sweep. The format ranking mostly holds. The batching step does not, and neither does note 1's chip-only finding for F16.

The llama.cpp build here is 11851, against 11669 on the Mac, because the prebuilt CUDA package for that build was what was available. Kernel changes between the two builds are possible and are a caveat on every cross-machine comparison below.

## Question

Does a lower-bit format cost less energy per decoded token, and how much does serving several sequences at once save, on a discrete NVIDIA GPU instead of Apple unified memory? Note 1's sharpest claim was that a chip-only measurement misranks F16: on the M5 Pro the GPU drops to about 11 W while it waits on memory, so F16 looks as cheap as Q4_K_M on the chip while the board shows it is the most expensive format. We test that claim here.

## Method, and what this machine cannot measure

The power backend is new (`joule/power_windows.py`), behind the same `Sampler` interface, so `measure.py` and `experiments/batching.py` are unchanged.

- **Chip reading (soc):** GPU power from `nvidia-smi --query-gpu=power.draw -lms`. This is the nearest analog to the Mac's chip reading, but it is the GPU package only. There is no CPU+GPU+DRAM package counter to read on this platform.
- **Board reading (sys):** whole-system DC power from the battery's `DischargeRate` (WMI `root/wmi` `BatteryStatus`), and **only while unplugged**. There is no board DC sensor readable on AC without a driver. Its real update rate on this machine is **about every 3 s** (measured), so it is a coarse mean over long windows only, and its idle baseline is too noisy to trust — board energy is reported **gross**, not net of idle.
- **CPU package power:** not measured. Intel RAPL needs a kernel driver, i.e. admin rights, so it is left at 0, not estimated.
- `nvidia-smi` intermittently reports a spurious ~11000 W power spike at idle; the sampler drops readings above a sane ceiling.

Because board power needs the charger out and chip power is most stable on AC, the study runs at **two operating points**: chip energy on AC, and a second full set on battery that carries both chip and board together. On battery the GPU is held to a lower power ceiling (about 55–60 W, against about 90–105 W on AC), so it runs slower. The two are not the same operating point, and both are shown.

Otherwise the method follows note 1: Qwen2.5 1.5B Instruct quantized from one F16 GGUF with `llama-quantize` (no imatrix) into the eight formats; decode is 128 tokens per repetition, `joule --seconds 15`, first quarter of each window dropped, two passes with the second in reverse order; perplexity is `llama-perplexity` on WikiText-2 raw, `-c 512 --chunks 60`; batching is `experiments/batching.py` at batch 1 to 8, three passes, chip power only.

## Results: formats, batch 1

Decode. Energy is the mean of the two passes (they agreed within about 5%). Perplexity standard errors are about 0.21.

| format | perplexity | AC chip mJ/tok | AC chip net mJ/tok | AC tok/s | batt board mJ/tok | batt chip mJ/tok | batt tok/s |
|---|--:|--:|--:|--:|--:|--:|--:|
| F16 | 9.65 | 753.0 | 588.9 | 128 | 740.1 | 614.1 | 94 |
| Q8_0 | 9.65 | 475.1 | 377.6 | 214 | 444.1 | 358.0 | 160 |
| Q6_K | 9.68 | 385.8 | 308.0 | 268 | 386.9 | 301.8 | 184 |
| Q5_K_M | 9.73 | 342.5 | 266.5 | 275 | 361.1 | 263.9 | 203 |
| Q4_K_M | 10.05 | 326.4 | 260.6 | 317 | 307.9 | 248.0 | 234 |
| Q4_0 | 10.11 | 294.8 | 235.9 | 354 | 269.2 | 222.2 | 261 |
| Q3_K_M | 10.87 | 396.2 | 315.3 | 258 | 371.6 | 301.9 | 193 |
| Q2_K | 16.02 | 291.3 | 231.8 | 351 | 284.7 | 224.7 | 255 |

1. **Energy still does not fall with bit width.** Q3_K_M costs more per token than Q4_K_M and Q5_K_M despite fewer bits, and Q2_K buys almost nothing over Q4_0 in energy while its perplexity collapses to 16. The cheapest formats are Q4_0 and Q2_K; the dividing line for quality is between Q4_0 (ppl 10.1) and Q3_K_M (10.9).

2. **Chip-only does NOT misrank F16 here — note 1's headline finding is hardware-specific.** On this discrete GPU the chip already names F16 the most expensive format, about 2.5x Q4_0 (753 vs 295 mJ/tok on AC). The reason is the opposite of the Mac's: this GPU holds roughly 90–105 W whether compute- or memory-bound rather than dropping to ~11 W, so chip energy per token is essentially power divided by throughput, and the slow formats are the expensive ones on the chip too. The whole-system reading adds only a near-constant overhead (board is about 1.15–1.38x chip across formats), so the board does not re-order anything. The effect that made package-only measurement misleading on Apple silicon does not appear on this dGPU. Note 4 gives the other half of the reason: NVIDIA's GPU reading includes the card's own memory, which Apple's chip reading leaves out.

3. **Q4_0 is the efficient 4-bit format here, as on the Mac.** Its perplexity is within error of Q4_K_M at lower chip and board energy and higher throughput. Nothing beats Q4_0 on both quality and board energy except by a margin inside the noise.

4. **The ranking is stable across operating points.** AC and battery disagree on absolute numbers (battery is slower under its power cap) but agree on the order: F16 worst, Q4_0 and Q2_K cheapest, Q3_K_M an out-of-order bump. That the ranking survives a ~45 W change in GPU power ceiling is some evidence it is about the formats, not the operating point.

Prefill is cheap by comparison: about 6 mJ/tok on AC for F16, roughly 100x less than its decode cost, the same prefill/decode split note 1 reports.

## Results: batching

Decode energy per token against batch size, chip (GPU) power only, three passes, on AC. 64 prompt + 512 generated tokens per sequence.

Q4_0:

| batch | chip mJ/tok | tok/s | GPU W | GPU MHz |
|--:|--:|--:|--:|--:|
| 1 | 267.5–294.0 | 336–359 | 96.9 | 2279 |
| 2 | 152.7–172.1 | 573–638 | 99.4 | 2094 |
| 3 | 120.6–130.4 | 749–821 | 100.0 | 2092 |
| 4 | 104.2–109.5 | 913–962 | 100.1 | 2139 |
| 5 | 86.9–94.2 | 1068–1127 | 99.6 | 2218 |
| 6 | 83.5–84.7 | 1149–1218 | 99.9 | 2170 |
| 7 | 79.4–82.0 | 1200–1268 | 100.0 | 2144 |
| 8 | 71.4–75.1 | 1347–1411 | 101.9 | 2236 |

Q4_K_M:

| batch | chip mJ/tok | tok/s | GPU W | GPU MHz |
|--:|--:|--:|--:|--:|
| 1 | 330.5–340.7 | 307–310 | 103.7 | 2178 |
| 2 | 187.9–195.2 | 508–511 | 97.1 | 1943 |
| 3 | 145.3–148.2 | 649–665 | 96.3 | 1909 |
| 4 | 123.4–127.9 | 766–782 | 97.0 | 2024 |
| 5 | 109.7–111.0 | 878–891 | 97.5 | 2003 |
| 6 | 80.1–82.2 | 1203–1215 | 97.7 | 2337 |
| 7 | 74.5–76.1 | 1287–1306 | 97.2 | 2373 |
| 8 | 60.4–62.3 | 1601–1616 | 98.3 | 2522 |

Batching saves about as much here as on the Mac — batch 8 cuts per-token energy by about 74% for Q4_0 and 82% for Q4_K_M — but by a different route. On the M5 Pro the GPU was memory-bound at batch 1 (18–24 W) and stepped to its ceiling at batch 2, so the second sequence paid for nearly the whole power step and batch 2 alone saved almost nothing. **This GPU is already at its ~100 W ceiling at batch 1**, so there is no step: power stays flat near 100 W across all batch sizes while throughput climbs, and energy per token falls smoothly with it from the first sequence on. The clock drifts between about 1900 and 2500 MHz without a clear trend, so it is throughput, not frequency, that drives the saving.

## Limits

- Two operating points, because board power is only readable unplugged and the GPU is power-capped there. Neither column is the Mac's "board DC input on AC"; the AC column has no board number at all, and the battery column is at a lower power ceiling.
- Board power is the battery discharge rate, updated about every 3 s, so it is a coarse mean and its idle-net is unreliable; only gross board energy is reported.
- No CPU package power on this machine without a driver, so there is no SoC-wide figure, only the GPU.
- One machine, one model size, one runtime, as in note 1. The cross-hardware contrast (finding 2) is exactly why a second machine was worth doing.
- Perplexity on WikiText-2 is a quality proxy, not a task score. The laptop was a working machine, not a thermally settled bench; passes agreed within about 5%.

## Reproduce

Windows, no admin. Install `git`, Python and the GitHub CLI per user (e.g. with `winget`), and unzip a prebuilt llama.cpp CUDA build onto `PATH`. Then, from a clone:

```powershell
python -m venv .venv; .\.venv\Scripts\python -m pip install -e .
# quantize 1.5b-f16.gguf into the eight formats with llama-quantize (no imatrix)
.\.venv\Scripts\joule <quant>\1.5b-*.gguf --seconds 15 --out results\quant-energy-windows-ac-run1.json
.\.venv\Scripts\python experiments\batching.py <quant>\1.5b-q4_0.gguf results\batching-windows-q4_0.json 1,2,3,4,5,6,7,8
llama-perplexity -m <quant>\1.5b-q4_0.gguf -f wiki.test.raw -c 512 --chunks 60 -ngl 99
```

Run the energy study twice, the second with the formats reversed, and run the board-power pass unplugged. Raw results: `results/quant-ppl-windows.txt`, `results/quant-energy-windows-{ac,battery}-run{1,2}.json`, `results/batching-windows-*.json`.
