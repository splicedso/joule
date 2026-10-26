"""Build the prompt sets for the Spliced drafter: training, validation and held-out evaluation.

Sources, both licensed for reuse:
  UltraChat 200k (MIT), first user turn of each conversation, for chat and writing.
  CodeAlpaca 20k (CC-BY-4.0), instruction plus input, for code.

Trace v1 trains on about ten times v0's prompts. Pass the training count on the command line
(default 35000); chat and code are drawn 2:1, as in v0. Training draws from UltraChat's three
train_gen shards and the first 15,000 CodeAlpaca rows; evaluation from UltraChat's test_gen split
and CodeAlpaca rows after 19,000, so no evaluation prompt can appear in training.

Two sets are held fixed from v0 and never redrawn here:
  - the 80 held-out EVALUATION prompts, read back from results/drafter/eval-prompts.jsonl as they are;
  - the 180 VALIDATION prompts, the same split train.py made from results/drafter/train-answers.jsonl
    (answers with text, seed 3, shuffled, first 5%). They are rebuilt here, written to
    valid-prompts.jsonl for the teacher run and to models/drafter-0.5b-data/valid.jsonl (the file
    train_trace.py reads), and excluded from the new training set by exact match.

    python experiments/drafter/prepare.py [TRAIN_COUNT]
"""

import json
import random
import sys
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).parents[2]
D = ROOT / "data" / "drafter"
OUT = ROOT / "results" / "drafter"
ANSWERS = OUT / "train-answers.jsonl"          # v0 answers, committed; source of the valid split
VALID_MODEL = ROOT / "models" / "drafter-0.5b-data" / "valid.jsonl"  # the file train_trace.py reads

UC_TRAIN = ["train_gen-00000-of-00003-a6c9fb894be3e50b.parquet",
            "train_gen-00001-of-00003-d6a0402e417f35ca.parquet",
            "train_gen-00002-of-00003-c0db75b92a2f48fd.parquet"]
UC_TEST = "test_gen-00000-of-00001-3d4cd8309148a71f.parquet"


def ultrachat_pool(files):
    rows = []
    for f in files:
        rows += pq.read_table(D / "ultrachat" / "data" / f, columns=["prompt"]).column("prompt").to_pylist()
    return [r.strip() for r in rows if 40 <= len(r.strip()) <= 1200]


def codealpaca_pool(lo, hi):
    rows = json.load(open(D / "codealpaca" / "code_alpaca_20k.json"))[lo:hi]
    pool = []
    for r in rows:
        p = r["instruction"].strip()
        if r.get("input", "").strip():
            p += "\n\n" + r["input"].strip()
        if 20 <= len(p) <= 1200:
            pool.append(p)
    return pool


def validation_split():
    """The 180 validation records, exactly as train.py derives them from the v0 answers."""
    rows = [json.loads(l) for l in ANSWERS.read_text().splitlines()]
    rows = [r for r in rows if r["answer"].strip()]
    random.Random(3).shuffle(rows)                 # same seed and order as train.py
    n_valid = max(50, len(rows) // 20)
    return rows[:n_valid]


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 35000
    OUT.mkdir(parents=True, exist_ok=True)
    VALID_MODEL.parent.mkdir(parents=True, exist_ok=True)

    # Fixed sets from v0, never redrawn.
    eval_rows = [json.loads(l) for l in (OUT / "eval-prompts.jsonl").read_text().splitlines()]
    valid_recs = validation_split()
    fixed = {r["prompt"] for r in eval_rows} | {r["prompt"] for r in valid_recs}

    # New training draw, 2:1 chat:code, excluding every fixed prompt.
    rng = random.Random(11)
    n_code = count // 3
    code_pool = [p for p in codealpaca_pool(0, 15000) if p not in fixed]
    n_code = min(n_code, len(code_pool))
    n_chat = count - n_code
    chat_pool = [p for p in ultrachat_pool(UC_TRAIN) if p not in fixed]
    if n_chat > len(chat_pool):
        raise SystemExit(f"need {n_chat} chat prompts, only {len(chat_pool)} available")
    train = [{"kind": "chat", "prompt": p} for p in rng.sample(chat_pool, n_chat)]
    train += [{"kind": "code", "prompt": p} for p in rng.sample(code_pool, n_code)]
    rng.shuffle(train)

    # Guard: no fixed prompt leaked into training.
    seen = {t["prompt"] for t in train}
    assert not (seen & fixed), "an eval or validation prompt appears in the training set"
    assert len(seen) == len(train), "duplicate prompt in the training set"

    (OUT / "train-prompts.jsonl").write_text("".join(json.dumps(t) + "\n" for t in train))
    (OUT / "valid-prompts.jsonl").write_text(
        "".join(json.dumps({"kind": "valid", "prompt": r["prompt"]}) + "\n" for r in valid_recs))
    VALID_MODEL.write_text("".join(json.dumps(
        {"messages": [{"role": "user", "content": r["prompt"]},
                      {"role": "assistant", "content": r["answer"]}]}) + "\n" for r in valid_recs))

    print(f"{len(train)} training prompts ({n_chat} chat, {n_code} code), "
          f"{len(valid_recs)} validation, {len(eval_rows)} eval held out", flush=True)
    print(f"teacher input: run teacher.py over valid-prompts.jsonl then train-prompts.jsonl "
          f"(same teacher.jsonl); train_trace.py reads {VALID_MODEL}", flush=True)


if __name__ == "__main__":
    main()
