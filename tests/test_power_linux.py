"""Linux amdgpu backend, tested against a fake sysfs tree so it needs no GPU."""

import sys
import time

import pytest

if sys.platform != "linux":
    pytest.skip("Linux power backend", allow_module_level=True)

from phase import power_linux
from phase.power import Sample


def _fake_sysfs(tmp_path, power_uw="24000000", sclk="0: 600Mhz \n1: 1110Mhz *\n2: 2900Mhz \n"):
    hwmon = tmp_path / "card0" / "device" / "hwmon" / "hwmon9"
    hwmon.mkdir(parents=True)
    (hwmon / "name").write_text("amdgpu\n")
    (hwmon / "power1_average").write_text(power_uw + "\n")
    (tmp_path / "card0" / "device" / "pp_dpm_sclk").write_text(sclk)
    return str(hwmon)


def test_read_sclk_reads_the_active_state(tmp_path):
    _fake_sysfs(tmp_path)
    assert power_linux._read_sclk_mhz(str(tmp_path / "card0" / "device")) == 1110.0


def test_read_sclk_is_zero_when_unreadable(tmp_path):
    assert power_linux._read_sclk_mhz(str(tmp_path)) == 0.0


def test_find_amdgpu_hwmon_skips_non_amdgpu(tmp_path, monkeypatch):
    other = tmp_path / "card0" / "device" / "hwmon" / "hwmon1"
    other.mkdir(parents=True)
    (other / "name").write_text("k10temp\n")  # no power1_average, wrong name
    hwmon = _fake_sysfs(tmp_path)
    monkeypatch.setattr(power_linux.glob, "glob", lambda _p: [str(other), hwmon])
    assert power_linux._find_amdgpu_hwmon() == hwmon


def test_find_amdgpu_hwmon_raises_when_absent(monkeypatch):
    monkeypatch.setattr(power_linux.glob, "glob", lambda _p: [])
    with pytest.raises(RuntimeError):
        power_linux._find_amdgpu_hwmon()


def test_sampler_records_watts_clock_and_zero_sys(tmp_path, monkeypatch):
    hwmon = _fake_sysfs(tmp_path)
    monkeypatch.setattr(power_linux.glob, "glob", lambda _p: [hwmon])
    with power_linux.Sampler(interval_ms=5) as s:
        time.sleep(0.05)
    assert s.samples, "sampler recorded no samples"
    sample = s.samples[0]
    assert isinstance(sample, Sample)
    assert sample.soc_w == 24.0          # 24_000_000 uW -> 24 W
    assert sample.gpu_w == 24.0          # gpu carries soc on the APU
    assert sample.gpu_mhz == 1110.0
    assert sample.sys_w == 0.0           # no whole-system reading without sudo
    assert sample.cpu_w == 0.0
