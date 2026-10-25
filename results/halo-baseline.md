# Linux baseline: Strix Halo, Qwen2.5 Q4_0

Energy per token for Qwen2.5 1.5B and 7B at Q4_0 on the AMD Ryzen AI Max+ 395
(Strix Halo) APU, all layers on the GPU. This is the cost half of the picture.
Joules per correct answer follows in the quality note, once `experiments/quality.py`
has run here; this file is the raw energy-per-token baseline it builds on.

- Machine: AMD Ryzen AI Max+ 395, Radeon 8060S (gfx1151), 125 GB unified, Linux
  (kernel 7.2.7+rex-amd64), on mains.
- llama.cpp build 620d2225c (11669). Vulkan backend (RADV, Mesa 25.0.7) and, for
  the 7B, the HIP/ROCm backend as well.
- `phase --seconds 20`, three passes, the second pass in reverse model order.
  Power is SoC only (the amdgpu package sensor); this board has no user-readable
  whole-system power, so sys is 0 and omitted here.
- Idle SoC power was 11.3 to 15.2 W across passes. The net columns subtract it.
  It is large next to the Mac's ~0.5 W, so every net figure here leans on it.

## Vulkan, three passes (min to max)

| model | phase | tok/s | SoC W | SoC mJ/tok | SoC net mJ/tok |
|---|---|---:|---:|---:|---:|
| 1.5B | prefill | 5156 to 5235 | 106.5 to 113.6 | 20.3 to 21.7 | 17.4 to 19.5 |
| 1.5B | decode | 193.4 to 196.1 | 111.5 to 115.2 | 572.5 to 588.4 | 494.5 to 530.1 |
| 7B | prefill | 1542 to 1544 | 135.3 to 141.1 | 87.6 to 91.5 | 77.8 to 84.2 |
| 7B | decode | 50.1 to 50.2 | 100.1 to 102.5 | 1993 to 2044 | 1691 to 1819 |

## 7B on HIP/ROCm, one run

| phase | tok/s | SoC W | SoC mJ/tok | SoC net mJ/tok |
|---|---:|---:|---:|---:|
| prefill | 1772.9 | 144.7 | 81.6 | 74.6 |
| decode | 49.7 | 94.9 | 1911.3 | 1662.2 |

## What the numbers say

- Decode costs about 28 times more energy per token than prefill (29x at 1.5B,
  23x at 7B). A single blended figure would hide the phase that dominates chat.
- The backend changes prefill more than decode. On the 7B, HIP prefill is 15%
  faster than Vulkan (1773 vs 1543 tok/s) at lower energy (82 vs about 90 mJ/tok),
  while decode throughput is the same on both (about 50 tok/s) with HIP about 5%
  lower energy. Prefill is compute bound, so rocBLAS helps; decode is memory
  bandwidth bound, so both backends hit the same wall.
- The highest power draw is 7B prefill, about 138 W, not decode. 7B decode pulls
  only about 100 W: at 50 tok/s the GPU spends its time waiting on memory, which
  is also why it draws less than 1.5B decode (about 113 W at 195 tok/s).

## Limits

- One machine, one quant (Q4_0), two sizes. No accuracy here, so no joules per
  correct answer yet; that is the quality note.
- The 7B HIP run is a single pass, so it has no spread. Vulkan has three.
- Idle is read on an otherwise quiet machine but not a thermally controlled one.
