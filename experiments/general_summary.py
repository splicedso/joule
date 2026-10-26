"""Summarize general_eval.py results: conditions side by side, passes averaged, spreads and cut-off replies shown.

    python experiments/general_summary.py results/general-*.json

Runs are grouped by (model, think, max_tokens, server args); each group should hold the two passes of one
condition. Per task: accuracy, tokens per answer, chip joules per correct answer, the pass-to-pass spread of
joules per correct, and replies that hit max_tokens (a cut-off reply scores wrong whatever it was about to say).
With two or more conditions, each is also shown as a ratio to the first on accuracy points and joules per correct.
"""
import json, sys
from collections import defaultdict


def load(paths):
    groups = defaultdict(list)
    for p in paths:
        d = json.load(open(p))
        o = d["overall"]
        groups[(o["model"], o.get("think"), o.get("max_tokens"), o.get("server_args", ""))].append(d)
    return groups


def summarize(runs):
    tasks = {}
    for name in runs[0]["tasks"]:
        s = [r["tasks"][name]["summary"] for r in runs if name in r["tasks"]]
        rows = [row for r in runs if name in r["tasks"] for row in r["tasks"][name]["rows"]]
        jpc = [x["chip_j_per_correct"] for x in s if x["chip_j_per_correct"]]
        mt = runs[0]["overall"].get("max_tokens") or 0
        tasks[name] = {"passes": len(s), "accuracy": sum(x["accuracy"] for x in s) / len(s),
                       "tokens_per_answer": sum(x["tokens_per_answer"] for x in s) / len(s),
                       "j_per_correct": sum(jpc) / len(jpc) if jpc else None,
                       "spread": (max(jpc) - min(jpc)) / (sum(jpc) / len(jpc)) if len(jpc) > 1 else None,
                       "cut_off": sum(1 for row in rows if mt and row["tokens"] >= mt) / len(rows), "n": s[0]["n"]}
    return tasks


def main():
    groups = load(sys.argv[1:])
    keys = list(groups)
    summ = {k: summarize(groups[k]) for k in keys}
    label = lambda k: f"{k[0]}, think={k[1]}, max {k[2]}" + (f", {k[3]}" if k[3] else "")
    print("| condition | task | n | passes | accuracy | tokens per answer | J per correct | spread | cut off |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in keys:
        for t, v in summ[k].items():
            j = f"{v['j_per_correct']:.1f}" if v["j_per_correct"] else "-"
            sp = f"{v['spread']:.1%}" if v["spread"] is not None else "-"
            print(f"| {label(k)} | {t} | {v['n']} | {v['passes']} | {v['accuracy']:.1%} | {v['tokens_per_answer']:.0f} | {j} | {sp} | {v['cut_off']:.0%} |")
    if len(keys) > 1:
        base = summ[keys[0]]
        print(f"\nAgainst {label(keys[0])}:")
        for k in keys[1:]:
            for t, v in summ[k].items():
                if t in base and v["j_per_correct"] and base[t]["j_per_correct"]:
                    print(f"  {label(k)}, {t}: accuracy {100 * (v['accuracy'] - base[t]['accuracy']):+.1f} points, "
                          f"tokens x{v['tokens_per_answer'] / base[t]['tokens_per_answer']:.1f}, J per correct x{v['j_per_correct'] / base[t]['j_per_correct']:.2f}")
    for k in keys:
        if len(groups[k]) != 2:
            print(f"\nnote: {label(k)} has {len(groups[k])} run(s), not the two passes of a condition")


if __name__ == "__main__":
    main()
