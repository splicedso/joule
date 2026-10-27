"""General-purpose quality and energy: maths, knowledge and code, one model, one machine, in one run.

quality.py measures joules per correct answer on GSM8K alone. A general-purpose model has to be judged on more
than arithmetic, so this runs three task sets through llama-server's chat endpoint, with chip energy sampled
over each set (idle measured first, as in quality.py):

- gsm8k: the first N problems of GSM8K test (MIT), answer read as in quality.py.
- mmlu_pro: MMLU-Pro test (MIT), the first N_PER_SUBJECT questions of each of its 14 subjects in file order,
  ten options, answer read from the last "answer is (X)" or the last lone capital letter A to J.
- humaneval: the 164 HumanEval problems (MIT). The model completes the function; the completion is run against
  the task's tests in a separate Python process with a 10 s limit. This EXECUTES MODEL-WRITTEN CODE, so it only
  runs when EXEC_OK=1 is set. On Linux the process runs inside bubblewrap (no network, home and /run hidden, the
  filesystem read-only except its own temporary directory; see sandboxed()); on macOS inside sandbox-exec with the
  same boundaries. SANDBOX=0 drops either, only for a machine that holds nothing else.

    uv run --with pyarrow python experiments/general_eval.py MODEL.gguf results/general-X.json [TASKS] [SLOTS]

TASKS defaults to gsm8k,mmlu_pro (add humaneval with EXEC_OK=1). Environment: N_GSM8K (250), N_PER_SUBJECT (20),
MAX_TOKENS (1024), CTX_PER_SLOT (4096), THINK ("0" or "1": passed as chat_template_kwargs.enable_thinking for
models that reason before answering; unset leaves the model's default), SERVER_ARGS (extra llama-server flags).
Thinking tokens count as generated tokens: they are what the energy pays for.
THINK_BUDGET=N (with THINK unset): ask with thinking on and at most N tokens; a reply stopped by that limit is
discarded and the question asked again with thinking off and MAX_TOKENS. Both replies' tokens count, and the row
records "fallback".
"""
import json, os, re, subprocess, sys, tempfile, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parent))
from phase.power import Sampler, idle_baseline, mean_power  # noqa: E402
import quality  # noqa: E402  (GSM8K data and answer reading)

PORT = 8794
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1024"))
THINK = os.environ.get("THINK")
THINK_BUDGET = int(os.environ.get("THINK_BUDGET", "0"))
MMLU_URL = "https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/resolve/main/data/test-00000-of-00001.parquet"
HE_URL = "https://huggingface.co/datasets/openai/openai_humaneval/resolve/main/openai_humaneval/test-00000-of-00001.parquet"
LETTERS = "ABCDEFGHIJ"


def fetch(url, path):
    p = Path(path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, p)
    return p


def parquet(path):
    import pyarrow.parquet as pq
    return pq.read_table(path).to_pylist()


def task_gsm8k():
    qs = quality.questions(int(os.environ.get("N_GSM8K", "250")))
    return [{"prompt": f"{quality.INSTRUCTION}\n\n{q['q']}", "gold": q["gold"]} for q in qs], \
        lambda item, text: (lambda g: g is not None and abs(g - item["gold"]) < 1e-6)(quality.extract(text))


def task_mmlu_pro():
    rows = parquet(fetch(MMLU_URL, "data/mmlu-pro-test.parquet"))
    per, seen, items = int(os.environ.get("N_PER_SUBJECT", "20")), {}, []
    for r in rows:
        if seen.get(r["category"], 0) >= per:
            continue
        seen[r["category"]] = seen.get(r["category"], 0) + 1
        opts = "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(r["options"]))
        items.append({"prompt": f"Answer the multiple-choice question. Think briefly, then finish with a line of the form "
                                f"'The answer is (X).'\n\n{r['question']}\n\n{opts}", "gold": r["answer"], "subject": r["category"]})

    def score(item, text):
        m = re.findall(r"answer is \(?([A-J])\)?", text) or re.findall(r"\b([A-J])\b", text)
        return bool(m) and m[-1] == item["gold"]
    return items, score


def sandboxed(cmd, workdir):
    """Wrap model-written code in bubblewrap on Linux: no network, the home directory and /run hidden behind empty
    tmpfs mounts (credentials, keyrings, SSH keys, the repo), the rest of the filesystem read-only, a private /tmp,
    and only the task's own temporary directory writable. The code runs under the system Python (stdlib only, which
    is all HumanEval's tests use). SANDBOX=0 runs unwrapped, for a machine that holds nothing else; on macOS there is
    no bubblewrap and the code runs unwrapped as before."""
    import shutil
    if os.environ.get("SANDBOX", "1") == "0":
        return [sys.executable if cmd[0] == "/usr/bin/python3" else cmd[0], *cmd[1:]]
    if sys.platform == "darwin":
        # macOS has no bubblewrap; sandbox-exec with the same boundaries: no network, the home directory unreadable
        # and unwritable (credentials, SSH keys, the repo), writes only in the task's own temporary directory. The
        # code runs under the system Python, which lives outside the home directory.
        home = os.path.realpath(os.path.expanduser("~"))
        wd = os.path.realpath(workdir)
        profile = ("(version 1)(allow default)(deny network*)"
                   f'(deny file-read* (subpath "{home}"))(deny file-write*)'
                   f'(allow file-read* file-write* (subpath "{wd}"))(allow file-write* (literal "/dev/null"))')
        return ["/usr/bin/sandbox-exec", "-p", profile, *cmd]
    bwrap = shutil.which("bwrap")
    if not bwrap:
        sys.exit("humaneval: bubblewrap (bwrap) not found; install it, or set SANDBOX=0 on a machine that holds nothing else")
    home = os.path.expanduser("~")
    return [bwrap, "--unshare-all", "--die-with-parent", "--new-session", "--ro-bind", "/", "/", "--dev", "/dev",
            "--proc", "/proc", "--tmpfs", "/tmp", "--tmpfs", "/run", "--tmpfs", home, "--bind", workdir, workdir,
            "--chdir", workdir, "--setenv", "HOME", workdir, *cmd]


def task_humaneval():
    if os.environ.get("EXEC_OK") != "1":
        sys.exit("humaneval executes model-written code; set EXEC_OK=1 to run it, on a machine that holds nothing else")
    rows = parquet(fetch(HE_URL, "data/humaneval-test.parquet"))[:int(os.environ.get("N_HUMANEVAL", "164"))]
    items = [{"prompt": "Complete this Python function. Reply with the whole function in one ```python code block.\n\n"
                        f"```python\n{r['prompt']}```", "task": r} for r in rows]

    def score(item, text):
        blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.S)
        code = blocks[-1] if blocks else text
        r = item["task"]
        program = f"{r['prompt']}\n{code}\n\n{r['test']}\ncheck({r['entry_point']})\n" if f"def {r['entry_point']}" not in code \
            else f"{code}\n\n{r['test']}\ncheck({r['entry_point']})\n"
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "t.py"; f.write_text(program)
            try:
                return subprocess.run(sandboxed(["/usr/bin/python3", "-I", str(f)], d), cwd=d, capture_output=True, timeout=10).returncode == 0
            except subprocess.TimeoutExpired:
                return False
    return items, score


TASKS = {"gsm8k": task_gsm8k, "mmlu_pro": task_mmlu_pro, "humaneval": task_humaneval}


def complete(prompt, max_tokens, think):
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0, "cache_prompt": False}
    if think in ("0", "1"):
        body["chat_template_kwargs"] = {"enable_thinking": think == "1"}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        out = json.load(r)
    choice = out["choices"][0]
    return choice["message"].get("content") or "", out["usage"]["completion_tokens"], choice.get("finish_reason")


def ask(prompt):
    if not THINK_BUDGET:
        text, tokens, _ = complete(prompt, MAX_TOKENS, THINK)
        return text, tokens, False
    text, tokens, finish = complete(prompt, THINK_BUDGET, "1")
    if finish != "length":
        return text, tokens, False
    text, more, _ = complete(prompt, MAX_TOKENS, "0")
    return text, tokens + more, True


def main():
    model, out = sys.argv[1], Path(sys.argv[2])
    names = (sys.argv[3] if len(sys.argv) > 3 else "gsm8k,mmlu_pro").split(",")
    slots = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    tasks = {n: TASKS[n]() for n in names}
    ctx = slots * int(os.environ.get("CTX_PER_SLOT", "4096"))
    server = subprocess.Popen(["llama-server", "-m", model, "-c", str(ctx), "-np", str(slots), "-ngl", "99", "--port", str(PORT),
                               "--no-webui", "--jinja", *os.environ.get("SERVER_ARGS", "").split()],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    results = {}
    try:
        for _ in range(900):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                    if json.load(r).get("status") == "ok":
                        break
            except Exception:
                time.sleep(1)
        ask("What is 1 + 1?")
        with Sampler(100) as s:
            idle = idle_baseline(s, 8)
            for name, (items, score) in tasks.items():
                t0 = time.monotonic()
                with ThreadPoolExecutor(slots) as ex:
                    replies = list(ex.map(lambda it: ask(it["prompt"]), items))
                t1 = time.monotonic()
                soc_w, _ = mean_power(s.window(t0, t1))
                rows = [{"correct": bool(score(it, text)), "tokens": tok, "reply": text, **({"fallback": True} if fell else {}),
                         **({"subject": it["subject"]} if "subject" in it else {})} for it, (text, tok, fell) in zip(items, replies)]
                correct, tokens, secs = sum(r["correct"] for r in rows), sum(r["tokens"] for r in rows), t1 - t0
                results[name] = {"summary": {"n": len(rows), "correct": correct, "accuracy": correct / len(rows), "seconds": secs,
                                             "tokens": tokens, "tokens_per_answer": tokens / len(rows), "tok_s": tokens / secs,
                                             "soc_w": soc_w, "chip_j": soc_w * secs,
                                             "chip_j_per_correct": soc_w * secs / correct if correct else None}, "rows": rows}
                print(name, json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in results[name]["summary"].items()}), flush=True)
    finally:
        server.terminate(); server.wait(timeout=60)
    total_j = sum(r["summary"]["chip_j"] for r in results.values()); total_c = sum(r["summary"]["correct"] for r in results.values())
    overall = {"model": Path(model).name, "slots": slots, "think": THINK, "think_budget": THINK_BUDGET, "max_tokens": MAX_TOKENS, "server_args": os.environ.get("SERVER_ARGS", ""),
               "idle_soc_w": idle[0], "mean_accuracy": sum(r["summary"]["accuracy"] for r in results.values()) / len(results),
               "chip_j_per_correct_all": total_j / total_c if total_c else None}
    print("overall", json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in overall.items()}))
    out.write_text(json.dumps({"overall": overall, "tasks": {k: v for k, v in results.items()}}, indent=2) + "\n")


if __name__ == "__main__":
    main()
