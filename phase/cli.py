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
