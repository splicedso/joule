# V1: a cluster someone could build

The first system that could be built from parts that exist, by a small team, and run with Fabric.
It uses what datacenters already know how to do, hot aisle and cold aisle, standard rack width,
front-to-back airflow, and puts our part, the decode carrier, inside it. Every number here is
labelled measured, datasheet, standard, placeholder or arithmetic. A design, not a product.
25 October 2026, evening.

## The decision: breathe like a datacenter

The earlier cell was a sealed block with a louvred top; it could not take enough air. V1 drops that.
Every module is a 19-inch rack sled with its own fans, air in through the front face from the cold
aisle, out the back into the hot aisle. The containment is the row, not the box. That is the
arrangement every air-cooled datacenter uses, and the one a single unit in an office also works in:
a sled on a desk breathes the same way.

## The sizes

**Carrier** (unchanged). Tray, module board, vapour chamber, a fin stack in its own duct, a handle.
One decode module per carrier, 0.25 m wide, 0.5 m deep, 0.17 m tall. Fins run front to back.

**Sled, 2U.** 19-inch rack width, 0.8 m deep, two carriers side by side, one 2U fan module behind
them (four 80 mm fans in a hot-swap cage, as in every 2U server), a host board at the rear right,
the power stage at the rear left, two 400G ports and the management port on the rear face. Air path:
front grille, carrier fins, fan cage, rear. The sled is the desk unit: it stands on rubber feet or
slides on rails.

| sled | value | basis |
|---|---|---|
| decode modules | 2 | design |
| module power, each, capped, 8 slots | 81 to 87 W | measured, note 23 |
| fans, 4 x 80 mm at design point | 40 to 60 W | datasheet range for 80 mm server fans |
| host, power stage, switch share | 60 W | placeholder |
| sled power, busy | about 290 W | arithmetic |
| sled power, idle | about 110 W | measured module idle 17 to 26 W x2 plus overhead placeholder |
| airflow needed at 290 W, 20 C rise | about 25 cfm | arithmetic: Q = P / (1.08 x dT), 290 W = 990 BTU/h |
| airflow four 80 mm fans deliver | 120 to 200 cfm free air | datasheet range; margin for fins and filter |
| 7B at 8 slots each, capped | about 380 tok/s, 111 J per correct answer modules only | measured, note 23, x2 |

**Pod, 42U rack.** Sixteen sleds (32U), one 2U prefill sled (a discrete GPU on the same air path),
one 1U switch at the top, one 2U power shelf at the bottom with the busbar feed, blanking panels in
the rest. Open Compute style busbar at the rear if the row has one, else the power shelf takes AC.
Standard 42U, 600 mm wide, 1,200 mm deep, on castors, with a front door grille and a rear door grille.

| pod | value | basis |
|---|---|---|
| decode modules | 32 | arithmetic |
| power, busy | about 5.5 kW (16 x 290 W + prefill 500 W + switch 150 W + shelf losses 3%) | arithmetic, placeholders marked above |
| power, idle | about 2.3 kW | arithmetic on sled idle; the number to attack |
| airflow, busy, 20 C rise | about 480 cfm | arithmetic |
| 7B tokens per second | about 6,100 | arithmetic from the measured sled |
| 7B per correct answer, busy, overhead included | about 216 J | arithmetic (fabric/v1.py): 111.3 x pod watts / module watts; fans, host, prefill and switch are nearly as much power as the 32 modules, so overhead roughly doubles the per-answer cost at full load |
| weight | under 500 kg | estimate, unverified |

**Row.** Pods side by side in a hot-aisle containment: cold aisle in front, hot aisle contained
behind, the room's air handlers pull from the hot aisle. Ten pods is 55 kW busy, 61,000 tokens per
second on a 7B, one switch tier above. The row's fabric is a leaf switch per pod and a spine pair per
row, standard Ethernet, nothing proprietary.

## What the budget says

Fabric's V1 budget (`spliced/fabric`, `python -m fabric.v1`) passes its three checks on paper: the
fan cage moves about 68 cfm after margin against 25 needed at a 20 C rise; the pod draws 5.3 kW busy
against an 8 kW feed; idle is 1.96 kW against a 2 kW target. It also says the thing that matters:
overhead at full load is 216 against 111 joules per correct answer, nearly double, because 32 capped
modules at 85 W are only 2.7 kW of a 5.3 kW pod. Fans at 50 W per sled, the prefill GPU and the host
boards are the rest. The design's first fight is not the module; it is everything around it.

## What the roofline says about the module

Fabric's roofline (`python -m fabric.roofline`) puts a 7B Q4_0 on a 230 GB/s part at a memory bound of
about 526 tokens per second at a batch of 8. The measured capped figure is 192, 37% of that bound. So at
eight slots a capped Strix Halo is not memory bound; it is compute bound on a die held at 1,800 MHz,
which is also why the cap costs 15% of speed at eight slots where it cost 4% at one (note 23). The
headroom to the memory bound is the module's upside: a less aggressive cap, or a part with the same
memory and more compute per watt, closes it. That trade is Fabric's to find, per request mix, and a
reason the cap should be a scheduler setting and not a fixed number.

## What V1 is not

Not liquid cooled, not a custom chip, not a custom enclosure. The only custom parts are the carrier
and the sled's sheet metal, both of which a small shop makes. The couplers and docks from the cell
concept are gone; the row connects with power whips and fibre like any row.

## Software

Fabric runs on every sled's host (Spliced Linux, docs/concepts/spliced-linux.md): the sled is the
scheduling unit, the pod's leaf switch is the handoff path for prefill to decode, and the row
controller is the same image in row mode. A single sled on a desk runs the same image with one
scheduling unit.

## What would have to be true, in order of cost to find out

1. Two carriers at 85 W each under a 4 x 80 mm fan cage hold their clock at 1,800 MHz at a 35 C inlet.
   One sled, one afternoon, a thermocouple and the power log. This is the first prototype. What we
   know today, and no more: every capped run of 25 October held 1,800 MHz throughout (clock sampled
   every 0.5 s) at 59 to 88 W package power, but no die temperature was recorded for any of them;
   temperature logging began at 17:34, after the last one. The one temperature we have is the
   harvest on auto at 119 W: GPU edge 94 C in a desktop chassis. The capped runs drew less and were
   very likely cooler. So "the clock holds warm" is not yet measured. A 20 minute capped run with the
   die pre-heated by the harvest, logged, would be the evidence; it needs root and is queued for the
   morning. The carrier's fin stack is sized for that measurement, whatever it says.
2. The sled's idle at the wall is at or below 110 W. Same afternoon.
3. Sixteen sleds in a rack stay within 20 C rise at the hot-aisle face. Needs sixteen sleds.
4. Joules per correct answer at the wall for a full pod, under Fabric, against the single-module figure.

Numbers 1 and 2 cost a sled's worth of parts. Nothing here is measured yet.
