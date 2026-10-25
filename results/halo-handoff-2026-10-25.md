# Strix Halo session handoff, 2026-10-25

State of the Linux (AMD Ryzen AI Max+ 395, gfx1151, 125 GB unified, shared GPU memory 90% / 113 GiB) work at the noon PT stop.

## Landed (merged or open PRs)
- #9 Linux baseline (energy/token, Qwen2.5 Q4_0) — merged
- #10 7B decode thread sweep (pp_dpm_sclk not CPU busy-wait) — merged
- #11 Quality baseline / note 19 (joules per correct answer) — merged
- #12 PyTorch ROCm on gfx1151 (32 TFLOPS bf16, ~230 GB/s) — merged
- #13 measure.py GPU warm-up (now env-configurable PHASE_WARMUP_S on main) — merged
- #14 on-policy vocab fix (0.5B 151936 vs 7B 152064) — merged
- #15 Trace v1 training curves + stock-vs-v1 eval — open
- (this) Lattice D + handoff

## Trace v1 (results/drafter/trace-v1.md)
No method cleared the +3-point agreement bar over stock 0.7616: off-policy ALPHA=2 flat; off-policy LR 3e-6 best at 0.7685 (+0.7); on-policy TVD declined (bf16-teacher vs Q4_0-target mismatch). Eval: speculative decoding ~1.5x faster / ~34% less chip energy than plain here, but v1 vs stock is a wash. Next lever: retrain on the full 35k teacher data at LR 3e-6.

## Lattice D (this PR, results/lattice-halo-*.json)
7B, GSM8K-250, slots 8, chip energy:
- Q4_0: 88.0%, 161.6 J/correct, 226 tok/s, 617 mJ/tok
- Q2_K-imat (GSM8K 1500-problem calib): 84.8%, 200.3 J/correct, 188 tok/s, 717 mJ/tok
At 7B, Q4_0 wins on every axis (note 20's result holds): calibration recovers most 2-bit accuracy (84.8%, not ~21%) but 2-bit still costs more energy per correct answer. Only pass 1 of the 7B pair landed (pass 2 was cut for time). 32B: did NOT complete a pass before the stop — 32B Q4_0 was ~14 min in and quality.py writes its JSON only at the end, so no 32B number landed. The 32B comparison (the actual open question: does 2-bit pay on the big memory-bound model?) is the first thing to finish next session. imatrices committed in results/lattice/imatrix-{7b,32b}-gsm8k.gguf; models/quant/{7b,32b}-Q2_K-imat.gguf and -Q4_0.gguf exist (gitignored).

## Running / paused at stop
- Teacher harvest (A): paused at ~10,005 prompts of 35,000. Resume: `PATH with vendor/llama.cpp/build-vulkan/bin; uv run python experiments/drafter/teacher.py results/drafter/train-prompts.jsonl data/drafter/teacher.jsonl` (resumable, skips done). Output data/drafter/teacher.jsonl (gitignored).
- Lattice 32B quality: STOPPED incomplete at the noon wind-down (no JSON written). Resume both: `experiments/lattice_32b.sh` (runs 32B Q4_0 then Q2_K-imat, N=250 slots 8), or directly `uv run python experiments/quality.py models/quant/32b-{Q4_0,Q2_K-imat}.gguf results/lattice-halo-32b-<q>-pass1.json 250 8`. Each 32B run is ~10-14 min. Also finish 7B pass 2 for spreads: `experiments/lattice_quality2.sh` (reruns all, skips nothing).
- Kinetic F (experiments/kinetic/prepare.py): CRASHED (~447M/1B train tokens; Python fatal dump in the log, cause not yet diagnosed — likely the streaming tokenizer). Rerun: `nice -n 19 .venv-torch/bin/python experiments/kinetic/prepare.py data/kinetic 1e9`. Needs `datasets` (installed in .venv-torch). Outputs data/kinetic/{valid,train}.bin (gitignored).

## Blocked
- Clock-cap (B): the pp_dpm_sclk mask does not pin the gfx1151 clock (v1). The v2 sweep (experiments/halo_clockcap.sh: tries force=low, DPM mask, OD table, verifies which lowers the clock, then measures 7B prefill/decode, restores + reads back) needs sudo, which still requires a live password on this box (no passwordless; not changed — security setting). Run it when Martin can enter the password in a terminal.

## Environment notes
- Backends: Vulkan (RADV, Mesa 25.0.7) and HIP/ROCm 10.0 both work at pin 620d2225c (no bump). llama.cpp in vendor/ (gitignored): build-vulkan, build-hip.
- Torch: .venv-torch (torch 2.10.0+rocm7.2.0 + triton + transformers 5.20.2 + datasets), from repo.radeon.com rocm-rel-7.2 cp313 wheels.
- All energy results are "shared 90%" (113 GiB). Cold-vs-warm: 7B decode reads ~100 W cold, ~126 W warm at the same tok/s; warm-up now in measure.py. The dedicated warm-vs-cold rerun did not run before the stop.
