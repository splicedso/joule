"""Lattice v1: quantization-aware fine-tuning, so a 1.5B keeps its answers at Q2_K size.

Standard quantization collapses below about 3.9 bits per weight: Qwen2.5 1.5B scores 66% on GSM8K-250
at Q4_0 and 21% at Q2_K; a GSM8K-calibrated importance matrix lifts Q2_K to 42% (note 20). This
fine-tunes the model with its linear weights fake-quantized to a Q2_K-shaped grid during the forward
pass, so the weights move to values the 2-bit grid can hold.

The grid: llama.cpp's Q2_K stores each weight as a 2-bit index q in 0..3 inside a group of 16, with a
scale and a minimum per group (w = min + scale * q). Here every linear in the transformer blocks gets a
learned float scale and minimum per group of 16 input weights (LSQ+ style: initialised from the group's
range, trained with the weights), rounding passes gradients straight through, and the master weights stay
in fp32 (a 1e-5 update on a 0.02 weight is below bf16's resolution and would be rounded away). Compute is
bf16 autocast. Embeddings and the output layer are not fake-quantized; llama.cpp quantizes those at its
own precision for Q2_K.

Data: GSM8K train (MIT) in the exact chat format quality.py evaluates (its instruction, the worked answer
with the calculator annotations removed and "#### N" rewritten as "The answer is N."), loss on the answer
tokens only, with the last 200 problems held out for a validation loss; plus a share of general text
(GENERAL_FRAC of the batches, 512-token windows of FineWeb-Edu from data/kinetic/train.bin, loss on every
token) so the model does not forget how to write.

At the end the fake-quantized values are written into the weights and the model is saved in Hugging Face
format; experiments/lattice_qat.sh converts it to GGUF and quantizes to Q2_K with the GSM8K imatrix, so
the artefact is a real Q2_K file quality.py can run.

    .venv-torch/bin/python experiments/lattice/qat.py models/hf-1.5b models/lattice-1.5b-qat

Environment: DATA (a JSONL of {"prompt", "response"} to train on instead of GSM8K's worked answers; one epoch then
counts the general-text batches on top), STEPS (0 = one epoch of GSM8K train), LR (1e-5), BATCH (8), SEQ (1024), GENERAL_FRAC (0.3),
GROUP (16), EVAL_EVERY (100), CKPT_EVERY (200: a resumable checkpoint in the output
directory, picked up automatically when the run is started again), DEVICE (cuda or cpu), SEED (3), QUANT (1; 0 trains the identical setup with fake quantization off:
fp32 masters for the same linears, same data, steps, LR and schedule, so only the grid differs), LORA_R (0; with QUANT=0, a rank-R LoRA on the
same linears with everything else frozen, merged into the weights at the end; LORA_ALPHA defaults to 2R).
"""

import json
import math
import os
import random
import shutil
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

STEPS = int(os.environ.get("STEPS", 0))
LR = float(os.environ.get("LR", 1e-5))
BATCH = int(os.environ.get("BATCH", 8))
SEQ = int(os.environ.get("SEQ", 1024))
GENERAL_FRAC = float(os.environ.get("GENERAL_FRAC", 0.3))
GROUP = int(os.environ.get("GROUP", 16))
EVAL_EVERY = int(os.environ.get("EVAL_EVERY", 100))
SEED = int(os.environ.get("SEED", 3))
QUANT = os.environ.get("QUANT", "1") != "0"   # 0: the same fine-tune with fake quantization off (the plain control)
DATA = os.environ.get("DATA")   # a JSONL of {"prompt", "response"} to train on instead of GSM8K's worked answers (e.g. RFT)
CKPT_EVERY = int(os.environ.get("CKPT_EVERY", 200))   # a resumable checkpoint in the output directory every N steps (0: never); a restart with the same output directory resumes from it
STOP_AFTER = int(os.environ.get("STOP_AFTER", 0))     # test hook: exit right after the checkpoint at this step, as a crash would
LORA_R = int(os.environ.get("LORA_R", 0))             # >0 (QUANT=0 only): train a rank-R LoRA on every block linear, the rest frozen; merged into the weights at the end
LORA_ALPHA = float(os.environ.get("LORA_ALPHA", 2 * LORA_R))
QMAX = 3                      # 2-bit: q in 0..3
HELD_OUT = 200
GSM8K_TRAIN = Path("data/gsm8k-train.jsonl")
GENERAL = Path("data/kinetic/train.bin")
INSTRUCTION = "Solve the problem. Think step by step, then finish with a line of the form 'The answer is N.'"
DEVICE = os.environ.get("DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")


class FakeQuant(torch.autograd.Function):
    """w_hat = min + scale * clamp(round((w - min) / scale), 0, QMAX), with LSQ+ gradients."""

    @staticmethod
    def forward(ctx, w, scale, mn):
        x = (w - mn) / scale
        q = x.round().clamp_(0, QMAX)
        ctx.save_for_backward(x, q)
        return mn + scale * q

    @staticmethod
    def backward(ctx, grad):
        x, q = ctx.saved_tensors
        inside = (x > -0.5) & (x < QMAX + 0.5)
        g = 1.0 / math.sqrt(x.shape[-1] * QMAX)                       # LSQ gradient scale
        w_grad = grad * inside
        s_grad = (grad * torch.where(inside, q - x, q)).sum(-1, keepdim=True) * g
        m_grad = (grad * (~inside)).sum(-1, keepdim=True) * g
        return w_grad, s_grad, m_grad


class QLinear(nn.Module):
    """nn.Linear whose weight is fake-quantized per group of GROUP input weights in every forward."""

    def __init__(self, lin: nn.Linear):
        super().__init__()
        out_f, in_f = lin.weight.shape
        assert in_f % GROUP == 0, (out_f, in_f)
        self.weight = nn.Parameter(lin.weight.detach().float())      # fp32 master
        self.bias = nn.Parameter(lin.bias.detach().float()) if lin.bias is not None else None
        g = self.weight.detach().view(out_f, in_f // GROUP, GROUP)
        lo, hi = g.min(-1, keepdim=True).values, g.max(-1, keepdim=True).values
        self.scale = nn.Parameter(((hi - lo) / QMAX).clamp(min=1e-6))
        self.min = nn.Parameter(lo.clone())

    def quantized_weight(self):
        out_f, in_f = self.weight.shape
        g = self.weight.view(out_f, in_f // GROUP, GROUP)
        return FakeQuant.apply(g, self.scale.clamp(min=1e-6), self.min).view(out_f, in_f)

    def forward(self, x):
        w = self.quantized_weight() if QUANT else self.weight
        return F.linear(x, w.to(x.dtype), None if self.bias is None else self.bias.to(x.dtype))

    def bake(self) -> nn.Linear:
        lin = nn.Linear(self.weight.shape[1], self.weight.shape[0], bias=self.bias is not None)
        with torch.no_grad():
            lin.weight.copy_((self.quantized_weight() if QUANT else self.weight).to(torch.bfloat16))
            if self.bias is not None:
                lin.bias.copy_(self.bias.to(torch.bfloat16))
        return lin.to(torch.bfloat16)


class LoRALinear(nn.Module):
    """nn.Linear kept frozen (bf16) plus a rank-LORA_R update B @ A (A fp32, Kaiming-uniform; B zeros, so the model starts
    unchanged), scaled by LORA_ALPHA / LORA_R; bake() merges the update into the weight and returns the plain nn.Linear."""

    def __init__(self, lin: nn.Linear):
        super().__init__()
        self.base = lin
        self.base.weight.requires_grad_(False)
        if self.base.bias is not None:
            self.base.bias.requires_grad_(False)
        out_f, in_f = lin.weight.shape
        self.lora_a = nn.Parameter(torch.empty(LORA_R, in_f, dtype=torch.float32, device=lin.weight.device))
        nn.init.kaiming_uniform_(self.lora_a, a=math.sqrt(5))
        self.lora_b = nn.Parameter(torch.zeros(out_f, LORA_R, dtype=torch.float32, device=lin.weight.device))
        self.scaling = LORA_ALPHA / LORA_R

    def forward(self, x):
        return self.base(x) + (x @ self.lora_a.t().to(x.dtype) @ self.lora_b.t().to(x.dtype)) * self.scaling

    def bake(self) -> nn.Linear:
        with torch.no_grad():
            self.base.weight += (self.lora_b @ self.lora_a * self.scaling).to(self.base.weight.dtype)
        self.base.weight.requires_grad_(True)
        return self.base


def swap(model, to_q=True):
    """Replace every nn.Linear in the transformer blocks with a QLinear, or a LoRALinear when LORA_R is set (or bake them back)."""
    n = 0
    for layer in model.model.layers:
        for parent in (layer.self_attn, layer.mlp):
            for name, child in list(parent.named_children()):
                if to_q and isinstance(child, nn.Linear):
                    setattr(parent, name, LoRALinear(child) if LORA_R else QLinear(child)); n += 1
                elif not to_q and isinstance(child, (QLinear, LoRALinear)):
                    setattr(parent, name, child.bake()); n += 1
    return n


def gsm8k_examples(tok):
    rows = [json.loads(l) for l in GSM8K_TRAIN.read_text().splitlines()]
    out = []
    for r in rows:
        body, final = r["answer"].rsplit("####", 1)
        body = re.sub(r"<<[^>]*>>", "", body).strip()
        answer = f"{body}\nThe answer is {final.strip()}."
        prompt = tok.apply_chat_template([{"role": "user", "content": f"{INSTRUCTION}\n\n{r['question']}"}],
                                         tokenize=False, add_generation_prompt=True)
        p_ids = tok(prompt, add_special_tokens=False)["input_ids"]
        a_ids = tok(answer + "<|im_end|>", add_special_tokens=False)["input_ids"]
        ids = (p_ids + a_ids)[:SEQ]
        labels = ([-100] * len(p_ids) + a_ids)[:SEQ]
        out.append((ids, labels))
    return out[:-HELD_OUT], out[-HELD_OUT:]


def data_examples(tok, path):
    """Chat examples from a JSONL of {"prompt": user text, "response": assistant text}, loss on the response only,
    in the same chat format as gsm8k_examples; 200 held out (seeded shuffle) for the validation loss."""
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    random.Random(SEED).shuffle(rows)
    out = []
    for r in rows:
        prompt = tok.apply_chat_template([{"role": "user", "content": r["prompt"]}], tokenize=False, add_generation_prompt=True)
        p_ids = tok(prompt, add_special_tokens=False)["input_ids"]
        a_ids = tok(r["response"] + "<|im_end|>", add_special_tokens=False)["input_ids"]
        out.append(((p_ids + a_ids)[:SEQ], ([-100] * len(p_ids) + a_ids)[:SEQ]))
    return out[:-HELD_OUT], out[-HELD_OUT:]


def general_batch(mm, rng, n, length=512):
    """Random windows of general text; labels are the ids (the loss shifts by one), loss on every token."""
    starts = rng.integers(0, len(mm) - length, size=n)
    return [(ids, ids) for ids in (np.asarray(mm[s:s + length]).astype(np.int64).tolist() for s in starts)]


def collate(examples, pad_id):
    L = max(len(ids) for ids, _ in examples)
    ids = torch.full((len(examples), L), pad_id, dtype=torch.long)
    labels = torch.full((len(examples), L), -100, dtype=torch.long)
    mask = torch.zeros((len(examples), L), dtype=torch.long)
    for i, (x, y) in enumerate(examples):
        ids[i, :len(x)] = torch.tensor(x); labels[i, :len(y)] = torch.tensor(y); mask[i, :len(x)] = 1
    return ids.to(DEVICE), labels.to(DEVICE), mask.to(DEVICE)


@torch.no_grad()
def quant_check(model, name="model.layers.0.mlp.down_proj"):
    """Proof the fake quantization is on: distinct values per group of the quantized weight (at most
    QMAX + 1) and the mean absolute error between the master weight and its quantized value."""
    mod = dict(model.named_modules())[name]
    w = mod.weight.detach().float()
    q = mod.quantized_weight().detach().float()
    out_f, in_f = w.shape
    groups = q.view(-1, GROUP)
    distinct = torch.tensor([len(torch.unique(g)) for g in groups[torch.randperm(groups.shape[0])[:4096]]])
    return {"linear": name, "shape": [out_f, in_f], "groups_sampled": int(distinct.numel()),
            "max_distinct_per_group": int(distinct.max()), "mean_distinct_per_group": round(float(distinct.float().mean()), 3),
            "mae_master_vs_quantized": float((w - q).abs().mean()), "mean_abs_master": float(w.abs().mean()),
            "frac_changed_by_quant": float(((w - q).abs() > 1e-7).float().mean())}


@torch.no_grad()
def validate(model, held, pad_id):
    model.eval(); tot = n = 0
    for i in range(0, len(held), BATCH):
        ids, labels, mask = collate(held[i:i + BATCH], pad_id)
        with torch.autocast(DEVICE, dtype=torch.bfloat16):
            logits = model(input_ids=ids, attention_mask=mask).logits
        loss = F.cross_entropy(logits[:, :-1].float().reshape(-1, logits.shape[-1]), labels[:, 1:].reshape(-1),
                               ignore_index=-100, reduction="sum")
        tot += loss.item(); n += (labels[:, 1:] != -100).sum().item()
    model.train()
    return tot / n


def main():
    src, out = sys.argv[1], Path(sys.argv[2])
    random.seed(SEED); rng = np.random.default_rng(SEED); torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(src)
    model = AutoModelForCausalLM.from_pretrained(src, dtype=torch.bfloat16).to(DEVICE)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})   # non-reentrant: gradients reach LoRA parameters inside a block even though the block's input (frozen embeddings) carries none
    model.config.use_cache = False
    if LORA_R and QUANT:
        sys.exit("LORA_R needs QUANT=0 (a LoRA on fake-quantized linears is not implemented)")
    n_q = swap(model, True)
    if LORA_R:   # only the LoRA factors train; embeddings, norms, biases and the output layer stay as loaded
        for n_, p in model.named_parameters():
            p.requires_grad_(n_.endswith(".lora_a") or n_.endswith(".lora_b"))
    train, held = data_examples(tok, DATA) if DATA else gsm8k_examples(tok)
    mm = np.memmap(GENERAL, dtype=np.uint32, mode="r")
    pad = tok.pad_token_id
    # with DATA, one epoch means every example once, so the steps given to general text are added on top
    total = STEPS or (math.ceil(len(train) / BATCH / (1 - GENERAL_FRAC)) if DATA else math.ceil(len(train) / BATCH))
    q_params = [p for n, p in model.named_parameters() if p.requires_grad and (n.endswith(".scale") or n.endswith(".min"))]
    w_params = [p for n, p in model.named_parameters() if p.requires_grad and not (n.endswith(".scale") or n.endswith(".min"))]
    opt = torch.optim.AdamW([{"params": w_params, "lr": LR}, {"params": q_params, "lr": LR, "weight_decay": 0.0}], weight_decay=0.0)
    warm = max(1, min(50, total // 10))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / total))))
    config = {"src": src, "total": total, "lr": LR, "batch": BATCH, "seq": SEQ, "general_frac": GENERAL_FRAC, "group": GROUP,
              "quant": QUANT, "data": DATA, "seed": SEED, "lora_r": LORA_R, "lora_alpha": LORA_ALPHA}
    ckpt = out / "checkpoint" / "latest.pt"
    start, resumed, t0 = 1, None, time.monotonic()
    if CKPT_EVERY and ckpt.exists():
        c = torch.load(ckpt, map_location=DEVICE, weights_only=False)
        if c["config"] != config:
            sys.exit(f"{ckpt} is from a different run ({c['config']} against {config}); remove it or use another output directory")
        model.load_state_dict(c["model"]); opt.load_state_dict(c["opt"]); sched.load_state_dict(c["sched"])
        log, order, pos, qc0 = c["log"], c["order"], c["pos"], c["qc0"]
        random.setstate(c["py_random"]); rng.bit_generator.state = c["np_rng"]; torch.set_rng_state(c["torch_rng"])
        if DEVICE == "cuda" and c.get("cuda_rng") is not None:
            torch.cuda.set_rng_state(c["cuda_rng"])
        t0 -= c["elapsed"]; start = resumed = c["step"] + 1
        print(f"{DEVICE}: resumed from the checkpoint at step {c['step']} of {total} ({c['elapsed'] / 60:.1f} min already spent)", flush=True)
    else:
        v0 = validate(model, held, pad)
        how = ('fake-quantized (group ' + str(GROUP) + ', ' + str(QMAX + 1) + ' levels)' if QUANT else
               f'with a rank-{LORA_R} LoRA (alpha {LORA_ALPHA:g}), {sum(p.numel() for p in w_params):,} trained parameters, the rest frozen' if LORA_R else
               'with fp32 masters, NOT quantized (QUANT=0)')
        print(f"{DEVICE}: {n_q} linears {how}; {len(train)} train, {len(held)} held out; "
              f"{total} steps, batch {BATCH}; held-out loss before training {v0:.4f}", flush=True)
        qc0 = quant_check(model) if QUANT else None
        print("quant check at step 0:" if QUANT else "QUANT=0: fake quantization off (plain fine-tune)", json.dumps(qc0) if QUANT else "", flush=True)
        log = [{"step": 0, "valid_loss": v0}]
        order = list(range(len(train))); random.shuffle(order)
        pos = 0
    model.train()
    for step in range(start, total + 1):
        if rng.random() < GENERAL_FRAC:
            batch = general_batch(mm, rng, BATCH)
        else:
            if pos + BATCH > len(order):
                random.shuffle(order); pos = 0
            batch = [train[i] for i in order[pos:pos + BATCH]]; pos += BATCH
        ids, labels, mask = collate(batch, pad)
        with torch.autocast(DEVICE, dtype=torch.bfloat16):
            logits = model(input_ids=ids, attention_mask=mask).logits
        loss = F.cross_entropy(logits[:, :-1].float().reshape(-1, logits.shape[-1]), labels[:, 1:].reshape(-1), ignore_index=-100)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
        if step % 10 == 0 or step == total:
            print(f"step {step}/{total} loss {loss.item():.4f} lr {sched.get_last_lr()[0]:.2e} {(time.monotonic() - t0) / 60:.1f} min "
                  f"peak {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB" if DEVICE == "cuda" else f"step {step} loss {loss.item():.4f}", flush=True)
        if step % EVAL_EVERY == 0 or step == total:
            v = validate(model, held, pad)
            log.append({"step": step, "train_loss": loss.item(), "valid_loss": v})
            print(f"step {step} held-out loss {v:.4f}", flush=True)
        if CKPT_EVERY and step % CKPT_EVERY == 0 and step < total:   # the model, the optimizer, the data order and every RNG: a resume replays the run exactly
            ckpt.parent.mkdir(parents=True, exist_ok=True)
            torch.save({"step": step, "config": config, "model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(),
                        "log": log, "order": order, "pos": pos, "qc0": qc0, "py_random": random.getstate(), "np_rng": rng.bit_generator.state,
                        "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state() if DEVICE == "cuda" else None,
                        "elapsed": time.monotonic() - t0}, ckpt.with_suffix(".tmp"))
            os.replace(ckpt.with_suffix(".tmp"), ckpt)
            print(f"checkpoint at step {step} ({ckpt.stat().st_size / 2**30:.1f} GiB)", flush=True)
            if STOP_AFTER == step:
                print(f"STOP_AFTER={step}: exiting here, as a crash would", flush=True); sys.exit(3)
    qc1 = quant_check(model) if QUANT else None
    if QUANT:
        print("quant check at the end:", json.dumps(qc1), flush=True)
    n_b = swap(model, False)
    model.config.use_cache = True
    model.to(torch.bfloat16).save_pretrained(out)
    tok.save_pretrained(out)
    shutil.rmtree(out / "checkpoint", ignore_errors=True)   # the final model is saved; the checkpoint has done its job
    (out / "train_log.json").write_text(json.dumps({"quant": QUANT, "data": DATA, "steps": total, "lr": LR, "batch": BATCH, "group": GROUP, "general_frac": GENERAL_FRAC, "checkpoint_every": CKPT_EVERY, "resumed_from": resumed,
                                                    "lora_r": LORA_R, "lora_alpha": LORA_ALPHA,
                                                    "baked_linears": n_b, "quant_check_step0": qc0, "quant_check_end": qc1, "peak_gib": torch.cuda.max_memory_allocated() / 2**30 if DEVICE == "cuda" else None,
                                                    "minutes": (time.monotonic() - t0) / 60, "log": log}, indent=2) + "\n")
    print(f"saved {out} ({n_b} linears baked) after {(time.monotonic() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
