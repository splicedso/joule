"""Top-1 agreement with the 7B on held-out answers: the number a draft model is actually judged on.

For each drafter, the share of held-out answer positions (v1's validation prompts, the 7B's own
tokens from teacher.py) where the drafter's top guess is the 7B's token.

    python experiments/drafter/agree.py data/drafter/teacher.jsonl results/drafter/agree-mac.json
"""

import json
import sys
from pathlib import Path

from mlx_lm import load

from train_kd import VALID, agreement, examples

MODELS = {"stock": "models/hf-0.5b", "spliced": "models/hf-drafter-0.5b", "v2": "models/hf-drafter2-0.5b"}


def main():
    held = {json.loads(l)["messages"][0]["content"] for l in VALID.read_text().splitlines()}
    out = {}
    for name, path in MODELS.items():
        model, tokenizer = load(path)
        _, valid = examples(sys.argv[1], tokenizer, held)
        out[name] = {"agreement": agreement(model, valid), "positions": sum(len(e["ids"]) for e in valid)}
        print(name, out[name], flush=True)
    Path(sys.argv[2]).write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
