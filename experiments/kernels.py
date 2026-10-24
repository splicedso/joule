"""Energy of one matrix-vector kernel per format, measured alone.

Note 2's energy model explained most formats by bytes moved, and left a residual per format:
Q4_0 cheaper than its bytes, Q5_K_M dearer. Note 4 found Q5_K_M and Q6_K swap order between
Metal and CUDA. Both point at the kernel that unpacks each format. This runs that kernel alone.

llama.cpp's test-backend-ops in perf mode times one MUL_MAT: a 4096 x 14336 weight matrix
(a 7B feed-forward layer) times one vector, which is what decode does. Upstream it runs for
one second, too short for the power sensor: a first version that repeated one-second runs
disagreed between passes by up to 40%, because process start, teardown and the sensor's own
averaging fell inside the window. experiments/test-backend-ops-perf-min-us.patch makes the
run length an environment variable, and each format now runs as one continuous loop of about
`seconds`. Its timed work is aligned backwards from the moment it prints; the first quarter
(clock ramp) and the last half second (teardown) are dropped.

Bytes per weight come from each format's block layout, so the kernel's achieved bandwidth and
its energy per byte follow. Q4_0 and Q4_K store exactly 0.5625 bytes per weight: identical
traffic, different unpacking, so the difference between them is the kernel alone.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from joule.power import Sampler, idle_baseline, mean_power

BIN = Path(__file__).parent.parent / "vendor/llama.cpp/build/bin/test-backend-ops"
M, K = 4096, 14336
# bytes per weight, from each format's block size in ggml-common.h
BYTES_PER_WEIGHT = {"f16": 2.0, "q8_0": 34 / 32, "q6_K": 210 / 256, "q5_K": 176 / 256,
                    "q4_K": 144 / 256, "q4_0": 18 / 32, "q3_K": 110 / 256, "q2_K": 84 / 256}
TAIL_S = 0.5
LINE = re.compile(r"MUL_MAT\(type_a=(\w+),.*?\):\s+(\d+) runs -\s+([\d.]+) us/run")


def run_once(fmt, seconds):
    env = dict(os.environ, PERF_MIN_US=str(int(seconds * 1e6)))
    out = subprocess.run([str(BIN), "perf", "-o", "MUL_MAT", "-b", "MTL0", "-p", f"type_a={fmt},.*n=1,"],
                         capture_output=True, text=True, env=env).stdout
    end = time.monotonic()
    m = LINE.search(out)
    if not m or m.group(1) != fmt:
        raise RuntimeError(f"no {fmt} matvec in output")
    runs, us = int(m.group(2)), float(m.group(3))
    return runs, us, end


def measure(sampler, fmt, seconds):
    runs, us, end = run_once(fmt, seconds)
    span = runs * us / 1e6
    window = sampler.window(end - span * 0.75, end - TAIL_S)
    soc_w, sys_w = mean_power(window)
    nbytes = M * K * BYTES_PER_WEIGHT[fmt]
    gb_s = nbytes / (us / 1e6) / 1e9
    return {"format": fmt, "us_per_run": us, "runs": runs, "gb_per_s": gb_s, "soc_w": soc_w, "sys_w": sys_w,
            "soc_nj_per_byte": soc_w / (gb_s * 1e9) * 1e9, "sys_nj_per_byte": sys_w / (gb_s * 1e9) * 1e9,
            "soc_uj_per_run": soc_w * us, "samples": len(window)}


def main():
    out = Path(sys.argv[1])
    order = sys.argv[2].split(",") if len(sys.argv) > 2 else list(BYTES_PER_WEIGHT)
    rows = []
    with Sampler(100) as s:
        idle = idle_baseline(s, 8)
        for fmt in order:
            time.sleep(3)
            r = measure(s, fmt, 15)
            r["soc_net_nj_per_byte"] = (r["soc_w"] - idle[0]) / (r["gb_per_s"] * 1e9) * 1e9
            rows.append(r)
            print(f"{fmt:5} {r['us_per_run']:7.1f} us  {r['gb_per_s']:6.1f} GB/s  chip {r['soc_w']:5.1f} W  "
                  f"{r['soc_nj_per_byte']:.3f} nJ/byte chip  {r['sys_nj_per_byte']:.3f} board  n={r['samples']}", flush=True)
    out.write_text(json.dumps({"shape": [M, K], "idle_w": {"soc": idle[0], "sys": idle[1]}, "rows": rows}, indent=2) + "\n")


if __name__ == "__main__":
    main()
