# Linux quality baseline: joules per correct answer on Strix Halo

Prediction, before the run: accuracy will match the Mac (same model, quant and
eval), energy per correct answer will be several times higher in line with the
baseline's mJ-per-token gap, and batched serving (slots 8) will cut joules per
correct answer about threefold as it did on the Mac. All three held.

GSM8K, first 250 questions, greedy, through llama-server. Qwen2.5 Q4_0, all
layers on the GPU, Vulkan, default threads (item 1b showed thread count does not
change decode power). Two passes, the second in reverse order. Chip gross is the
headline; net is shown beside it and is noisier, because idle SoC wanders 7 to
15 W run to run on this machine.

## Results (two passes, min to max)

| model | slots | accuracy | chip J/correct (gross) | net J/correct | tok/s |
|---|---:|---:|---:|---:|---:|
| 1.5B | 1 | 66.0% | 230.2 to 231.6 | 201.8 to 216.1 | 177.5 to 178.1 |
| 1.5B | 8 | 66.0 to 67.2% | 64.5 to 66.0 | 60.0 to 61.8 | 632 to 664 |
| 7B | 1 | 88.8% | 607.1 to 610.9 | 567.7 to 568.5 | 47.6 to 47.8 |
| 7B | 8 | 88.0 to 88.8% | 152.3 to 161.0 | 142.6 to 151.5 | 209 to 212 |

Accuracy matches the Mac baseline exactly (Mac: 1.5B 66%, 7B 88%), which is the
check that the harness measures the same thing on both machines.

## This machine against the Mac (chip gross J per correct answer)

| model | slots | Mac M5 Pro | Strix Halo | ratio |
|---|---:|---:|---:|---:|
| 1.5B | 1 | 40 | 231 | 5.8x |
| 1.5B | 8 | 13.8 | 65 | 4.7x |
| 7B | 1 | 102 | 609 | 6.0x |
| 7B | 8 | 35 | 157 | 4.5x |

The Halo pays about 5 to 6 times the chip energy per correct answer. That tracks
the baseline's mJ-per-token gap, so it is a property of the hardware, not of the
eval. Batching pays more here than on the Mac: slots 8 cuts joules per correct
answer 3.5 to 3.9 times, against about 2.9 times on the Mac, because the GPU's
throughput scales further with the batch (7B 48 to 212 tok/s, 4.4x).

## Why the chip energy is high: the clock does not idle under decode

The baseline's open question was why 7B decode draws about 100 W while bound on
memory. The shader clock answers it. Measured on the 7B (`results/halo-gpuclock.json`):

| phase | GPU clock | % of max | SoC W |
|---|---:|---:|---:|
| idle | 785 MHz | 27% | 13.6 |
| decode (memory bound) | 2900 MHz | 100% | 105 |
| prefill (compute bound) | 2892 MHz | 100% | 143 |

The clock sits at its 2900 MHz ceiling during decode, the same as during
compute-bound prefill, though decode runs at a quarter of prefill's throughput.
The GPU runs flat out while waiting on memory. A decode-time clock or power cap
is a lead for later; it would need a system setting, so it is not touched here.

## Limits

- One machine, one quant, GSM8K only. Net J per correct answer is noisier than
  gross because of the idle wander; gross is the number to compare.
- 7B slots 8 has the widest spread (152 to 161 J, about 6%), from batching and
  idle variance together.
