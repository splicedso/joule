# Handoff: the Mac lead (2026-10-25, 12:00 PT)

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

## Martin's latest site asks (12:00, not done)

- **Etched layout.** Study etched.com: a huge render at the top with the headline under it, then
  long sections split in two columns. The left column holds one large still render per section;
  the right column holds the heading and several paragraphs of real writing. Thin vertical column
  rules run down the page. Martin wants that: more writing, each block anchored by a render.
- **Standing wafer.** `render/wafer.py --stand` exists (wafer on edge, yawed 28 degrees) but the
  first renders are not shippable: banded shadow, one side blown out. Fix the lighting (dimmer
  HDRI, a soft key from the front, more samples), then use it on a page that has no render yet
  (Lab's writing section, or Learn).
- **Hero fall sharpness.** The 36 frames are 1200x750 at 24 samples and look soft. `package.py`
  now disables depth of field and denoises; re-render `--fall 36` at 1600x1000 and convert with
  the snippet in the session (composite on #eee, JPEG q82 into `assets/fall/`).
- Martin asked for everything centred. Page heads, section heads and model rows are centred;
  keep it that way in the Etched layout (centre the hero, two balanced columns below).

## Next, in order

1. Merge the Linux PR after checking it; finish note 22; publish it.
2. Check the home hero fall on a real scroll, at desktop and phone width.
3. Trace: decide between the 35k run and Q4_0-teacher on-policy; queue it on Linux.
4. Foundry: create its GitHub repo once Martin says yes, then a signed release.
