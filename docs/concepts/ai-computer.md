# The Spliced AI computer: plan (2026-10-26)

Martin, 26 October: "Build a compact, self-contained AI computer that runs open-weight models without needing the
internet or a cloud API. This is the plan for now, along with the open-weight lightweight models." Then: "so we can
plan and make a chassis, and plan the other systems."

**What it is.** A small box. Power and a network cable or Wi-Fi in; a private AI on the local network out. Phones and
laptops open it in a browser: chat, documents, code, all answered by open-weight models running inside the box. No
account, no internet, no cloud API. Our own lightweight models are the defaults, chosen by measured joules per correct
answer on this exact hardware.

**What it is not.** Not a datacenter product and not a chip: no competition with Etched. Not a laptop: it serves a
household, a team or an office, and it runs larger models than a laptop holds.

## The systems

Each system has a first spec, the decisions still open, an owner, and its next step. Martin owns the physical
systems; Claude sessions own the software; both own the product decisions.

### 1. Compute board (both)
- First choice: a Strix Halo board (AMD Ryzen AI Max+ 395, 128 GB unified memory) in the Mini-ITX format, such as
  Framework's Desktop mainboard (sold on its own; the base board is $799, the 128 GB board costs more; standard ATX
  power connectors; 120 W sustained, 140 W boost). It is the machine every Linux note was measured on.
- Why 128 GB: it holds a 30B-class mixture-of-experts model at 8 bits with room to spare, or DeepSeek V4 Flash
  (304B) at about 2.4 bits (`fabric/moe.py`).
- Open: which board vendor; the 64 GB board as a cheaper model.
- Next: confirm the 128 GB board's price and stock, and download its mechanical drawing.

### 2. Chassis (Martin)
- Target: under 5 litres (Framework's own case is 4.5 L, 96.8 x 205.5 x 226.1 mm), front-to-back air, one large fan,
  a front grille, rear I/O through the board's standard backplate opening, feet or a stand, no tools to open.
- Method: parametric code-CAD (so every dimension lives in one file), 3D-printed prototypes first, sheet metal or
  machined aluminium later.
- Must verify before any CAD: the exact Mini-ITX mounting-hole positions and keep-out zones, from the board maker's
  drawing or the Mini-ITX specification. Searches did not return coordinates; nothing is drawn from memory.
- Next: a cardboard or printed mock-up around the board's outline with the supply and fan placed, to check fit.

### 3. Power (Martin)
- The board takes standard ATX connectors (24-pin, plus a CPU connector whose pin count the sources disagree on:
  check Framework's documentation). A FlexATX supply (Framework uses 400 W, 150 x 81.5 x 40.5 mm) fits a small case.
- Later options: an external 19 to 20 V adapter with an internal DC-to-ATX board for a smaller box; a battery input.
- Next: confirm the CPU connector, choose the supply, budget the power path (board 140 W peak, fan, storage).

### 4. Cooling (Martin)
- About 150 W of heat from a closed box. Airflow per watt by hand calculation first, then a fan-and-thermometer test.
- Quiet matters: it sits in a room with people. Target and measure noise as well as temperature.
- Next: the hand calculation (air needed for 150 W at a 15 C rise), then the fan choice.

### 5. Front panel and controller (Martin)
- A small microcontroller: power button, status light, temperatures to fan speed, and the power reading the
  software shows. Optional small display showing the box's address and the model loaded.
- Next: decide what the board's own fan header and firmware already cover before adding a controller.

### 6. Storage and network (both)
- An NVMe drive large enough for a model library (about 2 TB holds a dozen models at several sizes).
- Ethernet plus Wi-Fi; the box can also host its own Wi-Fi network for places with no network at all.

### 7. Operating system (Claude, Linux session)
- Spliced Linux (`tools/spliced-linux`): an appliance image that boots straight into the model server and the web
  interface. Built and smoke-tested in a VM (PR 21 and 22); next it needs llama.cpp built against the image's Mesa,
  the web interface, and the clock and power services verified on real hardware.

### 8. Serving and interface (Claude, this session)
- llama-server for the models; Foundry's interface served by the box itself, so any browser on the network uses it.
  Foundry already shows tokens per second and energy per answer; the box version adds the model library and the
  measured settings (Q4_0 below 32B, the right number of requests at once, a draft only at low load).
- Next: the box server, which serves Foundry's interface and answers its calls over HTTP. Started 26 October.
- On the network (`--lan`) the box asks for its access code, made on first start (foundry 26081ff, 27 October).

### 9. Models (Claude, Linux session)
- The defaults are chosen on `experiments/general_eval.py` (maths, knowledge, executed code) by joules per correct
  answer on the box: today's candidates are Qwen2.5 7B, Qwen3.5 4B, Qwen3.6 35B-A3B and Granite 3.3 2B, with thinking
  off unless a task proves it pays (note 29, being measured).
- Our lightweight models: the rejection-sampling training run queued on Linux (beat the base on maths without losing
  knowledge or code), then the same recipe on the best base.

## Milestones

1. **Software on the box we own** (no purchase): the Strix Halo boots, serves the interface on the local network,
   answers offline, shows energy per answer. Bar: a phone on the same Wi-Fi gets an answer with the internet unplugged.
2. **The model lineup**: measured defaults, our trained model if it clears its bar.
3. **Chassis v0**: Martin's printed enclosure around a bought board, power and cooling measured under load.
4. **Five people use it** for a week; what they ask decides version 1.

Nothing is bought without Martin.
