"""Build the prompt sets for the Spliced drafter: training prompts and held-out evaluation prompts.

Sources, both licensed for reuse:
  UltraChat 200k (MIT), first user turn of each conversation, for chat and writing.
  CodeAlpaca 20k (CC-BY-4.0), instruction plus input, for code.

Training draws from UltraChat's train_gen split and the first 15,000 CodeAlpaca rows.
Evaluation draws from UltraChat's test_gen split and CodeAlpaca rows after 19,000, so no
evaluation prompt can appear in training; an exact-match check enforces it anyway.
"""

import json
import random
from pathlib import Path

import pyarrow.parquet as pq

D = Path(__file__).parents[2] / "data" / "drafter"
OUT = Path(__file__).parents[2] / "results" / "drafter"
random.seed(11)


def ultrachat(split_file, n):
    rows = pq.read_table(D / "ultrachat" / "data" / split_file, columns=["prompt"]).column("prompt").to_pylist()
    rows = [r.strip() for r in rows if 40 <= len(r.strip()) <= 1200]
    return random.sample(rows, n)


def codealpaca(lo, hi, n):
    rows = json.load(open(D / "codealpaca" / "code_alpaca_20k.json"))[lo:hi]
    prompts = []
    for r in rows:
        p = r["instruction"].strip()
        if r.get("input", "").strip():
            p += "\n\n" + r["input"].strip()
        if 20 <= len(p) <= 1200:
            prompts.append(p)
    return random.sample(prompts, n)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    train = [{"kind": "chat", "prompt": p} for p in ultrachat("train_gen-00000-of-00003-a6c9fb894be3e50b.parquet", 2400)]
    train += [{"kind": "code", "prompt": p} for p in codealpaca(0, 15000, 1200)]
    random.shuffle(train)
    held = [{"kind": "chat", "prompt": p} for p in ultrachat("test_gen-00000-of-00001-3d4cd8309148a71f.parquet", 40)]
    held += [{"kind": "code", "prompt": p} for p in codealpaca(19000, 20022, 40)]
    seen = {t["prompt"] for t in train}
    assert not [h for h in held if h["prompt"] in seen], "evaluation prompt found in training set"
    (OUT / "train-prompts.jsonl").write_text("".join(json.dumps(t) + "\n" for t in train))
    (OUT / "eval-prompts.jsonl").write_text("".join(json.dumps(h) + "\n" for h in held))
    print(len(train), "train prompts,", len(held), "held-out prompts")


if __name__ == "__main__":
    main()
