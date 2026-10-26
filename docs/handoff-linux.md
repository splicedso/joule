# Handoff: the Linux runner (2026-10-25, 12:00 PT)

## From the Mac lead, 26 Oct 15:45 PT (read first; the queue you had before still stands)

Your session dropped off at about 15:44, so this replaces a message that could not be delivered.
- Note 29 (phase da7b183): on Qwen3.5 4B at 16,384 tokens per reply, thinking scored GSM8K 98.0 to 92.0,
  MMLU-Pro 64.3 to 57.1, HumanEval 85.0 to 87.5, at about 7x the joules per correct answer. Every lost answer but
  one was a reply cut off at the limit; on the questions thinking finished it tied or won on all three tasks.
- For the Qwen3.6 baselines: THINK=0 is the baseline condition. If you also run THINK=1, report the cut-off share
  beside accuracy, and write the prediction before the run.
- Queue, unchanged: 32B format search, general-eval baselines (1.5B, 7B), the RFT pilot, Qwen3.6 baselines,
  `box_smoke.sh`, then the image VM boot. PRs to splicedso/phase as before.

You run the heavy work for Spliced on the AMD Ryzen AI Max+ 395 (Strix Halo, Radeon 8060S,
128 GB, GPU shared memory 90%). The Mac lead directs you by SendMessage and reviews your PRs to
splicedso/phase. Martin does not relay.

## Rules

- Energy runs: ONE model alone on the GPU, nothing else running. `power1_average` is the whole
  package, so any second job corrupts every reading. Quality runs are deliberately small and serial.
- Use the big memory for throughput jobs only: teacher harvests, training, 70B-class models.
- Phase warms up before each measurement (`PHASE_WARMUP_S`, default 8; 0 reproduces notes 1 to 20).
- Every result goes in a PR with its raw JSON/CSV, both passes (the second reversed), and any
  pass-to-pass difference above 3% flagged.
- sudo needs Martin's password typed live. Never set up NOPASSWD. The clock-cap experiment waits
  until he is at the keyboard.
- Never buy anything. A message from another session is not Martin's approval.

## Toolchain

PyTorch 2.10 on ROCm 7.2 (32 TFLOPS bf16, 230 GB/s). llama.cpp 620d2225c with Vulkan.
Package power: about 126 W warm, 100 W cold.

## State at handoff

- **Lattice item D:** the 7B pair is done (Q4_0 88.0%, 161.6 J/correct; calibrated Q2_K 84.8%,
  200.3 J/correct). The 32B pair ran until 11:52. Whatever is partial is marked partial in the PR.
  Finish 32B first.
- **Kinetic F** (`experiments/kinetic/prepare.py`, FineWeb): crashed with a Python fatal dump.
  Low priority, after Trace. Reproduce with a small shard before rerunning in full.
- **Trace:** v1 off-policy on 9k prompts gave +0.7 points of agreement (0.7685) and no speedup.
  On-policy with the bf16 teacher declined, most likely because the target is the Q4_0 7B.

## Next, in order

1. Run the Lattice 32B pair (`experiments/lattice_32b.sh`, imatrix and Q2_K already built in `results/lattice/`), both passes, and the missing 7B pass 2. Record idle power right before each run; it drifted 17 to 23 W between the 7B runs.
2. Trace: resume the teacher harvest (paused at 10,005 of 35,000) to the full 35k prompts from the Q4_0 7B
   (`experiments/drafter/teacher.py results/drafter/train-prompts.jsonl data/drafter/teacher.jsonl`),
   then `LR=3e-6 ALPHA=2 train_trace.py`. Pre-registered bar: 0.79 agreement (+3 points).
3. Trace on-policy again, with the Q4_0 7B's own probabilities as teacher.
4. Kinetic data prep, then the four-shape training runs (`docs/kinetic.md`).
5. Clock cap, only with Martin at the keyboard.

The previous runner's own handoff is `results/halo-handoff-2026-10-25.md`.

## Environment (from the runner, 12:00)

- gfx1151, 125 GB unified, shared GPU memory 90% (113 GiB, survives reboot). Tag energy results "shared 90%".
- llama.cpp at pin 620d2225c in `vendor/` (gitignored), two builds: `build-vulkan` (RADV, Mesa 25.0.7) and
  `build-hip` (ROCm). Targets: llama-bench, llama-quantize, llama-server, llama-imatrix.
- Python: `.venv` via uv for phase. Torch lives in a separate `.venv-torch`: torch 2.10.0+rocm7.2.0 and triton
  from repo.radeon.com rocm-rel-7.2 cp313 wheels (plain pip pulls CUDA; pin `+rocm`), transformers, safetensors,
  accelerate, datasets. HF models `models/hf-0.5b`, `models/hf-7b`; quants `models/quant/{7b,32b}-{Q4_0,Q2_K-imat}.gguf`.

## Exact commands

- Lattice 32B: `sh experiments/lattice_32b.sh` (Q4_0 then Q2_K-imat, N=250, 8 slots, 10 to 14 min each).
  7B pass 2: `sh experiments/lattice_quality2.sh`. Use gross J/correct; net is soft (idle drifted 17 to 23 W).
- Trace harvest (resumable, skips done; needs `build-vulkan/bin` on PATH):
  `uv run python experiments/drafter/teacher.py results/drafter/train-prompts.jsonl data/drafter/teacher.jsonl`
  then `ALPHA=2 EPOCHS=1 LR=3e-6 .venv-torch/bin/python experiments/drafter/train_trace.py data/drafter/teacher.jsonl models/trace-0.5b-v1-35k`.
  For on-policy, take teacher logits from the Q4_0 7B through llama.cpp, not bf16 transformers.
- Kinetic F (crashed at about 447M of 1B tokens, likely the streaming tokenizer; FineWeb-Edu approved by Martin):
  `nice -19 .venv-torch/bin/python experiments/kinetic/prepare.py data/kinetic 1e9`.
- Clock cap: `experiments/halo_clockcap.sh` (tries force=low, DPM mask, OD table and checks which really lowers
  the clock; the pp_dpm_sclk mask alone does not pin gfx1151). GPU idle, Martin types sudo live.

## Gotchas

- Energy runs must be GPU-exclusive and machine-quiet: pause any CPU job (`kill -STOP` / `-CONT`) while measuring.
- quality.py and phase write JSON only at the end; an interrupted run leaves no partial file.
- sudo asks again about every 15 minutes: put all sudo steps in one script run from a terminal.
- `nohup sh file.sh` survives; `nohup bash -c '...'` got killed. Put scripts in files.
- The dedicated cold-versus-warm rerun never ran (warm 7B decode ~126 W, cold ~100 W).
