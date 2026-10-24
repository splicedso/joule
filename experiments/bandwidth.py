"""Achieved GPU memory bandwidth on Apple Silicon, measured with MLX.

Decode reads every weight once per token, so the bandwidth a kernel can actually reach,
not the spec-sheet figure, is the ceiling on decode speed. Three patterns, each on a
1 GiB float16 array so nothing fits in cache:
  read   x.sum()      reads N bytes
  copy   x * 1        reads N, writes N
  add    x + y        reads 2N, writes N
  matvec W @ v        reads N (W is 32768 x 16384), the operation decode actually runs
Best of 20 timed repetitions after warmup.

The matvec figure is the one to use as the decode roof: a reduction kernel does not reach
the bandwidth a well-tiled matrix-vector kernel does.
"""

import json
import sys
import time

import mlx.core as mx

N = 1 << 29  # elements; float16 so 1 GiB


def best(fn, reps=20):
    for _ in range(3):
        mx.eval(fn())
    times = []
    for _ in range(reps):
        t = time.perf_counter()
        mx.eval(fn())
        times.append(time.perf_counter() - t)
    return min(times)


def main():
    x = mx.random.uniform(shape=(N,)).astype(mx.float16)
    y = mx.random.uniform(shape=(N,)).astype(mx.float16)
    mx.eval(x, y)
    nbytes = N * 2
    out = {}
    W = x.reshape(32768, 16384)
    v = mx.random.uniform(shape=(16384,)).astype(mx.float16)
    mx.eval(W, v)
    for name, fn, moved in (("matvec", lambda: W @ v, nbytes),
                            ("read", lambda: x.sum(), nbytes),
                            ("copy", lambda: x * 1, 2 * nbytes),
                            ("add", lambda: x + y, 3 * nbytes)):
        t = best(fn)
        out[name] = moved / t / 1e9
        print(f"{name:5} {out[name]:6.1f} GB/s")
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as f:
            json.dump({"gb_per_s": out, "bytes": nbytes, "dtype": "float16"}, f, indent=2)


if __name__ == "__main__":
    main()
