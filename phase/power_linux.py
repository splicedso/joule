"""Power sampling on Linux, behind the same Sampler interface as power.py.

Written for the AMD Ryzen AI MAX+ 395 (Strix Halo), an APU where the CPU, the
Radeon GPU and the memory controller share one package and one unified memory.
The Mac reads two points, the chip (soc) and the board's DC input (sys). On this
machine the honest equivalents a normal user can read, with no sudo, are:

- soc  -> the amdgpu hwmon `power1_average`, in microwatts. On this APU that
          sensor reports the whole package (CPU + GPU + memory interface), not
          the GPU alone: it tracks `amd-smi`'s APU socket power (about 24 W idle)
          while the GPU-only graphics figure is far lower. So it is the nearest
          thing here to the Mac's chip reading, and it is a whole-SoC figure.
          It is a rolling average: measured against a 7B Q4_0 decode load it
          rises from about 13.5 W idle to a steady 105 W and reaches 90% of that
          step in about 3 s, so short windows undercount. Use runs of 15 s or
          more (measure.py trims the first quarter of the window). power1_input
          on this driver reads the identical value, sample for sample, so there
          is no faster instantaneous sensor to prefer.
- sys  -> 0.0. There is no whole-system DC power a normal user can read on this
          board: it runs on mains only (the ACAD power supply exposes just
          `online`, no wattage) and the RAPL `energy_uj` counters are root-only.
          It is left at 0, not estimated. `amd-smi` does report a system figure,
          but reading it needs spawning a tool per sample, so it is not used.
- gpu  -> the same value as soc, because the sensor above is the package. The
          field is carried so experiments/batching.py, which reads gpu_w, works
          unchanged; it is not a GPU-only number on this APU.
- cpu  -> 0.0. A per-core sum exists only through `amd-smi`, not sysfs, so it is
          left at 0 rather than estimated.

gpu_mhz is the current GPU shader clock from `pp_dpm_sclk` (the line marked `*`).

Nothing here needs sudo: the hwmon and the clock files are world-readable.
"""

import glob
import os
import threading
import time

from .power import Sample

# The amdgpu hwmon index is not stable across boots, so the sampler finds the
# directory whose `name` is "amdgpu" and which exposes a package power reading.
_PACKAGE_POWER = "power1_average"  # microwatts, a rolling average (preferred over power1_input)


def _find_amdgpu_hwmon() -> str:
    """Return the amdgpu hwmon directory that exposes package power, or raise."""
    for hwmon in glob.glob("/sys/class/drm/card*/device/hwmon/hwmon*"):
        try:
            with open(os.path.join(hwmon, "name")) as f:
                if f.read().strip() != "amdgpu":
                    continue
        except OSError:
            continue
        if os.path.exists(os.path.join(hwmon, _PACKAGE_POWER)):
            return hwmon
    raise RuntimeError(
        "no readable amdgpu hwmon power1_average under /sys/class/drm/card*/device/hwmon; "
        "this backend expects an amdgpu GPU or APU")


def _read_int(path: str) -> int | None:
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _read_sclk_mhz(device_dir: str) -> float:
    """Current GPU shader clock in MHz from pp_dpm_sclk, or 0.0 if unreadable.

    pp_dpm_sclk lists the available states, one per line, the active one marked
    with a trailing `*`, e.g. "1: 1110Mhz *"."""
    try:
        with open(os.path.join(device_dir, "pp_dpm_sclk")) as f:
            for line in f:
                if line.rstrip().endswith("*"):
                    mhz = line.split(":", 1)[1].strip().split("Mhz")[0]
                    return float(mhz)
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


class Sampler:
    def __init__(self, interval_ms: int = 200):
        self.interval_ms = interval_ms
        self.samples: list[Sample] = []
        hwmon = _find_amdgpu_hwmon()
        self._power_path = os.path.join(hwmon, _PACKAGE_POWER)
        # The device directory (two levels up from the hwmon) holds pp_dpm_sclk.
        self._device_dir = os.path.dirname(os.path.dirname(hwmon))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self):
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval_ms / 1000 + 1.0)

    def _read(self):
        period = self.interval_ms / 1000.0
        while not self._stop.is_set():
            uw = _read_int(self._power_path)
            if uw is not None:
                soc_w = uw / 1e6
                mhz = _read_sclk_mhz(self._device_dir)
                # soc is the package; sys and cpu are unreadable here (see module
                # docstring) and left at 0. gpu carries soc for batching.py.
                self.samples.append(
                    Sample(time.monotonic(), soc_w, 0.0, soc_w, mhz, 0.0))
            self._stop.wait(period)

    def window(self, start: float, end: float) -> list[Sample]:
        return [s for s in self.samples if start <= s.t <= end]
