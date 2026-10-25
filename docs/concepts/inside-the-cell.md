# What is inside a cell

The parts list for the portable cell (docs/concepts/portable-cell.md), and the question Martin asked:
our own CPUs, or existing silicon. A decision document, not a bill of materials; prices are absent
on purpose. 25 October 2026.

## The decision

Buy the silicon, own everything above it. For the first three generations the cell runs on parts
that exist, chosen by our measurements, and what Spliced makes is the module layout, the cooling, the
enclosure, the dock, the operating system and the scheduler. A chip of our own is the fourth
generation at the earliest, and only once Fabric can show, from measured cells, which part of the
token's energy no bought part can remove. The reasons are below the parts list.

## The parts, by what they do

**Decode modules.** The decode-first module is a design around a commodity accelerator, not a new
die. Today the candidates are the parts we can measure: an AMD Ryzen AI Max+ 395 class APU with its
128 GB of unified LPDDR5X (the Strix Halo we own; 230 GB/s, capped it costs 111 J per correct answer
on a 7B at eight slots, note 23), or a discrete GPU module with HBM for the 32B class. The module
board, the cold plate and the capped clock are ours; the silicon is bought. Six per cell.

**Prefill module.** One compute-dense part per cell, on auto clock, with a tall heat sink: a discrete
GPU today. Its job is the first pass over every prompt; everything after is decode.

**Host.** One ordinary CPU per cell, an existing x86 or Arm server part, running the OS, the
scheduler, the prefix cache store and the dock controller. It is not in the token's critical path and
should be the cheapest part that has enough PCIe lanes and memory channels for the cache tier.

**Memory tiers for the cache.** Accelerator memory for the live KV cache; host DRAM for warm prefixes;
NVMe for cold ones. Which prefix goes where is Fabric's decision, and the break-even per tier is one
of the first experiments in docs/clusters-reading.md.

**Switch.** One Ethernet switch per cell, 400G class, forming the row fabric through the side docks.
Bought.

**Power.** No supply per cell: a busbar tap and a DC-DC stage sized for the cell's capped draw. The
conversion loss is the number the busbar exists to minimise.

**Cooling.** A liquid loop through the six cold plates and the prefill sink, a pump, and the louvred
heat band on top with its fans. The pump and fan power are the placeholders Fabric carries today.

**Dock controller.** A small board with the coupler sensors, the busbar interlock and the fibre
presence detect, so a cell knows when it is docked and the row knows when one is pulled.

## Own silicon: the case for and against

For: the measurements say decode wants a small die with as much bandwidth as can be attached, run at a
fixed low clock. No vendor sells exactly that; every accelerator carries compute sized for training or
for prefill, and a clock range we then cap in software. A die drawn to the decode roofline would spend
nothing on what decode does not use. That is the argument for a chip, and it is a real one.

Against, today: a two-person group with two machines cannot tape out a die, and a chip that is only
"the same as a bought one but with the compute removed" does not pay for a tape-out, because the
expensive part of a modern accelerator is the memory stack and the packaging, which we would be
buying anyway. The honest test is in Fabric: once cells are measured, split a token's joules into
memory traffic, compute, interconnect and overhead. If the compute share is small, the bought part
is already close to the roofline and a chip of our own would save little. If it is large, there is a
die to design. We do not know which yet, and the site will not say we do.

What is ours regardless: the module board, the cooling, the enclosure, the dock, the OS, the scheduler.
That is most of what a cell is, and it is what Etched and Anthropic each own in their own layer.
