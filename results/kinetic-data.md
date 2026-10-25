# Kinetic data: the 1B-token stream is complete, valid and deterministic

`experiments/kinetic/prepare.py` (FineWeb-Edu sample-10BT, Qwen2.5 tokenizer, uint32) was reported crashed at
"about 447M of 1B tokens" with a Python fatal dump. Checked 2026-10-25, 14:08 PDT, on the Strix Halo:

## Full pass over both files

| file | tokens | min id | max id | ids >= 151,936 | id 0 | end-of-text (documents) | mean document |
|---|---:|---:|---:|---:|---:|---:|---:|
| `data/kinetic/valid.bin` | 10,000,000 | 0 | 151,643 | 0 | 2,121 | 9,640 | 1,037 tokens |
| `data/kinetic/train.bin` | 1,000,000,000 | 0 | 151,643 | 0 | 249,840 | 974,500 | 1,026 tokens |

train.bin is exactly 4,000,000,000 bytes, which is the full 1e9 tokens: prepare.py appends with `tofile`,
so a crash mid-stream would have left a shorter file. Every id is inside Qwen2.5's vocabulary (151,936), the
maximum being the end-of-text token itself. Id 0 ("!") occurs at 0.025%, an ordinary token. Document
boundaries are evenly spread: the end-of-text density is 0.87 to 1.09 per thousand tokens at seven offsets
across the file (0, 250M, 447M, 448M, 500M, 750M, 999M).

## Reproduction on a small shard

`prepare.py <scratch> 2e6` (10M validation tokens, 2M training tokens, nice 19, alongside the Trace harvest):

- `valid.bin` byte-identical to `data/kinetic/valid.bin`; the first 2M tokens of `train.bin` byte-identical to
  the full file's. The stream is deterministic, so every shape trains on the same tokens in the same order.
- The crash reproduces and is at interpreter exit, after every token is written: `Fatal Python error:
  PyGILState_Release: thread state ... must be current when releasing`, `Python runtime state: finalizing`,
  exit code 134. It comes from the streaming dataset's background download thread (huggingface_hub retrying a
  GET on a closed socket while the interpreter finalizes). "447M" in the previous session was simply the last
  progress line it had read; the file was already complete at 10:56.

## Fix

prepare.py now flushes, closes both files and leaves with `os._exit(0)`, so it does not run the finalizer that
aborts. Verified on a 1e5-token shard: exit code 0, `valid.bin` identical again. No data was regenerated; the
files on disk from 10:56 are the ones the four shapes train on.

Trainer check: `experiments/kinetic/train.py wide` ran 10 steps on ROCm (gfx1151, torch 2.10+rocm7.2),
72.4M non-embedding parameters, loss 11.95 at step 10 (ln 151,936 is 11.93), saved in Hugging Face format.
The four-shape runs (`docs/kinetic.md`) are queued after the Trace retrain.
