# Concept: a portable datacenter cell

A design, not a product. A unit that is a datacenter on its own and a row of hundreds when
docked, built so that the cost of one is low and the cost of the hundredth is lower. 25 October 2026.

## Revision 2 (25 October, evening): air cooled, in parts, one carrier at every size

Martin: "make it air-coolable, that looks like a box with no space to air cool"; "make it more like a
system"; "for people doing local hosting too, not just big datacenters". So:

- **Air path.** Intake through the whole front door (filtered grille), a wall of eight 230 mm fans,
  ducted lanes front to back over the carriers, the prefill fin stack, exhaust through the rear door.
  The long sides are closed and carry the docks. Liquid stays as an option through the same couplers.
- **The carrier is the unit.** A tray, the module board, a vapour chamber the length of the tray, a fin
  stack in its own duct, a handle. Twelve per cell in two tiers of six, pulled from the front. One in
  a 0.32 by 0.28 by 0.62 m enclosure is the desk unit (`site/render/desk.py`): filtered intake, the
  carrier's duct, two rear fans, a host board beneath, power and two network ports.
- **Parts.** `site/render/cell.py` builds every part in its own named collection and exports STL at 1:10
  (`--parts DIR`; 25 parts, `site/render/parts/cell`), so a scale model can be printed.
- **Drawings.** `site/render/cell_drawings.py` draws plan, side and front with dimensions and the parts
  list from the same numbers, as SVG on the Designs page.
- **The lineup.** `site/render/lineup.py` shows package, carrier, desk unit and cell at true relative
  size in one frame, the way Etched shows its family.

The earlier text below describes the first revision and stays for the record.

## The unit

A low, narrow, deep block: 0.6 metres wide, 1.2 metres tall, 3.0 metres deep, on a skid with
forklift pockets along its length. The proportions of an accelerator card lying flat, stretched back.
Decode sleds (docs/concepts/decode-first.md) load from the narrow front in one column and run the
depth of the cell; heat leaves through a louvred band along the whole top, fed by the sleds'
liquid loop, so a cell standing alone needs only power and a network drop. The front is a single
door. Each long side is a dock: two coolant couplers, a fibre plate, and a busbar cover, all
blind-mate, so a second cell pushed against the first connects without a technician inside either.
Cells butt together side by side, so a row is wide and three metres deep, with every front door on
one aisle.

## The row

Cells butt together side by side. Coolant trunks run through the side docks, so the row shares one
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

- The top band rejects a full cell's heat at the design ambient without a chiller, at a fan power
  that keeps the cell's wall energy per correct answer below the single-chip figure in note 23.
- The blind-mate couplers hold pressure through a hundred dockings; the coolant trunk's pressure
  drop over a hundred cells stays within the pumps.
- The busbar carries a row's current without a conversion stage per cell, and a cell can be pulled
  live.
- The docked fabric carries cache handoffs between cells under decode time, which the two-box
  microbenchmark in docs/clusters-groundwork.md would be the first measurement of.
- The idle floor of a row at low load, at the wall, has to stay below the sum of its cells idling.

None of those are measured.

## What the simulator already says

Fabric's demo (`spliced/fabric`, `python -m fabric.sim demo`) runs 64 requests through one capped
module and through a row of four cells with one, two or four awake, using our measured per-token
costs and placeholder trunk overheads (150 W of pumps, 120 W of switch, 3% conversion). The row
costs 2.7 times one module per correct answer at that load, almost all of it overhead and idle. That
is the design's real question: the trunks have to be cheap at low load, and the sleep policy has to
be aggressive, or a cell alone beats a row. A prototype's first job is to replace those placeholders.
