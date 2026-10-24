"""Decode energy and perplexity for MLX formats, measured the same way as the llama.cpp sweep.

Energy: one continuous decode of about `seconds` worth of tokens after a short prompt, with
end-of-text ignored, so the window is decode only. Mean power over the window, first quarter
dropped, divided by decode tokens per second.

Perplexity: matches llama-perplexity. The WikiText-2 raw test text, the model's own
tokenizer, consecutive 512-token windows, negative log-likelihood over the second half of
each window only, first 60 windows.
"""

import json
import math
import sys
import time
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load
from mlx_lm.generate import generate_step

from joule.power import Sampler, idle_baseline, mean_power

PROMPT = "Write a short paragraph about how electricity reaches a house."
CTX, CHUNKS = 512, 60


def perplexity(model, tokenizer, text: str) -> tuple[float, float]:
    ids = tokenizer.encode(text)
    nll = []
    for c in range(CHUNKS):
        chunk = mx.array(ids[c * CTX:(c + 1) * CTX])[None]
        logits = model(chunk[:, :-1]).astype(mx.float32)
        losses = nn.losses.cross_entropy(logits, chunk[:, 1:], reduction="none")[0]
        nll.extend(losses[CTX // 2 - 1:].tolist())
    mean = sum(nll) / len(nll)
    sd = math.sqrt(sum((x - mean) ** 2 for x in nll) / (len(nll) - 1))
    return math.exp(mean), math.exp(mean) * sd / math.sqrt(len(nll))


def decode_tokens(model, prompt, n: int) -> tuple[int, float, float]:
    """Decode exactly n tokens in one stream. generate_step does not stop at end-of-text,
    so the GPU never idles between generations, as with llama-bench."""
    steps = generate_step(prompt, model, max_tokens=n)
    next(steps)
    start = time.monotonic()
    count = 1 + sum(1 for _ in steps)
    return count - 1, start, time.monotonic()


def decode_energy(sampler, model, tokenizer, seconds: float):
    prompt = mx.array(tokenizer.encode(PROMPT))
    _, a, b = decode_tokens(model, prompt, 64)
    n = max(256, int(seconds / ((b - a) / 63)))
    tokens, start, end = decode_tokens(model, prompt, n)
    tps = tokens / (end - start)
    soc_w, sys_w = mean_power(sampler.window(start + (end - start) / 4, end))
    return tps, soc_w, sys_w


def main():
    paths, out = sys.argv[1:-1], Path(sys.argv[-1])
    text = Path("data/wiki.test.raw").read_text()
    results = []
    with Sampler() as s:
        idle = idle_baseline(s, 8)
        for p in paths:
            model, tokenizer = load(p)
            time.sleep(4)
            tps, soc_w, sys_w = decode_energy(s, model, tokenizer, 15)
            ppl, err = perplexity(model, tokenizer, text)
            r = {"model": Path(p).name, "tokens_per_s": tps, "soc_w": soc_w, "sys_w": sys_w,
                 "soc_mj_per_tok": soc_w / tps * 1e3, "sys_mj_per_tok": sys_w / tps * 1e3,
                 "ppl": ppl, "ppl_err": err}
            results.append(r)
            print(f"{r['model']:24} {tps:6.1f} tok/s  chip {r['soc_mj_per_tok']:6.1f}  "
                  f"board {r['sys_mj_per_tok']:6.1f} mJ/tok  ppl {ppl:.2f} +/- {err:.2f}", flush=True)
            del model
            mx.clear_cache()
    out.write_text(json.dumps({"idle_w": {"soc": idle[0], "sys": idle[1]}, "results": results}, indent=2) + "\n")


if __name__ == "__main__":
    main()
