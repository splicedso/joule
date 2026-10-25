"""Kinetic: train one shape from scratch on a fixed token stream (docs/kinetic.md).

Each shape is a Qwen2-style decoder with about 50M non-embedding parameters and Qwen2.5's
vocabulary, so the four runs differ only in width and depth. Tokens come from a flat uint32
file (prepare.py), read in the same order for every shape. AdamW, cosine schedule with warm-up,
bf16 autocast. Held-out loss is logged every EVAL_EVERY steps; the model is saved in Hugging
Face format so convert_hf_to_gguf.py can turn it into GGUF for Phase.

    python experiments/kinetic/train.py SHAPE data/kinetic/train.bin data/kinetic/valid.bin models/kinetic-SHAPE

SHAPE is one of deep, base, wide, widest. MAX_STEPS caps a smoke test.
"""

import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import Qwen2Config, Qwen2ForCausalLM

SHAPES = {  # layers, width, attention heads, key-value heads; FFN is 3x width; head size is even for RoPE
    "deep": (24, 512, 8, 2),
    "base": (12, 720, 12, 3),
    "wide": (6, 1024, 16, 4),
    "widest": (4, 1260, 18, 6),
}
VOCAB = 151936
SEQ, BATCH, ACCUM = 1024, 16, 4
LR, WARMUP, EVAL_EVERY = 6e-4, 500, 500
MAX_STEPS = int(os.environ.get("MAX_STEPS", 0))
DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


def config(shape):
    layers, width, heads, kv = SHAPES[shape]
    return Qwen2Config(vocab_size=VOCAB, hidden_size=width, intermediate_size=3 * width, num_hidden_layers=layers,
                       num_attention_heads=heads, num_key_value_heads=kv, max_position_embeddings=SEQ,
                       tie_word_embeddings=True, rope_theta=10000.0)


def non_embedding_params(model):
    return sum(p.numel() for n, p in model.named_parameters() if "embed_tokens" not in n)


def batches(path, seed=0):
    data = np.memmap(path, dtype=np.uint32, mode="r")
    n = (len(data) - 1) // SEQ
    order = np.random.default_rng(seed).permutation(n)
    for i in range(0, n - BATCH + 1, BATCH):
        idx = order[i:i + BATCH]
        x = np.stack([data[j * SEQ:(j + 1) * SEQ + 1] for j in idx]).astype(np.int64)
        yield torch.from_numpy(x).to(DEVICE)


@torch.no_grad()
def held_out(model, path, n=20):
    model.eval()
    losses = []
    for k, x in enumerate(batches(path, seed=1)):
        if k >= n:
            break
        with torch.autocast(DEVICE, dtype=torch.bfloat16):
            losses.append(model(x[:, :-1], labels=x[:, :-1]).loss.item())
    model.train()
    return sum(losses) / len(losses)


def main():
    shape, train, valid, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    model = Qwen2ForCausalLM(config(shape)).to(DEVICE)
    params = non_embedding_params(model)
    tokens = len(np.memmap(train, dtype=np.uint32, mode="r"))
    total = MAX_STEPS or tokens // (SEQ * BATCH * ACCUM)
    print(f"{shape}: {params / 1e6:.1f}M non-embedding params, {total} steps on {DEVICE}", flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, betas=(0.9, 0.95), weight_decay=0.1)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / WARMUP) * 0.5 * (1 + math.cos(math.pi * min(1, s / max(1, total)))))
    log, step, micro, t0 = [], 0, 0, time.monotonic()
    for x in batches(train):
        with torch.autocast(DEVICE, dtype=torch.bfloat16):
            loss = model(x[:, :-1], labels=x[:, :-1]).loss / ACCUM
        loss.backward()
        micro += 1
        if micro % ACCUM:
            continue
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
        step += 1
        if step % EVAL_EVERY == 0 or step == total:
            v = held_out(model, valid)
            log.append({"step": step, "train_loss": loss.item() * ACCUM, "valid_loss": v})
            print(f"step {step}/{total} train {loss.item() * ACCUM:.3f} valid {v:.3f} "
                  f"{(time.monotonic() - t0) / 60:.0f} min", flush=True)
        if step >= total:
            break
    model.save_pretrained(out)
    (out / "train_log.json").write_text(json.dumps({"shape": shape, "params": params, "steps": step, "log": log}, indent=2) + "\n")


if __name__ == "__main__":
    main()
