# A local inference system, by the measurements

How to run a model well on one machine, decided by what we have measured rather than by
spec sheets. This is the recipe Foundry follows and the baseline every Spliced model has to
beat. Each decision cites the note that measured it. Where a decision is still provisional, it
says so. 25 October 2026.

## Summary

Run a 7B model at Q4_0, serve several requests at once, draft with a small model only where a
confidence threshold keeps the guesses good, cache the prompt prefix, and cap the shader clock on
machines that allow it. On the hardware we own, that recipe costs a third to a half of the naive
one per correct answer. Two-bit formats pay only from about 32B up.

## Decisions

**Format: Q4_0, unless the model is 32B or larger.** Q4_0 is the cheapest format per token at
every model width we measured, on the M5 Pro, the RTX 5070 Ti Laptop GPU and the Strix Halo
(notes 1, 4, 6). Below 4 bits the token gets more expensive, not cheaper, because unpacking the
format costs more than the bytes it saves (note 5): on a 7B, a calibrated 2-bit token costs 18%
more chip energy than a 4-bit one and Q4_0 is 21% cheaper per correct answer (note 22). At 32B
the sign flips: calibrated Q2_K costs 16% less per correct answer at equal accuracy. The
crossover sits between 7B and 32B on the Strix Halo and is machine dependent.

**Model size: the largest that fits with room to batch.** Per correct answer, a 7B serving eight
requests beats a 1.5B serving one, on both machines (note 19). Accuracy buys more than speed
loses. A 1.5B is the right choice only when memory forbids the 7B or when one request at a time
is all there is.

**Concurrency: as many requests at once as memory allows.** Eight requests at once cut energy
per token by 72% on the M5 Pro (note 1) and the second request alone saves 43% on a GPU that is
already at its ceiling at batch 1 (note 10). Decode is bound by reading the weights once per
step; every extra sequence in the step rides that read for free until memory or compute runs
out. For a single user this means batching their own tool calls and sub-requests, not waiting
for another user.

**Prompt handling: cache the prefix.** A prompt token costs about a fortieth of a generated one
(note 12), so short prompts are nearly free. Long ones are not: at an 8,000-token prompt,
prefill is 40% of a request's energy (note 18). Caching a shared prefix (a system prompt, a
document) removes exactly that cost. A long context also raises the cost of every decoded
token, because the key-value cache is read every step; an 8-bit cache does not win that back
(notes 13, 16, 17).

**Speculative decoding: on, with a confidence threshold, with the stock draft.** Drafting without
a threshold can be faster and more expensive at once; 16-token drafts on prose cost 3.6 to 3.95
times plain decoding (notes 7, 11). With the draft's confidence threshold at about 0.5 the energy
penalty disappears on every task tested and prose gets a free 1.3 times speed-up (note 9), and
the result holds in llama-server, the program deployments use (note 11). On the Strix Halo the
same setting cuts chip energy per token by a third (note 21). Our own Trace v1 draft raised
agreement by 0.7 points and bought nothing; the stock 0.5B draft is the one to ship until a
Trace clears the 3-point bar.

**Clock: cap the shader clock where the platform allows it.** On the Strix Halo, an 1,800 MHz cap
through the OD table cuts 7B decode energy per token 37% at 4% less speed, and 42% at 8% less
at 1,200 MHz (results/halo-clockcap.md). Per correct answer, the first pass of the capped
quality run shows 15 to 28% less energy with accuracy within a point; the two-pass result is in
note 23 when it lands. Decode is memory bound, so the shader clock buys little speed and costs
much power. Prefill is compute bound and loses a third of its speed under the cap, so a system
that does long prefill should lift the cap for it. This needs root and is Linux only so far.

**Measure warm.** A cold first measurement understates energy per token by 20 to 30%, because
the package draws about a quarter more once warm (Linux handoff, warm 126 W against cold 100 W
on the 7B). Every Phase run warms up first; every number here is a warm number.

**Idle is the floor.** The Strix Halo idles at 17 to 26 W across an afternoon; at a fifth of the
speed, under force-low, that floor is half the reading (results/halo-clockcap.md). A system that
runs slowly does not save energy per token. Finish fast, then idle.

## The reference configuration

| machine | model | format | slots | draft | clock | expected |
|---|---|---|---:|---|---|---|
| Apple M5 Pro, 24 GB | Qwen2.5 7B | Q4_0 | 8 | 0.5B, p-min 0.5 | none available | 14.8 J per correct answer at 1.5B scale (note 20); 7B at 8 slots beats it (note 19) |
| AMD Ryzen AI Max+ 395 | Qwen2.5 7B | Q4_0 | 8 | 0.5B, p-min 0.5 | OD 1,800 MHz | 153.8 J per correct answer on auto (note 22); about 110 capped (note 23, pass 1) |
| AMD Ryzen AI Max+ 395 | Qwen2.5 32B | Q2_K, calibrated | 8 | none measured | OD 1,800 MHz | 473.7 J per correct answer on auto (note 22); about 403 capped (note 23, pass 1) |

Foundry today ships the first row without the clock cap and with the draft off by default
(Fast mode turns it on). The gaps between Foundry and this table are the next things to build.

## Not yet measured

- Joules per correct answer with the draft on, at 8 slots. Notes 9 and 11 are per token at batch 1;
  batching may make the draft useless (the draft steals the bandwidth the batch would use).
- The clock cap on Apple silicon and on the RTX laptop. No control is known for the first; the second
  has one and has not been tried.
- Whether an 8-slot 7B beats a 1-slot 32B per correct answer on the Strix Halo. Both are measured
  alone; the comparison is not.
- Any of this on a model family other than Qwen2.5.
