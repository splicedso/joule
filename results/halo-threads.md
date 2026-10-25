# 7B decode: does CPU thread count change package power?

Prediction: if llama.cpp's CPU threads busy-wait during GPU decode, lowering the
thread count should cut the whole-package power (power1_average) at the same
tok/s. It did not.

7B Q4_0, Vulkan, all layers on GPU, `phase --seconds 20`, two passes each.

| threads | tok/s | SoC W (2 passes) |
|---|---:|---:|
| default | 50.1 to 50.3 | 99.2 to 99.5 |
| -t 1 | 50.2 to 50.3 | 99.1 to 100.4 |
| -t 4 | 50.2 to 50.3 | 98.8 to 99.6 |

Finding: thread count does not move 7B decode power. All three draw about 99 W
at about 50 tok/s, so the roughly 100 W is real GPU and memory draw in a memory
bound phase, not CPU busy-wait. No `-t` override is adopted; runs keep the
default threads. (Idle SoC wandered 6.9 to 15.4 W between runs, so net figures
spread more than gross; gross decode power is the steady number.)
