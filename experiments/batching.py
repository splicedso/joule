"""Decode energy per token against batch size, on one machine.

llama-batched-bench runs each batch size in turn (prefill, then decode) and reports
the time of each phase. Its timed work is the last thing it does, so walking the
phases backwards from the moment it exits gives each decode window on the sampler's
clock. Only chip power is used: the board reading is smoothed to about 1 Hz, too slow
for windows this short.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

from phase.power import Sampler, idle_baseline, mean_power

EDGE_S = 0.3


def run(sampler, model, batches, n_prompt, n_gen):
    cmd = ["llama-batched-bench", "-m", model, "-c", str(max(batches) * (n_prompt + n_gen) + 64),
           "-b", "2048", "-ub", "512", "-npp", str(n_prompt), "-ntg", str(n_gen),
           "-npl", ",".join(map(str, batches)), "--output-format", "jsonl"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    end = time.monotonic()
    rows = [json.loads(l) for l in out.splitlines() if l.startswith("{")]
    t = end
    results = []
    for r in reversed(rows):
        tg_end, tg_start = t, t - r["t_tg"]
        t = tg_start - r["t_pp"]
        window = sampler.window(tg_start + EDGE_S, tg_end - EDGE_S)
        soc_w, _ = mean_power(window)
        tokens_per_s = r["speed_tg"]
        n = len(window)
        results.append({"batch": r["pl"], "tokens_per_s": tokens_per_s, "soc_w": soc_w,
                        "gpu_w": sum(x.gpu_w for x in window) / n, "cpu_w": sum(x.cpu_w for x in window) / n,
                        "gpu_mhz": sum(x.gpu_mhz for x in window) / n,
                        "soc_mj_per_tok": soc_w / tokens_per_s * 1e3, "window_s": r["t_tg"],
                        "samples": len(window)})
    return results[::-1]


def main():
    model, out = sys.argv[1], Path(sys.argv[2])
    batches = [int(b) for b in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 2, 4, 8, 16, 32]
    runs = []
    with Sampler(100) as s:
        idle = idle_baseline(s, 8)
        for _ in range(3):
            time.sleep(4)
            runs.append(run(s, model, batches, 64, 512))
    out.write_text(json.dumps({"model": Path(model).name, "idle_soc_w": idle[0], "n_prompt": 64,
                               "n_gen": 512, "runs": runs}, indent=2) + "\n")
    for b in range(len(batches)):
        vals = [r[b]["soc_mj_per_tok"] for r in runs]
        tps = [r[b]["tokens_per_s"] for r in runs]
        mhz = sum(r[b]["gpu_mhz"] for r in runs) / len(runs)
        gw = sum(r[b]["gpu_w"] for r in runs) / len(runs)
        cw = sum(r[b]["cpu_w"] for r in runs) / len(runs)
        print(f"batch {batches[b]:>2}: {min(tps):7.1f}-{max(tps):7.1f} tok/s, "
              f"{min(vals):6.1f}-{max(vals):6.1f} mJ/tok chip, GPU {gw:5.1f} W @ {mhz:5.0f} MHz, CPU {cw:4.1f} W")


if __name__ == "__main__":
    main()
