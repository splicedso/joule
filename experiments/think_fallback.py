"""Replay a think-then-fall-back policy on recorded general_eval.py results.

Policy: let the model think up to BUDGET tokens; if it has not answered by then, ask again with thinking off.
Decoding here is repeatable (both passes of each condition produced identical tokens), so a reply that finished
under the budget is what a budget-capped run would return. A replay, not a measurement: the fallback is charged
BUDGET thinking tokens plus the recorded thinking-off reply.

Usage: python3 experiments/think_fallback.py OFF.json ON.json [limit]
"""
import json
import sys

BUDGETS = (1024, 2048, 4096, 8192, 16384)


def tasks(path):
    return json.load(open(path))["tasks"]


def replay(off, on, budget, limit):
    rows = []
    for task in off:
        correct = tokens = 0
        pairs = list(zip(off[task]["rows"], on[task]["rows"]))
        for plain, thought in pairs:
            if thought["tokens"] < min(budget, limit):
                correct += thought["correct"]
                tokens += thought["tokens"]
            else:
                correct += plain["correct"]
                tokens += budget + plain["tokens"]
        plain_tokens = sum(p["tokens"] for p, _ in pairs)
        plain_correct = sum(p["correct"] for p, _ in pairs)
        rows.append((task, len(pairs), correct, tokens, plain_correct, plain_tokens))
    return rows


def main():
    off, on = tasks(sys.argv[1]), tasks(sys.argv[2])
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 16384
    print("| budget | task | accuracy | thinking off | tokens per question | x thinking off |")
    print("|---:|---|---:|---:|---:|---:|")
    for budget in BUDGETS:
        rows = replay(off, on, budget, limit)
        rows.append(("all", *(sum(r[i] for r in rows) for i in range(1, 6))))
        for task, n, correct, tokens, plain_correct, plain_tokens in rows:
            print(f"| {budget:,} | {task} | {correct / n:.1%} | {plain_correct / n:.1%} | {tokens / n:,.0f} | {tokens / plain_tokens:.1f} |")


if __name__ == "__main__":
    main()
