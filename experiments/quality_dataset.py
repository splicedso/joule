"""Collect every joules-per-correct-answer measurement into one table: results/spliced-quality.csv.

One row per machine, model, format and serving width (slots), averaged over the repeat passes.
Accuracy is on the first 250 GSM8K test questions (experiments/quality.py). Only measured
values; the `note` column names the note each row comes from.
"""

import csv
import glob
import json
from pathlib import Path

R = Path(__file__).parent.parent / "results"
OUT = R / "spliced-quality.csv"
FIELDS = ["machine", "model", "format", "calibration", "slots", "questions", "accuracy", "chip_j_per_correct",
          "net_j_per_correct", "chip_mj_per_token", "tok_s", "passes", "note", "source"]
MACHINES = {"mac": "Apple M5 Pro, 24 GB", "halo": "AMD Ryzen AI Max+ 395, 128 GB"}


def mean(xs):
    return sum(xs) / len(xs)


def row(files, machine, model, fmt, calibration, note):
    s = [json.load(open(f))["summary"] for f in files]
    return {"machine": MACHINES[machine], "model": model, "format": fmt, "calibration": calibration,
            "slots": s[0]["slots"], "questions": s[0]["n"], "accuracy": round(mean([x["accuracy"] for x in s]), 4),
            "chip_j_per_correct": round(mean([x["chip_j_per_correct"] for x in s]), 2),
            "net_j_per_correct": round(mean([x["net_j_per_correct"] for x in s]), 2),
            "chip_mj_per_token": round(mean([x["chip_mj_per_token"] for x in s]), 1),
            "tok_s": round(mean([x["tok_s"] for x in s]), 1), "passes": len(s), "note": note,
            "source": " ".join(sorted(Path(f).name for f in files))}


def main():
    rows = []
    for machine in MACHINES:
        for size in ("1.5b", "7b"):
            for slots in (1, 8):
                files = sorted(glob.glob(str(R / f"quality-{machine}-{size}-s{slots}-*.json")))
                if files:
                    rows.append(row(files, machine, f"Qwen2.5 {size.upper()}", "Q4_0", "none", 19))
    for name, fmt, cal in (("Q2_K-plain", "Q2_K", "none"), ("Q2_K-imatgeneral", "Q2_K", "imatrix, general text"),
                           ("Q2_K-imat", "Q2_K", "imatrix, GSM8K-train"), ("Q4_0", "Q4_0", "none")):
        files = sorted(glob.glob(str(R / f"lattice-v0-energy-1.5b-{name}-run*.json")))
        if files:
            rows.append(row(files, "mac", "Qwen2.5 1.5B", fmt, cal, 20))
    for size in ("7b", "32b"):
        for name, fmt, cal in (("Q4_0", "Q4_0", "none"), ("Q2_K-imat", "Q2_K", "imatrix, GSM8K-train")):
            files = sorted(glob.glob(str(R / f"lattice-halo-{size}-{name}-pass[12].json")))  # not the 7B pass-1 re-run
            if files:
                rows.append(row(files, "halo", f"Qwen2.5 {size.upper()}", fmt, cal, 22))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
