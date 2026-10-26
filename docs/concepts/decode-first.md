# Concept: a decode-first inference module

A design, not a product. Spliced has built nothing in hardware. This is what our measurements say
an inference part should look like if it were designed for what decode actually costs, drawn so the
reasoning can be argued with. 25 October 2026.

## The argument

Decode reads every weight and every cached token once per step and does little arithmetic on
them (note 2). The part that serves decode well is therefore memory first: as much bandwidth as
can be attached, a compute die no larger than the bandwidth can feed, and a clock no higher than
the bandwidth can use. Our clock-cap measurement is the sharpest version of that point: capping a
memory-bound chip's shader clock at 1,800 MHz bought 37% per token for 4% of speed
(results/halo-clockcap.md). A decode part runs there by design, not by sysfs.

Prefill is the opposite, compute bound, and a prompt token costs a fortieth of a generated one
(note 18). Putting both on one die means buying compute that idles during decode and bandwidth
that idles during prefill. The literature splits them across different machines (DistServe,
Splitwise, Mooncake; docs/clusters-reading.md). This concept splits them across different
modules on one sled, so the cache transfer stays on one board.

## The module

- A small compute die in the middle of a ring of eight memory stacks on one interposer. The ring,
  not the die, sets the module's footprint.
- Bandwidth per module, not FLOPS per module, is the headline number. The die is sized to consume
  it at a capped clock, so the power stage row is short.
- A flat vapour-chamber cold plate instead of a tall fin stack: the module's thermal budget is
  what a capped clock draws, and a flat plate keeps the sled at 1U.
- Batching is the mechanism that pays for the memory (notes 1, 10, 19): the module is meant to run
  eight or more sequences per step, always, and the sled's scheduler keeps it there.

## The sled

Six decode modules in two rows behind one prefill module, a compute-dense part with a tall heat
sink, and a switch between. A request is prefilled once on the front module and its cache handed
to a decode module over the board, where the request lives for the rest of its life. Prefix cache
hits (note 18) skip the front module entirely.

## The rack

Twenty-four sleds in a 42U cabinet, a coolant distribution unit in the bottom four units, a
top-of-rack switch, a vertical busbar at the rear so no sled carries a power supply, and
quick-disconnect couplers on every sled face. Liquid from the start, because a flat cold plate is
what keeps the sled at 1U; the busbar removes twenty-four supplies and their conversion losses,
which is the overhead between chip energy and wall energy in every measurement we have made (note 1
found it at 2x on one chip for one format). Rendered by `site/render/rack.py`.

## What would have to be true

- Joules per correct answer at eight slots, decode only, under a cap, below the single-chip figure
  in note 23 by the width of the idle and prefill share it no longer carries.
- Cache transfer from the prefill module hidden under decode time for prompts up to the length
  where the two-box microbenchmark in docs/clusters-reading.md says the link saturates.
- The idle floor of a sled: six capped modules idling must cost less than one chip idling at 17 to
  26 W (results/halo-clockcap.md), or the design loses at low load.

- For the rack: its idle at low load, at the wall, below the sum of its parts idling; the coolant
  unit's pumps cheaper than the fans they replace; cache handoffs between sleds hidden under decode
  time by the switch.

None of those are measured. The groundwork order in docs/clusters-groundwork.md is how they
would be.
