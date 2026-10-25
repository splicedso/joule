"""Trace v1: train a draft model on the target's probabilities, in PyTorch, for the Linux machine.

The MLX trainer (train_kd.py) used 18 GB on the Mac for 3,400 prompts: it held every record
in Python lists and computed full-vocabulary logits at every position. This version streams
records from disk by byte offset and applies the 151k-way output layer only at answer
positions, so memory stays near the model and optimizer state.

Same signal as train_kd.py: cross-entropy against the 7B's renormalized top-20 distribution,
positions where the stock draft's top guess differs from the 7B's weighted 1 + ALPHA. Weights
train in float32 with bf16 autocast; held-out top-1 agreement is checked every EVAL_EVERY
steps and the best weights are kept. Same held-out split as v0 (v1's validation prompts).

    python experiments/drafter/train_trace.py data/drafter/teacher.jsonl models/trace-0.5b-v1

Environment: ALPHA (default 2), EPOCHS (1), LR (1e-5), MAX_STEPS (0 = no cap, for smoke tests).
"""

import json
import os
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "models/hf-0.5b"
VALID = Path("models/drafter-0.5b-data/valid.jsonl")
ALPHA = float(os.environ.get("ALPHA", 2))
EPOCHS = int(os.environ.get("EPOCHS", 1))
LR = float(os.environ.get("LR", 1e-5))
MAX_STEPS = int(os.environ.get("MAX_STEPS", 0))
MICRO, ACCUM, MAX_LEN, WARMUP, EVAL_EVERY, PATIENCE = 4, 2, 1536, 100, 200, 5
DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


def index(path, held):
    """Byte offsets of training records, and the parsed held-out records (small)."""
    train, valid = [], []
    with open(path, "rb") as f:
        while True:
            off = f.tell()
            line = f.readline()
            if not line:
                break
            prompt = json.loads(line)["prompt"]
            (valid.append(json.loads(line)) if prompt in held else train.append(off))
    return train, valid


def read(path, offsets):
    with open(path, "rb") as f:
        out = []
        for off in offsets:
            f.seek(off)
            out.append(json.loads(f.readline()))
        return out


def batch(recs, tok):
    """Token ids, the answer positions, and the 7B's top ids and renormalized probabilities there."""
    seqs, pos, tid, tlp = [], [], [], []
    for b, r in enumerate(recs):
        prompt = tok.encode(r["template"], add_special_tokens=False)
        n = min(len(r["ids"]), MAX_LEN - len(prompt))
        if n <= 0:
            continue
        seqs.append((prompt + r["ids"][:n])[:-1])
        for j in range(n):
            pos.append((len(seqs) - 1, len(prompt) - 1 + j))
            k = len(r["top_ids"][j])
            tid.append(r["top_ids"][j] + [r["top_ids"][j][0]] * (20 - k))
            tlp.append(r["top_lp"][j] + [-1e9] * (20 - k))
    L = max(len(s) for s in seqs)
    ids = torch.zeros(len(seqs), L, dtype=torch.long)
    mask = torch.zeros(len(seqs), L, dtype=torch.long)
    for b, s in enumerate(seqs):
        ids[b, :len(s)] = torch.tensor(s)
        mask[b, :len(s)] = 1
    rows, cols = torch.tensor(pos).T
    return (ids.to(DEVICE), mask.to(DEVICE), rows.to(DEVICE), cols.to(DEVICE),
            torch.tensor(tid, device=DEVICE), torch.softmax(torch.tensor(tlp, device=DEVICE), -1))


def answer_logits(model, ids, mask, rows, cols):
    hidden = model.model(input_ids=ids, attention_mask=mask).last_hidden_state
    return model.lm_head(hidden[rows, cols]).float()


@torch.no_grad()
def agreement(model, valid, tok):
    model.eval()
    hit = total = 0
    for i in range(0, len(valid), MICRO):
        ids, mask, rows, cols, tid, _ = batch(valid[i:i + MICRO], tok)
        with torch.autocast(DEVICE, dtype=torch.bfloat16):
            guess = answer_logits(model, ids, mask, rows, cols).argmax(-1)
        hit += (guess == tid[:, 0]).sum().item()
        total += len(guess)
    model.train()
    return hit / total


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float32).to(DEVICE)
    stock = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16).to(DEVICE).eval()
    stock.requires_grad_(False)
    held = {json.loads(l)["messages"][0]["content"] for l in VALID.read_text().splitlines()}
    train, valid = index(src, held)
    best = agreement(model, valid, tok)
    print(f"{DEVICE}: {len(train)} train, {len(valid)} valid; stock agreement {best:.4f}", flush=True)

    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / WARMUP))
    best_state, best_step, misses, trained_best, steps, log = None, 0, 0, 0.0, 0, []
    random.seed(3)
    t0 = time.monotonic()
    for epoch in range(EPOCHS):
        random.shuffle(train)
        for i in range(0, len(train) - MICRO + 1, MICRO):
            ids, mask, rows, cols, tid, tp = batch(read(src, train[i:i + MICRO]), tok)
            with torch.autocast(DEVICE, dtype=torch.bfloat16):
                with torch.no_grad():
                    weight = 1 + ALPHA * (answer_logits(stock, ids, mask, rows, cols).argmax(-1) != tid[:, 0]).float()
                lp = F.log_softmax(answer_logits(model, ids, mask, rows, cols), -1)
            ce = -(tp * lp.gather(-1, tid)).sum(-1)
            loss = (ce * weight).sum() / weight.sum()
            (loss / ACCUM).backward()
            if (i // MICRO + 1) % ACCUM:
                continue
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            steps += 1
            if MAX_STEPS and steps >= MAX_STEPS:
                break
            if steps % EVAL_EVERY:
                continue
            agree = agreement(model, valid, tok)
            log.append({"step": steps, "epoch": epoch, "loss": loss.item(), "agreement": agree})
            print(f"step {steps} loss {loss.item():.4f} held-out agreement {agree:.4f} "
                  f"{(time.monotonic() - t0) / 60:.0f} min", flush=True)
            if agree > best:
                best, best_step = agree, steps
                best_state = {k: v.detach().to("cpu", copy=True) for k, v in model.state_dict().items()}
            misses = 0 if agree > trained_best else misses + 1
            trained_best = max(trained_best, agree)
            if misses >= PATIENCE:
                break
        if misses >= PATIENCE or (MAX_STEPS and steps >= MAX_STEPS):
            break

    print(f"best held-out agreement {best:.4f} at step {best_step}", flush=True)
    if best_state is not None:
        model.load_state_dict(best_state)
    model.to(torch.bfloat16).save_pretrained(out)
    tok.save_pretrained(out)
    (out / "train_log.json").write_text(json.dumps({"alpha": ALPHA, "lr": LR, "best_step": best_step,
                                                    "best_agreement": best, "log": log}, indent=2) + "\n")


if __name__ == "__main__":
    main()
