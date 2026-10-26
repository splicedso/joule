"""Is a transformers teacher faithful to the Q4_0 7B the draft is judged against?

Held-out agreement scores a draft against the Q4_0 7B's own greedy tokens (teacher.py, through
llama.cpp). On-policy training needs a teacher that scores the student's rollouts, and that
teacher lived in transformers, so Trace v1's on-policy run used the bf16 7B: a different model
from the one the draft is judged on. This measures the gap. For each teacher, the share of
held-out answer positions where its top-1 is the token the Q4_0 7B actually wrote, and the mean
absolute difference between its log-probability of that token and llama.cpp's.

    .venv-torch/bin/python experiments/drafter/teacher_check.py data/drafter/teacher.jsonl results/drafter/teacher-check-halo.json

Teachers: the bf16 7B (models/hf-7b) and the Q4_0 7B's weights dequantized into transformers
(models/quant/7b-Q4_0.gguf through gguf_file). Numerics differ from llama.cpp's kernels; the
weights do not.
"""

import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).parent))
from train_trace import BASE, DEVICE, VALID, index, read  # noqa: E402

HF7 = "models/hf-7b"
TEACHERS = {"bf16": HF7, "q4_0-dequant": "models/quant/7b-Q4_0.gguf"}


def load(spec):
    if spec.endswith(".gguf"):
        return AutoModelForCausalLM.from_pretrained(HF7, gguf_file=str(Path(spec).resolve()), torch_dtype=torch.bfloat16)
    return AutoModelForCausalLM.from_pretrained(spec, torch_dtype=torch.bfloat16)


@torch.no_grad()
def check(model, tok, valid):
    hit = total = 0
    lp_diff = 0.0
    for r in valid:
        prompt = tok.encode(r["template"], add_special_tokens=False)
        ids = torch.tensor([prompt + r["ids"]], device=DEVICE)
        with torch.autocast(DEVICE, dtype=torch.bfloat16):
            logits = model(input_ids=ids).logits[0, len(prompt) - 1:-1].float()
        lp = torch.log_softmax(logits, -1)
        got = torch.tensor(r["ids"], device=DEVICE)
        hit += (lp.argmax(-1) == got).sum().item()
        total += len(r["ids"])
        mine = lp.gather(-1, got[:, None])[:, 0]
        theirs = torch.tensor([r["top_lp"][j][r["top_ids"][j].index(t)] if t in r["top_ids"][j] else float("nan")
                               for j, t in enumerate(r["ids"])], device=DEVICE)
        ok = ~torch.isnan(theirs)
        lp_diff += (mine[ok] - theirs[ok]).abs().sum().item()
    return {"top1_agreement_with_q4_0_tokens": hit / total, "positions": total, "mean_abs_logprob_diff": lp_diff / total}


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    tok = AutoTokenizer.from_pretrained(BASE)
    held = {json.loads(l)["messages"][0]["content"] for l in VALID.read_text().splitlines()}
    _, valid = index(src, held)
    res = {"device": DEVICE, "held_out_records": len(valid)}
    for name, spec in TEACHERS.items():
        t0 = time.monotonic()
        model = load(spec).to(DEVICE).eval()
        res[name] = check(model, tok, valid)
        res[name]["seconds"] = round(time.monotonic() - t0, 1)
        print(name, json.dumps(res[name]), flush=True)
        del model
        torch.cuda.empty_cache() if DEVICE == "cuda" else None
    out.write_text(json.dumps(res, indent=2) + "\n")


if __name__ == "__main__":
    main()
