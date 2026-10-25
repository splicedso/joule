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

## Next, in order

1. Review the capped-quality PR (note 23) and the 7B re-run; update note 22's 7B rows on the site if the means move.
2. Review the Trace 35k retrain PR when it lands (bar: 0.79 held-out agreement).
2. The capped J-per-correct run (quality.py at OD 1800, 7B and 32B, 8 slots, two passes, about 1.5 h
   GPU-exclusive): Linux asked Martin directly at 14:30 whether to run it now (pausing the resumable
   harvest) or after the retrain. Martin answered at 14:50: run it now, pause the harvest, resume after.
   Relayed to Linux verbatim with the run spec (7B Q4_0, 32B Q4_0 and 32B calibrated Q2_K at OD 1800,
   8 slots, two passes, prediction pushed first, readback committed, harvest resumed after).
3. Kinetic (14:30): data complete and verified (1e9 uint32 tokens, all ids in vocabulary, shard reproduction
   byte-identical); the prepare.py crash is a PyGILState abort at interpreter exit after every token is
   written; a small fix PR is coming; train.py smoke-tested on ROCm (10 steps, wide shape, 72.4M params).
   The four-shape runs queue after the retrain. PR 19 (the exit fix and `results/kinetic-data.md`) reviewed
   and merged at 14:45; the fix is `os._exit(0)` after flushing and closing both files, documented in place.
2. Check the home hero fall on a real scroll, at desktop and phone width.
3. Trace: decide between the 35k run and Q4_0-teacher on-policy; queue it on Linux.
4. Foundry: create its GitHub repo once Martin says yes, then a signed release.
