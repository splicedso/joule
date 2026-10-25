# Concept: a portable datacenter cell

A design, not a product. A unit that is a datacenter on its own and a row of hundreds when
docked, built so that the cost of one is low and the cost of the hundredth is lower. 25 October 2026.

## The unit

One rack of decode sleds (docs/concepts/decode-first.md) in a sealed, pallet-sized enclosure:
1.2 by 1.0 metres on a skid, 2.2 metres tall, forklift pockets below, lifting eyes above. Heat
rejection is on top, a louvred fin block fed by the sleds' liquid loop, so a cell standing alone
needs only power and a network drop. The front is a single door. Each side is a dock: two
coolant couplers, a fibre plate, and a busbar cover, all blind-mate, so a second cell pushed against
the first connects without a technician inside either.

## The row

Cells butt together end to end. Coolant trunks run through the side docks, so the row shares one
loop and the top blocks share the rejection load; the busbar passes through, so a row takes power
at one end and distributes it internally; fibre passes through, so the switches in each cell form
one fabric. A row of a hundred is one unit to the scheduler and a hundred units to the forklift.
A cell pulled out for service breaks nothing but its own compute: the docks on its neighbours
close.

## Why the unit cost stays low

- The sleds use the decode-first module, which spends its silicon on commodity stacked memory
  rather than a large die, and runs capped. The expensive part of an accelerator is what this design
  leaves out.
- No per-cell power supplies: the busbar does the conversion once per row.
- No raised floor, no chilled-water plant, no building: the cell is its own room, and the top block
  rejects heat to air. Where the ambient allows, that is the whole cooling system.
- One enclosure design, one door, one dock, built in volume. The variable parts are the sleds.
- A cell is sold, shipped and installed as one item on one pallet.

What we are not claiming: a price. We have not costed the enclosure, the pumps or the memory, and
will not put a number here until a bill of materials exists.

## What would have to be true

- The top block rejects a full rack's heat at the design ambient without a chiller, at a fan power
  that keeps the cell's wall energy per correct answer below the single-chip figure in note 23.
- The blind-mate couplers hold pressure through a hundred dockings; the coolant trunk's pressure
  drop over a hundred cells stays within the pumps.
- The busbar carries a row's current without a conversion stage per cell, and a cell can be pulled
  live.
- The docked fabric carries cache handoffs between cells under decode time, which the two-box
  microbenchmark in docs/clusters-groundwork.md would be the first measurement of.
- The idle floor of a row at low load, at the wall, has to stay below the sum of its cells idling.

None of those are measured.
