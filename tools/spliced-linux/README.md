# Spliced Linux

The appliance image for Spliced nodes: an upstream kernel with the amdgpu driver, a read-only root,
one service manager, and one workload, Fabric, with the power logger and the clock policy as services.
Built with mkosi from this recipe. Not a distribution.

Status: a recipe, untested. The first deliverable is an image that boots the Strix Halo box and
reproduces note 23's capped figures within 3%; nothing is claimed until it does.

```bash
sudo mkosi            # builds image/spliced.raw (Debian stable base, pinned packages below)
sudo mkosi qemu       # boots it in a VM for a smoke test (no GPU)
```

What the image does on boot: `spliced-clock.service` writes the OD-table cap (1,800 MHz) and verifies
it under a short load, `spliced-power-log.service` samples package power, clocks and temperatures
every 10 s to /var/lib/spliced/power.csv, `spliced-fabric.service` starts the scheduler, which starts
the pinned llama-server for the model in /var/lib/spliced/models. Metrics on :9100 carry the image hash.
