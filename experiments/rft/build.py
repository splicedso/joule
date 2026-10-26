"""Rejection-sampling fine-tuning, step 2: keep the correct answers, at most PER_PROBLEM distinct ones per problem.

    python experiments/rft/build.py data/rft/samples-1.5b.jsonl data/rft/rft-1.5b.jsonl
"""
import json, os, sys
from collections import defaultdict
from pathlib import Path

PER_PROBLEM = int(os.environ.get("PER_PROBLEM", "2"))
rows = [json.loads(l) for l in Path(sys.argv[1]).read_text().splitlines()]
keep = defaultdict(list)
for r in sorted(rows, key=lambda r: (r["source"], str(r["id"]), r["sample"])):
    k = (r["source"], r["id"])
    if r["correct"] and r["finish"] != "length" and len(keep[k]) < PER_PROBLEM and r["response"].strip() not in {x["response"].strip() for x in keep[k]}:
        keep[k].append(r)
out = [{"source": r["source"], "id": r["id"], "prompt": r["prompt"], "response": r["response"].strip()} for v in keep.values() for r in v]
Path(sys.argv[2]).write_text("".join(json.dumps(r) + "\n" for r in out))
by = defaultdict(int)
for r in out: by[r["source"]] += 1
print(json.dumps({"examples": len(out), "by_source": by, "problems": len(keep)}))
