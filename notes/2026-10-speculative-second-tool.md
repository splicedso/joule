# Same result, second tool: speculative decoding through llama-server

Spliced research note 11, 24 October 2026. Apple M5 Pro, 24 GB, llama.cpp build 11669. Target Qwen2.5 7B Q4_0, draft Qwen2.5 0.5B Q4_0.

Notes 7 and 9 measured speculative decoding with `llama-speculative-simple`, an example program in llama.cpp. Real deployments use `llama-server`, a different program with its own scheduling, batching and request handling. A result that holds in one tool might be a property of that tool. This note repeats both experiments through `llama-server`, and records why the same experiment could not be run on our Windows laptop.

## Method

`experiments/speculative_server.py`. Every condition, plain decoding included, runs through `llama-server`: one server process per condition, warmed up with a short request before measurement, then the three prompts of note 7 (new code, prose, an edit), 384 generated tokens each, greedy. The server reports its own decode time and the numbers of drafted and accepted tokens; the measurement window is aligned to that decode time as in note 7. Chip energy only, for the reason note 7 gives. Three repetitions per condition in a shuffled order. Two sessions: the strategies of note 7, then the thresholds of note 9.

Plain decoding repeated within 2% to 7% in the first session and within 17% to 20% in the second, so the second session's percentages are less precise. Every comparison is against plain decoding within the same session.

## Results

Chip energy relative to plain decoding, with the same figures from notes 7 and 9 (which used `llama-speculative-simple`):

| prompt | strategy | accepted | speed | energy, server | energy, note 7 or 9 |
|---|---|---:|---:|---:|---:|
| code | draft-2 | 81% | 1.50x | 0.97 | 1.06 |
| code | draft-4 | 71% | 1.80x | 0.76 | 0.83 |
| code | draft-8 | 53% | 1.37x | 0.97 | 1.05 |
| code | draft-16 | 33% | 0.76x | 1.91 | 2.15 |
| prose | draft-2 | 61% | 1.27x | 1.12 | 1.24 |
| prose | draft-4 | 45% | 1.32x | 1.01 | 1.10 |
| prose | draft-8 | 28% | 0.86x | 1.52 | 1.70 |
| prose | draft-16 | 14% | 0.40x | 3.60 | 3.95 |
| edit | draft-4 | 99% | 2.24x | 0.62 | 0.64 |
| edit | draft-8 | 97% | 2.24x | 0.60 | 0.62 |
| edit | ngram | 100% | 5.59x | 0.27 | 0.32 |
| code | draft-8, p 0.5 | 66% | 1.49x | 0.92 | 0.84 |
| prose | draft-8, p 0.5 | 68% | 1.25x | 1.04 | 0.99 |
| edit | draft-8, p 0.5 | 97% | 2.25x | 0.62 | 0.61 |
| prose | draft-16, p 0.8 | 94% | 1.05x | 1.11 | 1.09 |

## 1. Every finding holds in the second tool

- **Faster can still cost more.** On prose, drafting 2 tokens is 1.27 times faster than plain decoding and costs 12% more energy.
- **Long drafts on unpredictable text are still the worst case**: drafting 16 tokens on prose costs 3.60 times plain decoding's energy, at 0.40 times its speed.
- **Copying from the context still wins on edits**: 5.59 times the speed at 27% of the energy.
- **A threshold of 0.5 still removes the penalty**: prose is within 4% of plain decoding's energy at 1.25 times the speed, and code and edits save energy.

The acceptance rates are almost identical between the two tools (for example 14%, 28%, 45% and 61% on prose here against 14%, 28%, 45% and 60% in note 7), which is expected: the draft model and target are the same, and greedy decoding makes the same guesses.

## 2. The server is slightly cheaper relative to plain decoding

In all 11 rows from the first session, the server's energy ratio is lower than the example program's, by 3% to 16%. The four threshold rows, from the noisier second session, land within 1 to 8 points of note 9 in the other direction, inside that session's spread. Both measure plain decoding through the same program as their speculative conditions, so the ratios are internally consistent; the difference is in how each program handles speculation. One plausible cause is that the server's request scheduling overlaps draft and verification work better, but we have not measured that. The direction of every finding is the same; the size is slightly more favourable to speculation in the server.

## 3. Why there is no Windows number

The Windows laptop of notes 4 and 10 could not run this experiment. Windows Smart App Control, a reputation-based security policy available on new Windows 11 installs, blocks the unsigned library `mtmd.dll` that `llama-server` loads at start-up (code-integrity events 3033 and 3077, load error 4551). The official llama.cpp release builds are not code-signed, so any fresh download is blocked the same way, while the tools used in notes 4 and 10 (`llama-bench`, `llama-quantize`, `llama-completion`) do not load that library and run. Turning the policy off needs administrator rights and cannot be undone without reinstalling, so we did not. A measurement is not worth weakening a machine's security, and that machine's next study uses the tools it can run.

This is a practical finding for anyone deploying local inference on Windows: on machines with Smart App Control, unsigned llama.cpp server builds will not start.

## Limits

One machine, one model pair, three prompts, greedy decoding. The second session was noisy (plain decoding varied by up to 20% between repeats). The cause of the server's slightly better ratios is not established.

## Reproduce

```bash
uv run python experiments/speculative_server.py results/speculative-server-mac.json
uv run python experiments/speculative_server.py results/speculative-pmin-server-mac.json \
  plain,draft-8,draft-8-p0.5,draft-8-p0.8,draft-8-p0.95,draft-16,draft-16-p0.8
```

Raw results: `results/speculative-server-mac.json`, `results/speculative-pmin-server-mac.json`, `results/summary-speculative-server-mac.json`, `results/summary-speculative-pmin-server-mac.json`.
