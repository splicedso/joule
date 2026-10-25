"""Record the target's full next-token distribution over its own answers: data for drafter v2.

Drafter v1 learned from the 7B's text alone. v2 learns from its probabilities: for every token
of every answer, the 7B Q4_0's top 20 candidates and their log-probabilities. The answers are
regenerated greedily through llama-server, so the token ids are exactly the target's own, in the
same vocabulary the 0.5B uses. 8 slots, 384 tokens, as generate.py.

    python experiments/drafter/teacher.py results/drafter/train-prompts.jsonl data/drafter/teacher.jsonl

Resumable: prompts already in the output file are skipped. The output is large (about 300 MB)
and lives in data/, which is not committed.
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
PORT = 8792
SLOTS = 8
MAX_TOKENS = 384
TOP_K = 20


def post(path, body):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)


def ask(prompt):
    text = post("/apply-template", {"messages": [{"role": "user", "content": prompt}]})["prompt"]
    out = post("/completion", {"prompt": text, "n_predict": MAX_TOKENS, "temperature": 0, "n_probs": TOP_K,
                               "cache_prompt": False})
    steps = out["completion_probabilities"]
    return {"template": text, "ids": [s["id"] for s in steps],
            "top_ids": [[t["id"] for t in s["top_logprobs"]] for s in steps],
            "top_lp": [[round(t["logprob"], 4) for t in s["top_logprobs"]] for s in steps]}


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.parent.mkdir(parents=True, exist_ok=True)
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
            rec = ask(p["prompt"])
            with lock:
                with dst.open("a") as f:
                    f.write(json.dumps({**p, **rec}) + "\n")
                n += 1
                tokens += len(rec["ids"])
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
