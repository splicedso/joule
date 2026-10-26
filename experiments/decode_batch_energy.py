"""Experiment: decode energy per token against batch size, one model, one machine, at the chip.

The first experiment the cluster reading note ranks (docs/clusters-reading.md, section 8): where does
joules per token stop falling as the batch grows? Runs llama-server with --parallel N for N in BATCHES,
sends N identical-length requests at once, reads llama-server's timings for tokens and seconds, and the
machine's power sampler for watts over the same window. Two passes, the second reversed. Writes one JSON.

    uv run python experiments/decode_batch_energy.py models/qwen2.5-7b-instruct-q4_0.gguf results/decode-batch-mac-7b.json

Mac: power from macmon (chip only). Linux: from the amdgpu hwmon (package). Wall power is not measured
here; the note says so. Never run with a browser or Blender open. ANSWER=512 in the environment lengthens
every window four times (keep 128 for a row meant to compare with note 24). BATCHES=1,2,4 picks batches;
SERVER_ARGS adds llama-server flags (a draft model, which needs --spec-type: "-md draft.gguf --spec-type draft-simple --spec-draft-n-max 4 --spec-draft-p-min 0.5 -ngld 99").
"""
import json, os, shutil, subprocess, sys, threading, time, urllib.request

MODEL, OUT = sys.argv[1], sys.argv[2]
BATCHES = [int(b) for b in os.environ.get("BATCHES", "1,2,4,8,16,32").split(",")]
SERVER_ARGS = os.environ.get("SERVER_ARGS", "").split()  # extra llama-server flags, e.g. a draft model
ANSWER = int(os.environ.get("ANSWER", 128))  # tokens per answer; note 24 used 128. A 1.5B at batch 1 gives a 0.7 s window at 128: raise it for small models
PROMPT = "Write a plain paragraph about the weather in a city of your choice, about two hundred words long."
PROMPTS = {"weather": PROMPT, "power": "Explain to a new engineer how a power supply in a laptop turns mains electricity into the voltages the processor needs, step by step.\n\n"}
PROMPT = PROMPTS[os.environ.get("PROMPT", "weather")]  # "power": note 11's prose prompt, where a 0.5B draft is accepted far more often
SERVER = shutil.which("llama-server") or "/opt/homebrew/bin/llama-server"
PORT = 18555


def linux_power_file():
    """The GPU's package power sensor. /sys/class/drm also lists connectors (card0-HDMI-A-1, card0-DP-1, ...),
    in no fixed order, and they have no hwmon; picking the first card* entry sampled nothing on the Strix Halo
    (2026-10-26). Find the device whose hwmon has power1_average instead, and fail loudly if there is none."""
    import glob
    found = sorted(glob.glob("/sys/class/drm/card*/device/hwmon/hwmon*/power1_average"))
    if not found:
        raise RuntimeError("no amdgpu power1_average under /sys/class/drm/card*/device/hwmon: cannot measure power")
    return found[0]


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
        f = linux_power_file()
        while not stop.is_set():
            out.append(int(open(f).read()) / 1e6); time.sleep(0.2)


def one(batch):
    srv = subprocess.Popen([SERVER, "-m", MODEL, "--port", str(PORT), "--parallel", str(batch), "-c", str(batch * 1024), "-ngl", "99", "--log-disable"] + SERVER_ARGS,
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
        if not w:  # the sampler thread died or never ran: a row without power is void, not NaN
            raise RuntimeError(f"batch {batch}: no power samples in a {secs:.1f} s window; result would be void")
        toks = sum(x["predicted_n"] for x in timings)
        drafted = sum(x.get("draft_n", 0) for x in timings); accepted = sum(x.get("draft_n_accepted", 0) for x in timings)
        watts = sum(w) / len(w) if w else float("nan")
        return {"batch": batch, "tokens": toks, "seconds": secs, "tok_s": toks / secs, "watts": watts, "mj_per_token": watts * secs / toks * 1000, "samples": len(w),
                "draft_n": drafted, "draft_accepted": accepted}
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


def require_quiet(seconds=5, limit=float(os.environ.get("MAX_IDLE_W", "3"))):
    """macOS: stop before measuring if the chip is busy at rest (another job inflates every row). Linux's
    package sensor idles far higher, so the check is macOS only."""
    if sys.platform != "darwin":
        return
    stop = threading.Event(); w = []; t = threading.Thread(target=power_samples, args=(stop, w), daemon=True); t.start()
    time.sleep(seconds); stop.set(); t.join(timeout=2)
    idle = sum(w) / len(w) if w else float("nan")
    print(f"idle chip power {idle:.2f} W over {seconds} s")
    if not idle <= limit:
        sys.exit(f"the machine is not idle ({idle:.2f} W at rest, limit {limit} W): check `ps -Ao pcpu,comm -r | head` and "
                 "`docker stats --no-stream`; set MAX_IDLE_W to override")


require_quiet()
rows = []
for order, batches in ((1, BATCHES), (2, list(reversed(BATCHES)))):
    for b in batches:
        r = one(b); r["pass"] = order; rows.append(r); print(r)
json.dump({"model": os.path.basename(MODEL), "machine": sys.platform, "answer_tokens": ANSWER, "power": "chip (macmon) on darwin, package hwmon on linux; not wall", "server_args": " ".join(SERVER_ARGS), "prompt": os.environ.get("PROMPT", "weather"), "rows": rows}, open(OUT, "w"), indent=1)
print("wrote", OUT)
