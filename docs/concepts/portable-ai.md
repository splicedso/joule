# Portable AI hardware: options (internal, 2026-10-26)

Martin, 26 October, after turning down the measurement instrument: "some portable engineering thing, a portable data
center or something like that, something with AI, not competing with Etched, something else, not sure what."
A sourced market survey ran the same day; its findings are summarized here with the sources it gave.

## What the survey found

- **The carry case already exists.** SolarIA sells local LLMs, document search, translation and transcription on a
  Ryzen 9 box with a BLUETTI 768 Wh power station and a 350 W panel, from $23,495 (solaria.solutions, checked).
  Survival Expert sells a Mac Mini with a 7B model and a Jackery in a Pelican case for $2,499.
- **Buyers are unproven.** No procurement, program or published need for battery-powered LLM servers was found.
  Defence buys air-gapped AI as software; humanitarian groups lean to models on phones; schools pay about $500 for
  offline content boxes (RACHEL-Plus). Starlink keeps shrinking "no connectivity" as a market.
- **The parts are buyable.** A 1 kWh LiFePO4 power station is about 12 kg and $465 on sale. Framework sells its
  Strix Halo mainboard on its own. A Strix Halo box draws about 100 W running a model, 160 to 180 W at peak.
- **A laptop plus a power station** (an HP ZBook Ultra with the same Strix Halo chip and 128 GB, about $2,700 to
  $3,000) already gives most buyers most of the way.

## What our own measurements add

On a 1 kWh battery, from the Strix Halo's measured package energy (wall power would be higher):

| work | joules per correct answer | correct answers per kWh |
|---|---:|---:|
| 7B Q4_0, 8 requests at once (note 19) | 153.8 | about 23,000 |
| 7B Q4_0, 8 at once, clock capped (note 23) | 111.3 | about 32,000 |
| 1.5B Q4_0, one request (note 27) | 228.6 | about 16,000 |

But idle decides runtime: at 20 to 30 W the same battery is empty in 33 to 50 hours with no questions asked. So the
real engineering in any portable AI unit is the **power front end**: a small always-on board (a microcontroller and a
radio at a watt or two) that keeps the unit reachable and wakes the AI board only when someone asks, with DC input
from a battery, a vehicle or a panel. Spliced's original product was an always-on sensing runtime with a battery
planner; this is the same idea with an AI board behind it.

## The options

1. **A vehicle- or vessel-mounted AI unit** (the survey's pick). It runs on 12/24 V DC, senses the ignition, and
   is mounted against vibration. The vehicle replaces the battery and the panel. Buyers: research vessels, survey
   and utility fleets, expeditions. Competitors: rugged Jetson AGX Orin boxes at $3,500 to $9,000, capped at 64 GB.
   A Strix Halo unit holds 128 GB, enough for DeepSeek V4 Flash at about 2.6 bits.
2. **The field case**, our version of SolarIA's: the power front end, a 128 GB board, measured answers per
   watt-hour, at a fraction of $23,495. Weaker demand evidence, and the same buyers as option 1 on foot.
3. **A DC power and wake module for AI mini PCs** (EVO-X2, DGX Spark, Framework): the power front end sold on its
   own, so owners can run their box from a battery, a vehicle or a panel and let it sleep. The cheapest start
   ($300 to $600 in parts, the survey's estimate), the most electrical engineering, and the smallest market.

## Recommendation

Build the power front end first, because all three options need it, and test it on the Strix Halo we already own.
That box plus a power station and a microcontroller board can measure the runtime with and without wake-on-request.
Then take the result to one named niche, research vessels or expeditions, as option 1, using a bought board and a
bought power stage. Design our own battery and solar charging only after someone has paid.

The biggest risk is the survey's: no buyer has yet been seen paying for a battery-powered LLM server at a price
that covers a $2,500 board. The front-end test costs little and teaches the electrical engineering either way.
Every purchase is Martin's decision.
