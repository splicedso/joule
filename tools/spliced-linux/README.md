# Spliced Linux

The appliance image for Spliced nodes: Debian trixie (kernel 6.12, Mesa 25) with the amdgpu driver and firmware,
one service manager, the power logger and the clock policy as services. Built with mkosi from this recipe.
Not a distribution.

Status: builds and boots in a VM (2026-10-25, `results/spliced-linux-build.md`). gfx1151 has not been exercised:
the VM has no GPU, and the image has not been booted on the Strix Halo box. Nothing is claimed about the
notes' numbers until it reproduces note 23's capped figures within 3% on the box.

What is and is not in this build:
- The root filesystem is read-write. The read-only root and the separate state partition are not built yet
  (no `repart.d`); `/var/lib/spliced` is a directory on the root.
- Fabric is not in the image. `spliced-fabric.service` is shipped but disabled; nothing creates
  `/opt/fabric` or `/etc/spliced/node.toml` (only the `.example`).
- llama.cpp is not in the image; `/opt/llama.cpp.pin` records the commit the notes use (620d2225c). The
  clock policy needs a GPU load to verify the cap and fails, saying so, until a load tool is present.

Build, unprivileged (no sudo; mkosi from git, `uv tool install git+https://github.com/systemd/mkosi.git@v25.3`):

```bash
mkosi --tools-tree=default -f build            # image/spliced.raw; -f because mkosi skips an existing output
mkosi --tools-tree=default --profile=smoke -f build   # the same with root autologin on the console (VM only)
mkosi --tools-tree=default --console=read-only \
      --kernel-command-line-extra="spliced.smoke console=hvc0 systemd.journald.forward_to_console=1" vm
```

With `spliced.smoke` on the kernel command line, `spliced-smoke.service` prints the failed units, the three
Spliced units' status, the power log's head and the mounts to the console, then powers the VM off.

What the image does on boot: `spliced-clock.service` writes the OD-table cap (1,800 MHz) and verifies it
under a GPU load, exiting non-zero if there is no amdgpu device, no OD table, no load tool, a zero clock
reading or a cap that does not hold; `spliced-power-log.service` samples package power, the shader clock,
GPU busy and every named hwmon temperature every 10 s to `/var/lib/spliced/power.csv`, and exits non-zero
if there is no amdgpu device.
