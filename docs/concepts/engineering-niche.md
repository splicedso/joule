# Spliced's engineering niche (internal, 2026-10-26)

Martin asked, 26 October: "maybe we shouldn't make clusters since we are already so similar to Etched, we make AI
model variants, but what is our engineering thing, I want something I have to engineer", then "find what
engineering niche related to open weight and AI labs we can make, that would be not super expensive to start but
can scale." This page answers it from a sourced market survey run the same day; the survey's claims carry their
sources there and are summarized here.

## The recommendation

**Measured energy for AI, as an instrument.** A calibrated power-measurement device with open software that ties
power to tokens and to correct answers, plus a published reference dataset of open-weight models measured with it.
The hardware is the entry; the dataset and the token-synced software are what nobody else has.

Why this one:
- Every Spliced note runs into the same wall: chip-only sensors, a board reading smoothed to about 1 Hz, and
  sensors that disagree across machines. NVIDIA's own driver samples about a quarter of the runtime on A100 and
  H100 (arXiv 2312.02741). The public AI Energy Score leaderboard reads only that driver path. The boundary choice
  alone moved Google's per-prompt figure 2.4 times (arXiv 2508.15734).
- It is electrical engineering at a student's scale: current sensing, ADCs, a four-layer board, firmware,
  calibration. No foundry, no datacenter.
- It is cheap to start: an open design already exists. PowerSensor3 (ASTRON, arXiv 2504.17883, April 2025) is
  open hardware, firmware and software: up to 4 rails, 20 kHz, time markers, under about EUR 100 in parts.
- It scales: from our own research, to reviewers and labs, to per-rack instruments if there is demand.

## What the survey says against it

- Cheap per-rail hardware is not new. BENCHLAB ($199), ElmorLabs PMD2X (about $109) and Powenetics v2 (about 1 kHz,
  EUR 500 to 975) exist, and PowerSensor3 is free to build. The hardware alone is not a moat.
- Compliance does not need it. MLPerf Power accepts only wall power on Yokogawa analyzers. The EU AI Act's Annex XI
  accepts "known or estimated" energy. No rule anywhere requires per-rail or per-token measurement.
- Our own machines are single-package chips (M5 Pro, Strix Halo APU), so there is no separate GPU cable to tap. On a
  laptop the instrument measures DC input. A Strix Halo desktop board still has several supply rails (below), and
  measuring them all is still far finer than the 1 Hz board reading we use now.
- The biggest risk: people who care already have free or cheap options, so paying demand may stay at a few hundred
  units.

## The cheap test, before anything is designed

1. Build two PowerSensor3 units from the open files, about EUR 200 in parts and boards. Martin decides the purchase;
   nothing is bought without him.
2. Measure the M5 Pro's and the Strix Halo's DC input at 20 kHz alongside `phase`'s sensors, synced to tokens. The
   first note: how far the built-in sensors are from the truth on the machines people own. That note is useful
   whatever happens next.
3. Publish it, and see who asks to buy one. If labs, reviewers or hardware makers ask, design Spliced's own board:
   USB-C PD pass-through for laptops, 12 V input for mini PCs, isolation, a calibration certificate, and the token
   sync built into `phase`. If nobody asks, the instrument still makes every later note more accurate.

## Alternatives considered

- **Edge inference boards for small models:** competing with Jetson Orin Nano Super ($249) and the Raspberry Pi AI
  HAT+ 2 ($130), using someone else's chip. Little moat.
- **Rack power-swing telemetry for training clusters:** a real need (a Microsoft, OpenAI and NVIDIA paper on
  training power swings), but mains-voltage certification and hyperscaler sales cycles. Too heavy to start.
- **GPU connector and per-pin monitors:** crowded (Thermal Grizzly WireView Pro II, PMD2X, BENCHLAB 2), and only
  loosely tied to AI labs.
- **Clusters:** what Etched does, capital-heavy, and not needed for either the models or the measurements. The
  cluster designs stay a research thread on the site.

## A path for an EE student, starting now

- Weeks 1 to 2: read the PowerSensor3 paper and repository; shunt and Hall current sensing; sampling and aliasing;
  KiCad basics.
- Weeks 3 to 4: order the boards (Martin's call), assemble, flash, and bring it up.
- Weeks 5 to 6: calibrate against a bench supply and a good multimeter; write the token-sync bridge into `phase`.
- Weeks 7 to 8: the first measurement note.
- After that: a Spliced board revision, if the test says there are buyers.

## The first board (2026-10-27 00:43, after a second survey)

Martin asked again on 27 October for "something small but impactful that I could start off". The answer above stands;
this makes its first step concrete. A sourced survey the same night found four things that shape it:

- **A Strix Halo desktop board draws on five rails, not one.** Framework's published Desktop schematic (CC BY 4.0,
  `Mainboard_Interfaces_Schematic_Framework_Desktop_Ryzen_AI_Max.pdf` in FrameworkComputer/Framework-Desktop, page
  107) feeds the APU from the 8-pin EPS at 12 V (29.8 A design budget), and takes 12 V (4.6 A), 3.3 V (9.6 A), 5 V
  (10.5 A) and 5 V standby from the 24-pin. These are design budgets, not measurements. A meter on the 12 V line
  alone would miss the rest of the board.
- **The board already measures its APU feed.** The same page shows a TI INA236 with a 1 mOhm shunt on the EPS line,
  on the embedded controller's SMBus. Nothing found says the operating system can read it. If it can, it is a free
  cross-check on the biggest rail.
- **Nobody ties power to requests.** BENCHLAB 2 ($249), ElmorLabs PMD-USB ($60), PMD2X and Powenetics v2 (about
  1,000 samples a second, EUR 975) tap the same connectors, and none publishes an API that lines readings up with
  software events. The nearest is Otii's Ace, which records a device's serial log beside its power trace, up to 5 A.
- **No USB-C to ATX supply exists for a board like this.** TI's TPS26750 can draw 48 V at 5 A from USB-C, but its
  evaluation board is a scarce prototype. Small DC-to-ATX supplies such as the picoPSU-150-XT give 6 A on 3.3 V and
  5 V, under the Framework board's budgets.

**So the first board is an ATX tap: 24-pin and 8-pin EPS in, the same out, one current monitor per rail.** It sits
between a normal power supply and the board, so it carries no risk beyond the supply's own protection and never
touches mains. It is Martin's to design in KiCad: five channels of the same circuit, two connector pairs and a small
microcontroller. That is a real board, but a small one.

- **Sensor:** TI INA228 on every rail. 20-bit, up to 85 V on the bus (the same part works at 48 V later), conversions
  from 50 us, and an energy accumulator in the chip, so no energy is lost between reads. The LTC2947 has its shunt
  built in but stops at 15 V; the INA238 has no accumulator.
- **Shunts:** about 1 mOhm on the EPS rail (30 A gives 30 mV, inside the INA228's 40.96 mV range, about 0.9 W of
  heat), and a few mOhm on the smaller rails. Kelvin connections, wide copper, and 2 oz outer layers. Values to be
  fixed from the datasheet before layout.
- **Readout:** an RP2040 reads the five monitors and streams over USB with its own timestamps, synced to the host
  clock. `phase` already records when each request starts and ends, so energy per request and per correct answer
  come from the same files as today.
- **Calibration:** against a bench supply, a known load and a good multimeter, then against the chip's own sensors on
  the Strix Halo box and, where it can be read, the board's INA236.

**Order of work.** Nothing is bought without Martin.
1. Read the INA228 datasheet and schematic page 107. Breadboard one channel from an INA228 breakout (sold at $15 to
   $29) on a 12 V supply and a resistor load, read it from a Raspberry Pi Pico.
2. Draw the five-channel schematic in KiCad; review it together before layout.
3. Lay out the board, order it with the connectors and shunts, assemble, and bring it up one rail at a time.
4. Firmware and the `phase` bridge (ours), then calibration.
5. The first note: what a Strix Halo board draws, rail by rail, per correct answer, against what its own sensors say.

PowerSensor3 stays the reference to read before drawing anything: its paper and repository show how a 20 kHz
open meter handles sampling, isolation and time markers. Building our own board instead of starting with it follows
from the five rails and the pass-through. The PowerSensor3 parts are no longer the first purchase.

**What comes after.** The same INA228 channels, at 48 V, become the input stage of the AI computer's own supply:
USB-C power from a 240 W charger or a power station, through a TPS26750-class controller, converted to the rails
above. That is a power supply design, with inrush, heat and USB-C negotiation, so it waits until the tap board works.

