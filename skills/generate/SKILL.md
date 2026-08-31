---
name: generate
description: Produce a tailored resume, cover letter, and optional application-form answers for a job already analyzed by jd-intake. Compiles and compresses the PDFs.
---

## When to use

The user says "generate the resume/cover letter for {Company}", "tailor my CV for
{Company}", or "/generate". Requires `{dir}/analysis.md` from the `jd-intake` skill —
if it is absent, tell the user to run `/jd-intake` first and stop.

## Flags

- `--length 1|2` — résumé page target. Default: `profile.yml`
  `conventions.default_resume_length` (fixture: `1`).
- `--with-projects` — include the Personal Projects section (2-page template only).
  Default: `profile.yml` `conventions.default_include_projects` (fixture: `false`).
  Passing `--with-projects` with `--length 1` forces `--length 2` (the 1-page
  template has no projects block) — warn the user when you do this.
- `--order relevance|chronological` — experience-block ordering. Default
  `chronological` (reverse-chronological, most recent role first). `relevance` orders
  by the ordering decision recorded in `analysis.md` `## Framing`.
- `--answers "Q1; Q2; ..."` — also write `{dir}/answers.md`, one grounded answer per
  `;`-separated question.

## Inputs and paths

- All plugin-internal paths use `${CLAUDE_PLUGIN_ROOT}`: scripts
  (`${CLAUDE_PLUGIN_ROOT}/scripts/*.ps1`), templates
  (`${CLAUDE_PLUGIN_ROOT}/templates/*.tex`), the retriever agent
  (`${CLAUDE_PLUGIN_ROOT}/agents/sot-retriever.md`), and `reference/`
  (`${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`,
  `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`).
- **Template override:** before using a bundled template, check for a repo-level
  override. If `./templates/<name>.tex` exists in the user's working repo, use it
  instead of `${CLAUDE_PLUGIN_ROOT}/templates/<name>.tex`. `<name>` is
  `resume_1page`, `resume_2page`, or `cover_letter`.
- **Source-of-truth dir** and **output dir**: dot-source
  `${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.ps1`, call `Get-JobAppConfig`. It returns
  `Root` (the directory where `jobapp.config.yml` was found by walking up from the
  current working directory, or `(Get-Location).Path` if none), `SourceOfTruthDir`
  (default `resume_sections/`), and `OutputDir` (default `applications/{Company}`).
  The source-of-truth dir is `<Root>/<SourceOfTruthDir>`. `profile.yml` has **no**
  `output_dir` key — resolve `{dir}` by substituting the literal token `{Company}` in
  `.OutputDir` with the company name and joining onto `.Root`
  (e.g. `<Root>/applications/Testco`), exactly as `jd-intake` does.
- `{dir}/analysis.md` must already exist. If not: "run `/jd-intake` for {Company}
  first" and stop.

## Reading `analysis.md` (Task 6 output)

Parse it with these exact rules:

- `## Fit` — the classification is the **first whitespace-delimited token** of the
  first non-blank line under the `## Fit` heading, lower-cased, trailing punctuation
  stripped. It is one of `strong` / `stretch` / `hard-mismatch`. The line has the
  form `<token> — <reason>`.
  **If the token is `hard-mismatch`, STOP.** Tell the user the role is a hard
  mismatch, that `jd-intake` already flagged it, and generate nothing (no `.tex`, no
  PDF, no `answers.md`).
- `## Essential` — a numbered list (`1.`, `2.`, …). Each item is an essential
  criterion with a stable ordinal used by the next section.
- `## Criteria → Evidence` — the heading contains a literal U+2192 arrow `→` (match
  it exactly, not `->`). The body is a table with columns
  `Criterion | Evidence (file:line) | Status`. `Status` is exactly one of `met` /
  `partial` / `gap`. Use the `met`/`partial` rows' `file:line` citations as the
  starting set of evidence to surface; treat `gap` rows as things the résumé must
  **not** claim.
- `## Framing` — lead role(s), ordering decision, emphasis / de-emphasis, and the
  `factual-bounds.md` rules relevant to this application.

## Steps

1. **Load context.** Read `{dir}/analysis.md`, `{sourceDir}/profile.yml`, and
   `{sourceDir}/factual-bounds.md` (load `factual-bounds.md` **verbatim** — it is a
   hard constraint set, not a summary). Apply the `analysis.md` parse rules above.
   If `## Fit` is `hard-mismatch`, stop here.

2. **Retrieve JD-relevant material.** Dispatch the `sot-retriever` agent
   (`${CLAUDE_PLUGIN_ROOT}/agents/sot-retriever.md`) in `retrieve` mode with
   `{ mode: "retrieve", jd: <text of {dir}/jd.md>, sourceDir: <resolved source-of-truth dir> }`.
   It returns ranked bullets per section, each with a `file:line`, plus a `## Gaps`
   block. Every bullet, metric, and named skill you place in the output must trace to
   one of these `file:line` citations (or another confirmed line you read yourself in
   step 1). Do not draft from memory of the conversation.

3. **Select the résumé template.** `--length 1` → `resume_1page`; `--length 2` (or
   `--with-projects`) → `resume_2page`. Resolve the override: repo `./templates/<name>.tex`
   if it exists, else `${CLAUDE_PLUGIN_ROOT}/templates/<name>.tex`.

4. **Fill the résumé template.** See "Résumé placeholders" below for every field.
   - Header (`{{NAME}} {{PHONE}} {{EMAIL}} {{GITHUB_USERNAME}}`): from `profile.yml`,
     verbatim.
   - Industrial Experience: repeat the `\resumeSubheading … \resumeItemListEnd`
     block once per role in `profile.yml` `conventions.roles`, in the order set by
     `--order`. company / title / dates / location come from `profile.yml`
     **verbatim, never re-derived**; tech stack + bullets come from the retriever.
   - Introduction and Skills: from retrieved introduction / skills content.
   - Education: one `\resumeSubheading` line per entry in
     `profile.yml` `conventions.education`.
   - Personal Projects: only with `--with-projects` (2-page template).
   - LaTeX-escape every substituted value (see "LaTeX escaping" below) — in
     particular `C#` → `C\#`, `&` → `\&`.

5. **Bounds check (before writing anything).** Re-read every line you are about to
   place against `factual-bounds.md` and the `analysis.md` `gap` rows:
   - No bullet may claim a technology, employer, project, metric, or scope that a
     bound forbids or that the source of truth does not support.
   - Keep every tech stack tied to the employer/project it belongs to — no blending.
   - No numeric metric appears that is not recorded verbatim in the source of truth.
   - If the JD or `analysis.md` pushes for content that would violate a bound, **STOP
     and ask the user.** Do not silently comply and do not silently omit. If the user
     supplies a new true fact, tell them which source-of-truth file to add it to
     (`companies/<slug>.md`, `skills.md`, `profile.yml`, etc.) and have them re-run
     after updating — do not write it into the résumé from the chat alone.

6. **Write and compile the résumé.** Write `{dir}/resume.tex`. Run:
   `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/compile_latex.ps1 -TexPath {dir}/resume.tex`.
   This is the CLI form: on success it prints `OK: <pdf> (N page…)` to stdout and
   exits 0; on failure it writes the LaTeX log tail to stderr and exits non-zero. It
   returns **no object** — read the exit code and the `OK:` line, exactly as
   `skills/review-application/SKILL.md` does.
   - **Non-zero exit ⇒ failure:** surface the stderr log tail, keep the `.tex`, do
     **not** compress, do **not** claim success. Fix the LaTeX (usually an unescaped
     special character) and recompile.
   - **Page count** is the integer in the `OK: … (N page…)` line. If it exceeds the
     `--length` target: warn the user and list candidate trims (drop the
     lowest-ranked bullet from each role, shorten the intro, drop a de-emphasized
     skill group). Do not ship an over-length résumé silently.

7. **Compress.** On success:
   `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/compress_pdf.ps1 -PdfPath {dir}/resume.pdf`.

8. **Cover letter.** Fill `cover_letter` (override-resolved) — see "Cover-letter
   placeholders" below. Content must follow the cover-letter rules in
   `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md` §7:
   1. state the total professional software-engineering experience duration;
   2. name the specific companies worked at;
   3. name the specific business domains / sectors;
   4. name the specific tech stacks, each tied to the company where it was used.
   Obey every `factual-bounds.md` cover-letter rule (e.g. no university mention).
   Write `{dir}/cover_letter.tex`, then
   `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/compile_latex.ps1 -TexPath {dir}/cover_letter.tex`
   (same CLI contract — non-zero exit ⇒ failure; the `OK: … (N page…)` line must
   report 1 page), then
   `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/compress_pdf.ps1 -PdfPath {dir}/cover_letter.pdf`.

9. **Plain-text cover letter.**
   `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.ps1 -TexPath {dir}/cover_letter.tex`
   → `{dir}/cover_letter.txt` (the script hoists the `Subject:` line to the top).
   Regenerate it any time `cover_letter.tex` changes.

10. **Answers (only if `--answers`).** Write `{dir}/answers.md`: one `##` heading per
    question, each answer grounded in the same retrieved bullets (cite the
    `file:line` inline), followed by a compact one-to-two-sentence variant for
    short-field forms. No new facts beyond the source of truth.

11. **Clean up.** Remove `.aux`, `.log`, **and** `.out` from `{dir}`.
    `compile_latex.ps1` deliberately leaves `.log` (it parses the page count from
    it); `generate` deletes it afterwards. Leave `resume.tex`, `cover_letter.tex`,
    `jd.md`, `analysis.md`, and the PDFs/txt in place.

12. **Report.** Output:
    - every file written, with the résumé's real page count from `compile_latex.ps1`;
    - a table of every metric and every named skill used in the résumé or cover
      letter, each with its source-of-truth `file:line` (Ruling: no claim without a
      citation);
    - any deviation from `profile.yml` conventions (and why);
    - any `analysis.md` `gap` the documents do not paper over (expected — state it);
    - the ordering decision used and whether `--with-projects` forced `--length 2`.

## Résumé placeholders

`templates/resume_1page.tex` and `templates/resume_2page.tex`:

| Placeholder | Fill |
|---|---|
| `{{NAME}}` `{{PHONE}}` `{{EMAIL}}` `{{GITHUB_USERNAME}}` | `profile.yml` `name` / `phone` / `email` / `links.github` — verbatim. `links.github` is the handle only (the template wraps it as `github.com/<handle>`). If `profile.yml` has no `links.github`, replace the whole `$|$ \href{...github...}` fragment in the header with nothing. |
| `{{INTRODUCTION_BULLETS}}` | Inline LaTeX for the Introduction item body: 3–5 short clauses from retrieved `introduction.md` content, each optionally led by `\textbf{Topic:}`. Join clauses with the LaTeX line-break sequence `\\ \vspace{3pt}` (a double backslash then the spacing command), matching the template's Skills block. It sits inside one `\item{ … }` — do not add `\item`. |
| Industrial Experience block — `\resumeSubheading{ {{JOB_TITLE}} }{ {{EMPLOYMENT_DATES}} }{ {{COMPANY_NAME}} }{ {{LOCATION}} }` then `\resumeItemListStart … \resumeItemListEnd` | **A pattern, repeated once per role** in `profile.yml` `conventions.roles` (fixture "Sample Dev" has 2 roles → 2 blocks), ordered per `--order`. `JOB_TITLE` = role `title`; `EMPLOYMENT_DATES` = `"<start> -- <end>"` (en-dash `--`); `COMPANY_NAME` = role `company`; `LOCATION` = role `location` — **all four verbatim from `profile.yml`**. |
| `{{TECH_STACK}}` | The retrieved "Integrated Tech Stack" line for **that** company (`companies/<slug>.md`), JD-relevant subset allowed, never blended with another company. Rendered as the first `\resumeItem{\textbf{Tech Stack:} …}`. |
| `{{BULLET_POINT_1..3}}` | Retrieved bullets for that role, best-first. **The count is not fixed at 3** — emit as many `\resumeItem{…}` lines as the role warrants (3–6). Add or delete `\resumeItem{…}` lines within the block; drop the `{{BULLET_POINT_N}}` tokens you do not use. Each bullet verb-first, past tense (present only for an ongoing duty in a current role). |
| `{{EDUCATION_ENTRIES}}` | One line per entry in `profile.yml` `conventions.education`: `\resumeSubheading{<institution>}{<start> -- <end>}{<credential>}{<location>}`. No GPA / grades / distinctions (experienced-hire default). |
| `{{LANGUAGES_LIST}}` | Comma-separated languages from the `### Core Languages` group in `<Root>/<SourceOfTruthDir>/skills.md`, JD-relevant subset. Read that file directly for the category grouping — `sot-retriever` `retrieve` mode returns flat ranked bullets, not `###` categories. Label in template: "Programming Languages" (1-page) / "Core Languages" (2-page). |
| `{{FRAMEWORKS_AND_TOOLS_LIST}}` | Comma-separated frameworks / tools / platforms / concepts from the other `###` groups in `<Root>/<SourceOfTruthDir>/skills.md` (same direct read), JD-relevant subset. |

`resume_2page.tex` only — Personal Projects (filled **only** with `--with-projects`;
also a repeat-per-project pattern, one block per relevant `projects/<slug>.md`):
`{{PROJECT_NAME}}` (project name), `{{PROJECT_GITHUB_URL}}` (repo URL, or replace the
`\href{…}{\underline{…}}` wrapper with the bare name if none), `{{PROJECT_TECH_STACK}}`,
`{{PROJECT_ROLE}}` (e.g. "Personal project"), `{{PROJECT_BULLET_1..2}}` (retrieved
project bullets; add/remove `\resumeItem{…}` lines as needed). If `--with-projects` is
not set, use `resume_1page` / `resume_2page` with the Personal Projects section
deleted entirely.

## Cover-letter placeholders

`templates/cover_letter.tex`:

| Placeholder | Fill |
|---|---|
| `{{NAME}}` `{{PHONE}}` `{{EMAIL}}` `{{GITHUB_USERNAME}}` | Same as the résumé header, from `profile.yml`. |
| `{{DATE}}` | Today's date, long form, e.g. `September 1, 2026`. |
| `{{RECIPIENT_NAME}}` | The named contact from the JD if it gives one; else `Hiring Manager`. |
| `{{RECIPIENT_TITLE}}` | Used in the `Dear {{RECIPIENT_TITLE}},` salutation. The contact's title from the JD if given; else `Hiring Manager`. |
| `{{COMPANY_NAME}}` | The hiring company's name as the JD states it (`{dir}/jd.md`). If the JD names no company, fall back to the `{Company}` argument. |
| `{{COMPANY_ADDRESS}}` | The office location from the JD (`{City}, {Region}, {Country}`). If the JD gives only a city, use that; if it gives nothing, delete the `{{COMPANY_ADDRESS}} \\` line from the recipient block. |
| `{{JOB_TITLE}}` | The role title from the JD. |
| `{{REQ_ID}}` | The requisition / reference ID from the JD. **If the JD has none**, delete the entire ` (Ref / Req ID: {{REQ_ID}})` fragment from the subject line so it reads `Subject: Application for the Position of <JOB_TITLE>` — no dangling "Ref: ". |
| `{{INTRO_PARAGRAPH}}` | Opening: the role applied for + company, and the total professional SDE experience duration (workflow-rules §7.1). |
| `{{BODY_PARAGRAPH_1}}` `{{BODY_PARAGRAPH_2}}` | The evidence paragraphs. Between them they must name the companies (§7.2), the business domains / sectors (§7.3), and the company-tied tech stacks (§7.4) — every stack tied to the company it was used at, consistent with the source of truth. Draw only on retrieved material. |
| `{{OUTRO_PARAGRAPH}}` | Close: fit summary + thanks. No overclaiming of `gap` criteria. |

`factual-bounds.md` still applies to the letter — e.g. "Do not mention the
university in cover letters" means no `conventions.education` institution appears
anywhere in `cover_letter.tex`.

## LaTeX escaping

Every value substituted into a template must be LaTeX-safe. Replace, in each
substituted value: `\` → `\textbackslash{}`, then `&` → `\&`, `%` → `\%`, `$` → `\$`,
`#` → `\#`, `_` → `\_`, `{` → `\{`, `}` → `\}`, `~` → `\textasciitilde{}`, `^` →
`\textasciicircum{}`. The common real cases here: `C#` → `C\#`, `Frameworks & Tools`
label already escaped in the template, `R&D` → `R\&D`. Do not escape LaTeX you are
deliberately emitting (`\resumeItem`, `\textbf`, `--`).

## Guardrails

- Company names, job titles, employment dates, and locations come from `profile.yml`
  **verbatim** — never re-derived from the JD or the conversation.
- No skill, tool, employer, project, or metric appears that is not in the
  source-of-truth directory. A genuine gap stated honestly is the expected outcome
  for some criteria; papering over it is a bounds violation.
- `factual-bounds.md` is a hard constraint. On any conflict: STOP and ask.
- English-only output regardless of conversation language.
- `jd.md` stays in `{dir}` (workflow-rules §5) — this skill never deletes it.
- Full workflow rules: `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`.
  ATS checklist: `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`.
