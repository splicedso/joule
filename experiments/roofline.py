"""Roofline for decode: how close each format gets to the memory-bandwidth ceiling.

Decoding one token reads every weight tensor once, except the token embedding table, of
which it reads one row. The GGUF stores the output head as its own tensor, so the vocabulary
matrix is read in full through that, not through the embedding. At short context the KV
cache is negligible, so bytes per token is the sum of every tensor but token_embd, and the
fastest decode possible is achieved matvec bandwidth divided by that. Measured speed over that ceiling is how
much of the memory system the kernel actually uses.
"""

import json
import sys

from gguf import GGUFReader

BW = json.load(open("results/bandwidth-m5pro.json"))["gb_per_s"]["matvec"] * 1e9


def bytes_per_token(path):
    return sum(int(t.n_bytes) for t in GGUFReader(path).tensors if t.name != "token_embd.weight")

runs = [{r["model"]: r for r in json.load(open(f))["results"] if r["phase"] == "decode"}
        for f in ("results/quant-energy-1.5b.json", "results/quant-energy-1.5b-run2.json")]
rows = []
for name in runs[0]:
    size = bytes_per_token(f"models/quant/{name}")
    tps = sum(r[name]["tokens_per_s"] for r in runs) / 2
    ceiling = BW / size
    board = sum(r[name]["sys_j_per_tok"] for r in runs) / 2
    rows.append({"format": name.split("-")[1].split(".")[0], "gb_per_token": size / 1e9, "tok_s": tps,
                 "ceiling_tok_s": ceiling, "efficiency": tps / ceiling,
                 "achieved_gb_s": tps * size / 1e9, "board_mj": board * 1e3,
                 "board_nj_per_byte": board / size * 1e9})
print(f"{'format':7} {'GB':>5} {'tok/s':>6} {'ceiling':>7} {'eff':>5} {'GB/s':>6} {'board mJ':>8} {'nJ/byte':>7}")
for r in rows:
    print(f"{r['format']:7} {r['gb_per_token']:5.2f} {r['tok_s']:6.1f} {r['ceiling_tok_s']:7.1f} {r['efficiency']:5.0%} "
          f"{r['achieved_gb_s']:6.1f} {r['board_mj']:8.1f} {r['board_nj_per_byte']:7.3f}")
json.dump({"bandwidth_gb_s": BW / 1e9, "rows": rows}, open(sys.argv[1], "w"), indent=2)
