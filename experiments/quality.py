"""Joules per correct answer: energy and accuracy measured in the same run.

Energy per token rewards a model that answers quickly and wrongly. This measures what a
user pays for: the energy of a whole evaluation divided by the number of questions answered
correctly. The evaluation is GSM8K (grade-school maths word problems, MIT licence): the first
N questions of the test set, greedy, through llama-server's chat endpoint, with the answer
read from \\boxed{}, else the last "The answer is", else the last number in the reply.

Chip energy is sampled over the whole run; idle power, measured first, gives a net figure too.
SLOTS requests run in parallel, so the same harness measures batch 1 and batched serving.

    python experiments/quality.py models/quant/1.5b-Q4_0.gguf results/quality-mac-1.5b.json [N] [SLOTS]
"""

import json
import re
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from phase.power import Sampler, idle_baseline, mean_power  # noqa: E402

DATA_URL = "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl"
CACHE = Path("data/gsm8k-test.jsonl")
PORT = 8793
MAX_TOKENS = 384
INSTRUCTION = "Solve the problem. Think step by step, then finish with a line of the form 'The answer is N.'"


def questions(n):
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(DATA_URL, CACHE)
    rows = [json.loads(l) for l in CACHE.read_text().splitlines()[:n]]
    return [{"q": r["question"], "gold": float(r["answer"].split("####")[-1].strip().replace(",", ""))} for r in rows]


def extract(text):
    nums = (re.findall(r"\\boxed\{\$?(-?[\d,]*\.?\d+)", text)
            or re.findall(r"answer is[^0-9-]*?(-?[\d,]*\.?\d+)", text, re.I)
            or re.findall(r"-?[\d,]*\.?\d+", text))
    try:
        return float(nums[-1].replace(",", "")) if nums else None
    except ValueError:
        return None


def ask(question):
    body = json.dumps({"messages": [{"role": "user", "content": f"{INSTRUCTION}\n\n{question}"}],
                       "max_tokens": MAX_TOKENS, "temperature": 0, "cache_prompt": False}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        out = json.load(r)
    return out["choices"][0]["message"]["content"], out["usage"]["completion_tokens"]


def main():
    model, out = sys.argv[1], Path(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 250
    slots = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    qs = questions(n)
    server = subprocess.Popen(["llama-server", "-m", model, "-c", str(slots * 2048), "-np", str(slots), "-ngl", "99",
                               "--port", str(PORT), "--no-webui"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(300):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                    if json.load(r).get("status") == "ok":
                        break
            except Exception:
                time.sleep(1)
        ask("What is 1 + 1?")  # warm the server so loading is not in the window
        with Sampler(100) as s:
            idle = idle_baseline(s, 8)
            t0 = time.monotonic()
            with ThreadPoolExecutor(slots) as ex:
                replies = list(ex.map(lambda q: ask(q["q"]), qs))
            t1 = time.monotonic()
            soc_w, sys_w = mean_power(s.window(t0, t1))
    finally:
        server.terminate()
        server.wait(timeout=30)

    rows = []
    for q, (text, tokens) in zip(qs, replies):
        got = extract(text)
        rows.append({"gold": q["gold"], "got": got, "correct": got is not None and abs(got - q["gold"]) < 1e-6,
                     "tokens": tokens, "reply": text})
    correct = sum(r["correct"] for r in rows)
    seconds, tokens = t1 - t0, sum(r["tokens"] for r in rows)
    chip_j, net_j = soc_w * seconds, (soc_w - idle[0]) * seconds
    summary = {"model": Path(model).name, "n": n, "slots": slots, "correct": correct, "accuracy": correct / n,
               "seconds": seconds, "tokens": tokens, "tok_s": tokens / seconds, "soc_w": soc_w, "idle_soc_w": idle[0],
               "chip_j": chip_j, "chip_j_per_correct": chip_j / correct if correct else None,
               "net_j_per_correct": net_j / correct if correct else None, "chip_mj_per_token": chip_j / tokens * 1000}
    print(json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in summary.items()}), flush=True)
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n")


if __name__ == "__main__":
    main()
