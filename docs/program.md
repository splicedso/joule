# The Spliced research program

From October 2026, fewer notes and better ones, and our own models.

## The quality bar

Every note from now on:

1. **States its prediction before the run.** The note says whether the prediction held.
2. **Measures quality as well as cost.** Energy per token alone rewards a model that answers badly. The headline metric is **joules per correct answer** on a fixed evaluation (`experiments/quality.py`), next to energy per token.
3. **Runs on two machines where it can,** with the hardware difference stated.
4. **Reports the spread of every cell** and puts the repeat pass in reverse order.

A note that can't meet these waits.

## Machines

| machine | memory | role |
|---|---|---|
| AMD Ryzen AI Max+ 395 (Strix Halo), Linux | 128 GB unified, 113 GiB to the GPU | heavy work: training (PyTorch on ROCm 7.2, 32 TFLOPS bf16), teacher data, 32B to 70B models |
| Apple M5 Pro, macOS | 24 GB | light measurement, analysis, writing; jobs kept to a few GB |
| RTX 5070 Ti laptop, Windows | 12 GB GPU | paused |

## The laptop bar

Every model we build is judged by one question: does it make Foundry, our local app, better on an
ordinary laptop? A model ships in Foundry only when it beats Foundry's current default, measured by
`experiments/quality.py` on the M5 Pro and the Strix Halo, on both:

- **joules per correct answer**, at 1 and 8 requests at once, and
- **accuracy**, within 1 point or better.

Today's default, from our own measurements: Qwen2.5 1.5B and 7B Instruct at Q4_0 (note 20), with
speculative decoding on machines where it saves energy (note 21). Trace, Lattice and Kinetic each
have to beat that, not the stock model in isolation.

## Our models

Each family has one job, one target number, and a page that says whether it hit it.

### Trace: draft models that trace a larger model

Small models trained to predict one specific large model, for speculative decoding.

- **Trace-0.5B v0** (note 15): sequence-level distillation from Qwen2.5 7B. Held-out loss 6% lower than stock, acceptance about 3% higher. Too small a gain to ship.
- A logit-distillation attempt on 3,400 prompts overfit: its top-1 agreement with the 7B was 75.4% held out, against 76.0% for the stock model.
- **Trace v1, status (2026-10-25, 14:30):** off-policy on 9,000 prompts gave +0.7 points of agreement (0.7685) and no speedup (note 21); on-policy with a bf16 teacher declined. The harvest of the Q4_0 7B's top-20 distribution is at 10,000 of 35,180 prompts on the Strix Halo (paused for the capped run, resumable); the retrain at LR 3e-6, ALPHA=2 follows it, against the 0.79 bar. The PyTorch trainer reproduces the stock model's held-out agreement on both machines (0.7606 Mac, 0.7616 Halo).
- **Trace v1, target:** top-1 agreement with the target at least 3 points above the stock draft on held-out prompts, and a measured speedup with lower energy per correct answer. Planned changes: 10 times more prompts (about 35,000), the teacher's distribution streamed from disk, and training on Linux. Then a Trace for a 72B target, where a draft's speedup matters most.

### Lattice: models that keep their answers at fewer bits

Quantization-aware fine-tuning, so a model holds its accuracy in the low-bit formats our notes found cheapest.

- **Baseline (Mac, GSM8K-250, 2026-10-25):** Qwen2.5 1.5B scores 21% at Q2_K, 66% at Q3_K_M and Q4_0, and 70 to 72% from Q5_K_M to F16. Standard quantization holds at about 3.9 bits and collapses below it. The energy half of that run is not usable (passes disagreed by up to 24%, because the machine was in use), so it is to be rerun idle.
- **Lattice item D (note 22, 2026-10-25):** on the Strix Halo, at 32B the GSM8K-calibrated Q2_K costs 473.7 J per correct answer at 95.6% against Q4_0's 563.6 at 94.8%: 16% less, with 2-bit tokens 10% cheaper and 9% faster. At 7B Q4_0 is still 21% cheaper. The crossover is between 7B and 32B on that machine: fewer bits pay once memory traffic dominates the token. The pre-registered margin ("under 15%") was missed.
- **Clock cap (results/halo-clockcap.md, 2026-10-25):** capping the Strix Halo's shader clock at 1,800 MHz through the OD table cuts 7B Q4_0 decode energy per token 37% at 4% less speed (42% at 1,200 MHz, 8% slower); prefill loses a third of its speed. Per correct answer under the cap is being measured now (7B Q4_0, 32B Q4_0, 32B calibrated Q2_K, 8 slots).
- **Lattice v0 (note 20):** an importance matrix calibrated on GSM8K-train lifts Q2_K from 21% to 42% at the same size (37% with general-text calibration). Joules per correct answer fall 40%, but Q4_0 is still cheaper per answer on the M5 Pro, because a 2-bit token costs more energy there. Next: 7B and 32B on the Strix Halo, where memory dominates.
- **Lattice v1, target:** a Qwen2.5 1.5B at Q2_K size (about 3.3 bits per weight) that scores at least 60% where stock Q2_K scores 21%, at lower joules per correct answer than Q4_0. Method: quantization-aware fine-tuning on the Linux machine.

### Shape study (was Kinetic; not a model family)

A model trained from scratch, its width, depth and vocabulary chosen from our measurements of what each costs per token on real hardware.

- 2026-10-25, 16:30, Martin: two model families, not three. The four-shape runs stay as a research study of what width, depth and vocabulary cost per token (a note, not a release), last in the queue after Lattice v1. A third family is named only when Trace and Lattice clear their bars, and it would have to be something worth the name.
- Data (2026-10-25): 1B tokens of FineWeb-Edu, complete and verified deterministic (`results/kinetic-data.md`); the trainer runs on ROCm.
- Plan: `docs/kinetic.md`. Four shapes at about 50M parameters (24x512, 12x720, 6x1024, 4x1260, all 71.6 to 74.1M non-embedding), the same 1B tokens, trained on the Strix Halo, measured on both machines. Starts after Trace v1.

## Systems

The measurements add up to a recipe for running a model on one machine (`docs/local-systems.md`,
the site's Systems page): Q4_0 below 32B, the largest model that leaves room to batch, as many
requests at once as memory allows, the prefix cached, a draft with a 0.5 confidence threshold, the
shader clock capped where the platform allows. Foundry is that recipe as an app. Clusters are
groundwork only (`docs/clusters-groundwork.md`): nothing is claimed until measured.

## Models roadmap (2026-10-25, 16:25)

In flight on the Strix Halo: the Trace v1 harvest to 35,180 prompts (about 12 h), then the retrain and
its eval against the 0.79 bar. Two families, Trace and Lattice; the shape study runs last. Being prepared
beside the harvest: Lattice v1, quantization-aware fine-tuning of the 1.5B to a Q2_K-shaped grid, bar
60% on GSM8K-250 at Q2_K size and cheaper per correct answer than Q4_0 on the M5 Pro; and a Trace for a
72B target, which starts only if the 7B retrain clears its bar. Every run has its prediction committed
first. The Mac stays light: evaluation of small artefacts, writing, and the site.

## Frontier, open source, and what two people can do

Martin's aim (25 October): the next Etched and Anthropic, a hardware company and a model company,
open-source models now, a closed frontier-class model as a possibility. What that means in practice:

- **What we can train today** is small: 0.5B to 1.5B on one Strix Halo, which is Trace and Lattice. A
  frontier-class model needs thousands of accelerators for months. No plan here pretends otherwise.
- **The path that is real:** be the group whose small models are the best per joule on the hardware
  people own, measured and published; then the group whose cells serve the best open large models at
  the lowest cost per correct answer; then, with revenue and cells, train larger models on our own
  cells, where the training cost per token is the number we already know how to measure. Each step is
  a measurement before it is a claim.
- **Open or closed:** everything measured is open. Model weights are open while the models are small
  and the point is credibility. A closed model is a business decision for when there is a model worth
  closing; there is no work on one and the site says nothing about one.
- **Frontier-class on the site:** never, until a model exists that can be measured against one.

## Fabric: the cluster software

`spliced/fabric` (local for now) is the control software for the designs and the simulator that costs
them from our measurements: a scheduler that keeps decode modules batched and splits prefill from
decode, a prefix cache with handoff accounting over a link, a clock policy, cells and rows with shared
trunks and a sleep policy, and a report that prints joules per correct answer with the share of every
joule that is derived rather than measured. The same scheduler is meant to drive llama-server on the
two machines we own (`fabric/testbed.py`, not yet written), which is how the link and overhead numbers
stop being literature and placeholders. Nothing Fabric prints is a result until that testbed runs.

## Order

1. Quality harness: joules per correct answer.
2. Linux baseline, and the harness on Linux.
3. Trace v1 on Linux.
4. Lattice v1.
5. Kinetic.

## Open and for profit

Spliced is a for-profit company. Phase, the notes and the raw data are public under Apache-2.0
(this repository). The models we release are open: weights and the training recipe, under the same
licence as the base model they come from. Foundry is a private repository for now. A closed-source
model is a possibility the company has not started on and makes no claim about; nothing on the site
says one exists.

Models are published on the GitHub releases of this repository until the company has a Hugging Face account.
