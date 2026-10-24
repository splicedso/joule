"""Does speculative decoding save energy, or only time?

A small draft model proposes k tokens; the large target model checks all k in one batched
forward pass and keeps the ones it agrees with. Decode is memory bound, so checking k tokens
costs about the same weight reads as generating one, and when drafts are accepted the target
reads its weights fewer times per token. But the draft model's work, and the target's work on
rejected drafts, both cost energy. Whether the net is a saving is a measurement, not a given.

Conditions, all with Qwen2.5 7B Q4_0 as the target, greedy, a fixed 384 generated tokens:
  plain        llama-completion, no speculation
  draft-k      llama-speculative-simple with Qwen2.5 0.5B Q4_0 drafting k = 2, 4, 8, 16 tokens
  ngram        llama-speculative-simple drafting by copying n-grams already in the context,
               no draft model at all

Prompts: write new code, write prose, and edit code given in the prompt (where most of the
output repeats the input, which n-gram drafting is built for).

Each tool prints how long its generation took, and generation is the last thing it does, so
the decode window is [end - seconds, end]; the first fifth is dropped for the power ramp.
Three repetitions per condition and prompt, in a shuffled order each time.
"""

import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

from joule.power import Sampler, idle_baseline, mean_power

TARGET = "models/quant/7b-Q4_0.gguf"
DRAFT = "models/quant/0.5b-Q4_0.gguf"
N = 384
CODE = Path(__file__).with_name("speculative_edit_input.py").read_text()
PROMPTS = {
    "code": "Write a complete Python module that parses ISO 8601 date strings, including time zones "
            "and fractional seconds, with docstrings and unit tests.\n\n",
    "prose": "Explain to a new engineer how a power supply in a laptop turns mains electricity into the "
             "voltages the processor needs, step by step.\n\n",
    "edit": "Here is a Python file. Rewrite the whole file with type hints added to every function. "
            "Change nothing else.\n\n```python\n" + CODE + "```\n\nThe rewritten file:\n\n```python\n",
}
COMMON = ["-c", "4096", "-ngl", "99", "--temp", "0", "--ignore-eos", "-n", str(N)]
PLAIN_RE = re.compile(r"eval time =\s+([\d.]+) ms /\s+(\d+) runs")
SPEC_RE = re.compile(r"decoded\s+(\d+) tokens in\s+([\d.]+) seconds")
ACC_RE = re.compile(r"accept\s+=\s+([\d.]+)%")


def command(cond, prompt):
    if cond == "plain":
        return ["llama-completion", "-m", TARGET, "-p", prompt, "-no-cnv", *COMMON]
    spec = ["llama-speculative-simple", "-m", TARGET, "-p", prompt, *COMMON]
    if cond == "ngram":
        return spec + ["--spec-type", "ngram-simple"]
    k = cond.split("-")[1]
    return spec + ["--spec-type", "draft-simple", "-md", DRAFT, "-ngld", "99", "--spec-draft-n-max", k]


def run(sampler, cond, prompt):
    out = subprocess.run(command(cond, prompt), capture_output=True, text=True)
    end = time.monotonic()
    log = out.stdout + out.stderr
    if cond == "plain":
        m = PLAIN_RE.search(log)
        seconds, tokens, accept = float(m.group(1)) / 1e3, int(m.group(2)), None
    else:
        m = SPEC_RE.search(log)
        tokens, seconds = int(m.group(1)), float(m.group(2))
        a = ACC_RE.search(log)
        accept = float(a.group(1)) / 100 if a else None
    window = sampler.window(end - seconds * 0.8, end - 0.1)
    soc_w, sys_w = mean_power(window)
    return {"tokens": tokens, "seconds": seconds, "tok_s": tokens / seconds, "accept": accept,
            "soc_w": soc_w, "sys_w": sys_w, "soc_mj": soc_w * seconds / tokens * 1e3,
            "sys_mj": sys_w * seconds / tokens * 1e3, "samples": len(window)}


def main():
    out = Path(sys.argv[1])
    conds = ["plain", "draft-2", "draft-4", "draft-8", "draft-16", "ngram"]
    jobs = [(c, p) for c in conds for p in PROMPTS]
    rows = []
    random.seed(7)
    with Sampler(100) as s:
        idle = idle_baseline(s, 8)
        for rep in range(3):
            random.shuffle(jobs)
            for cond, p in jobs:
                time.sleep(2)
                r = run(s, cond, PROMPTS[p])
                r.update(cond=cond, prompt=p, rep=rep)
                rows.append(r)
                acc = f"{r['accept']:.0%}" if r["accept"] is not None else "  -"
                print(f"{rep} {cond:8} {p:5} {r['tok_s']:5.1f} tok/s accept {acc:>4}  chip {r['soc_mj']:6.1f} mJ  "
                      f"board {r['sys_mj']:6.1f} mJ  n={r['samples']}", flush=True)
    out.write_text(json.dumps({"idle_w": {"soc": idle[0], "sys": idle[1]}, "n": N, "rows": rows}, indent=2) + "\n")


if __name__ == "__main__":
    main()
