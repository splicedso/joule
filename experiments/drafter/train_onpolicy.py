"""Trace v1, on-policy: the draft writes, the target grades every token it wrote.

Off-policy distillation (train_trace.py: the student imitates text the 7B wrote) left held-out
agreement flat at about 0.756 against the stock draft's 0.7616 on both machines. DistillSpec
(Zhou et al., 2023) found on-policy data works better for draft models: the student generates,
and the teacher's distribution over the student's own tokens is the target, so training lands on
exactly the positions where the draft goes wrong.

Each step: the student greedily continues a batch of training prompts by GEN tokens; the teacher
scores the prompt plus those tokens in one forward pass; the loss is the total variation distance
(TVD) between teacher and student next-token distributions at the generated positions (DistillSpec's
best divergence for acceptance). Held-out top-1 agreement on the off-policy validation set
(the 7B's own answers, from teacher.py) is checked every EVAL_EVERY steps and the best weights kept.

    python experiments/drafter/train_onpolicy.py data/drafter/teacher.jsonl TEACHER models/trace-0.5b-v1-onpolicy

TEACHER is a Hugging Face directory (the bf16 7B) or a .gguf (the Q4_0 7B's weights dequantized into
transformers, so the teacher is the model the draft is judged on; see teacher_check.py).
Environment: LR (3e-6), STEPS (300), GEN (128), MICRO (4), DIV (tvd or kl), MAX_STEPS for smoke tests,
STUDENT (default the stock 0.5B; a checkpoint directory to continue from, e.g. the 35k off-policy model).
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

sys.path.insert(0, str(Path(__file__).parent))
from train_trace import BASE, DEVICE, VALID, agreement, index, read  # noqa: E402

LR = float(os.environ.get("LR", 3e-6))
STEPS = int(os.environ.get("MAX_STEPS") or os.environ.get("STEPS", 300))
GEN = int(os.environ.get("GEN", 128))
MICRO = int(os.environ.get("MICRO", 4))
DIV = os.environ.get("DIV", "tvd")
EVAL_EVERY = int(os.environ.get("EVAL_EVERY", 50))


@torch.no_grad()
def rollout(student, tok, prompts):
    """Greedy continuations from the student; returns token ids, attention mask and the generated span."""
    tok.padding_side = "left"
    enc = tok([p["template"] for p in prompts], return_tensors="pt", padding=True).to(DEVICE)
    student.eval()
    with torch.autocast(DEVICE, dtype=torch.bfloat16):
        out = student.generate(**enc, max_new_tokens=GEN, do_sample=False, pad_token_id=tok.pad_token_id)
    student.train()
    start = enc["input_ids"].shape[1]
    mask = (out != tok.pad_token_id).long()
    mask[:, :start] = enc["attention_mask"]
    return out, mask, start


def divergence(s_logits, t_logits, valid):
    # Qwen2.5 0.5B and 7B pad their vocab differently (151936 vs 152064); the real
    # tokens are the shared prefix, so compare over the common size.
    v = min(s_logits.size(-1), t_logits.size(-1))
    s_logits, t_logits = s_logits[..., :v], t_logits[..., :v]
    s, t = F.log_softmax(s_logits.float(), -1), F.log_softmax(t_logits.float(), -1)
    if DIV == "kl":
        d = F.kl_div(s, t, log_target=True, reduction="none").sum(-1)        # KL(teacher || student)
    else:
        d = 0.5 * (t.exp() - s.exp()).abs().sum(-1)                          # total variation distance
    return (d * valid).sum() / valid.sum().clamp(min=1)


def main():
    src, teacher_dir, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    tok = AutoTokenizer.from_pretrained(BASE)
    student = AutoModelForCausalLM.from_pretrained(os.environ.get("STUDENT", BASE), torch_dtype=torch.float32).to(DEVICE)
    if teacher_dir.endswith(".gguf"):  # the Q4_0 7B's own weights, dequantized (the model the draft is judged on)
        teacher = AutoModelForCausalLM.from_pretrained("models/hf-7b", gguf_file=str(Path(teacher_dir).resolve()),
                                                       torch_dtype=torch.bfloat16).to(DEVICE).eval()
    else:
        teacher = AutoModelForCausalLM.from_pretrained(teacher_dir, torch_dtype=torch.bfloat16).to(DEVICE).eval()
    teacher.requires_grad_(False)
    held = {json.loads(l)["messages"][0]["content"] for l in VALID.read_text().splitlines()}
    train, valid = index(src, held)
    best = agreement(student, valid, tok)
    print(f"{DEVICE}: {len(train)} prompts, {len(valid)} held out; stock agreement {best:.4f}", flush=True)
    opt = torch.optim.AdamW(student.parameters(), lr=LR, weight_decay=0.0)
    random.seed(3)
    best_state, best_step, log, t0 = None, 0, [], time.monotonic()
    for step in range(1, STEPS + 1):
        prompts = read(src, random.sample(train, MICRO))
        ids, mask, start = rollout(student, tok, prompts)
        with torch.no_grad(), torch.autocast(DEVICE, dtype=torch.bfloat16):
            t_logits = teacher(input_ids=ids, attention_mask=mask).logits[:, start - 1:-1]
        with torch.autocast(DEVICE, dtype=torch.bfloat16):
            s_logits = student(input_ids=ids, attention_mask=mask).logits[:, start - 1:-1]
        loss = divergence(s_logits, t_logits, mask[:, start:].float())
        loss.backward()
        torch.nn.utils.clip_grad_norm_(student.parameters(), 1.0)
        opt.step(); opt.zero_grad(set_to_none=True)
        if step % EVAL_EVERY and step != STEPS:
            continue
        agree = agreement(student, valid, tok)
        log.append({"step": step, "loss": loss.item(), "agreement": agree})
        print(f"step {step} {DIV} {loss.item():.4f} held-out agreement {agree:.4f} {(time.monotonic() - t0) / 60:.0f} min", flush=True)
        if agree > best:
            best, best_step = agree, step
            best_state = {k: v.detach().to("cpu", copy=True) for k, v in student.state_dict().items()}
    print(f"best held-out agreement {best:.4f} at step {best_step}", flush=True)
    if best_state is not None:
        student.load_state_dict(best_state)
    student.to(torch.bfloat16).save_pretrained(out)
    tok.save_pretrained(out)
    (out / "train_log.json").write_text(json.dumps({"div": DIV, "lr": LR, "gen": GEN, "best_step": best_step,
                                                    "best_agreement": best, "log": log}, indent=2) + "\n")


if __name__ == "__main__":
    main()
