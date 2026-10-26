"""How much matrix size matters: the same formats across four model widths.

A single matrix repeated in a loop is the wrong instrument at small sizes: a 1536 x 1536
matrix is 1.3 to 4.7 MB, it stays in the chip's cache between runs, and the benchmark then
measures cache bandwidth, not memory. Real decode streams every layer's weights, far more
than any cache holds. So the sweep uses real models of four widths, Qwen2.5 0.5B, 1.5B, 3B
and 7B (hidden size 896, 1536, 2048, 3584), each quantized from its own F16 GGUF.

This script reads the energy runs made with `phase` and normalises them per weight: decode
energy per token divided by the weights read per token (every tensor except the token
embedding table, as in note 2). It also reports the share of the bandwidth roof, using the
307 GB/s llama.cpp's own F16 kernel reaches (note 5).
"""

import json
import sys
from pathlib import Path

from gguf import GGUFReader

ROOF_GB_S = 307.0
WIDTHS = {"0.5b": 896, "1.5b": 1536, "3b": 2048, "7b": 3584}
# WIDTHS="granite2b:2048,3b:2048" names other models (files models/quant/<name>-<FORMAT>.gguf) and their hidden size
import os
if os.environ.get("WIDTHS"):
    WIDTHS = {k: int(v) for k, v in (x.split(":") for x in os.environ["WIDTHS"].split(","))}
FORMATS = ["Q4_0", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]


def read_weights(path):
    weights = nbytes = 0
    for t in GGUFReader(path).tensors:
        if t.name == "token_embd.weight":
            continue
        weights += int(t.n_elements)
        nbytes += int(t.n_bytes)
    return weights, nbytes


def main():
    runs = [{r["model"]: r for r in json.load(open(f))["results"] if r["phase"] == "decode"} for f in sys.argv[1:-1]]
    rows = []
    for size, width in WIDTHS.items():
        for fmt in FORMATS:
            name = f"{size}-{fmt}.gguf"
            got = [r[name] for r in runs if name in r]
            if not got:
                continue
            weights, nbytes = read_weights(f"models/quant/{name}")
            tps = sum(g["tokens_per_s"] for g in got) / len(got)
            soc = sum(g["soc_j_per_tok"] for g in got) / len(got)
            board = sum(g["sys_j_per_tok"] for g in got) / len(got)
            # board is 0 where whole-system power is unreadable (e.g. Windows on AC);
            # report the spread only when there is a board signal.
            spread = (max(g["sys_j_per_tok"] for g in got) - min(g["sys_j_per_tok"] for g in got)) / board if board else 0.0
            rows.append({"size": size, "width": width, "format": fmt, "weights": weights, "bytes": nbytes,
                         "tok_s": tps, "roof_share": tps * nbytes / 1e9 / ROOF_GB_S,
                         "soc_pj_per_weight": soc / weights * 1e12, "board_pj_per_weight": board / weights * 1e12,
                         "board_mj": board * 1e3, "spread": spread})
    print(f"{'size':5} {'format':7} {'roof':>5} {'chip pJ/w':>9} {'board pJ/w':>10} {'spread':>6}")
    for r in rows:
        print(f"{r['size']:5} {r['format']:7} {r['roof_share']:5.0%} {r['soc_pj_per_weight']:9.1f} {r['board_pj_per_weight']:10.1f} {r['spread']:6.1%}")
    Path(sys.argv[-1]).write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
