"""Speculative decoding energy through llama-server, for machines without llama-speculative-simple.

The prebuilt Windows CUDA release of llama.cpp ships llama-server but not the speculative
example tool. llama-server supports the same speculative decoding (draft model, n-gram
drafting, the draft confidence threshold), so this runs the note 7 and note 9 experiment
through it. Every condition, plain decoding included, goes through the same server
program, one server process per condition, so the comparison is like for like.

Each request asks for exactly N tokens (ignore_eos), greedy. The server reports its own
decode time and, for speculative conditions, how many tokens were drafted and accepted.
The decode window is [end - decode_seconds, end] on the sampler's clock; the first fifth
is dropped for the power ramp, as in speculative.py. GPU/chip energy only.

    python experiments/speculative_server.py results/speculative-server.json [conditions]
"""

import json
import random
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from phase.power import Sampler, idle_baseline, mean_power

sys.path.insert(0, str(Path(__file__).parent))
from speculative import DRAFT, N, PROMPTS, TARGET  # noqa: E402


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def server_args(cond):
    args = ["-m", TARGET, "-c", "4096", "-ngl", "99", "--no-webui"]
    if cond == "plain":
        return args
    if cond == "ngram":
        return args + ["--spec-type", "ngram-simple"]
    parts = cond.split("-")
    args += ["--spec-type", "draft-simple", "-md", DRAFT, "-ngld", "99", "--spec-draft-n-max", parts[1]]
    if len(parts) > 2:
        args += ["--spec-draft-p-min", parts[2][1:]]
    return args


class Server:
    def __init__(self, cond):
        self.port = free_port()
        self.proc = subprocess.Popen(["llama-server", *server_args(cond), "--port", str(self.port)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=2) as r:
                    if json.load(r).get("status") == "ok":
                        return
            except Exception:
                pass
            if self.proc.poll() is not None:
                raise RuntimeError(f"llama-server exited for {cond}")
            time.sleep(1)
        raise RuntimeError(f"llama-server did not become ready for {cond}")

    def complete(self, prompt):
        body = json.dumps({"prompt": prompt, "n_predict": N, "ignore_eos": True, "temperature": 0,
                           "cache_prompt": False}).encode()
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/completion", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            out = json.load(r)
        return out["timings"], time.monotonic()

    def close(self):
        self.proc.terminate()
        self.proc.wait(timeout=30)


def run(sampler, server, prompt):
    t, end = server.complete(prompt)
    tokens, seconds = t["predicted_n"], t["predicted_ms"] / 1e3
    drafted, accepted = t.get("draft_n"), t.get("draft_n_accepted")
    window = sampler.window(end - seconds * 0.8, end - 0.1)
    soc_w, sys_w = mean_power(window)
    return {"tokens": tokens, "seconds": seconds, "tok_s": tokens / seconds,
            "accept": accepted / drafted if drafted else None, "drafted": drafted, "accepted": accepted,
            "soc_w": soc_w, "sys_w": sys_w, "soc_mj": soc_w * seconds / tokens * 1e3,
            "sys_mj": sys_w * seconds / tokens * 1e3, "samples": len(window)}


def main():
    out = Path(sys.argv[1])
    conds = sys.argv[2].split(",") if len(sys.argv) > 2 else ["plain", "draft-2", "draft-4", "draft-8", "draft-16", "ngram"]
    rows = []
    random.seed(7)
    with Sampler(100) as s:
        idle = idle_baseline(s, 8)
        for rep in range(3):
            order = conds[:]
            random.shuffle(order)
            for cond in order:
                server = Server(cond)
                try:
                    server.complete("Hello")  # warm up: load weights and compile kernels outside the window
                    prompts = list(PROMPTS)
                    random.shuffle(prompts)
                    for p in prompts:
                        time.sleep(2)
                        r = run(s, server, PROMPTS[p])
                        r.update(cond=cond, prompt=p, rep=rep)
                        rows.append(r)
                        acc = f"{r['accept']:.0%}" if r["accept"] is not None else "  -"
                        print(f"{rep} {cond:13} {p:5} {r['tok_s']:5.1f} tok/s accept {acc:>4}  chip {r['soc_mj']:6.1f} mJ  n={r['samples']}", flush=True)
                finally:
                    server.close()
    out.write_text(json.dumps({"idle_w": {"soc": idle[0], "sys": idle[1]}, "n": N, "tool": "llama-server",
                               "rows": rows}, indent=2) + "\n")


if __name__ == "__main__":
    main()
