# Spliced Linux

What runs inside a cell, from the kernel up. A design, not a distribution; nothing is built. 25 October 2026.

## What it is

A minimal, immutable Linux image for one job: run Fabric on a cell. It is not a general-purpose
distribution and not a fork of one. It is a build recipe, the way an appliance vendor makes one:
an upstream kernel with the accelerator drivers we measure with (amdgpu with the OD-table clock
controls, the NVIDIA open driver where a prefill part needs it), a read-only root, a single service
manager, and Fabric as the only workload. Updates are whole images, signed, applied to a second
partition and switched at reboot, so a cell is always in a known state and a bad update rolls back by
itself.

## Why our own image and not a stock server OS

- **The clock policy needs root on sysfs.** Fabric's capped decode state is a write to the OD table.
  On a stock OS that is a privileged exception; on ours it is the default, set at boot and verified
  under load the way the clock-cap sweep did it (results/halo-clockcap.md).
- **Energy accounting is part of the OS.** Every cell reports package power, clock and busy for every
  module at 10 s, the way Linux's power logger does now, into a time series Fabric reads. The number
  a cell reports is the number the site publishes; there is no second measurement path.
- **Nothing else runs.** The idle floor of a cell is a design number (docs/concepts/portable-cell.md);
  a stock image's background services are joules we did not budget for.
- **The dock is a device.** Coupler sensors, the busbar interlock and the fibre presence line are a
  kernel device with a state Fabric can read, not a script.

## What is in it

| layer | choice | ours or bought |
|---|---|---|
| kernel | upstream LTS, amdgpu and the NVIDIA open module, no other drivers | bought (upstream), our config |
| firmware | vendor accelerator firmware; our dock controller firmware | mixed |
| root | read-only, built from a recipe, two slots, signed | ours (the recipe) |
| services | one manager; Fabric, the power logger, the dock daemon, a metrics exporter, SSH on the maintenance port only | ours |
| inference runtime | llama.cpp server builds we pin and measure, one per accelerator | bought (upstream), our pins |
| scheduler | Fabric | ours |
| cache store | Fabric's prefix cache over host DRAM and NVMe | ours |
| management | one row controller image, the same recipe with Fabric in row mode | ours |

## The build

A reproducible image from a text recipe, the pinned kernel, the pinned llama.cpp commit (the same
commit the notes measure with, so a cell's numbers are our numbers), and Fabric at a tagged version.
Every image carries the hashes of everything in it, and a cell's metrics report the image hash, so
any published figure names the exact software that produced it.

## What would have to be true

- The image boots the two machines we own and reproduces note 23's capped figures within 3%.
- The idle floor with only our services running is below the measured 17 to 26 W of the stock
  desktop image on the Strix Halo.
- An image update applies and rolls back without a technician.

None of those are built. The first is the one that costs nothing but time: a recipe that boots the
Strix Halo and runs quality.py under the cap is the first deliverable, and it is a measurement.
