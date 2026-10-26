"""Experiment: decode energy per token against batch size, one model, one machine, at the chip.

The first experiment the cluster reading note ranks (docs/clusters-reading.md, section 8): where does
joules per token stop falling as the batch grows? Runs llama-server with --parallel N for N in BATCHES,
sends N identical-length requests at once, reads llama-server's timings for tokens and seconds, and the
machine's power sampler for watts over the same window. Two passes, the second reversed. Writes one JSON.

    uv run python experiments/decode_batch_energy.py models/qwen2.5-7b-instruct-q4_0.gguf results/decode-batch-mac-7b.json

Mac: power from macmon (chip only). Linux: from the amdgpu hwmon (package). Wall power is not measured
here; the note says so. Never run with a browser or Blender open.
"""
import json, os, shutil, subprocess, sys, threading, time, urllib.request

MODEL, OUT = sys.argv[1], sys.argv[2]
BATCHES = [1, 2, 4, 8, 16, 32]
ANSWER = 128
PROMPT = "Write a plain paragraph about the weather in a city of your choice, about two hundred words long."
SERVER = shutil.which("llama-server") or "/opt/homebrew/bin/llama-server"
PORT = 18555


def power_samples(stop, out):
    """Sample chip power at 5 Hz into out (watts)."""
    if sys.platform == "darwin":
        p = subprocess.Popen(["macmon", "pipe", "-i", "200"], stdout=subprocess.PIPE, text=True)
        for line in p.stdout:
            if stop.is_set(): break
            try: out.append(json.loads(line)["all_power"])
            except Exception: pass
        p.terminate()
    else:
        d = [x for x in os.listdir("/sys/class/drm") if x.startswith("card")][0]
        hw = [h for h in os.listdir(f"/sys/class/drm/{d}/device/hwmon")][0]
        f = f"/sys/class/drm/{d}/device/hwmon/{hw}/power1_average"
        while not stop.is_set():
            out.append(int(open(f).read()) / 1e6); time.sleep(0.2)


def one(batch):
    srv = subprocess.Popen([SERVER, "-m", MODEL, "--port", str(PORT), "--parallel", str(batch), "-c", str(batch * 1024), "-ngl", "99", "--log-disable"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(120):
            try: urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1); break
            except Exception: time.sleep(1)
        # warm-up: one short batch
        send(batch, 16)
        stop = threading.Event(); w = []; t = threading.Thread(target=power_samples, args=(stop, w), daemon=True); t.start()
        t0 = time.time(); timings = send(batch, ANSWER); secs = time.time() - t0
        stop.set(); t.join(timeout=2)
        toks = sum(x["predicted_n"] for x in timings)
        watts = sum(w) / len(w) if w else float("nan")
        return {"batch": batch, "tokens": toks, "seconds": secs, "tok_s": toks / secs, "watts": watts, "mj_per_token": watts * secs / toks * 1000, "samples": len(w)}
    finally:
        srv.terminate(); srv.wait(timeout=10)


def send(batch, n):
    res = [None] * batch
    def go(i):
        body = json.dumps({"prompt": PROMPT, "n_predict": n, "temperature": 0, "cache_prompt": False}).encode()
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/completion", data=body, headers={"Content-Type": "application/json"})
        res[i] = json.loads(urllib.request.urlopen(req, timeout=600).read())["timings"]
    ts = [threading.Thread(target=go, args=(i,)) for i in range(batch)]
    for t in ts: t.start()
    for t in ts: t.join()
    return res


rows = []
for order, batches in ((1, BATCHES), (2, list(reversed(BATCHES)))):
    for b in batches:
        r = one(b); r["pass"] = order; rows.append(r); print(r)
json.dump({"model": os.path.basename(MODEL), "machine": sys.platform, "answer_tokens": ANSWER, "power": "chip (macmon) on darwin, package hwmon on linux; not wall", "rows": rows}, open(OUT, "w"), indent=1)
print("wrote", OUT)
