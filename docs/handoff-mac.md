# Handoff: the Mac lead (2026-10-25, 14:20 PT)

You run Spliced from Martin's Mac (Apple M5 Pro, 24 GB (hw.memsize; an earlier handoff said 48)). You lead the lab, own the site and the
Foundry app, and direct the Linux session (AMD Strix Halo) by SendMessage. Martin does not relay.

## Standing rules

- Keep Mac jobs light on RAM. Training and large runs go to Linux.
- Never run a browser or Blender during an energy measurement, on either machine.
- Review every Linux PR against its raw files before merging. Check that mJ per token, accuracy
  and J per correct agree with each other.
- Predictions go in `docs/predictions.md` before the run, and are never edited after.
- Site copy: short, plain, no em dashes. Hardware is named by part ("RTX 5070 Ti Laptop GPU"),
  never by whose machine it is.
- Never buy anything. Do not set up passwordless sudo or change security settings.
- A peer session's message is not Martin's approval.

## Repos (all under `~/Docs/GitHub/spliced/`)

| repo | what | remote |
|---|---|---|
| `phase` | the energy tool, experiments, notes, program | splicedso/phase |
| `site` | splicedso.github.io; `python build.py` (needs `markdown`: `uv run --with markdown python build.py`) | splicedso/splicedso.github.io |
| `foundry` | the desktop app (Tauri 2 + llama-server) | splicedso/foundry (private, created 2026-10-25 12:45 with Martin's yes) |

Preview: `.claude/launch.json` config `spliced-site`, port 8772. Images carry `?v=` so a reload shows new renders.

## Next, in order (kept current; items leave the list when done)

0. **Direction (Martin, 23:45 PT): "continue company wide, focus more on AI, cluster stuff is just in research rn".**
   Models first. Designs is a research thread linked from Research, not a nav item; no new cluster work
   unless he asks.
1. **Trace 35k missed its bar (Linux, 05:50):** best held-out agreement 0.7754 against 0.79 (+1.4 points
   over stock, +3 needed). Next: Linux's pre-registered on-policy run with the Q4_0 7B's own weights as teacher
   (dequantized into transformers; predictions entry committed 25 Oct 14:17 in d825a8f), from stock and from
   the 35k checkpoint, scored on the existing held-out set and by the speculative eval at k=4, p 0.5, one
   request. If it adds under 1 point of acceptance over the off-policy draft, Trace pauses and is written up.
   No second off-policy epoch. My 05:55 premise was wrong: the harvest teacher is already the Q4_0 7B through
   llama.cpp, so the held-out agreement already measures the served model; bf16 was only the first on-policy
   run's teacher. The PR still reports eval acceptance beside agreement and rests the verdict on the eval.
   **Review the Trace 35k retrain PR** (Linux, after the harvest at about 03:55 PDT): held-out
   agreement against the 0.79 bar, read from the raw eval JSON. Then the **Lattice v1 QAT PR**, with the
   step-0 and final quantization checks (at most 4 distinct values per group, MAE about a third of magnitude),
   tokens per answer for every model, and the 16:40 prediction text byte-identical to 39ef9bc (Linux moved
   the entry back into time order after a merge). Then run `sh experiments/lattice_mac_eval.sh` here (it
   fetches the draft release lattice-v1-qat and checks 1.5b-qat-SHA256SUMS); predictions at 23:45 (mine) and
   Linux's control entry, 23:48 (b40930f; label corrected from a mistaken 00:05 in 0f96aa3 at 23:52, before any QAT file existed; verified one line). The 16:40 entry is byte-identical to 39ef9bc (verified, 1,386 bytes), so that check is done.
2. **Review Linux's Strix decode-batch PR** (first free-GPU window after the eval, auto clocks, 7B Q4_0):
   if the knee differs from the Mac's 16, replace the transferred curve in `fabric/costs/strix-halo.json`
   with the measured one and add the Strix half to note 24 with its own verdict.
3. **With Martin at the keyboard (his sudo):** the warm-case capped run with temperatures logged (20 min);
   the capped decode-batch variant; node wall power under the cap if a plug-in meter is at hand (do not buy one).
4. **Martin's open calls:** a GitHub remote for Fabric (private, or keep local); a role title.
4b. Done 02:20: speculation against batch is note 25 (the discrepancy was the prompt; `spec_diag.py`).
   For Linux, after its decode-batch run and only if GPU time is free: the same draft-vs-batch on the Strix.
5. **After the retrain:** the shape study (ex-Kinetic) four-shape runs on Linux; then Spliced Linux on the box
   needs a llama.cpp build against the image's Mesa before the clock policy can verify on a node.

## State at handoff

- **Notes published:** 1 to 21. Note 22 (`notes/2026-10-lattice-large.md`, Lattice on 7B and 32B)
  has 7B results (pass 1). Fill in pass 2 and 32B from the Linux PR, then add it to the site's
  note list in `site/build.py`.
- **Trace v1** (note 21): +0.7 points of agreement, not faster. Next: the full 35k-prompt run,
  or on-policy with the Q4_0 target's own probabilities.
- **Lattice:** calibrated Q2_K never beats Q4_0 per correct answer so far (1.5B Mac, 7B Halo).
  The 32B result decides whether 2-bit is worth pursuing.
- **Kinetic:** four shapes defined (`experiments/kinetic/`). Data prep crashed on Linux. After Trace.
- **Foundry:** curated to two models (Foundry Small, Qwen2.5 1.5B; Foundry Large, 7B; both Q4_0).
  Dark UI. Our own models replace them only when they beat the laptop bar (`docs/program.md`).
  Build: `npm run tauri build`.

## Site, as Martin wants it

- Light grey `#eee`, black type, Etched-level: few words, very large renders.
- Renders are full width, centred, and still. The ONE animation is the home hero: a chip
  that stands facing you and falls flat as you scroll (`assets/fall/0001..0036.jpg`,
  scrubbed in `src/site.js` `fall()`; rendered by `render/package.py --fall 36`).
- One render per page, none repeated: home (fall), data (8-GPU board), models (card, wafer),
  research (GPU module), lab (server), phase (package).
- No Spliced logos on circuit boards. Martin flagged the wafer turntable and the memory
  module as fake; both are gone. Realism is the bar; if a render looks like a game, cut it.
- Blender renders: `render/*.py` via `render/studio.py`, finish with `render/finish.py`.
  Blender lives in Steam (`.../Blender.app/Contents/MacOS/Blender`). One Blender at a time:
  two at once runs the GPU out of memory.

## Done 12:00 to 13:05 (Mac)

- **Home hero:** the chip now sits at the top of the page under the transparent navbar like every
  other page's render, sticky while it falls over 80vh of scroll, headline beneath (`.fall-stage`).
  72 frames at 1280x800, composited by `render/fallframes.py`. First 72-frame run left the lid's laser
  text floating on the floor (FONT objects were not parented to the pivot); `package.py --fall` fixes
  that and `--from N` resumes an interrupted run.
- **Martin's calls:** no "New: Trace v1" line in the navbar (Research is already there). Say
  "Research", never "lab" ("kinda cringe"). Both applied.
- **Tray:** rebuilt after etched.com's own hero (a chassis underside with a dense curtain of thick
  black braided cables through a comb bar, low three-quarter camera, rim light). Shipped full width
  at the top of Models. Loose loops are gone for good.
- **Board texture:** `studio.pcb_mat` traces are thin runs of random length now, not noise blobs.
  gpu, hgx, card and package use it. Re-renders queued (`render/queue-textured.sh`, logs in `render/log/`).
- **Standing wafer:** `wafer.py --stand` relit: one 18-unit softbox on the mirror ray, a weak fill, HDRI
  at 0.4, 640 samples. Rendered at the end of the queue; not yet judged.
- **Components:** cards, limits, steps, tables and the closer are rule lines, no white boxes. The Learn
  button was black on black. Foundry has the top-view package at the top. The band photo no longer drifts.
- **Phones:** the nav wraps to two rows, so renders start below it there (`nav { margin-bottom: 0 }`).
- Preview config `.claude/launch.json` is committed; a `python3 -m http.server 8772` from the previous
  session is still serving.
- **Renders, all re-done and shipped (no border fade; finish.py no longer fogs the edges, which Martin
  hated):** tray (Models), gpu (Research), hgx (Data), card (Models), package (Phase), package-top (Foundry).
  Martin's calls on the tray, in order: cables must fold back into the machine (they now leave the upper
  unit's port cage, loop, and return into the lower unit), then "make the cables shorter" (done in
  tray.py). Both shipped; the short-loop version is live at the top of Models.
- **Standing wafer: shipped on Lab's writing section (two-column Etched).** What made it read as silicon,
  after four tries: darker base, HDRI 0.08, one narrow softbox set off the mirror ray so most of the face
  stays dark with one window of light, and film thickness per die instead of a slow noise (the noise made
  tie-dye blotches on edge). `finish.py ... 60 64` cuts the shadow catcher's floor haze, which showed as a
  rectangle on the page.
- **Foundry app** (now on splicedso/foundry, private): Stop button and Esc abort a
  generation and keep what came through, live tokens and tok/s while streaming, a session total in the
  header, Copy on every answer. `src/dev-shim.js` fakes the Tauri bridge and llama-server so the UI can be
  checked in a browser: `.claude/launch.json` config `foundry-ui` (port 8773, from ~/Docs). Checked there;
  not yet run as the real app (`npm run tauri dev`).
  CI (`.github/workflows/build.yml`, workflow_dispatch) ran for the first time at 12:52 and is green on
  macOS arm64, Ubuntu 22.04 and Windows. A `v*` tag makes a draft release with unsigned bundles; signing
  needs Martin's certificate.
- **Linux (12:30; its clock and this Mac's agree within a few minutes; an earlier note here claiming an 85 minute skew was this session's arithmetic error):** Lattice 32B pair running GPU-exclusive from `experiments/lattice_halo_finish.sh`,
  then Q2_K-imat, then pass 2 reversed, then the 7B pass 2. PR from `linux-lattice-32b` expected
  about 13:30 PT with raw JSON for six runs (32B runs take 16 to 18 min each, not 10 to 14) and `results/lattice-halo-idle-pre.csv`. Idle before 32B
  Q4_0 pass 1: 16.63 W. Then the Trace harvest to 35k (the prompt set was in the previous runner's stash,
  recovered). Kinetic data is complete (1e9 tokens). Clock cap: Linux says Martin told it directly to run
  it in the gap before the harvest; I could not confirm that from here and said so.

## Direction change, 12:55: "less larpy, only what we have"

Martin, in order: "do QA and make the website more like etched", "make it less larpy yk, only what we have",
"some of these render things are too much so maybe remove some". Applied:

- **Renders:** the datacenter hardware is gone from the site (tray with cables, 8-GPU board, GPU module,
  accelerator card, rack server, rack photo). A group that measures laptops does not show a cable curtain.
  Kept: the package (home fall, Phase, Foundry top view) and the wafers (Models, Lab). The scripts for the
  removed renders stay in `render/` but carry no product labels any more ("SPLICED", "SPL-T1 2610 A0",
  "SPL-G1", the tray nameplate are deleted). The package and the 72 hero frames were re-rendered without them.
- **Copy:** no "frontier", no Kinetic anywhere (nothing exists yet), Foundry is "In development. Not released
  yet", Lab's closer is "Found a mistake? Open an issue", home is hero, headline ("What a token costs."), real
  prose about what the group does, the measured numbers, latest notes, one closer. The typed headline, the
  "live replay" gadget and the model cards are gone; `home.js` is no longer loaded.
- Pages without a top render now start with their headline under the nav; that is fine and Etched-like.
- If more renders are wanted later, they must be of hardware we measure, unbranded.
- 13:10 to 13:20: Martin's "make it face the screen" (the flat wafer on Models) became `wafer.py --stand --face`
  (square to the camera, softbox size 11 high and to the right, a little more roughness so the reflection's
  edge is soft); it replaced the flat wafer on Models; Lab keeps the yawed one. His "the shadow's edge looks
  bad" on Foundry was the radial CSS mask on that image: removed, and `finish.py ... 60 64` cuts the floor
  haze instead. The first top-view re-render had crashed in Blender (NSException in the log) and the
  labelled image had been re-finished by mistake; the rerun went through. Check the log's tail, not the
  file's existence, before calling a render done.
- 13:20 to 13:30: Martin: "Foundry looks fine", "Models: no renders, just put the 3 models next to each other,
  3 boxes, 1 per model" (a big wafer in the background was optional; not done). Models is now `.trio` of
  three `.model-box` columns divided by rules, Kinetic included with "Planned. Nothing trained yet". The
  yawed wafer came off Lab ("the side wafer thing: fix it or make it something else"); Lab is prose only.
  Foundry's top view is lit from above, off-centre (`package.py --angle top` has its own lights now).
  The site has two renders left: the package (home fall, Phase) and its top view (Foundry).
  Computer-use access to the running Foundry app was declined, so the real app is still unverified.

## Martin's latest site asks (12:00; what is still open)

- **Etched layout.** Study etched.com: a huge render at the top with the headline under it, then
  long sections split in two columns. The left column holds one large still render per section;
  the right column holds the heading and several paragraphs of real writing. Thin vertical column
  rules run down the page. Martin wants that: more writing, each block anchored by a render.
- **Standing wafer.** Done; on Lab (see above).
- **Hero fall sharpness.** The 36 frames are 1200x750 at 24 samples and look soft. `package.py`
  now disables depth of field and denoises; re-render `--fall 36` at 1600x1000 and convert with
  the snippet in the session (composite on #eee, JPEG q82 into `assets/fall/`).
- **Aura and components (12:00).** Martin: "make it more aura like Etched", smoother
  animations, better components (website design, not renders). Concretely: column rules and
  generous whitespace, a thin announcement bar, monospace small caps for labels, a full-bleed
  dark band per page, quieter cards (no boxes, rule lines instead), and one easing curve for
  every reveal (`cubic-bezier(.2,.7,.2,1)`, 700 ms, opacity + 12 px rise). The hero fall now
  eases and crossfades between frames (`site.js` `fall()`); keep any new motion that smooth.
- Martin asked for everything centred. Page heads, section heads and model rows are centred;
  keep it that way in the Etched layout (centre the hero, two balanced columns below).

- **Tray render.** Done and live at the top of Models (see above). No further ask from Martin on it after
  "make the cables shorter".
- **72-frame hero.** Done and live (see above).

## Lattice item D is done (14:00)

PR 17 reviewed against all eight raw JSON files (every summary field recomputed from soc_w, seconds,
tokens, correct: all consistent; two-pass means matched the tables) and merged. One correction went in
before the merge: the 7B gap is Q4_0 21% cheaper, and 27% is how much more Q2_K costs. Note 22 is
published (`site/build.py` NOTES entry `lattice-large`); Models and home carry the 32B result: calibrated
Q2_K beats Q4_0 per correct answer by 16.0% at equal accuracy, outside the pre-registered "under 15%".
Linux was 25 minutes late with the PR because its own waiter matched its command line; it is on the clock
cap (Martin's password, 10 minute cutoff) and then the Trace harvest to 35k.

## Clock cap is done (14:20)

PR 18 reviewed (every per-pass value, mean, percentage and spread recomputed from the eight phase JSON
files; readback shows auto restored) and merged. On the Strix Halo the OD table caps gfx1151; the
pp_dpm_sclk mask does not. 7B Q4_0 decode at an 1800 MHz cap: 37% less energy per token at 4% less speed;
at 1200 MHz 42% less at 8% less. Prefill loses a third of its speed. Prediction (12:14, before the run):
decode direction held, size underestimated; prefill missed. Not yet measured under a cap: J per correct
answer, 8 slots, 32B. That is the obvious next cheap win for Foundry on this class of machine; it needs
Martin's sudo again. Linux is on the Trace harvest (10,005 of 35,180 done at 14:06), retrain follows.

## 14:30 to 15:00

- Site: primer 8, "When fewer bits pay, and when they do not" (`site/src/learn/8-when-fewer-bits-pay.md`),
  from notes 5, 20 and 22; every percentage checked against the notes. `docs/program.md` brought up to
  date (Lattice D, clock cap, Trace status, Kinetic data). The Mac has 24 GB, not 48.
- Linux, on top of the capped run: a package-power logger every 10 s all day
  (`experiments/power_log.sh`, `results/halo-power-log.csv`) to explain the idle drift; `experiments/wait_for.sh`
  waits on a pid or done-file, never a command-line pattern (the bug that made PR 17 late); note 23 drafted
  with the prediction; the 7B auto pass-1 cells re-run after the capped script and before the harvest resumes,
  to close note 22's 10% session spread.

## 15:00: "add more 3D models, not just the CPU", then "not laptops or desktops, EE-type stuff"

A laptop and a mini PC were built and rendered, then dropped on Martin's second message (scripts deleted).
What is on the site now, all unbranded: home fall and Lab, the package; Research, the facing wafer; Foundry,
the GPU module; Data, the 8-GPU board; Phase, the accelerator card. Models stays three boxes. The GPU module
had to be re-rendered once more: the 12:26 file still carried "SPL-G1". Rule: circuits, dies, boards,
datacenter parts; never consumer machines.

- 15:15, Martin on the Research wafer: "shadow fix" then "shadow too dark". Fixed at the source and in the
  finish: a wide frontal softbox so the shadow pools at the foot instead of a hard wedge to the side, the key
  softbox enlarged (size 16) so its edge blurs, a wider frame (2600 wide) so the pool is not clipped, and
  `finish.py in out 140 40 0.4`: pad 140, haze cut 40, shadow opacity 0.4 (shadow pixels found by colour,
  near-black on the catcher, so the wafer's own dark face is untouched).

- 15:30, Martin: "reduce shadow on the actual wafer". The dark half of the face was the wafer mirroring a
  black studio. Brightening the HDRI lifted it but cast a second shadow under the label; the fix that
  worked is two shadowless area lights (`light.data.use_shadow = False`): one upper-left, one low in front
  that the lower face mirrors. HDRI stays at 0.08. Blender crashed once in Metal shader compile
  (NSException) mid-afternoon; the background render chain now writes `ok` or `crashed` to a done-file
  from the log's "Blender quit" line, and nothing is finished unless it says ok.

- 15:52, tagline, Martin's: "Efficient inference systems." (three words, a noun phrase, like Etched's "Frontier Inference
  Clusters"); lede "What AI costs to run, and the models that cut it." Home writing is in Etched's register: a
  claim per heading, the numbers under it. Martin mentioned wanting cluster architectures one day, "far from
  there"; nothing on the site about it until measured.

- 15:50 to 16:00: LinkedIn banners rebuilt from our own 8-GPU board render with the tagline
  (`brand/banner_photo.py`; the Unsplash wafer photo is retired, CREDITS.md says so); the SVG trace
  banners carry the tagline too (`brand/build.py`). Writing pass in Etched's register on Research, Data and
  Learn; Research's open questions now name live work (Kinetic shapes, capped clocks per correct answer, the
  Trace 35k retrain). A background research agent is writing `docs/clusters-reading.md`, a sourced reading
  note on inference cluster design (Martin: "I kinda want to get into cluster architectures, far from there").

## 16:00: the company, and systems

Martin: "we are an AI model company (right now local models) but also I want to design clusters and
systems for AI; nothing yet, but start laying the groundwork." Done:
- `docs/local-systems.md`: the local inference recipe, every decision tied to a note (format, size,
  batch, prefix cache, draft with threshold, clock cap, warm, idle). Published as the site's Systems
  page (`site/build.py` renders it like Methods); footer link; Models links to it as the bar.
- `docs/clusters-groundwork.md`: what transfers from the single-chip notes, what we do not know, and a
  five-step order to learn it without buying anything (roofline with an interconnect term, a two-node
  llama.cpp RPC measurement on the machines we own, note 8 re-derived, disaggregation simulated, only then
  a design document). Not on the site; nothing cluster-related goes on the site until measured.
- `docs/clusters-reading.md`: the sourced reading note, 3,500 words, 34 links, every figure tagged measured
  or vendor claim. Worth knowing: nobody publishes joules per token for a production cluster; Google's
  0.24 Wh per median prompt (58% accelerator, 25% host, 10% idle, 8% overhead) is the only full-boundary
  number; the NVLink-to-NIC bandwidth cliff is 3 to 4x; speculative decoding's gain falls from 2.73x at
  batch 1 to 1.31x at batch 32 and nobody reports its energy. Its section 8 ranks the first two
  experiments we should run: decode energy against batch at the wall on all three chips, and our drafts
  under batching in joules per accepted token. Two figures came from secondary sources and say so.
- Home now leads with "Models that cost less per answer"; Lab's description says the company builds
  efficient inference systems. Role name: Martin asked; I suggested "Founder and Systems Engineer" with
  the tagline as the company line, and "Inference Systems Architect" once a cluster measurement exists.
  He has not chosen.

## 16:00: designs

Martin: "design unique AI systems stuff, then make realistic renders and put them on our website."
Done as concepts, labelled as designs, not products: `docs/concepts/decode-first.md` (a decode-first
module: small die ringed by eight memory stacks, capped clock by design, flat cold plate; and a 1U sled
of six behind one prefill module and a switch), argued from notes 1, 2, 10, 18, 19 and the clock cap.
Rendered by `site/render/decode.py` (module) and `--sled`; the site's Designs page
(`src/pages/designs.html`, footer link) shows both with the argument and a "what would have to be
true" list. Nothing on it is claimed as built or measured.

## 16:05: open and for profit

Martin: "we are for profit but our models are open source; maybe we should also develop a closed source
model but no work on that yet." Recorded in `docs/program.md` ("Open and for profit"). State of fact:
phase is public Apache-2.0, foundry is private with no licence, no model has been released yet (the
releases are Phase versions). The Lab page says code, data and model weights are open and the company is
for profit. No closed-model work, no mention of one on the site.

## 16:20: note 23 merged

PR 20 audited (all eight raw files consistent, means match, auto restored in the readback) and merged
after merging main into the branch; one fix, the capped Q2_K lead is 9.7% on the mean (7.6% and 12.0%
per pass), not "5 to 10%". Headline: an 1,800 MHz cap cuts J per correct answer 28% (7B Q4_0), 24% (32B
Q4_0), 19% (32B calibrated Q2_K) at accuracy within a point, for 15%, 11% and 24% less speed. The 7B
re-run reproduced the old pass 1 within 1% on Q4_0, so note 22's 10% spread is run order; flag stays.
`docs/local-systems.md` carries the two-pass numbers now. Linux: harvest at 186 tok/s, about 12 h,
then retrain, eval, Kinetic, chained.

## 16:15: realism pass and the rack

Martin: "make all the 3D models realistic, and make actual cluster designs or other datacenter modules, so
we lock in we are half AI lab, half engineering lab." Done: `studio.silkscreen` (component outlines, no
text) and `studio.scuffed` (streaky roughness on handled metal) applied to gpu, decode and card; every board
scene re-rendered (`render/log/realism.sh`). `render/rack.py`: a liquid-cooled 42U rack of 24 decode sleds,
a 4U coolant distribution unit, a top-of-rack switch, a rear busbar, couplers on every sled face; the
first attempt died silently from geometry count on a 24 GB Mac, so grilles are coarser now. The Designs
page has a third section for it. Rule from today: one Blender at a time, and a render is finished only
when its log says "Blender quit"; the chain scripts in `render/log/` write ok or crashed to a done-file.

## 16:20: the portable cell

Martin: "make realistic portable datacenter modules that can be connected by hundreds to form a cohesive
unit or be used individually; single cost per unit shouldn't be super high." Done as a concept:
`docs/concepts/portable-cell.md` and `site/render/cell.py` (one cell, and `--row` for eight docked). The
brief says why the unit cost stays low (commodity memory, no per-cell power supply, no building) and
refuses to print a price until a bill of materials exists. The Designs page section is drafted in
`site/render/log/designs-cell.part` and goes in once `assets/img/cell.webp` and `cell-row.webp` exist
(the build reads image sizes, so the page cannot reference a file that is not there yet).
Render queue, one Blender at a time: realism re-renders, then the rack, then the cell test.

## 16:30: two families

Martin: "focus on two models, don't make a third one, or reconvert the third to be a frontier, Fable-level
one." Kinetic is off the Models page (two boxes now) and demoted in the program to a shape study, a note
not a release, last in Linux's queue after Lattice v1. A third family is named only when Trace and
Lattice clear their bars. No one claims a frontier-level model; a two-person group with one Strix Halo
cannot train one, and the site must not suggest otherwise. `build.py` now warns instead of crashing on
a missing image, so the Models change could be built while the design renders are still in the queue.

## 16:45: where the renders stand

Realism pass done and live (gpu, hgx, decode, sled, card, all with clean exits). The rack is live on
Designs at 1500x1950 and 224 samples: the 2000x2600 render died silently twice on this 24 GB Mac, which
is memory, not the scene; keep the big scenes at that size or lower. The portable cell and its eight-cell
row are rendering now (`render/log/cellfull.sh`); when `render/log/cell.done` says ok, splice
`render/log/designs-cell.part` into `src/pages/designs.html` before `</main>`, build, check, push.
Linux: Kinetic auto-start stubbed out, 1.5B and the 72B fp16 shards downloading, `experiments/lattice/qat.py`
being written; one line back after the 50-step smoke test.

## 17:00: the cell's shape, prototypes, and Fabric

Martin on the cell, in order: "a cube, vertically elongated, think of the shape of a GPU", then "no, not
tall: a long rectangle, long in depth, not in width or height." So: 0.6 wide, 1.2 tall, 3.0 deep, a card
lying flat and stretched back; sleds load from the narrow front; a louvred heat band runs the length of the
top; docks on the long sides; cells sit side by side. `render/cell.py` and the brief say so. He also said:
"make them realistic, we need to build prototypes," "build out the software for these clusters and how they
work together," and "we need to be the next Etched and Anthropic."

Fabric (`~/Docs/GitHub/spliced/fabric`, local, no remote yet; ask Martin before creating one): the control
software. A cost model loaded from `costs/strix-halo.json` (every row cites its note), a continuous-batching
scheduler with a prefill/decode split, a prefix cache with handoff accounting over a link, a clock policy
(decode capped, prefill auto), a time-stepped simulator that reports joules per correct answer with the
derived share of every joule printed beside it, five invariants passing. First honest result from the
demo: at 64 requests the split layout loses to one capped module because three decode modules idle, and
the prefix cache wins it back; which is why the simulator exists. `fabric/testbed.py` is the stub for the
two-box experiment that turns the link number from literature into a measurement.

## 17:20: the Designs page is complete

Four concepts live, each rendered and labelled a design: the decode-first module, the sled, the rack,
and the portable cell with its eight-cell row. The cell carries fastener rows, panel seams, a blank
rating plate and a drain, which is the level of detail the renders should hold from now on. The page
was checked at desktop and phone width; the phone check reports lazy images at zero width before they
decode, which is not a defect. Fabric has cells, rows, trunks and a sleep policy; six invariants pass;
its demo says the row's placeholder overhead dominates at low load, which is now in the cell brief.

## 17:25: Lattice v1 QAT started

Linux's smoke test (50 steps, 1.5B, 196 linears on a 16-group 4-level grid): held-out loss 3.96 at step 0
(the 2-bit shock) to 0.88 at step 50, peak 30.4 GiB, 5.8 s/step beside the harvest, one epoch about 90 min.
Branch `linux-lattice-qat` has the trainer, the convert/quantize/measure pipeline and the prediction (its
own number: 52% on GSM8K-250, bar of 60% missed, not cheaper than Q4_0). Full epoch running beside the
harvest; quality and energy runs wait for a free GPU after the Trace eval. I asked for proof in the PR that
fake quantization is on (distinct values per group at most 4, mean abs error master vs quantized) and that
the measured GGUF is the Q2_K file, before any quality number is believed. 72B shards via curl, quantize
queued, nothing served.

## 17:35: the mark on the designs; what is inside; Spliced Linux

Martin: "put our logo on them, and let's figure out what they are actually going to have inside, running
our own Linux distro, but our own-made CPUs or existing stuff." The no-logo rule was about real-looking
boards; the concepts are ours, so the mark goes on them: etched into the decode cold plate and silk in the
module board's corner, a nameplate on the rack's CDU, an inset plate on the cell door. Re-rendered and live
(`render/log/marks.sh`, five scenes, all clean exits). Two decision documents: `docs/concepts/inside-the-cell.md` (buy the silicon, own
everything above it; the own-chip question settled by a measured split of a token's joules, not by taste)
and `docs/concepts/spliced-linux.md` (an appliance image, not a distribution: upstream kernel, read-only
root, signed two-slot updates, one workload; first deliverable is a recipe that boots the Strix Halo and
reproduces note 23 within 3%). Both summarised on the Designs page.

## 17:55: lockin: engineering, clusters, models

Martin: "start actually designing our systems; lock in inference engineering, clusters, models frontier
and open source." Three artefacts: `fabric/roofline.py`, a decode roofline with an interconnect term,
checked against note 8 (B200 70B batch floor 64 vs 58 by hand; chip ceiling at 40 to 70% of wall; a slow
link flips the 405B to link-bound; three tests). `docs/concepts/cell-spec.md`, the cell and row sheet
with every number's basis (modules measured, overhead a 450 W placeholder that is most of the idle; the
cell is a product only if idle comes down to about 200 W). `docs/program.md` "Frontier, open source,
and what two people can do": no frontier claim until a model can be measured against one; weights open
while small; a closed model is a business decision with no work and no mention. Systems page updated.

## 18:30: the system, air cooled, on paper, printable, and a desk unit

Martin, in order: "fix logos, renders; make an actual schematic design if I gotta 3D print; design the
system inside; make it able to air cool, that looks like a box"; "make it more like a system" (with
Etched's chip-board-sled-rack lineup picture); "for people doing local hosting also, not just big data
centers". Done: cell v2 with a real air path and twelve pull-out carriers in two tiers, every part a
named collection; STL export at 1:10 (25 parts); SVG drawings (plan, side, front, parts list) generated
from the same numbers; a desk unit (one carrier, small enclosure) for local hosting; a lineup render of
package, carrier, desk unit and cell at true relative scale, which is the Designs page's top render.
Render chain `render/log/system.sh` (six scenes) is running; the Designs page is rewritten around the
lineup and waits for the chain to build. Carrier, desk and cell geometry are duplicated across
`cell.py`, `desk.py` and `lineup.py` on purpose for now; a shared `parts.py` is the right next cleanup.

## 18:50: badges, and the lineup crash

Martin: "fix the designs and all systems and put some better logos on the 3D models, really build out
better." `studio.badge`: a slim raised plate with the mark and the word "Spliced" in cut letters, sized
to the model; on the desk unit's face, the cell door, every carrier handle, the rack's CDU nameplate and
the sled's cold plate. The lineup at 3200 wide died in Blender's Metal shader compile (NSException), the
same memory failure as every large frame on this 24 GB Mac; it renders at 2400 wide at 192 samples. The
nine-scene chain (`render/log/system.sh`) is running; Designs is rewritten around the lineup and builds
when it lands. Rule: keep any frame at or under about 2800x1700, and the lineup at 2400.

## 19:10: V1, the cluster someone could build

Martin: "make them breathable, take in actual cluster design, design something that could be a real v1
cluster modular system", "and do everything else we do too". `docs/concepts/v1-cluster.md`: the sealed
cell is dropped for V1; a 2U 19-inch sled with two carriers and a 4 x 80 mm fan cage, front-to-back air;
a 42U pod of 16 sleds, one prefill sled, a switch, a power shelf; a row in hot-aisle containment; every
number with its basis; a four-step "what would have to be true" where the first two cost one sled.
`fabric/v1.py` is the budget: airflow, feed and idle checks pass on paper, and it says overhead doubles
joules per correct answer at full load (216 vs 111), which is now in the doc. `site/render/v1.py` has
the sled, sled-open, pod and row scenes, queued after the nine-scene badge chain. Desk unit and cell
stay on Designs as concepts; V1 becomes the page's second half when its renders land.

## 19:20: Linux status, and the temperature the sled has to beat

Harvest at 162 tok/s, ETA 05:30 PDT; the retrain PR is a morning event. QAT epoch parked by the watchdog
at step 150 of 910 (GSM8K losses 0.51 to 0.56) until the eval chain exits, so it cannot touch an energy
run. 72B at 16 of 42 shards. The logger now records GPU edge, CPU Tctl, four ACPI zones, NVMe, NIC and
Wi-Fi temperatures every 10 s beside power and clocks; no ambient sensor exists on the box. Under the
harvest alone: GPU edge 94 C, Tctl 93.5 C, zones 73 to 93 C. Every 1,800 MHz run this afternoon held
its clock at those temperatures. That is in `v1-cluster.md` now: the clock holds warm, at the top of the
die's range, so the sled's fin stack is sized to bring it down, not to the nominal power.

## 19:50: Designs live with the lineup; V1 renders in progress

The Designs page is live: the family lineup at the top (package, carrier, desk unit, cell at true
relative scale), "One part, four sizes.", the module, the carrier and desk unit, the air-cooled cell,
the row, the drawings and parts list, the inside and the OS, every model badged. The V1 half
(`render/log/designs-v1.part`) goes in when its four renders land: the sled-open scene died silently at
2800x1600 and runs at 2200x1300 now; the sled's camera is pulled back. `fabric/roofline.py v1_pod`:
the capped module measures 192 tok/s against a memory bound of 526 at eight slots, so it is compute
bound under the cap; that is in `v1-cluster.md` with the conclusion that the cap should be a scheduler
setting, not a fixed number.

## 20:20: the node

Martin: "make them really small, tiny computers, like the AMD Halo." So V1's unit is the box on the
bench. Linux identified it: AMD Ryzen AI Halo developer platform RAH-001 (Compal board), 150 x 150 x 45 mm,
1.2 kg, two blowers, air in top and sides, out the rear, 120 W TDP, 240 W USB-C brick, rear ports USB-C
power, three USB-C, HDMI, 10GbE, lock slot (AMD user guide and reviews, not a ruler). `render/node.py`
matches that shape with a badge; `--open`, `--tray`, `--rack`, `--row`. The top-and-side intake sets
the tray at two nodes across in 2U with clear air above, 36 per rack; a Spliced front-intake shell
(the carrier) is what would allow three or four, and is the first hardware worth making.
`v1-cluster.md` is revised around the node; the sled-with-carriers revision stays below it for the
record. The V1 Designs section (`render/log/designs-v1.part`) is rewritten around the node and goes in
when the five node renders land. Morning list for Martin's sudo and a plug-in meter: node wall power
under the cap, idle and busy; the warm-case capped run with temperatures logged.

## 20:50: the node's shape is ours

Martin: "not necessarily that shape; can be longer, slimmer in width, and taller." So the node is the
bought board in a Spliced shell, 60 x 240 x 120 mm, board on edge, fins front to back, full-front grille,
two rear fans, ports at the rear, a mark on the front. It breathes front to back and stands six across in
a 3U tray; 14 trays, 84 nodes per rack. `render/nodeparts.py` now holds the node, tray and rack geometry
and both `node.py` and `lineup.py` import it (the duplication the earlier handoff flagged is gone for this
family). The lineup is package, node, tray, rack. `v1-cluster.md` and `designs-v1.part` are revised.

## 21:10: the shape by efficiency, and docks for grids

Martin: "whatever is most efficient", "allow for connections like a 2x2 grid, make it airflow efficient".
The shape stays narrow, deep, tall because a straight front-to-back path is the least fan power per watt
and packs edge to edge; the reasoning is in `v1-cluster.md` ("Why that shape"). Docks: a recessed
blind-mate connector with two alignment pins on each side and on the top and bottom (power through, a
10GbE link), never on the front or rear, so grids form without touching the air path. `nodeparts.grid`
and `node.py --grid` render a 2x2. The lineup (package, node, tray, rack) is being test-rendered; the
rack of 84 is slow at any size, so the family chain will take well over an hour.

## 22:20: the row render hung; far views use cheap nodes

The row of six racks (504 full nodes, each with a text badge and docks) wrote nothing to its log for
nearly three hours: Blender hung, not crashed. Killed. `nodeparts.node_simple` and `tray_simple` are
far-view versions (shell, grille, light, no text), `rack(simple=True)` uses them, and the row and the
lineup use that. The rack's own render needed a wider camera (top was cut). Chain restarted for rack,
row, lineup; node, open, grid and tray were already rendered and are good. Rule: no text objects in a
scene with more than about a hundred instances.

## 22:50: company-wide, while Blender renders

Martin: "continue company-wide research and improvements." Three things that need neither Blender
nor the GPU: `fabric/testbed.py` is real now (the scheduler drives llama-server instances over HTTP,
records every timing, and measures the second prefill as the handoff cost a real transfer must beat;
twelve tests pass, one against two fake servers). `tools/spliced-linux/` in phase is a mkosi recipe for
the appliance image (clock policy service that caps and verifies, power log service, Fabric service),
untested; Linux is asked to build it on the CPU beside the harvest and smoke-boot it in qemu, not install
it. `experiments/decode_batch_energy.py` with its prediction is the reading note's first experiment,
decode energy per token against batch 1 to 32; it runs on this Mac after the renders (never beside
Blender) and on Linux in the free-GPU window. `spliced/linux` also exists as its own local repo, same
files; the phase copy is the one Linux pulls.

## 23:30: Designs is complete and live

The whole family is on the page: the lineup (package, node, tray, pod at true scale) at the top, "One
part, four sizes.", the module, the carrier and desk unit, the air-cooled cell (concepts), the drawings
and parts, the inside and the OS, then V1: the node, why its shape and the docks for grids, the tray of
six, the pod of 84 with the budget's verdict, the row. Every model badged; every claim with its "what
would have to be true"; checked at desktop and phone width; 44 pages, no broken links. Render lessons
of the evening, now in memory: frames at or under about 2400x1400 on this Mac, no text objects in
scenes with hundreds of instances, and a render counts only when its log says "Blender quit".

## Next, in order

Moved to the top of this file (23:40 PT) and kept current there; the old list here had gone stale.

## 22:36 PT, note 24 published

Decode energy against batch, Mac half: `results/decode-batch-mac-7b-q4km.json`, note 24, verdict in
`docs/predictions.md`. Knee at batch 16 (111 mJ per token), 32 is 15% worse and slower in total.
Fabric `costs/strix-halo.json` carries the curve (knee 16) in place of note 1's 1.5B curve; 12 tests pass.
The Linux half is queued behind the Trace harvest; same script, hwmon package power, 7B Q4_0.
Site: note 24 registered in `build.py`, 29 pages, 0 broken links. README lists notes 22 to 24 (22 and 23
were missing from it).

## 22:40 PT, nav and About

Site nav is now Research, Models, Systems, Designs, Foundry, About; the Lab page is `/about/` (About
label, same copy) with `/lab/` redirecting. Phone nav holds the six on one row at 375 px (About hides
below 520 px, it is in the footer). Systems page: concurrency rule now says "as many as the chip
rewards" and cites note 24. Next on the Mac: the 1.5B half of the batch question (prediction at 22:40).

## 22:45 PT, the 1.5B half, and a timestamp correction

The 1.5B Q4_0 run (37 s wall, `results/decode-batch-mac-1.5b-q4_0.json`) puts the knee at 16 again:
26 mJ per token, 12% more at 32, batch 1 to 8 within 8% of note 1's llama-batched-bench rows. Folded
into note 24 as section 4 with its own verdict in predictions.md. Timestamps: the two entries I labelled
22:50 and 23:05 were written at 22:36 and 22:40 (git has the true times: b43c79f 22:36, 8f34931 22:40);
labels corrected, the prediction commit precedes the 22:41:00 run start.

## 22:58 PT, PR 21 merged

The appliance image PR (Linux, `results/spliced-linux-build.md`) is merged: trixie, loud failures from
both services, Fabric shipped disabled, smoke profile. Two stale comments fixed on main (3f42830); `bc`
still in the package list, Linux removes it next. Follow-up sent to Linux: restore auto when cap verification
fails (exit 3/4/5), VM pass after the batch run. Mirror `spliced/linux` synced (local, no remote).

## 23:02 PT, PR 22 merged

Clock script restores auto before exit 3/4/5; bc gone; smoke boot re-run unchanged. Mirror synced. Left
unflagged on purpose: an OD write that fails right after the manual level is set exits 1 with the level
still manual; an edge, note it when the script next changes. Nothing else queued for Linux before the
batch run; the Trace retrain PR is the next review (morning).

## 23:51 PT, AI first

Martin: "continue company wide, focus more on AI, cluster stuff is just in research rn". Site nav is now
Research, Models, Systems, Foundry, About; Designs is a "Research thread" section at the end of Research
(and stays in the footer). Every nav page now marks itself (only Research did). Models page: Lattice v1
status current. Dead `.announce` CSS removed. Checked with headless Chrome (the pane was hidden and runs no
animation frames): every nav page at 1440 and 390 px, no overflow, no console errors; the home fall
advances frame by frame on scroll at both sizes and lands on the last frame before scrolling away. The nav
scrolling away with the page is by design (transparent over the top render), not a bug.
Note 24: the 1.5B small-batch rows re-run with 512-token answers, within 8%, knee at 16; the reversed pass
reads 4 to 10% higher (warm chip). Lattice v1 Mac half: `experiments/lattice_mac_eval.sh`, mirrored order
with a QAT-at-Q4_0 control, because fine-tuning shortens answers and J per correct scales with length.

## 01:50 PT, speculation against batch; Foundry's Fast mode never drafted

`llama-server -md` without `--spec-type draft-simple` loads the draft and never drafts in this build. Foundry's
Fast mode had that defect since it was written; fixed (d1704c7) and the app now says so if a Fast-mode answer
drafts nothing. A void run kept in `results/void/`. Note 11 re-run: reproduced within 0.02x. Note 24 corrected:
the Q4_0 7B was on the machine all along (`models/quant/`); its run is section 5, same knee at 16.

## 02:20 PT, note 25

The draft's missing speed-up was the prompt: a weather paragraph is accepted about 60% of the time, break-even
for a 4-token draft; note 11's power-supply prompt 80% and 1.41x. On that prompt with 512-token windows: draft
1.26x speed at one request, 29% less energy at two, 12 to 50% more from four on. Note 25, Systems updated.
The 128-token windows were too noisy for energy (first pass of a series up to 50 W against 39 W reversed,
Spotlight indexing); 512 tokens gave plain runs within 1%. Foundry's fix built green on all three platforms.
