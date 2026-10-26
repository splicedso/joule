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
- Our own machines are single-package chips (M5 Pro, Strix Halo APU). There are no separate cables to tap, so on
  them the instrument measures DC input. That is still far finer than the 1 Hz board reading we use now.
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
