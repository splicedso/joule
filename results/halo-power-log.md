# Package power log: first look (2026-10-25, 14:37 to 16:08 PDT)

`experiments/power_log.sh` samples `power1_average`, the active shader clock and GPU busy every 10 s into
`results/halo-power-log.csv` (memory, fabric and display clocks, display power state and load average added
at 15:59). Why: idle drifted 16.6 to 25.9 W across the Lattice D runs and every net-of-idle figure carries it.
This is the first 90 minutes; the full page waits for a day of samples.

## What the first 544 samples say

- Idle (GPU busy under 5%, 16 samples between runs): 6.1 to 21.1 W, mean 16.1 W. The 6 W readings all fall in
  one stretch, 15:29 to 15:44.
- That stretch is the flagged one in note 23: the 32B calibrated Q2_K pass 2 ran at 64 to 67 W for its first 15
  minutes at the same 1,785 MHz shader clock and 97 to 98% GPU busy as its pass 1 (which ran at 88 W), then at
  75 to 87 W from 15:45 to its end. The shader clock did not move; something else in the package did. The
  display was on at 15:59 when the logger started recording it; whether it was off from 15:29 to 15:44 is
  not known, which is why the display state is now logged.
- Idle right before each run, from the run scripts' own 10 s samples: capped runs 18.2, 10.6, 17.5, 16.0, 6.3,
  19.2 W (in run order); the 7B auto re-run 16.9 and 21.1 W. The lowest two came after the two longest runs.
- Under load the package draws 83 to 88 W at the 1,800 MHz cap and 125 to 140 W on auto; the 7B on auto drew
  140 W when it was the first run after the cap and 126 W when it followed an hour of 32B runs (note 22's
  flagged spread, reproduced in the re-run).

## What to do with a day of data

Idle before and after each run against time of day, the run before it, the memory and fabric clocks and the
display state; and the 7B's 126-against-140 W question, which needs a run with the logger's full columns on
both sides of a state change.
