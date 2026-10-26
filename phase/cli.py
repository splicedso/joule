import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

from .measure import measure
from .power import Sampler, idle_baseline


def machine() -> dict:
    if platform.system() == "Windows":
        return _machine_windows()
    if platform.system() == "Linux":
        return _machine_linux()
    def sysctl(key):
        return subprocess.run(["sysctl", "-n", key], capture_output=True, text=True).stdout.strip()
    on_ac = "AC Power" in subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True).stdout
    return {"chip": sysctl("machdep.cpu.brand_string"), "ram_bytes": int(sysctl("hw.memsize")),
            "macos": platform.mac_ver()[0], "on_ac": on_ac}


def _machine_windows() -> dict:
    import ctypes
    import winreg

    def cpu_name():
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
            return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()

    class _MEM(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    mem = _MEM()
    mem.dwLength = ctypes.sizeof(_MEM)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))

    class _PWR(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                    ("BatteryLifePercent", ctypes.c_byte), ("SystemStatusFlag", ctypes.c_byte),
                    ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
    pwr = _PWR()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(pwr))

    try:
        gpus = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                              capture_output=True, text=True).stdout.strip().splitlines()
    except FileNotFoundError:
        gpus = []
    return {"chip": cpu_name(), "ram_bytes": int(mem.ullTotalPhys),
            "windows": platform.version(), "gpus": [g.strip() for g in gpus],
            "on_ac": pwr.ACLineStatus == 1}


def _machine_linux() -> dict:
    def cpu_name():
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
        return platform.processor()

    def ram_bytes():
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) * 1024  # kB -> bytes
        except (OSError, ValueError, IndexError):
            pass
        return 0

    def gpus():
        try:
            out = subprocess.run(["lspci"], capture_output=True, text=True).stdout
        except FileNotFoundError:
            return []
        return [ln.split(":", 2)[-1].strip() for ln in out.splitlines()
                if any(k in ln for k in ("VGA", "Display", "3D"))]

    def on_ac():
        # A desktop or a plugged-in laptop: any Mains supply reporting online=1.
        for online in subprocess.run(
                ["sh", "-c", "cat /sys/class/power_supply/*/online 2>/dev/null"],
                capture_output=True, text=True).stdout.split():
            if online.strip() == "1":
                return True
        return False

    return {"chip": cpu_name(), "ram_bytes": ram_bytes(),
            "linux": platform.release(), "gpus": gpus(), "on_ac": on_ac()}


def table(results: list[dict]) -> str:
    lines = ["| model | phase | tok/s | SoC W | sys W | SoC mJ/tok | sys mJ/tok | SoC net mJ/tok | sys net mJ/tok |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        lines.append(
            f"| {r['model']} | {r['phase']} | {r['tokens_per_s']:.1f} | {r['soc_w']:.1f} | {r['sys_w']:.1f} | "
            f"{r['soc_j_per_tok'] * 1e3:.1f} | {r['sys_j_per_tok'] * 1e3:.1f} | "
            f"{r['soc_net_j_per_tok'] * 1e3:.1f} | {r['sys_net_j_per_tok'] * 1e3:.1f} |")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(prog="phase", description="Measure energy per token for llama.cpp models.")
    p.add_argument("models", nargs="+", help="GGUF files")
    p.add_argument("--prefill", type=int, default=512, help="prompt tokens per prefill repetition")
    p.add_argument("--decode", type=int, default=128, help="generated tokens per decode repetition")
    p.add_argument("--seconds", type=float, default=20.0, help="target timed seconds per phase")
    p.add_argument("--idle", type=float, default=10.0, help="seconds of idle baseline")
    p.add_argument("--cooldown", type=float, default=5.0, help="seconds between phases")
    p.add_argument("--out", type=Path, help="write JSON results here")
    p.add_argument("--max-idle-soc", type=float, default=3.0,
                   help="macOS: stop if idle chip power is above this many watts (a busy machine inflates every figure; "
                        "a quiet M5 Pro idles near 0.6 W)")
    p.add_argument("--allow-busy", action="store_true", help="measure even when idle chip power is above --max-idle-soc")
    p.epilog = "Arguments after -- are passed to llama-bench."
    argv = sys.argv[1:] if argv is None else argv
    split = argv.index("--") if "--" in argv else len(argv)
    a = p.parse_args(argv[:split])
    extra = argv[split + 1:]

    info = machine()
    if not info["on_ac"]:
        print("warning: on battery; sys power reads battery discharge, not adapter input", file=sys.stderr)
    results = []
    with Sampler() as s:
        idle = idle_baseline(s, a.idle)
        print(f"idle: SoC {idle[0]:.2f} W, sys {idle[1]:.2f} W", file=sys.stderr)
        if sys.platform == "darwin" and idle[0] > a.max_idle_soc and not a.allow_busy:
            print(f"error: the machine is not idle (SoC {idle[0]:.2f} W at rest, limit {a.max_idle_soc:.1f} W). "
                  "Something else is using the chip (check `ps -Ao pcpu,comm -r | head` and `docker stats --no-stream`); "
                  "every figure would carry it. Re-run when it is quiet, or pass --allow-busy.", file=sys.stderr)
            return 2
        for model in a.models:
            for phase, n in (("prefill", a.prefill), ("decode", a.decode)):
                time.sleep(a.cooldown)
                r = measure(s, idle, model, phase, n, a.seconds, extra)
                results.append(r.as_dict())
                print(f"{r.model} {phase}: {r.tokens_per_s:.1f} tok/s, "
                      f"{r.soc_j_per_tok * 1e3:.1f} mJ/tok SoC", file=sys.stderr)

    print(table(results))
    if a.out:
        a.out.write_text(json.dumps({"machine": info, "idle_w": {"soc": idle[0], "sys": idle[1]},
                                     "settings": {"prefill": a.prefill, "decode": a.decode,
                                                  "seconds": a.seconds, "bench_args": extra},
                                     "results": results}, indent=2) + "\n")
