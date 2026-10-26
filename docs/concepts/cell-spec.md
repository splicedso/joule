# Cell and row: the spec sheet

Numbers for the portable cell and a row of them, every one traced to a measurement, a datasheet, a
placeholder or arithmetic, and labelled which. A target sheet for a prototype, not a product sheet.
25 October 2026.

## One cell

| item | value | basis |
|---|---|---|
| envelope | 0.6 m wide, 1.2 m tall, 3.0 m deep, on a 0.1 m skid | design |
| decode modules | 6, each one AMD Ryzen AI Max+ 395 class part, 128 GB unified LPDDR5X | design; the part we measure |
| prefill module | 1 discrete GPU, auto clock | design |
| host | 1 server CPU, 64 GB DRAM, 2 x 4 TB NVMe for the cold prefix tier | design |
| decode clock | capped at 1,800 MHz | measured: note 23 |
| decode power, each, at 8 slots under cap | 81 to 87 W package | measured: note 23 (81.4 to 87.0 W across the three cells) |
| decode power, cell, 6 modules | about 510 W | arithmetic |
| prefill power | 300 to 700 W, part dependent | datasheet range |
| host, switch, pumps, fans, conversion | 450 W | placeholder (Fabric trunks: 150 pump, 120 switch, 3% conversion, plus host and fans) |
| cell power, busy | about 1.3 to 1.7 kW | arithmetic on the above |
| cell power, idle, all modules idle | about 170 W modules plus 450 W overhead | measured idle 17 to 26 W per module (note 23); overhead placeholder |
| 7B Q4_0 throughput, cell, 8 slots each | about 1,150 tok/s | measured 192.1 tok/s per module under cap (note 23) times 6 |
| 7B joules per correct answer, modules only | 111.3 J | measured: note 23 |
| 7B joules per correct answer, cell, busy, overhead included | about 140 J | arithmetic: 111.3 times (1 + 450 W overhead / 1,700 W) at full load; worse at low load |
| 32B Q2_K calibrated, cell | about 280 tok/s, 384.7 J per correct answer modules only | measured: note 23 |
| heat to reject | equal to cell power, up to 1.7 kW | arithmetic |
| coolant loop | one, through 6 cold plates and the prefill sink; two couplers per side dock | design |
| row fabric | one 400G switch, 32 ports, 2 ports per side dock | design |
| weight | under 400 kg, forklift | estimate, unverified |

## A row of 100

| item | value | basis |
|---|---|---|
| footprint | 60 m wide, 3 m deep, one aisle of doors | arithmetic |
| power, busy | about 130 to 170 kW | arithmetic |
| 7B tokens per second | about 115,000 | arithmetic |
| 7B per correct answer at full load | about 140 J | same as one cell; a row has no per-token advantage, only a per-overhead one if trunks are shared |
| shared trunks | one coolant trunk, one busbar, one fabric; row controller image | design |
| what the row buys | fewer pumps and switches per cell if trunks are shared, and the sleep policy | Fabric's demo says overhead dominates at low load (portable-cell.md) |

## What the sheet shows

The modules are measured and cheap; everything around them is a placeholder and is most of the idle
power. That is the prototype's whole job: measure the 450 W, then make it smaller. A cell that idles at
620 W to serve nothing loses to a laptop; a cell that idles at 200 W and serves 1,150 tokens a second at
140 J per correct answer is a product.

## Comparison the sheet allows

Note 8's measured datacenter rows: an 8x B200 server at 0.101 J per token on a 70B at the wall. Our
cell on a 7B at 8 slots under cap: 111.3 J per correct answer over about 180 tokens per answer is about
0.6 J per token, modules only, on a ten-times smaller model. The datacenter part wins per token by a wide
margin because it batches far deeper (note 8: 58 or more sequences per weight pass). The cell's argument
is not per-token energy against a B200; it is per correct answer on the model that fits the job, idle
behaviour, and cost per unit. That comparison is honest only once the overhead is measured.
