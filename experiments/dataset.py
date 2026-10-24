"""Collect every decode-energy measurement into one table: results/spliced-decode-energy.csv.

One row per machine, runtime, model and format (and batch, where it was varied), averaged
over the repeat passes the note used. Only measured values: nothing is interpolated or
fitted. The `note` column says which research note the row comes from, and `source` which
results files.
"""

import csv
import json
import re
from pathlib import Path

R = Path(__file__).parent.parent / "results"
OUT = R / "spliced-decode-energy.csv"
MAC = "Apple M5 Pro, 24 GB"
WIN = "Intel Core Ultra 9 285H, RTX 5070 Ti Laptop, 32 GB"
FIELDS = ["machine", "runtime", "model", "params_b", "format", "batch", "tok_s", "chip_mj", "board_mj",
          "chip_point", "board_point", "power_state", "passes", "note", "source"]
PARAMS = {"0.5b": 0.5, "1.5b": 1.5, "3b": 3.1, "7b": 7.6}


def decode_rows(files):
    runs = [{r["model"]: r for r in json.load(open(R / f))["results"] if r["phase"] == "decode"} for f in files]
    return {k: [r[k] for r in runs if k in r] for k in runs[0]}


def mean(xs):
    return sum(xs) / len(xs)


def size_and_format(name):
    m = re.match(r"(0\.5b|1\.5b|3b|7b)-(\w+)\.gguf", name, re.I)
    return m.group(1).lower(), m.group(2).upper()


def llamacpp(files, note, machine=MAC, chip="chip (SoC)", board="board DC input", state="AC", skip=()):
    rows = []
    for name, got in decode_rows(files).items():
        size, fmt = size_and_format(name)
        if fmt in skip:
            continue
        rows.append({"machine": machine, "runtime": "llama.cpp b11669", "model": f"Qwen2.5 {size.upper()}",
                     "params_b": PARAMS[size], "format": fmt, "batch": 1,
                     "tok_s": round(mean([g["tokens_per_s"] for g in got]), 1),
                     "chip_mj": round(mean([g["soc_j_per_tok"] for g in got]) * 1e3, 1),
                     "board_mj": round(mean([g["sys_j_per_tok"] for g in got]) * 1e3, 1),
                     "chip_point": chip, "board_point": board, "power_state": state,
                     "passes": len(got), "note": note, "source": " ".join(files)})
    return rows


def main():
    rows = []
    rows += llamacpp(["quant-energy-1.5b.json", "quant-energy-1.5b-run2.json"], 1)
    rows += llamacpp(["quant-energy-7b.json", "quant-energy-7b-run2.json"], 3, skip=("F16",))
    rows += llamacpp(["quant-energy-windows-battery-run1.json", "quant-energy-windows-battery-run2.json"], 4,
                     machine=WIN, chip="GPU (nvidia-smi, includes VRAM)", board="battery discharge", state="battery")
    rows += llamacpp(["quant-energy-windows-ac-run1.json", "quant-energy-windows-ac-run2.json"], 10,
                     machine=WIN, chip="GPU (nvidia-smi, includes VRAM)", board="", state="AC")
    for r in rows:
        if r["note"] == 10:
            r["runtime"], r["board_mj"] = "llama.cpp b11851 (CUDA)", ""
        if r["note"] == 4:
            r["runtime"] = "llama.cpp b11851 (CUDA)"
    for name, got in decode_rows(["width-run1.json", "width-run2.json"]).items():
        size, fmt = size_and_format(name)
        if size in ("0.5b", "3b"):
            rows += [r for r in llamacpp(["width-run1.json", "width-run2.json"], 6) if r["model"] == f"Qwen2.5 {size.upper()}" and r["format"] == fmt]
    for q, fmt in (("q4_0", "Q4_0"), ("q4_k_m", "Q4_K_M")):
        runs = json.load(open(R / f"batching-gpu-1.5b-{q}.json"))["runs"]
        for i in range(len(runs[0])):
            rows.append({"machine": MAC, "runtime": "llama.cpp b11669", "model": "Qwen2.5 1.5B", "params_b": 1.5,
                         "format": fmt, "batch": runs[0][i]["batch"],
                         "tok_s": round(mean([r[i]["tokens_per_s"] for r in runs]), 1),
                         "chip_mj": round(mean([r[i]["soc_mj_per_tok"] for r in runs]), 1), "board_mj": "",
                         "chip_point": "chip (SoC)", "board_point": "", "power_state": "AC", "passes": len(runs),
                         "note": 1, "source": f"batching-gpu-1.5b-{q}.json"})
    for r in llamacpp(["width-windows-run1.json", "width-windows-run2.json"], 12, machine=WIN,
                      chip="GPU (nvidia-smi, includes VRAM)", board="", state="AC"):
        if r["model"] in ("Qwen2.5 0.5B", "Qwen2.5 3B", "Qwen2.5 7B") or r["format"] in ("Q5_K_M", "Q6_K"):
            r["runtime"], r["board_mj"] = "llama.cpp b11851 (CUDA)", ""
            rows.append(r)
    for q, fmt in (("q4_0", "Q4_0"), ("q4_k_m", "Q4_K_M")):
        runs = json.load(open(R / f"batching-windows-{q}.json"))["runs"]
        for i in range(len(runs[0])):
            rows.append({"machine": WIN, "runtime": "llama.cpp b11851 (CUDA)", "model": "Qwen2.5 1.5B", "params_b": 1.5,
                         "format": fmt, "batch": runs[0][i]["batch"],
                         "tok_s": round(mean([r[i]["tokens_per_s"] for r in runs]), 1),
                         "chip_mj": round(mean([r[i]["soc_mj_per_tok"] for r in runs]), 1), "board_mj": "",
                         "chip_point": "GPU (nvidia-smi, includes VRAM)", "board_point": "", "power_state": "AC",
                         "passes": len(runs), "note": 10, "source": f"batching-windows-{q}.json"})
    names = {"NVIDIA H100-NVL-94GB": "8x NVIDIA H100 NVL server", "NVIDIA B200-SXM-180GB": "8x NVIDIA B200 server"}
    models = {"llama2-70b-99": ("Llama 2 70B", 70), "llama3.1-8b": ("Llama 3.1 8B", 8), "llama3.1-405b": ("Llama 3.1 405B", 405)}
    for r in csv.DictReader(open(R / "mlperf-llm-power.csv")):
        if r["model"] not in models or r["scenario"] != "Offline":
            continue
        model, params = models[r["model"]]
        rows.append({"machine": names[r["accelerator"]], "runtime": f"MLPerf v{r['round']} ({r['submitter']})",
                     "model": model, "params_b": params, "format": r["dtype"].upper(), "batch": "server-chosen",
                     "tok_s": round(float(r["tok_s"]), 1), "chip_mj": "", "board_mj": round(float(r["j_per_tok"]) * 1e3, 1),
                     "chip_point": "", "board_point": "server at the wall", "power_state": "AC", "passes": 1,
                     "note": 8, "source": "mlperf-llm-power.csv"})
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "rows ->", OUT.name)


if __name__ == "__main__":
    main()
