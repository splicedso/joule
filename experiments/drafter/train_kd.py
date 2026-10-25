"""Drafter v2: train the 0.5B on the 7B's probabilities, weighted toward the tokens it gets wrong.

Note 15 found that v1, trained on the 7B's text, lowered held-out loss 6% but raised acceptance
only about 3%: it improved tokens the stock draft already got right. v2 changes two things.

1. Soft targets. At every answer position the loss is the cross-entropy against the 7B's own
   top-20 distribution (teacher.py), renormalized, not against the single token it chose.
2. Weighting. Positions where the stock 0.5B's top guess differs from the 7B's count
   1 + ALPHA times as much, because those are the guesses a draft model loses.

Starts from the stock 0.5B, so v2 and v1 differ only in the training signal. Same split as v1:
prompts in v1's validation set are held out. AdamW, learning rate 1e-5, effective batch 8,
two epochs. Writes a Hugging Face model directory that convert.sh can quantize.

    python experiments/drafter/train_kd.py data/drafter/teacher.jsonl models/hf-drafter2-0.5b
"""

import json
import random
import shutil
import sys
import time
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from mlx.utils import tree_flatten, tree_map
from mlx_lm import load

BASE = "models/hf-0.5b"
VALID = Path("models/drafter-0.5b-data/valid.jsonl")
ALPHA = 2.0
MICRO, ACCUM, EPOCHS, LR, MAX_LEN = 4, 2, 2, 1e-5, 1536


def examples(path, tokenizer, held):
    train, valid = [], []
    for line in Path(path).read_text().splitlines():
        r = json.loads(line)
        if not r["ids"]:
            continue
        prompt = tokenizer.encode(r["template"], add_special_tokens=False)
        n = min(len(r["ids"]), MAX_LEN - len(prompt))
        if n <= 0:
            continue
        ex = {"prompt": prompt, "ids": r["ids"][:n], "top_ids": r["top_ids"][:n], "top_lp": r["top_lp"][:n]}
        (valid if r["prompt"] in held else train).append(ex)
    return train, valid


def batch(exs):
    """Inputs, and per answer position: its index in the sequence, the 7B's top ids and probabilities."""
    L = max(len(e["prompt"]) + len(e["ids"]) for e in exs) - 1
    k = len(exs[0]["top_ids"][0])
    A = max(len(e["ids"]) for e in exs)
    inp = [[0] * L for _ in exs]
    pos, tid, tp, mask = ([[0] * A for _ in exs] for _ in range(4))
    tid = [[[0] * k for _ in range(A)] for _ in exs]
    tp = [[[0.0] * k for _ in range(A)] for _ in exs]
    for b, e in enumerate(exs):
        seq = (e["prompt"] + e["ids"])[:-1]
        inp[b][:len(seq)] = seq
        for j in range(len(e["ids"])):
            pos[b][j] = len(e["prompt"]) - 1 + j
            ids, lps = e["top_ids"][j], e["top_lp"][j]
            ids, lps = (ids + [ids[0]] * k)[:k], (lps + [-1e9] * k)[:k]
            tid[b][j], tp[b][j] = ids, lps
            mask[b][j] = 1
    tp = mx.softmax(mx.array(tp), axis=-1)  # renormalize the top 20
    return mx.array(inp), mx.array(pos), mx.array(tid), tp, mx.array(mask, dtype=mx.float32)


def answer_logits(model, inp, pos):
    logits = model(inp)
    return mx.take_along_axis(logits, pos[..., None], axis=1).astype(mx.float32)


def loss_fn(model, inp, pos, tid, tp, mask, weight):
    lp = nn.log_softmax(answer_logits(model, inp, pos), axis=-1)
    ce = -(tp * mx.take_along_axis(lp, tid, axis=-1)).sum(-1)
    w = weight * mask
    return (ce * w).sum() / w.sum()


def agreement(model, exs):
    """Share of held-out answer positions where the model's top guess is the 7B's token."""
    hit = total = 0
    for i in range(0, len(exs), MICRO):
        inp, pos, tid, _, mask = batch(exs[i:i + MICRO])
        guess = answer_logits(model, inp, pos).argmax(-1)
        hit += ((guess == tid[..., 0]) * mask).sum().item()
        total += mask.sum().item()
    return hit / total


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    model, tokenizer = load(BASE)
    stock, _ = load(BASE)
    stock.freeze()
    held = {json.loads(l)["messages"][0]["content"] for l in VALID.read_text().splitlines()}
    train, valid = examples(src, tokenizer, held)
    print(f"{len(train)} train, {len(valid)} valid; stock agreement {agreement(stock, valid):.4f}", flush=True)

    opt = optim.AdamW(learning_rate=LR)
    grad = nn.value_and_grad(model, loss_fn)
    random.seed(3)
    steps, t0 = 0, time.monotonic()
    for epoch in range(EPOCHS):
        random.shuffle(train)
        acc, losses = None, []
        for i in range(0, len(train) - MICRO + 1, MICRO):
            inp, pos, tid, tp, mask = batch(train[i:i + MICRO])
            weight = 1 + ALPHA * (answer_logits(stock, inp, pos).argmax(-1) != tid[..., 0])
            loss, g = grad(model, inp, pos, tid, tp, mask, weight)
            acc = g if acc is None else tree_map(lambda a, b: a + b, acc, g)
            losses.append(loss.item())
            if len(losses) % ACCUM == 0:
                opt.update(model, tree_map(lambda a: a / ACCUM, acc))
                mx.eval(model.parameters(), opt.state)
                acc, steps = None, steps + 1
                if steps % 50 == 0:
                    print(f"epoch {epoch} step {steps} loss {sum(losses[-100:]) / len(losses[-100:]):.4f} "
                          f"{(time.monotonic() - t0) / 60:.0f} min", flush=True)
        print(f"epoch {epoch} done; held-out agreement {agreement(model, valid):.4f}", flush=True)

    shutil.copytree(BASE, out, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.safetensors", "*.index.json"))
    mx.save_safetensors(str(out / "model.safetensors"), dict(tree_flatten(model.parameters())), metadata={"format": "pt"})
    print("saved", out, flush=True)


if __name__ == "__main__":
    main()
