# The cost of unpacking

Spliced research note 5, 24 October 2026. Apple M5 Pro, 24 GB, llama.cpp build 11669 (620d2225c) built from source with Metal.

Note 2's energy model explained most formats by the bytes they move and left a residual it could not explain: Q4_0 cost 29% less than its bytes predicted, Q5_K_M 19% more. Note 4 then found Q5_K_M and Q6_K swap order between Apple and NVIDIA. Both point at the kernel that unpacks each format before multiplying. This note measures that kernel on its own.

## Method

llama.cpp's `test-backend-ops` in perf mode runs one matrix-vector product: a 4096 x 14336 weight matrix, the size of a 7B model's feed-forward layer, times one vector, which is exactly what decode does. We ran it for each format under the power sampler (`experiments/kernels.py`).

**A first version failed, and why is worth knowing.** Upstream, each perf run lasts one second. Repeating one-second runs, the two passes disagreed by up to 40%: Q4_0 measured 0.167 nJ per byte in one pass and 0.095 in the other. In a one-second run, process start, teardown and the sensor's own averaging interval are a large share of the window. A one-line patch (`experiments/test-backend-ops-perf-min-us.patch`) makes the run length an environment variable, and each format now runs as one continuous 15-second loop, with the first quarter and the last half second dropped. The two passes, the second in reverse order, then agreed within 2.3% for every format but F16 (5.4%).

Bytes per weight come from each format's block layout. **Q4_0 and Q4_K store exactly the same 0.5625 bytes per weight**, so they read identical traffic and differ only in how the bits are unpacked: a natural controlled experiment.

## Results

| format | bytes per weight | time per matvec | bandwidth | chip power | chip nJ per byte | chip pJ per weight | board pJ per weight |
|---|---:|---:|---:|---:|---:|---:|---:|
| F16 | 2.000 | 381.7 us | 308 GB/s | 11.0 W | 0.036 | 71.4 | 324.6 |
| Q8_0 | 1.063 | 220.0 us | 284 GB/s | 19.8 W | 0.070 | 74.3 | 231.7 |
| Q6_K | 0.820 | 172.1 us | 280 GB/s | 30.4 W | 0.108 | 89.0 | 215.8 |
| Q5_K | 0.688 | 140.1 us | 288 GB/s | 41.7 W | 0.145 | 99.5 | 214.8 |
| Q4_K | 0.563 | 107.7 us | 307 GB/s | 36.0 W | 0.117 | 66.0 | 152.9 |
| Q4_0 | 0.563 | 108.8 us | 304 GB/s | 25.8 W | 0.085 | 47.8 | 126.6 |
| Q3_K | 0.430 | 96.5 us | 261 GB/s | 52.6 W | 0.201 | 86.5 | 160.2 |
| Q2_K | 0.328 | 65.7 us | 293 GB/s | 46.8 W | 0.160 | 52.4 | 94.9 |

Means of two passes. Energy per weight is what decides what a model costs, since every format holds the same number of weights.

<!-- chart:kern -->

## 1. At this size every format is memory bound, and they differ in power, not time

Every kernel moves 261 to 308 GB/s. In time, all of them are limited by memory. But the chip draws 11 W for F16 and up to 53 W for Q3_K. F16 needs no unpacking, so the chip idles while it waits for memory. Every quantized format keeps the arithmetic units busy unpacking bits while the memory streams. The work is hidden in time, behind the memory, and shows up in power.

Subtracting F16's 0.036 nJ per byte, which is close to the cost of streaming memory through the chip with nothing else to do, leaves the unpacking cost alone: 0.034 nJ per byte for Q8_0, 0.049 for Q4_0, 0.082 for Q4_K, 0.109 for Q5_K, 0.166 for Q3_K.

## 2. The controlled pair: Q4_K's unpacking costs 40% more than Q4_0's

Same bytes, same speed (107.7 and 108.8 microseconds), and the chip draws 36.0 W for Q4_K against 25.8 W for Q4_0: **40% more chip energy and 21% more board energy** for the same traffic. Q4_0 stores one scale per block of 32 weights. Q4_K nests 6-bit scales and minimums inside super-blocks of 256, which costs extra arithmetic for every weight.

At the whole-model level, note 1 measured Q4_K_M at 22% more board energy than Q4_0. The kernel accounts for essentially all of it. **That is note 2's largest residual, explained.**

## 3. Below 4 bits, unpacking costs more than the bytes it saves

Q3_K reads 24% fewer bytes than Q4_0 and costs 27% more board energy per weight (160 against 127 pJ). Its unpacking, three bits split across planes with nested scales, is the most expensive of any format here. This is why Q3_K_M lost to Q4_0 in every note so far, on both machines. Q2_K, at 95 pJ per weight, is cheaper still, but note 1 showed its quality is far worse.

## 4. Q5_K and Q6_K cost the same per weight

At the board, Q5_K and Q6_K cost 215 and 216 pJ per weight. Q5_K reads fewer bytes and spends the saving on harder unpacking. So the kernel energy does not decide their order, and note 1's Q5_K_M penalty on the Mac must come from how the kernels run at the 1.5B model's smaller matrix shapes, where note 3 showed fixed costs matter more. That also explains why the order flipped on NVIDIA in note 4: it depends on the kernel and the shape, not on the format.

## A correction to note 2

Note 2 took 266 GB/s as the roof, measured with an MLX matrix-vector kernel, and said llama.cpp's own kernels might reach more. They do: the F16 kernel moves 306 to 309 GB/s. The roofline shares in notes 2 and 3 are therefore overstated by about 15%. The rankings and conclusions do not change, since every format is scaled by the same roof, but the absolute figures were overstated, and this note is where that is recorded.

## What to take from this

1. Quantization trades memory traffic for arithmetic. On this hardware the traffic dominates the time and the arithmetic shows up as power, so a format can be just as fast and still cost more.
2. The format name does not tell you the cost. Two formats with identical bytes differ by 40% in chip energy, entirely from how they unpack.
3. A measurement window has to be long compared to everything you do not want in it. One-second runs gave 40% disagreement; fifteen-second runs gave 2%.

## Limits

One matrix shape, one machine, one llama.cpp build. The kernels are Metal kernels and note 4 showed CUDA ranks some formats differently. Q4_K_M and the other `_M` variants mix several K-formats across layers, so a model's cost is a weighted mix of these rows, not one of them.

## Reproduce

```bash
git clone https://github.com/ggml-org/llama.cpp vendor/llama.cpp && cd vendor/llama.cpp
git checkout 620d2225c && git apply ../../experiments/test-backend-ops-perf-min-us.patch
cmake -B build -DGGML_METAL=ON -DLLAMA_BUILD_TESTS=ON && cmake --build build --target test-backend-ops
cd ../.. && uv run python experiments/kernels.py results/kernels.json
```

Raw results: `results/kernels-run1.json`, `results/kernels-run2.json`, `results/summary-kernels.json`.
