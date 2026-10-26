"""Score several drafts on one held-out set: top-1 agreement with the Q4_0 7B's own tokens.

The held-out set is the 180 validation prompts' answers as the Q4_0 7B wrote them through llama.cpp
(teacher.py, greedy, n_probs 20); each draft's guess at every answer position is compared with that
model's top-1, the same score train_trace.py uses during training. Every draft is scored by this one
script on the same records, so the numbers compare like for like.

    .venv-torch/bin/python experiments/drafter/score_drafts.py data/drafter/teacher.jsonl results/drafter/score-halo.json \\
        stock=models/hf-0.5b v1-9k=models/trace-0.5b-v1-lr3e6 ...
"""

import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).parent))
from train_trace import BASE, DEVICE, VALID, agreement, index  # noqa: E402


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    drafts = dict(a.split("=", 1) for a in sys.argv[3:])
    tok = AutoTokenizer.from_pretrained(BASE)
    held = {json.loads(l)["messages"][0]["content"] for l in VALID.read_text().splitlines()}
    _, valid = index(src, held)
    res = {"held_out_records": len(valid), "positions": sum(len(r["ids"]) for r in valid),
           "reference": "top-1 of the Q4_0 7B through llama.cpp (teacher.py)", "drafts": {}}
    for name, path in drafts.items():
        model = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16).to(DEVICE)
        res["drafts"][name] = {"path": path, "agreement": agreement(model, valid, tok)}
        print(name, path, f"{res['drafts'][name]['agreement']:.4f}", flush=True)
        del model
    out.write_text(json.dumps(res, indent=2) + "\n")


if __name__ == "__main__":
    main()
