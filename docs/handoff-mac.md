# Handoff: the Mac lead (2026-10-25, 13:55 PT)

You run Spliced from Martin's Mac (Apple M5 Pro, 48 GB). You lead the lab, own the site and the
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
| `foundry` | the desktop app (Tauri 2 + llama-server) | none yet, local only. Ask Martin before creating one |

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

## Done 12:00 to 13:55 (Mac)

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
- **Standing wafer: not shippable after two relights.** The first (big softbox on the mirror ray) washed it to a
  pastel disc; the second (dimmer, set off the ray, HDRI 0.18) gives a bright-to-dark gradient but the face still
  reads as tie-dye, not silicon. `render/log/wafer-test.png` is the latest. Next try: darker base (0.2), dies with
  internal block structure at this angle, HDRI 0.1, and a narrower softbox so most of the face stays dark.
- **Foundry app** (local repo, no remote; ask Martin before creating one): Stop button and Esc abort a
  generation and keep what came through, live tokens and tok/s while streaming, a session total in the
  header, Copy on every answer. `src/dev-shim.js` fakes the Tauri bridge and llama-server so the UI can be
  checked in a browser: `.claude/launch.json` config `foundry-ui` (port 8773, from ~/Docs). Checked there;
  not yet run as the real app (`npm run tauri dev`).
- **Linux (13:00):** Lattice 32B pair running GPU-exclusive from `experiments/lattice_halo_finish.sh`,
  then Q2_K-imat, then pass 2 reversed, then the 7B pass 2. PR from `linux-lattice-32b` expected
  13:15 to 13:30 PT with raw JSON for six runs and `results/lattice-halo-idle-pre.csv`. Idle before 32B
  Q4_0 pass 1: 16.63 W. Then the Trace harvest to 35k (the prompt set was in the previous runner's stash,
  recovered). Kinetic data is complete (1e9 tokens). Clock cap: Linux says Martin told it directly to run
  it in the gap before the harvest; I could not confirm that from here and said so.

## Martin's latest site asks (12:00; what is still open)

- **Etched layout.** Study etched.com: a huge render at the top with the headline under it, then
  long sections split in two columns. The left column holds one large still render per section;
  the right column holds the heading and several paragraphs of real writing. Thin vertical column
  rules run down the page. Martin wants that: more writing, each block anchored by a render.
- **Standing wafer.** `render/wafer.py --stand`: see the Done list above; still not shippable. When it is,
  use it on a page that has no second render yet (Lab's writing section, or Learn).
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

## Next, in order

1. Merge the Linux PR after checking it; finish note 22; publish it.
2. Check the home hero fall on a real scroll, at desktop and phone width.
3. Trace: decide between the 35k run and Q4_0-teacher on-policy; queue it on Linux.
4. Foundry: create its GitHub repo once Martin says yes, then a signed release.
