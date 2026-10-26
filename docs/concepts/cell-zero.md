# Cell Zero: a portable cluster you can build (design brief, 2026-10-26)

Martin, 26 October: "besides working on models, what else should we do; I want to be an engineering startup, not
just something I Claude Code, something I actually have to work on; who cares if it's ambitious, we should design
something useful, maybe portable clusters."

**What it is.** Four Strix Halo-class compute boards in one wheeled case, with one power input, one network port and
its own cooling. Plugged into a wall socket, it runs a frontier-class open model privately, with no datacenter and no
cloud: DeepSeek V4 Flash on one or two boards, or GLM-5.2 (753B) across three. It is the small end of the cell on the
Designs page, made buildable, and the "runs on one of our clusters" of the flagship plan.

**Who it is for.** Teams that want a frontier-class model on their own premises and cannot run GPU servers:
small firms with confidential data, research groups, events and field sites with mains power. This is a hypothesis;
the first job in the business column below is to test it.

**Why it is not Etched.** Etched makes chips for datacenters. Cell Zero uses bought boards and sells a whole working
system to a customer who has no datacenter.

## The numbers it starts from (ours)

| | value | source |
|---|---|---|
| memory per board for the model | about 113 GB | the Strix Halo's 90% GPU share |
| power per board decoding one request | about 104 W package | note 26 |
| peak per mini PC at the wall | 160 to 180 W | ServeTheHome, EVO-X3 review (market survey) |
| idle per board | about 20 W package | Fabric cost table |
| DeepSeek V4 Flash, 1 board at 2.4 bits | about 57 tok/s ceiling, 1.8 J per token | `fabric/moe.py`, modelled |
| GLM-5.2 at 2.6 bits | 3 boards, about 15 tok/s per stream, 46 with the pipeline full | `fabric/moe.py`, modelled |
| network share, pipeline split | under 1% on 10GbE | `fabric/moe.py` |

So the case must carry about 750 W at peak (four boards at 180 W, plus a switch and fans) from one mains socket,
which a single 1 kW supply can do, and reject that heat with air.

## Work packages, and who owns them

**Martin (the engineering):**
1. **Power.** One mains supply, one distribution board for four compute boards: fusing per board, sequenced
   power-up, a current sense per board, an emergency off. First, read what power input the chosen board takes
   (ATX connectors or a single DC input); that decides the design. KiCad.
2. **Thermal.** Front-to-back air through four lanes, about 750 W out of a closed case at 35 C room air. Start with a
   hand calculation (airflow needed per watt), then a cardboard and fan mock-up with a thermometer before any CAD.
3. **Enclosure.** A wheeled case or a 19-inch 4U shell: board mounting, filtered intake, cable runs, handles, CAD and
   3D-printed brackets.
4. **Controller.** A small microcontroller board on the distribution board: fan curves from temperatures, power
   sequencing, a status display, and power readings the software can log.

**Claude sessions (the software):** the operating image (Spliced Linux), Fabric splitting a model across the four
boards, the model itself (the flagship), and the measurement of joules per correct answer on the finished box.

**The business column (both):** five conversations with possible buyers before the first board is bought: would
they pay for a frontier-class model in a box on their premises, and at what price?

## Order

1. Now, at no cost: the power and thermal hand calculations, the board's power input, the first sketch of the case,
   the buyer conversations. Software continues in parallel.
2. When Martin decides to buy: one board, then two, linked, measuring a model split across them.
3. Then the full four-board Cell Zero.

Nothing is bought without Martin.
