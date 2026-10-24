"""Power sampling on Windows, behind the same Sampler interface as power.py.

The Mac reads two points: the chip (soc) and the logic board's DC input (sys).
On a Windows laptop with a discrete NVIDIA GPU the honest equivalents are:

- soc  -> GPU power from `nvidia-smi --query-gpu=power.draw`, the nearest thing
          to the Mac's chip reading. It is the GPU package only, not a whole-SoC
          figure: there is no CPU+GPU+DRAM package counter to read here.
- sys  -> whole-system DC power as the battery reports it: `DischargeRate` from
          the WMI class `BatteryStatus` in `root/wmi`, in milliwatts, and only
          while the machine is unplugged. On AC the battery does not discharge
          and this reads 0, so sys is unusable on AC. It also updates slowly
          (seconds, measured per machine), so it is a mean over long windows only.
- cpu  -> 0.0. Intel RAPL / MSR package power needs a kernel driver, i.e. admin
          rights, so it is not read here. It is left at 0, not estimated.

gpu_w carries the same value as soc_w so experiments/batching.py, which reads the
gpu_w field directly, works unchanged. gpu_mhz is the GPU graphics clock.

Nothing here needs admin rights: nvidia-smi ships with the driver and the WMI
battery class is readable by a normal user.
"""

import shutil
import subprocess
import threading
import time
from statistics import median

from .power import Sample

# nvidia-smi with -lms intermittently reports a spurious power.draw (seen as a
# ~11000 W spike every third sample while the GPU sits at a low-power idle state,
# against a true draw of ~20 W). No laptop GPU draws anywhere near this, so a
# reading above this ceiling is a driver glitch and is dropped rather than
# averaged into a window. The ceiling is far above any real board power.
_MAX_GPU_W = 1000.0


# The battery poller asks the WMI BatteryStatus class for its discharge rate (mW)
# and whether the pack is discharging. One long-lived PowerShell process is cheaper
# than re-spawning CIM queries; it prints a line per reading that the reader thread
# forward-fills onto every GPU sample.
_BATTERY_PS = (
    "$ErrorActionPreference='SilentlyContinue';"
    "while($true){"
    "  $b=Get-CimInstance -Namespace root/wmi -ClassName BatteryStatus;"
    "  if($b){ \"{0} {1} {2}\" -f ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()),"
    "          [int]$b.DischargeRate,[int][bool]$b.Discharging }"
    "  else { 'none' }"
    "  Start-Sleep -Milliseconds 250"
    "}"
)


class Sampler:
    def __init__(self, interval_ms: int = 200):
        if shutil.which("nvidia-smi") is None:
            raise RuntimeError("nvidia-smi not found; it ships with the NVIDIA driver")
        self.interval_ms = interval_ms
        self.samples: list[Sample] = []
        self._gpu: subprocess.Popen | None = None
        self._batt: subprocess.Popen | None = None
        self._batt_w = 0.0            # latest whole-system discharge, watts (0 on AC)
        self._batt_seen = False       # have we ever read a non-AC discharge value
        self._batt_changes: list[float] = []  # monotonic times DischargeRate changed
        self._last_batt_raw = None

    def __enter__(self):
        self._batt = subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _BATTERY_PS],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        threading.Thread(target=self._read_battery, daemon=True).start()
        self._gpu = subprocess.Popen(
            ["nvidia-smi", "--query-gpu=power.draw,clocks.gr",
             "--format=csv,noheader,nounits", "-lms", str(self.interval_ms)],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        threading.Thread(target=self._read_gpu, daemon=True).start()
        return self

    def __exit__(self, *exc):
        for proc in (self._gpu, self._batt):
            if proc is not None:
                proc.kill()
                proc.wait()

    def _read_gpu(self):
        for line in self._gpu.stdout:
            parts = line.split(",")
            if len(parts) < 2:
                continue
            try:
                gpu_w = float(parts[0])
                mhz = float(parts[1])
            except ValueError:
                continue  # [N/A] / [Not Supported] rows
            if not 0.0 <= gpu_w <= _MAX_GPU_W:
                continue  # spurious nvidia-smi spike (see _MAX_GPU_W)
            self.samples.append(
                Sample(time.monotonic(), gpu_w, self._batt_w, gpu_w, mhz, 0.0))

    def _read_battery(self):
        for line in self._batt.stdout:
            line = line.strip()
            if not line or line == "none":
                continue
            fields = line.split()
            if len(fields) < 3:
                continue
            try:
                rate_mw = int(fields[1])
                discharging = fields[2] == "1"
            except ValueError:
                continue
            self._batt_w = rate_mw / 1000.0 if discharging else 0.0
            if discharging:
                self._batt_seen = True
            if rate_mw != self._last_batt_raw:
                self._batt_changes.append(time.monotonic())
                self._last_batt_raw = rate_mw

    def window(self, start: float, end: float) -> list[Sample]:
        return [s for s in self.samples if start <= s.t <= end]

    def battery_update_s(self) -> float | None:
        """Median seconds between distinct DischargeRate values: the real sys rate.

        None until at least two changes have been seen (e.g. while on AC)."""
        c = self._batt_changes
        if len(c) < 2:
            return None
        gaps = [b - a for a, b in zip(c, c[1:])]
        return median(gaps)
