---
name: jd-intake
description: Analyze a job description — save it verbatim, extract essential/desirable criteria, map each criterion to source-of-truth evidence, and classify fit. Run before generate.
---

## When to use

The user pastes a job description, uploads a JD file, or says "analyze this JD for
{Company}", "assess fit for {Company}", or "/jd-intake". Run this before the
`generate` skill so the resume/cover-letter step drafts from retrieved evidence, not
from memory of the conversation.

## Steps

1. **Resolve `{Company}` and the output directory.**
   - Determine `{Company}` from what the user said. If it is unclear or missing, ask
     before continuing.
   - Dot-source `${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.ps1` and call
     `Get-JobAppConfig`. `Get-JobAppConfig` walks up from the current working
     directory to find `jobapp.config.yml`; the defaults it returns are taken
     relative to that root (the directory containing `jobapp.config.yml`, or the cwd
     if none is found).
   - Take `.OutputDir` (default `applications/{Company}`). Substitute the literal
     token `{Company}` in that template string with the company name (e.g.
     `applications/Testco`). Create the directory if absent (`mkdir -p` semantics).
   - Also take `.SourceOfTruthDir` (default `resume_sections/`) — the retrieve step
     needs it. If it does not exist, tell the user to run `/ingest` first and stop.

2. **Save the raw JD.** Write the job description **verbatim** — exactly as the user
   provided it, no reformatting, no trimming — to `{dir}/jd.md`.

3. **Extract the JD structure into `{dir}/analysis.md`.** Write these sections, in
   this order:
   - `## Essential` — the must-have criteria, bulleted, verbatim where possible.
     Number them if the JD numbers them, so later sections can refer to "essential
     #4".
   - `## Desirable` — the nice-to-have criteria.
   - `## Responsibilities` — what the person will actually do day to day.
   - `## Keywords` — the concrete skills, tools, and domain terms an ATS would scan
     for (technologies, protocols, platforms, methodologies).
   - `## Language / Stack emphasis` — what this role leads with (primary language,
     backend vs front-end weighting, database, platform tooling); one short
     paragraph or a few bullets.

4. **Retrieve evidence and build `## Criteria → Evidence`.**
   - Dispatch the `sot-retriever` agent
     (`${CLAUDE_PLUGIN_ROOT}/agents/sot-retriever.md`) in `retrieve` mode with
     `{ mode: "retrieve", jd: <the JD text>, sourceDir: <resolved source-of-truth dir> }`.
     It returns the most relevant bullets per section, each annotated with its
     `file:line`, plus a `## Gaps` list of things the JD asks for that are absent
     from the source of truth.
   - Append `## Criteria → Evidence` to `analysis.md`: a table with columns
     `Criterion | Evidence (file:line) | Status`. One row per **essential**
     criterion (add desirable criteria as extra rows only if they materially affect
     framing).
   - `Status` is exactly one of `met` / `partial` / `gap`:
     - `met` — the source of truth clearly satisfies the criterion; cite the
       `file:line`(s).
     - `partial` — related evidence exists but falls short (wrong specific tool,
       less depth/duration than asked, adjacent domain); cite what exists and name
       the shortfall.
     - `gap` — nothing in the source of truth supports it. Evidence cell is `—`.
   - Every `met` and `partial` row MUST cite a real `file:line` that exists in the
     source-of-truth directory. Never write a `file:line` you have not confirmed.

5. **Write `## Fit`.** State one classification token — exactly one of:
   - `strong` — most essentials `met`, no hard gap.
   - `stretch` — real gaps, but a credible transferable story (adjacent tools or
     domain, clearly learnable from what is present).
   - `hard-mismatch` — an essential requires years of something entirely absent from
     the source of truth and there is no transferable bridge.

   Follow the token with one sentence of reasoning that names the deciding
   criteria. Use the token verbatim and lowercase — later steps parse this line.

6. **Write `## Framing`.**
   - Which role(s) to lead with and why (relevance to this JD).
   - Ordering: relevance vs strict reverse-chronological.
   - Language / stack emphasis for the resume, and what to de-emphasize.
   - Which rules in `<sourceDir>/factual-bounds.md` are relevant to this application
     (technologies to keep scoped to a specific employer/project, claims never to
     make, metrics not to invent, cover-letter constraints).

7. **If `## Fit` is `hard-mismatch`,** tell the user plainly, in the chat, that the
   role is a hard mismatch and recommend skipping it before they invest effort in a
   tailored application. Do not run `generate`. Do not produce a resume or cover
   letter.

## Guardrails

- Every `met` / `partial` row cites a real `file:line` in the source-of-truth
  directory. No invented evidence, no guessed line numbers.
- Never soften a `gap` to `partial` without a concrete citation for the partial
  evidence. A genuine gap stated honestly is the expected outcome for some criteria.
- Do not add a skill, tool, employer, or metric that is not in the source of truth
  just because the JD asks for it — that is a `gap`, not a `met`.
- `jd.md` is verbatim. `analysis.md` always has all eight `##` sections in order:
  `## Essential`, `## Desirable`, `## Responsibilities`, `## Keywords`,
  `## Language / Stack emphasis`, `## Criteria → Evidence`, `## Fit`, `## Framing`.
- This skill only reads the source of truth and writes `jd.md` + `analysis.md`. It
  does not run LaTeX or generate application documents — that is the `generate`
  skill.
- Full workflow rules: `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`.
