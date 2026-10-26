"""Rejection-sampling fine-tuning, step 1: the model answers its own training problems; the correct answers are kept.

GSM8K train (MIT; the last 200 problems left out, as qat.py holds them out) in quality.py's exact prompt, graded by
quality.py's answer reader; MBPP train (CC-BY-4.0, 374 problems) in general_eval.py's code-prompt style, graded by running
its asserts inside the same bubblewrap sandbox as HumanEval (general_eval.sandboxed). SAMPLES answers per problem at
TEMPERATURE through llama-server, SLOTS at once, a distinct seed per answer. Resumable: answers already in OUT are kept.

Budget: after CALIBRATE requests it projects the total time; if that is over MAX_HOURS with SAMPLES=4, it drops to 2
samples per problem for every problem and records the decision in the summary.

    uv run --with pyarrow python experiments/rft/sample.py models/quant/1.5b-Q4_0.gguf data/rft/samples-1.5b.jsonl
"""
import json, os, re, subprocess, sys, time, urllib.request, zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

sys.path.insert(0, str(Path(__file__).parents[1]))
import quality  # noqa: E402
import general_eval as ge  # noqa: E402

SAMPLES = int(os.environ.get("SAMPLES", "4"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.8"))
SLOTS = int(os.environ.get("SLOTS", "32"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "768"))
MAX_HOURS = float(os.environ.get("MAX_HOURS", "6"))
CALIBRATE = int(os.environ.get("CALIBRATE", "512"))
LIMIT = int(os.environ.get("LIMIT", "0"))          # smoke tests: only the first LIMIT problems of each set
PORT = 8795
MBPP_URL = "https://huggingface.co/datasets/google-research-datasets/mbpp/resolve/main/full/train-00000-of-00001.parquet"
CODE_PROMPT = "Write a Python function for this task. Reply with the whole function in one ```python code block.\n\n{text}\n\nYour code should pass these tests:\n{tests}"


def problems():
    rows = [json.loads(l) for l in Path("data/gsm8k-train.jsonl").read_text().splitlines()][:-200]
    gsm = [{"source": "gsm8k", "id": i, "prompt": f"{quality.INSTRUCTION}\n\n{r['question']}",
            "gold": float(r["answer"].split("####")[-1].strip().replace(",", ""))} for i, r in enumerate(rows)]
    mb = [{"source": "mbpp", "id": r["task_id"], "prompt": CODE_PROMPT.format(text=r["text"], tests="\n".join(r["test_list"])),
           "tests": r["test_list"], "setup": r.get("test_setup_code") or ""} for r in ge.parquet(ge.fetch(MBPP_URL, "data/mbpp-train.parquet"))]
    return (gsm[:LIMIT] + mb[:LIMIT]) if LIMIT else gsm + mb


def correct(p, text):
    if p["source"] == "gsm8k":
        g = quality.extract(text)
        return g is not None and abs(g - p["gold"]) < 1e-6
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.S)
    program = f"{blocks[-1] if blocks else text}\n\n{p['setup']}\n" + "\n".join(p["tests"]) + "\n"
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "t.py"; f.write_text(program)
        try:
            return subprocess.run(ge.sandboxed(["/usr/bin/python3", "-I", str(f)], d), cwd=d, capture_output=True, timeout=10).returncode == 0
        except subprocess.TimeoutExpired:
            return False


def ask(prompt, seed):
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE,
            "seed": seed, "cache_prompt": False}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        out = json.load(r)
    c = out["choices"][0]
    return c["message"].get("content") or "", out["usage"]["completion_tokens"], c.get("finish_reason")


def main():
    model, out = sys.argv[1], Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    probs = problems()
    done = set()
    if out.exists():
        for l in out.read_text().splitlines():
            r = json.loads(l); done.add((r["source"], r["id"], r["sample"]))
    jobs = [(p, k) for k in range(SAMPLES) for p in probs if (p["source"], p["id"], k) not in done]   # sample 0 of every problem first
    print(f"{len(probs)} problems, {SAMPLES} samples each, {len(done)} done, {len(jobs)} to go", flush=True)
    server = subprocess.Popen(["llama-server", "-m", model, "-c", str(SLOTS * (MAX_TOKENS + 1024)), "-np", str(SLOTS), "-ngl", "99",
                               "--port", str(PORT), "--no-webui", "--jinja"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lock, n, toks, t0, decided = Lock(), 0, 0, time.monotonic(), {"samples": SAMPLES, "cut": False}
    try:
        for _ in range(600):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                    if json.load(r).get("status") == "ok":
                        break
            except Exception:
                time.sleep(1)

        def work(job):
            nonlocal n, toks
            p, k = job
            if k >= decided["samples"]:
                return
            seed = zlib.crc32(f"{p['source']}:{p['id']}:{k}".encode()) & 0x7FFFFFFF   # reproducible across runs, unlike hash()
            text, ntok, finish = ask(p["prompt"], seed)
            row = {"source": p["source"], "id": p["id"], "sample": k, "seed": seed, "prompt": p["prompt"], "response": text,
                   "tokens": ntok, "finish": finish, "correct": bool(correct(p, text))}
            with lock:
                with out.open("a") as f:
                    f.write(json.dumps(row) + "\n")
                n += 1; toks += ntok
                if n == CALIBRATE and decided["samples"] == 4:
                    per = (time.monotonic() - t0) / n
                    projected = per * len(jobs)
                    print(f"calibration: {per:.3f} s per answer, projected {projected / 3600:.1f} h for {len(jobs)} answers", flush=True)
                    if projected > MAX_HOURS * 3600:
                        decided.update(samples=2, cut=True, projected_h_at_4=projected / 3600)
                        print("over budget: cutting to 2 samples per problem", flush=True)
                if n % 500 == 0:
                    el = time.monotonic() - t0
                    print(f"{n} answers, {toks / el:.0f} tok/s, {el / 60:.0f} min", flush=True)

        with ThreadPoolExecutor(SLOTS) as ex:
            list(ex.map(work, jobs))
    finally:
        server.terminate(); server.wait(timeout=60)
    rows = [json.loads(l) for l in out.read_text().splitlines()]
    summ = {"model": Path(model).name, "temperature": TEMPERATURE, "samples_per_problem": decided["samples"], "cut_to_2": decided["cut"],
            "projected_h_at_4": decided.get("projected_h_at_4"), "seconds_this_run": time.monotonic() - t0, "answers": len(rows)}
    for src in ("gsm8k", "mbpp"):
        rs = [r for r in rows if r["source"] == src]
        ids = {r["id"] for r in rs}
        summ[src] = {"problems": len(ids), "answers": len(rs), "correct_rate": sum(r["correct"] for r in rs) / max(1, len(rs)),
                     "problems_with_a_correct_answer": len({r["id"] for r in rs if r["correct"]}) / max(1, len(ids)),
                     "tokens_per_answer": sum(r["tokens"] for r in rs) / max(1, len(rs)),
                     "hit_max_tokens": sum(r["finish"] == "length" for r in rs)}
    print(json.dumps(summ, indent=1))
    out.with_suffix(".summary.json").write_text(json.dumps(summ, indent=2) + "\n")


if __name__ == "__main__":
    main()
