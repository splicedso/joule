# Who the box is for (internal, 2026-10-27 13:03 PT)

Martin, 27 October: "find a niche we can fit into". The box is in `ai-computer.md`: a small machine that runs
open-weight models with no internet and no cloud API. `portable-ai.md` found no buyer for a battery-powered LLM
server. This picks a buyer for the office box instead. Sources are linked at the end. Most are vendor and law-firm
pages, so treat prices as list prices and legal readings as commentary, not rulings.

## The pick: small US defense and ITAR shops

Machine shops, electronics makers and engineering firms of 10 to 200 people that hold Controlled Unclassified
Information (CUI) or ITAR technical data: drawings, specs, test reports. They have a legal reason not to paste that
data into ChatGPT or Claude, no IT department to run a GPU server, and no cheap way to get AI today.

**Why they can't use the usual tools.**
- DFARS 252.204-7012 requires any cloud service that stores or processes covered defense information to meet FedRAMP
  Moderate. The commercial versions of ChatGPT, Claude and Copilot do not.
- NIST SP 800-171 applies to every system that handles CUI, so an AI tool that sees CUI is inside the assessment
  boundary like any other computer.
- ITAR technical data must not reach foreign persons, which a public cloud service cannot promise.

**What they can buy today.**
- Microsoft 365 Copilot in GCC High: about $30 per user per month, on top of a GCC High licence of about $39 per user
  per month, after a move to GCC High.
- Appliances priced for larger firms: Entropic Black from $30,000 plus $2,000 a month; ibl.ai pilots from $15,000;
  VRLA Tech and LLM.co by quote.
- Per-seat software for their own PCs: AirgapAI, from $697 per user perpetual.
- Do it themselves: a DGX Spark or a Mac Studio and someone who can set it up.

**The gap is a box they plug in.** A small, quiet machine, priced like a few years of Copilot seats, that sits inside
their CUI boundary, sends nothing out, and needs no IT staff. That is the Spliced box with a short list of features
added.

**Why us.**
- The box is offline by design: no telemetry, no account, no cloud. In this niche that is the main requirement, not a
  limitation.
- We pick the models and settings by measured joules per correct answer on the exact hardware (notes 19 to 33). We
  can show what the box gets right, not just what it runs.
- It needs no data centre: one machine under 5 litres, at about 100 W running a model.

## What this niche would require that the box lacks

1. **Accounts and an audit log**: a named login for each person, and a record of every prompt and answer that stays
   on the box. The box server has no login today.
2. **FIPS-validated encryption** for data at rest and on the network. Spliced Linux is our own image and has no
   validated module. The likely fix is building on a distribution that has one, not validating our own.
3. **Offline updates**: signed model and software updates from a USB stick, with no network path to us.
4. **Documents for their assessment**: a short paper the shop can put in its System Security Plan. It covers what the
   box stores, where, who can reach it, and that nothing leaves.
5. **Documents as the first use**: ask questions of their own drawings, specs and procedures, cited to the page.
   Foundry is chat only today.

Items 1, 3 and 5 are software the Claude sessions can build. Item 2 decides the operating system. Item 4 is writing.

**What item 2 takes (Linux session's check, 27 October).** Disk encryption counts only on the exact kernel a FIPS 140-3
certificate names, so the kernel must be both certified and new enough for this GPU (gfx1151 needs Linux 6.9 or later).
Our image is Debian, which has no certificate. Of the active certificates, only Rocky Linux 9 with CIQ's FIPS kernel
(certificate 5452) covers a kernel that knows gfx1151; RHEL 9, Alma 9, Oracle 9, Ubuntu 22.04 and 24.04, SLES 15 and Amazon
Linux 2023 certify older kernels. RHEL 10, SLE 16 and Amazon Linux's 6.12 kernel have no certificate yet. So the one path today
is a Rocky 9 image on CIQ's subscription (price not published, untested on this board, without the newer ROCm fixes; Vulkan is
fine). Network encryption is easier: the distributions' OpenSSL modules carry their own certificates.

## Risks, plainly

- **The deadline that drove urgency is paused.** The Department of War suspended CMMC Phase 2 (third-party Level 2
  assessments) on 13 July 2026, with no restart date. DFARS 7012, NIST SP 800-171 and Level 2 self-assessments
  still apply, and so does ITAR, but fewer shops are being pushed to act this year.
- **The rules may change.** The FY2026 NDAA (section 1513) tells the department to write an AI security framework
  into DFARS and CMMC, with no date. It could favour approved clouds over boxes.
- **Defence buys software through integrators.** `portable-ai.md` found defence buys air-gapped AI as software. That
  holds for primes; small shops are the bet here, and they are reached through managed service providers that do
  their compliance, not directly.
- **A box is not compliance.** We can make the box easy to fit inside a boundary; the shop's assessment still covers
  it. We must never claim "CMMC compliant" or "ITAR certified": no such certification exists for a product.
- **Model export.** Shipping open-weight models is not itself a problem, but the shop's data must never leave the box,
  including in support. We never touch a customer's box remotely.

## Second choices, and why not first

- **Small law firms.** Confidentiality is a real driver, but ABA Formal Opinion 512 lets lawyers use cloud AI with
  care, and the market is crowded (Harvey, Entropic, ibl.ai, iternal).
- **Tax preparers.** Section 7216 makes disclosing return information a crime, and commentators treat pasting it into
  a public AI tool as disclosure. But the IRS has not ruled on AI, whether a local model avoids 7216 is unsettled,
  the work is seasonal, and preparers live inside tax software we don't touch.

## First step (no purchase, no customer contact without Martin)

Make the five people of milestone 4 (`ai-computer.md`) five people at small defense or ITAR shops, found through
managed service providers that serve them. Before that, build items 1 and 5 on the box we own. Item 1 is accounts and
the audit log; item 5 is document questions on a sample engineering spec. Then measure accuracy and joules per correct
answer on that spec, as for every other result.

## Sources

- [Secureframe: AI governance for CMMC Level 2](https://secureframe.com/blog/cmmc-level-2-ai-governance)
- [Spheron: CMMC 2.0 and self-hosted models](https://www.spheron.network/blog/cmmc-2-0-compliant-gpu-cloud-defense-contractor-guide-2026/)
- [Elevate Consult: the AI framework coming to CMMC](https://elevateconsult.com/insights/ai-framework-coming-to-cmmc-what-defense-contractors-need-to-know-before-implementation/)
- [Clark Hill: DoW pauses CMMC Phase 2](https://www.clarkhill.com/news-events/news/dow-pauses-cmmc-phase-2-defense-contractors/)
- [cmmcmap: what applies after the suspension](https://cmmcmap.com/blog/november-2026-cmmc-deadline/)
- [Daymark: Microsoft 365 Copilot licensing in GCC High](https://www.daymarksi.com/blog/microsoft-365-copilot-licensing-in-gcc-high-what-it-costs-what-you-need-and-how-to-pilot-without-over-buying)
- [Entropic Black](https://entropic.qu.ai/black), [VRLA Tech](https://vrlatech.com/ai-workstations-gpu-servers-for-defense-contractors-vrla-tech/), [iternal: AI for government contractors](https://iternal.ai/ai-for-government-contractors), [iternal: private AI appliances](https://iternal.ai/best-private-ai-appliances)
- [Morris Manning & Martin: tax return information, consent and AI](https://mmmpressions.mmmlaw.com/post/102ity8/tax-return-information-consent-and-ai)
- [Winthrop: return preparers using AI under 7216](https://winthrop.com/bold-perspectives/you-may-be-a-return-preparer-using-ai-without-violating-sections-7216-and-6713/)
