"""Have the target model answer every training prompt: the data the drafter learns to imitate.

The drafter should predict what Qwen2.5 7B Q4_0 actually writes, not what a human wrote, so
the training text is the target's own greedy output (sequence-level distillation). The
target runs in llama-server with 8 parallel slots and 8 requests in flight, so decoding is
batched (note 1: batching cuts energy per token sharply). Answers are capped at 384 tokens.
The chat endpoint applies the model's own chat template.

    python experiments/drafter/generate.py results/drafter/train-prompts.jsonl results/drafter/train-answers.jsonl

Resumable: prompts already answered in the output file are skipped.
"""

import json
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

TARGET = "models/quant/7b-Q4_0.gguf"
PORT = 8790
SLOTS = 8
MAX_TOKENS = 384


def ask(prompt):
    body = json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": MAX_TOKENS,
                       "temperature": 0, "cache_prompt": False}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        out = json.load(r)
    return out["choices"][0]["message"]["content"], out["usage"]["completion_tokens"]


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    prompts = [json.loads(l) for l in src.read_text().splitlines()]
    done = {json.loads(l)["prompt"] for l in dst.read_text().splitlines()} if dst.exists() else set()
    todo = [p for p in prompts if p["prompt"] not in done]
    print(f"{len(done)} done, {len(todo)} to go", flush=True)
    server = subprocess.Popen(["llama-server", "-m", TARGET, "-c", str(SLOTS * 2048), "-np", str(SLOTS),
                               "-ngl", "99", "--port", str(PORT), "--no-webui"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(300):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                    if json.load(r).get("status") == "ok":
                        break
            except Exception:
                time.sleep(1)
        lock, n, tokens, t0 = Lock(), 0, 0, time.monotonic()

        def work(p):
            nonlocal n, tokens
            answer, k = ask(p["prompt"])
            with lock:
                with dst.open("a") as f:
                    f.write(json.dumps({**p, "answer": answer, "tokens": k}) + "\n")
                n += 1
                tokens += k
                if n % 50 == 0:
                    rate = tokens / (time.monotonic() - t0)
                    print(f"{n}/{len(todo)}  {rate:.0f} tok/s  eta {(len(todo) - n) * (tokens / n) / rate / 60:.0f} min", flush=True)

        with ThreadPoolExecutor(SLOTS) as ex:
            list(ex.map(work, todo))
    finally:
        server.terminate()
        server.wait(timeout=30)
    print("done", flush=True)


if __name__ == "__main__":
    main()
