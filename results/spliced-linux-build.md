# Spliced Linux appliance recipe: first build and smoke test (2026-10-25, Strix Halo as build host)

`tools/spliced-linux/` landed untested. This is what a build on the Linux box found, as a user without root
(mkosi 25.3 from git, `--tools-tree=default`, unprivileged user namespaces; the box has no mkosi, debootstrap,
mmdebstrap, systemd-nspawn, mtools or ukify installed and apt needs Martin's password).

## Build attempts

**Attempt 1, the recipe as landed (22:26, unprivileged, tools tree from Debian testing):** the tools tree built
(374 packages); the image install failed at apt with `E: Package 'firmware-amd-graphics' has no installation
candidate` (finding 2 below). No image.

**Attempt 2, with the minimal fixes applied on this branch** (`Release=trixie`, `Repositories=main,non-free-firmware`,
`bc` added, `Autologin=yes` for the VM, both units `After=sysinit.target`, postinst using `mkosi-chroot` and
`$BUILDROOT`): built. `image/spliced.raw`, 1.1 GB (599 MB used), Debian trixie, kernel 6.12.113+deb13-amd64, systemd-boot, 2 min
after the tools tree is cached. Note: `mkosi build` silently skips when the output exists; three of my
rebuilds were no-ops until `-f`. The `tools` tree is 1.6 GB under `image/` (gitignored).

## What is wrong in the recipe, from reading it (before any build)

1. **Debian bookworm cannot drive this GPU.** Bookworm ships kernel 6.1 and Mesa 22.3; gfx1151 (Strix Halo)
   needs a 6.12+ kernel with its firmware and Mesa 25 for RADV. The box itself runs a 7.2 kernel on a
   trixie (Debian 13) base, and the llama.cpp build every note uses is linked against Mesa 25.0.7.
   `Release=trixie` is the minimum; the kernel may still need backports or the vendor kernel.
2. **`firmware-amd-graphics` is in `non-free-firmware`,** which mkosi's Debian default (`main`) does not
   enable: the package install fails or the GPU has no firmware. Needs `Repositories=main,non-free-firmware`.
3. **`mkosi.postinst` runs on the host, not in the image.** Since mkosi v15 scripts run outside the image;
   `systemctl enable ...` and `mkdir -p /var/lib/spliced ...` act on the build host's filesystem (as root,
   on the host's own units and directories). Inside-the-image commands need `mkosi-chroot`, or the
   enablement symlinks and directories belong in `mkosi.extra/`.
4. **Both logger and clock units create a dependency cycle:** `After=multi-user.target` together with
   `WantedBy=multi-user.target` (a unit wanted by a target cannot also be ordered after it; systemd breaks
   the cycle by dropping a job). `After=sysinit.target` (or nothing) is what they mean.
5. **The clock service's verification is vacuous.** Its "load" is a Python loop on the CPU; the shader clock
   stays at its 600 MHz idle under that, so "active max <= cap" passes with or without the cap. The sweep's
   check (`experiments/halo_clockcap.sh`) uses a llama-bench decode; the image has no llama binary to
   do that (see 7).
6. **`spliced-power-log` needs `bc`,** which is not in the package list; the service exits on its first
   sample. Also its `temps_c` column packs every hwmon temperature into one space-separated field with no
   names, so a reader cannot tell the GPU edge from the NVMe.
7. **Nothing installs llama.cpp or Fabric.** The postinst writes a pin file; `spliced-fabric.service`
   execs `/opt/fabric/.venv/bin/python`, which no step creates ("vendored by the build script before mkosi
   runs": there is no such script), and `/etc/spliced/node.toml` is only shipped as `.example`, so Fabric
   fails on boot even if it were present. The pinned llama.cpp has to be built against the image's Mesa
   (not copied from the host) or the numbers are not the notes' numbers.
8. **The read-only root and the state partition exist only in the README.** No `repart.d` definitions,
   no `/var/lib/spliced` mount, no fstab; `ro` on the kernel command line alone leaves `/var` unwritable,
   so the logger's CSV and the model directory cannot be written.
9. **No way to log in for the smoke test:** no root password, autologin or SSH key, and no `ssh` enablement.
   `Autologin=yes` for the VM, authorized keys for nodes.
10. `mkosi qemu` is `mkosi vm` since v24; the README's commands assume `sudo`, which the box's policy
    does not give unattended (unprivileged builds work, see above).
11. `KernelCommandLine=... amdgpu.ppfeaturemask=0xffffffff` was not needed for the OD table on the box
    today (default mask); harmless, but it also enables every experimental PM feature. Worth a note.
12. Smaller: `RemoveFiles=/usr/share/locale` breaks Python's locale lookups in some tools; `lm-sensors`
    is unused (the logger reads sysfs); `CompressOutput=no` on a multi-GB raw image is fine for a build
    host but not for shipping; the ESP needs `mtools` on an unprivileged build host.

## Smoke test in qemu

`mkosi --tools-tree=default --console=read-only --kernel-command-line-extra="spliced.smoke console=hvc0
systemd.journald.forward_to_console=1" vm`, unprivileged, TCG (this user is not in the kvm group); the VM has no
GPU. A flag-gated `spliced-smoke.service` (added in this branch, only active with `spliced.smoke` on the kernel
command line) prints the failed units and the three Spliced units' status to the console and powers off.

**As landed (plus the fixes needed to build):** boots to multi-user in 10 s. `spliced-clock` exits 0 with no GPU
present ("cap 1800 MHz, active max 0 MHz"): the verification was vacuous, since its load was a CPU loop and a
missing device read as a held cap. `spliced-power-log` ran, printing `ls: cannot access` and a `bc` syntax error
every 10 s and writing no usable file. `spliced-fabric` failed 203/EXEC five times (no `/opt/fabric/.venv`) and hit
its start limit. `agetty` could not exec `/bin/login` on tty1 or hvc0 (the `login` package was missing), so
autologin did nothing. My first smoke unit carried the same `After=multi-user.target` cycle as the recipe's
units and never ran, which is how the cycle was confirmed.

**After the defect fixes below:** boots, `login` works on tty1 and hvc0, `spliced-clock` exits 2 with
"no amdgpu device with an OD table; not capped", `spliced-power-log` exits 2 with "no amdgpu device with hwmon;
not logging" (and is restarted by `Restart=always` until the start limit; on a node without a GPU that is the
right noise), `spliced-fabric` is disabled and not started, the smoke unit reports and powers the VM off at
25 s. Expected in a VM; what it proves is that a missing GPU is now a failure, not a success.

## Fixed in this branch (defects only; claims shrunk to what boots)

- `Release=trixie`, `Repositories=main,non-free-firmware`; `login` added, `bc` dropped (awk does the division).
- `spliced-clock`: exits 2 without an amdgpu OD table, 3 without a GPU load tool (the pinned `llama-bench`
  on the configured model, or `SPLICED_LOAD`), 4 if the active clock reads 0 under load, 5 if the cap does
  not hold; the load is a GPU load, not a CPU loop.
- `spliced-power-log`: exits 2 without an amdgpu device; creates its output directory; names every
  temperature column (`<hwmon>_<tempN>_c`) instead of one unlabelled field; awk instead of bc.
- Both units `After=sysinit.target` (no cycle); `mkosi.postinst` enables units with `mkosi-chroot` and creates
  directories under `$BUILDROOT`, so it no longer touches the build host.
- `spliced-fabric.service` shipped but not enabled; no fake venv. `Autologin` moved to `mkosi.profiles/smoke`
  (VM only). README rewritten: read-write root, no state partition, no Fabric, no llama.cpp, no sudo, gfx1151
  not exercised, the exact build and smoke commands.

## Still wrong or missing (not fixed here)

- No read-only root, no state partition, no `repart.d`, nothing mounts `/var/lib/spliced`.
- No llama.cpp build in the image (it must be built against the image's Mesa, not copied from the host),
  so the clock policy cannot verify on a node until that exists; no Fabric install step; `node.toml` is an example.
- `KernelCommandLine=ro` is set but the root comes up read-write (gpt-auto remounts it); `ro` is a claim
  without a mechanism. `amdgpu.ppfeaturemask=0xffffffff` enables every experimental PM feature; the OD table
  worked on the box today with the default mask.
- Not booted on the Strix Halo box (not installed, per instruction), so the kernel's gfx1151 support, the
  firmware and Mesa 25 RADV are untested in this image; `systemd-ssh-generator` warns in the VM (no vsock),
  harmless.
- `RemoveFiles=/usr/share/locale` is kept; `lm-sensors` is still installed and unused.

Logs: `logs/mkosi_build{,2,6,7}.log`, `logs/mkosi_vm{,2,4,5}.log` on the box (not committed).

## Follow-up (22:57): a failed verification restores auto

`spliced-clock` exits 3, 4 and 5 only after the cap has been written, so a node whose verification failed
would have kept running under an unverified cap. It now restores auto (the OD-table reset and the auto level,
the same three writes as `spliced-clock auto`) before exiting on any of those, and says so. The VM path
(exit 2, before any write) is unchanged: the smoke boot after the change shows the same messages, login on
both consoles, Fabric not started, power-off at 25 s. `bc` removed from the package list (the findings above
said it was dropped; it was not).
