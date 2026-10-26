"""Summarize a decode_batch_energy.py result: one row per batch, both passes side by side.

    uv run python experiments/decode_batch_summary.py results/decode-batch-mac-7b-q4km.json

Prints a markdown table (tok/s total, tok/s per request, watts, mJ/token per pass, the mean, the
saving against batch 1, and the pass spread) and a JSON line with the per-token factor Fabric's cost
table takes (costs/*.json, "batch_scaling").
"""
import json, sys

d = json.load(open(sys.argv[1]))
by = {}
for r in d["rows"]:
    by.setdefault(r["batch"], {})[r["pass"]] = r
base = None
print(f'{d["model"]} on {d["machine"]}, {d["answer_tokens"]}-token answers, power: {d["power"]}\n')
print("| batch | tok/s | tok/s per request | W | mJ/token pass 1 | pass 2 | mean | vs batch 1 | spread |")
print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
factor = {}
for b in sorted(by):
    p1, p2 = by[b][1], by[b][2]
    m = (p1["mj_per_token"] + p2["mj_per_token"]) / 2
    spread = abs(p1["mj_per_token"] - p2["mj_per_token"]) / m
    if base is None: base = m
    factor[str(b)] = round(m / base, 3)
    tok_s = (p1["tok_s"] + p2["tok_s"]) / 2
    w = (p1["watts"] + p2["watts"]) / 2
    print(f'| {b} | {tok_s:.1f} | {tok_s / b:.1f} | {w:.1f} | {p1["mj_per_token"]:.0f} | {p2["mj_per_token"]:.0f} | {m:.0f} | {100 * (1 - m / base):.0f}% less | {100 * spread:.1f}% |')
print("\nper_token_factor:", json.dumps(factor))
