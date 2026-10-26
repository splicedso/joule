"""Diagnostic: which setting removes speculative decoding's batch-1 speed-up.

One llama-server per (row, condition), one request at a time, three repetitions after a warm-up; speed is the
server's own predicted_per_second, so prompt processing and HTTP overhead are excluded. Rows start from
decode_batch_energy.py's settings and change one thing at a time toward speculative_server.py's (note 11).

    uv run python experiments/spec_diag.py results/spec-diag-mac.json
"""
import json, statistics, subprocess, sys, time, urllib.request

TARGET, DRAFT, PORT = "models/quant/7b-Q4_0.gguf", "models/quant/0.5b-Q4_0.gguf", 18557
WEATHER = "Write a plain paragraph about the weather in a city of your choice, about two hundred words long."
POWER = ("Explain to a new engineer how a power supply in a laptop turns mains electricity into the "
         "voltages the processor needs, step by step.\n\n")
BASE = {"slots": ["--parallel", "1", "-c", "1024"], "prompt": WEATHER, "n": 128, "ignore_eos": False}
ROWS = {
    "batch script": {},
    "power-supply prompt": {"prompt": POWER},
    "384 forced tokens": {"n": 384, "ignore_eos": True},
    "default slots, 4096 context": {"slots": ["-c", "4096"]},
    "note 11 settings": {"slots": ["-c", "4096"], "prompt": POWER, "n": 384, "ignore_eos": True},
}
DRAFT_ARGS = ["-md", DRAFT, "--spec-type", "draft-simple", "--spec-draft-n-max", "4", "--spec-draft-p-min", "0.5", "-ngld", "99"]


def ask(cfg):
    body = json.dumps({"prompt": cfg["prompt"], "n_predict": cfg["n"], "ignore_eos": cfg["ignore_eos"],
                       "temperature": 0, "cache_prompt": False}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/completion", data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=600).read())["timings"]


def cell(cfg, draft):
    srv = subprocess.Popen(["llama-server", "-m", TARGET, "--port", str(PORT), "-ngl", "99", "--log-disable", *cfg["slots"],
                            *(DRAFT_ARGS if draft else [])], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(120):
            try: urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1); break
            except Exception: time.sleep(1)
        ask({**cfg, "n": 16})
        runs = [ask(cfg) for _ in range(3)]
    finally:
        srv.terminate(); srv.wait(timeout=10)
    return {"tok_s": statistics.mean(r["predicted_per_second"] for r in runs), "tokens": statistics.mean(r["predicted_n"] for r in runs),
            "drafted": sum(r.get("draft_n", 0) for r in runs), "accepted": sum(r.get("draft_n_accepted", 0) for r in runs)}


out = []
for name, change in ROWS.items():
    cfg = {**BASE, **change}
    plain, draft = cell(cfg, False), cell(cfg, True)
    row = {"row": name, "plain": plain, "draft": draft, "speedup": draft["tok_s"] / plain["tok_s"],
           "acceptance": draft["accepted"] / max(1, draft["drafted"])}
    out.append(row)
    print(f'{name:30s} plain {plain["tok_s"]:5.1f} tok/s  draft {draft["tok_s"]:5.1f}  speed-up {row["speedup"]:.2f}x  '
          f'accepted {100 * row["acceptance"]:.0f}%  tokens {plain["tokens"]:.0f}/{draft["tokens"]:.0f}', flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
