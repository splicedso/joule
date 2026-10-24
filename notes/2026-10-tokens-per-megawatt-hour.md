# Tokens per megawatt-hour

Spliced research note 8, 24 October 2026. An analysis of published datacenter measurements, set beside our own laptop data.

Notes 1 to 7 measured inference on laptops. The AI build-out is happening in datacenters, where the question is the same one at a different scale: how many tokens does a unit of energy buy, and what decides it? This note answers it from measured wall power, not from spec sheets or estimates.

## The data, and how little of it there is

MLCommons publishes every MLPerf Inference submission with a summary file. Submitters may also measure the whole system's power at the wall, under MLPerf's power rules, and a few do. We took the v5.0 and v5.1 summary files from `mlcommons/inference_results_v5.0` and `v5.1` and kept every closed-division datacenter LLM result with measured power (`results/mlperf-llm-power.csv`).

There are two systems. In v5.0, Fujitsu's 8x NVIDIA H100 NVL server on Llama 2 70B. In v5.1, Lenovo's 8x NVIDIA B200 server on Llama 2 70B, Llama 3.1 8B and Llama 3.1 405B. Every other LLM result in those rounds reports speed only. That two systems are all the public, audited, wall-measured LLM inference energy data in the current rounds is itself a finding.

The figures are tokens per second of **output** and watts at the **wall** for the whole server, accelerators, CPUs, memory, fans and power supplies, but not the building's cooling.

## Results

| system | model | weights | scenario | tokens/s | wall watts | joules per token | billion tokens per MWh |
|---|---|---|---|---:|---:|---:|---:|
| 8x H100 NVL | Llama 2 70B | FP8 | Offline | 18,085 | 4,952 | 0.274 | 13.1 |
| 8x H100 NVL | Llama 2 70B | FP8 | Server | 16,849 | 4,994 | 0.296 | 12.1 |
| 8x B200 | Llama 2 70B | FP4 | Offline | 102,909 | 10,401 | 0.101 | 35.6 |
| 8x B200 | Llama 2 70B | FP4 | Server | 99,159 | 10,442 | 0.105 | 34.2 |
| 8x B200 | Llama 3.1 8B | FP4 | Offline | 146,960 | 9,436 | 0.064 | 56.1 |
| 8x B200 | Llama 3.1 405B | FP4 | Offline | 1,637 | 9,892 | 6.04 | 0.6 |

<!-- chart:mwh -->

## 1. A generation of hardware bought 2.7 times the tokens per joule

On the same model and task, the B200 server used 0.101 J per token and the H100 NVL server 0.274: 2.7 times fewer joules, 35.6 billion tokens per megawatt-hour against 13.1 billion. It also drew twice the power and produced 5.7 times the tokens.

This is not a clean comparison of chips, and should not be quoted as one. The H100 NVL is a 400 W card in a PCIe-style server; the B200 is NVIDIA's flagship at around 1,000 W. The H100 result used 8-bit weights and the B200 result 4-bit. The software stacks differ by a year. What it measures is what a buyer got: the best audited server of each generation, as submitted.

## 2. The efficiency comes from batching, and the roofline shows how much

Decode is memory bound (note 2). Each 8x B200 server has 8 x 7.7 TB/s of memory bandwidth. Llama 2 70B at 4 bits is at least 35 GB of weights. Decoding one sequence at a time, the server could produce at most 61.6 TB/s / 35 GB = **1,760 tokens per second**. It measured 102,909. So it must be generating, on average, at least **58 tokens for every pass over the weights**: serving 58 or more sequences at once.

That is the same lever note 1 measured on a laptop, where serving 8 requests at once cut energy per token by 72%. In the datacenter it is pulled much further. Batching is the difference between the roofline's ceiling and what these systems achieve, and it is most of why a datacenter token costs so little energy.

## 3. The small-model penalty again, at datacenter scale

On the same B200 server, per billion parameters:

| model | joules per token | millijoules per billion parameters |
|---|---:|---:|
| Llama 3.1 8B | 0.064 | 8.0 |
| Llama 2 70B | 0.101 | 1.4 |
| Llama 3.1 405B | 6.04 | 14.9 |

The 8B model costs 5.6 times as much per parameter as the 70B. Note 6 found the same shape on a laptop: narrow models leave the hardware underused, so each weight costs more. It is the same physics at a thousand times the power.

The 405B figure is the outlier, 60 times the 70B's energy per token for 5.8 times the parameters. The likely reason is the benchmark, not the model: MLPerf counts only output tokens, and the 405B task's prompts are drawn from long-context datasets (LongBench, GovReport, Ruler), so a large amount of prefill work is charged to relatively few output tokens. We have not verified the average input length, so this is a hypothesis, and the 405B figure should not be compared with the others as a cost of the model.

## 4. From the server to the building

Wall power excludes the building: cooling, power conversion and lighting, captured as PUE, the ratio of facility energy to IT energy. Google reports a fleet PUE of 1.09; the industry average in Uptime Institute's 2024 survey is 1.56. The same B200 server delivers 32.7 billion tokens per MWh of facility energy at Google's PUE and 22.8 billion at the industry average. Where a model runs changes its energy per token by 40% before any engineering.

For scale, Google's 2025 report on Gemini put a median text prompt at 0.24 Wh including idle machines and cooling, with the accelerators alone 58% of it. That figure counts prompts, not tokens, and covers a production mix, so it cannot be compared directly with these benchmark tokens. It is the only first-party production figure that splits accelerator, host, idle and facility energy, and the split is worth knowing: the accelerators are only a little over half.

## 5. A laptop next to a datacenter

On the M5 Pro, Qwen2.5 7B Q4_0 decoding one request at a time cost 1.15 J per token at the board (note 3): 151 mJ per billion parameters, about 100 times the B200 server's 1.4 on a 70B model. Most of that gap is not the chip. It is batch size (one sequence against at least 58), model size (7B against 70B, note 6) and what is counted (board DC input against the wall). A laptop serving one person is a different job from a server serving hundreds, and the comparison mostly measures that.

## What to take from this

1. The public data on datacenter LLM energy is thin: two audited systems with wall power in the latest two MLPerf rounds.
2. One hardware generation bought 2.7 times the tokens per joule, but it changed the chip, the number format and the software at once.
3. Batching is the main reason datacenter tokens are cheap. The roofline says a B200 server must be processing 58 or more sequences per weight pass to reach its measured throughput.
4. Model size, benchmark design and building efficiency each move energy per token as much as the hardware does.

## Limits

Two systems from two submitters, at different precisions and power levels. Tokens per second count output tokens only. The roofline bound uses 4 bits per weight and ignores quantization scales, so the true minimum batch is somewhat higher than 58. Wall power is what MLPerf's power rules measure; it excludes facility overhead, which we apply with published PUE figures, not measurements.

## Sources

- MLPerf Inference v5.0 and v5.1 results, `summary_results.json`: https://github.com/mlcommons/inference_results_v5.0, https://github.com/mlcommons/inference_results_v5.1
- B200 memory bandwidth (7.7 TB/s, HGX B200): https://www.nvidia.com/en-us/data-center/hgx/
- MLPerf 405B dataset sources: https://arxiv.org/pdf/2603.05692
- Google fleet PUE: https://www.datacenters.google/efficiency
- Uptime Institute 2024 global survey: https://datacenter.uptimeinstitute.com/rs/711-RIA-145/images/2024.GlobalDataCenterSurvey.Report.pdf
- Google, measuring the environmental impact of AI inference (2025): https://arxiv.org/pdf/2508.15734

## Reproduce

`results/mlperf-llm-power.csv` holds every row used. It is extracted from the two summary files by filtering for closed datacenter results with `has_power` set and a Llama model.
