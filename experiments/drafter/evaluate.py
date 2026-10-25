"""Does the Spliced drafter beat the stock draft model? Acceptance, speed and energy, held out.

Target Qwen2.5 7B Q4_0. Two draft models, both converted and quantized through the same
pipeline so only their training differs: the stock Qwen2.5 0.5B Instruct, and the Spliced
drafter (the same model fine-tuned on the 7B's own answers). Each drafts up to 4 or 8
tokens with a 0.5 confidence threshold (note 9). Plain decoding is the reference.

Prompts are the first 20 chat and 20 code prompts of the held-out set, which no training
example contains, in the chat format the models were trained on. 256 generated tokens,
greedy, chip energy, through llama-server as in speculative_server.py. Two passes, the
second in reverse order.

    python experiments/drafter/evaluate.py results/drafter/eval-mac.json
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import speculative_server as ss  # noqa: E402
from phase.power import Sampler, idle_baseline  # noqa: E402

DRAFTS = {"stock": "models/quant/drafter-stock-Q4_0.gguf", "spliced": "models/quant/drafter-spliced-Q4_0.gguf",
          "v2": "models/quant/drafter-v2-Q4_0.gguf", "v1": "models/quant/drafter-v1-Q4_0.gguf"}
N = 256
CONDS = ["plain", "stock-4", "spliced-4", "stock-8", "spliced-8"]


def server_args(cond):
    """plain, or NAME-K[-pP]: draft model NAME drafting up to K tokens, threshold P (default 0.5)."""
    args = ["-m", ss.TARGET, "-c", "4096", "-ngl", "99", "--no-webui"]
    if cond == "plain":
        return args
    parts = cond.split("-")
    p = parts[2][1:] if len(parts) > 2 else "0.5"
    return args + ["--spec-type", "draft-simple", "-md", DRAFTS[parts[0]], "-ngld", "99",
                   "--spec-draft-n-max", parts[1], "--spec-draft-p-min", p]


def chat(prompt):
    return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"


def main():
    out = Path(sys.argv[1])
    conds = sys.argv[2].split(",") if len(sys.argv) > 2 else CONDS
    held = [json.loads(l) for l in open("results/drafter/eval-prompts.jsonl")]
    prompts = [h for h in held if h["kind"] == "chat"][:20] + [h for h in held if h["kind"] == "code"][:20]
    ss.N = N
    ss.server_args = server_args
    rows = []
    with Sampler(100) as s:
        idle = idle_baseline(s, 8)
        for rep, order in enumerate((conds, conds[::-1])):
            for cond in order:
                server = ss.Server(cond)
                try:
                    server.complete(chat("Hello"))
                    for i, p in enumerate(prompts):
                        time.sleep(1)
                        r = ss.run(s, server, chat(p["prompt"]))
                        r.update(cond=cond, kind=p["kind"], prompt_index=i, rep=rep)
                        rows.append(r)
                    got = [r for r in rows if r["cond"] == cond and r["rep"] == rep]
                    acc = [r["accept"] for r in got if r["accept"] is not None]
                    print(f"{rep} {cond:16} {sum(r['tok_s'] for r in got) / len(got):6.1f} tok/s  "
                          f"accept {sum(acc) / len(acc) if acc else 0:.0%}  chip {sum(r['soc_mj'] for r in got) / len(got):6.1f} mJ/tok", flush=True)
                finally:
                    server.close()
    out.write_text(json.dumps({"idle_w": {"soc": idle[0], "sys": idle[1]}, "n": N, "drafts": DRAFTS, "rows": rows}, indent=2) + "\n")


if __name__ == "__main__":
    main()
