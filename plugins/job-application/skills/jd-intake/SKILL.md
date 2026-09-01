---
name: jd-intake
description: Analyze a job description - save it verbatim, extract essential/desirable criteria, map each criterion to source-of-truth evidence, and classify fit. Run before generate.
---

## When to use

The user pastes a job description, uploads a JD file, or says "analyze this JD for
{Company}", "assess fit for {Company}", or "/job-application:jd-intake". Run this
before the `generate` skill so the resume/cover-letter step drafts from retrieved
evidence, not from memory of the conversation.

## Steps

1. **Resolve `{Company}` and the output directory.**
   - Determine `{Company}` from what the user said. If it is unclear or missing, ask
     before continuing.
   - Run `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.py`,
     which prints the resolved config as JSON. It returns a `root` key — the
     directory where `jobapp.config.yml` was found by walking up from the current
     working directory, or the current directory if none is found — plus
     `browser_path`, `source_of_truth_dir`, and `output_dir`.
   - Take `output_dir` (default `applications/{Company}`), substitute the literal
     token `{Company}` with the company name, then join onto `root`: `{dir}` is
     `<root>/<output_dir with {Company} substituted>` (e.g.
     `<root>/applications/Testco`). Create the directory if absent (`mkdir -p`
     semantics).
   - Also resolve the source-of-truth dir as `<root>/<source_of_truth_dir>` (default
     `resume_sections/`) — the retrieve step needs it. If it does not exist, tell the
     user to run `/job-application:ingest` first and stop.

2. **Save the raw JD.** Write the job description **verbatim** — exactly as the user
   provided it, no reformatting, no trimming — to `{dir}/jd.md`.

3. **Extract the JD structure into `{dir}/analysis.md`.** Write these sections, in
   this order:
   - `## Essential` — the must-have criteria. **Always emit this as a numbered list
     (`1.` `2.` …), regardless of the JD's own formatting**, so later sections and
     downstream steps have a stable anchor like "essential criterion 4". Verbatim
     wording where possible.
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
   - The retriever returns bullets grouped by source file plus a `## Gaps` block; it
     does **not** emit a status. You must re-pivot that output onto one row per
     essential criterion, and YOU assign each row's Status (`met` / `partial` /
     `gap`) by judging whether the cited bullets actually satisfy that criterion. A
     criterion with no supporting bullet and a matching entry in the retriever's
     `## Gaps` block is `gap`.
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

5. **Write `## Fit`.** Write the classification as the FIRST word of the section's
   first line, followed by ` — ` and the one-sentence reason. Exactly:
   `<token> — <reason>` where `<token>` is one of `strong` / `stretch` /
   `hard-mismatch` (verbatim, lowercase). Nothing precedes the token on that line —
   no bullet, no bold, no "Fit:" prefix. Later steps parse the first word of this
   line, so a stray capitalised word (e.g. a criterion named "Strong relational
   database skills") must never lead it.
   - `strong` — most essentials `met`, no hard gap.
   - `stretch` — real gaps, but a credible transferable story (adjacent tools or
     domain, clearly learnable from what is present).
   - `hard-mismatch` — an essential requires years of something entirely absent from
     the source of truth and there is no transferable bridge.

   Worked example:
   `stretch — Meets the core API/SQL/Python essentials; the iPaaS and HL7/FHIR gaps are bridgeable with framing.`

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
