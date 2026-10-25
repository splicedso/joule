# Clusters: the groundwork

Spliced builds small models for local inference today. Martin wants to design inference clusters
and the systems around them later. This page is the groundwork: what we already know that
transfers, what we do not, and the order in which to learn it without buying anything. Nothing
here is a plan to build; it is a plan to be ready to design. 25 October 2026.

Reading note with sources: `docs/clusters-reading.md`.

## What we already know that transfers

Every finding below was measured on one chip. Each one is a statement about a cluster too,
because a cluster is many of these chips plus the links between them.

- **Decode is bound by reading the weights, once per step** (note 2). At cluster scale the weights
  are spread over many chips and the read is spread with them, so the step time is set by the
  slowest chip's memory and by the links that carry the activations between chips. The roofline
  from note 2 is the right tool; it needs an interconnect term.
- **Batching is the lever** (notes 1, 10, 19): 72% less energy per token at eight requests on one
  chip, and the datacenter rows in note 8 say a B200 server has to batch 58 or more sequences per
  weight pass to reach its published tokens per joule. Clusters exist to batch.
- **Long context eats the batch** (notes 13, 16, 17): the key-value cache grows with context and
  with the batch, and it is read every step. Where the cache lives, how it moves between chips and
  whether it is shared across requests is most of cluster design.
- **Prefill and decode want different machines** (note 18): prefill is compute bound, decode is
  memory bound, and a prompt token costs a fortieth of a generated one. That asymmetry is why the
  current literature splits the two across different hardware (see the reading note).
- **Energy per correct answer, not per token** (notes 19, 22). A cluster metric that stops at tokens
  per second rewards the wrong design.
- **Speculation pays only with a confidence threshold, at low batch** (notes 9, 11, 21). At high
  batch the draft competes with the batch for the same bandwidth. Our draft models are a local
  story first.
- **Power management is a system lever** (results/halo-clockcap.md): capping a memory-bound chip's
  clock bought 37% per token for 4% of speed. At cluster scale this is per-rack power capping
  against a tokens-per-joule target, and it is where a company that measures has an edge.

## What we do not know

- Interconnect energy: joules per byte moved between chips, by link type. None of our machines has
  one. The numbers are in the literature (reading note) and not yet in our table.
- How key-value cache traffic scales with batch and context across chips, measured rather than
  modelled.
- The idle and underutilisation floor of a rack. Our single-chip idle drifts 17 to 26 W; a rack's
  idle fraction decides its real tokens per joule and nobody publishes it per request.
- Cooling and power delivery overheads: the gap between chip energy and wall energy that note 1
  found at 2x on one chip for one format, measured at rack scale.
- Anything about MoE serving. We have only measured dense models.

## The order to learn it, without buying anything

The reading note's section 8 lists five experiments two machines can run honestly, and ranks the
first two: an energy roofline of decode against batch size on all three chips at the wall, and
draft models under batching measured in joules per accepted token. Both extend what we already do
and produce curves other people can compare against. They slot in as steps 1 and 2 below; the
paper-only steps follow them.


1. **Extend the roofline with an interconnect term** (docs, no hardware). Take note 2's model,
   add a per-step transfer of activations and cache across a link of given bandwidth and latency,
   and fit it to published tensor-parallel results. Output: a page that predicts step time and
   energy for a model split across N chips, with the assumptions written down.
2. **A two-node measurement we can do**: the Strix Halo and the Mac on one network, serving one
   model split between them with llama.cpp's RPC backend over the fastest link we own. The result
   will be slow and that is the point: the energy per token at a known link bandwidth is a data point
   the roofline can be checked against. Hardware: what we have. Honest, because the note says the
   link is 10 Gb or Thunderbolt, not NVLink.
3. **Re-derive note 8 from first principles**: for each MLPerf system with wall power, split the
   published energy into weights read, cache read, interconnect and idle using the extended
   roofline, and say how much each system leaves on the table. Output: a note that names the
   dominant term per system class.
4. **Simulate disaggregated prefill and decode** with our own per-token prefill and decode costs
   (note 18) and a cache transfer cost from the literature: at what prompt length and request mix
   does splitting pay, on paper. Output: a note with a prediction that a later measurement can fail.
5. **Only then** a design document for a small cluster: node, link, cache placement, power policy,
   with every number traced to a measurement or a cited source and a cost line that says what it
   would take to build. That document is the first thing that could justify spending.

## What this means for the company

The model work and the cluster work meet at one metric, joules per correct answer, and one method,
predict first and measure. The models are what we can ship now. The clusters are what the
measurements are for later. Neither claim goes on the site until the measurement behind it exists.
