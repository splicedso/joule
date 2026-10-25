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
- **Trace v1, status (2026-10-25):** 35,000 prompts prepared, the 7B's top-20 distribution being recorded on the Strix Halo (about 2,500 prompts an hour); training starts at about 8,000. The PyTorch trainer reproduces the stock model's held-out agreement on both machines (0.7606 Mac, 0.7616 Halo).
- **Trace v1, target:** top-1 agreement with the target at least 3 points above the stock draft on held-out prompts, and a measured speedup with lower energy per correct answer. Planned changes: 10 times more prompts (about 35,000), the teacher's distribution streamed from disk, and training on Linux. Then a Trace for a 72B target, where a draft's speedup matters most.

### Lattice: models that keep their answers at fewer bits

Quantization-aware fine-tuning, so a model holds its accuracy in the low-bit formats our notes found cheapest.

- **Baseline (Mac, GSM8K-250, 2026-10-25):** Qwen2.5 1.5B scores 21% at Q2_K, 66% at Q3_K_M and Q4_0, and 70 to 72% from Q5_K_M to F16. Standard quantization holds at about 3.9 bits and collapses below it. The energy half of that run is not usable (passes disagreed by up to 24%, because the machine was in use), so it is to be rerun idle.
- **Lattice v0 (note 20):** an importance matrix calibrated on GSM8K-train lifts Q2_K from 21% to 42% at the same size (37% with general-text calibration). Joules per correct answer fall 40%, but Q4_0 is still cheaper per answer on the M5 Pro, because a 2-bit token costs more energy there. Next: 7B and 32B on the Strix Halo, where memory dominates.
- **Lattice v1, target:** a Qwen2.5 1.5B at Q2_K size (about 3.3 bits per weight) that scores at least 60% where stock Q2_K scores 21%, at lower joules per correct answer than Q4_0. Method: quantization-aware fine-tuning on the Linux machine.

### Kinetic: a small model shaped by energy

A model trained from scratch, its width, depth and vocabulary chosen from our measurements of what each costs per token on real hardware.

- Plan: `docs/kinetic.md`. Four shapes at about 50M parameters (24x512, 12x720, 6x1024, 4x1260, all 71.6 to 74.1M non-embedding), the same 1B tokens, trained on the Strix Halo, measured on both machines. Starts after Trace v1.

## Order

1. Quality harness: joules per correct answer.
2. Linux baseline, and the harness on Linux.
3. Trace v1 on Linux.
4. Lattice v1.
5. Kinetic.

Models are published on the GitHub releases of this repository until the lab has a Hugging Face account.
