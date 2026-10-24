"""How well does each drafter predict the target's answers? Held-out loss, no speculation involved.

For each example in the validation split (the 5% of the 7B's answers held back from
training), the mean negative log-likelihood each model assigns to the answer tokens, with the
prompt as context. Lower means the model predicts the 7B better. Reported as loss and as
perplexity, for the stock 0.5B and the distilled one.

    python experiments/drafter/loss.py results/drafter/loss-mac.json
"""

import json
import math
import sys
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load

MODELS = {"stock": "models/hf-0.5b", "spliced": "models/hf-drafter-0.5b"}
VALID = Path("models/drafter-0.5b-data/valid.jsonl")


def answer_nll(model, tokenizer, ex):
    msgs = ex["messages"]
    prompt = tokenizer.apply_chat_template(msgs[:1], add_generation_prompt=True, tokenize=True)
    full = tokenizer.apply_chat_template(msgs, tokenize=True)
    ids = mx.array(full)[None]
    logits = model(ids[:, :-1]).astype(mx.float32)
    losses = nn.losses.cross_entropy(logits, ids[:, 1:], reduction="none")[0]
    answer = losses[len(prompt) - 1:]
    return float(answer.sum()), answer.size


def main():
    rows = [json.loads(l) for l in VALID.read_text().splitlines()]
    out = {}
    for name, path in MODELS.items():
        model, tokenizer = load(path)
        total, n = 0.0, 0
        for ex in rows:
            s, k = answer_nll(model, tokenizer, ex)
            total, n = total + s, n + k
        out[name] = {"loss": total / n, "perplexity": math.exp(total / n), "tokens": n, "examples": len(rows)}
        print(f"{name:8} loss {total / n:.4f}  perplexity {math.exp(total / n):.3f}  over {n} answer tokens", flush=True)
        del model
        mx.clear_cache()
    Path(sys.argv[1]).write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
