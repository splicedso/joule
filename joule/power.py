"""Power sampling on Apple Silicon through macmon, which needs no sudo.

soc is the chip (CPU + GPU + ANE + DRAM interface) at 200 ms resolution.
sys is the logic board's DC input as the SMC reports it: about 1 Hz and
smoothed, so it is only trusted as a mean over a long steady window.
"""

import json
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    t: float
    soc_w: float
    sys_w: float
    gpu_w: float = 0.0
    gpu_mhz: float = 0.0
    cpu_w: float = 0.0


class Sampler:
    def __init__(self, interval_ms: int = 200):
        if shutil.which("macmon") is None:
            raise RuntimeError("macmon not found; install it with: brew install macmon")
        self.interval_ms = interval_ms
        self.samples: list[Sample] = []
        self._proc: subprocess.Popen | None = None

    def __enter__(self):
        self._proc = subprocess.Popen(
            ["macmon", "pipe", "-i", str(self.interval_ms)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        threading.Thread(target=self._read, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self._proc.kill()
        self._proc.wait()

    def _read(self):
        for line in self._proc.stdout:
            row = json.loads(line)
            self.samples.append(Sample(time.monotonic(), row["all_power"], row["sys_power"],
                                       row["gpu_power"], row["gpu_freq_mhz"], row["cpu_power"]))

    def window(self, start: float, end: float) -> list[Sample]:
        return [s for s in self.samples if start <= s.t <= end]


def mean_power(samples: list[Sample]) -> tuple[float, float]:
    if not samples:
        raise ValueError("no power samples in window; the run was too short")
    n = len(samples)
    return sum(s.soc_w for s in samples) / n, sum(s.sys_w for s in samples) / n


def idle_baseline(sampler: Sampler, seconds: float) -> tuple[float, float]:
    start = time.monotonic()
    time.sleep(seconds)
    # The sys reading lags by about a second, so skip the first part.
    return mean_power(sampler.window(start + min(2.0, seconds / 2), time.monotonic()))


# Pick the backend for this machine. macmon on macOS, nvidia-smi + WMI battery on
# Windows (see power_windows.py). Sample, mean_power and idle_baseline are shared,
# so measure.py and experiments/batching.py import from here unchanged.
import platform as _platform  # noqa: E402

if _platform.system() == "Windows":
    from .power_windows import Sampler  # noqa: F811
