# Void runs

Kept for the record, never cited as results.

- `spec-batch-mac-7b-draft-no-spec-type.json` (2026-10-26 01:37): `-md` without `--spec-type`; the draft never drafted.
- `width-granite-run{1,2}.json`, `summary-width-granite.json` (2026-10-26 10:03 to 10:23): the machine was not idle.
  Idle chip power 9.7 and 11.2 W against 0.6 W in note 6's session, from a Docker container (`node:22-bookworm`,
  restarted every few seconds, about 180% CPU) belonging to another project. The same-session Qwen2.5 3B reference
  read 23 to 45% above note 6 on the board and 29 to 77% on the chip, at the same speed. Both `phase` and
  `decode_batch_energy.py` now refuse to measure on macOS when idle chip power is above 3 W.
