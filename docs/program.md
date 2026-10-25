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
| AMD Ryzen AI Max+ 395 (Strix Halo), Linux | 125 GB unified | heavy work: training, teacher data, 70B-class models |
| Apple M5 Pro, macOS | 24 GB | light measurement, analysis, writing; jobs kept to a few GB |
| RTX 5070 Ti laptop, Windows | 12 GB GPU | paused |

## Our models

Each family has one job, one target number, and a page that says whether it hit it.

### Trace: draft models that trace a larger model

Small models trained to predict one specific large model, for speculative decoding.

- **Trace-0.5B v0** (note 15): sequence-level distillation from Qwen2.5 7B. Held-out loss 6% lower than stock, acceptance about 3% higher. Too small a gain to ship.
- A logit-distillation attempt on 3,400 prompts overfit: its top-1 agreement with the 7B was 75.4% held out, against 76.0% for the stock model.
- **Trace v1, target:** top-1 agreement with the target at least 3 points above the stock draft on held-out prompts, and a measured speedup with lower energy per correct answer. Planned changes: 10 times more prompts (about 35,000), the teacher's distribution streamed from disk, and training on Linux. Then a Trace for a 72B target, where a draft's speedup matters most.

### Lattice: models that keep their answers at fewer bits

Quantization-aware fine-tuning, so a model holds its accuracy in the low-bit formats our notes found cheapest.

- **Lattice v1, target:** Qwen2.5 1.5B at 3 bits or below per weight, with GSM8K accuracy within 1 point of Q4_0, and lower joules per correct answer than Q4_0.

### Kinetic: a small model shaped by energy

A model trained from scratch, its width, depth and vocabulary chosen from our measurements of what each costs per token on real hardware.

- Starts once the quality harness and Trace v1 are done. Target: beat a same-size Qwen on joules per correct answer for a narrow task.

## Order

1. Quality harness: joules per correct answer.
2. Linux baseline, and the harness on Linux.
3. Trace v1 on Linux.
4. Lattice v1.
5. Kinetic.

Models are published on the GitHub releases of this repository until the lab has a Hugging Face account.
