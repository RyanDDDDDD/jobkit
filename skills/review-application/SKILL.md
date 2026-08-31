---
name: review-application
description: QA a generated application (resume + cover letter) against factual bounds, JD coverage, internal consistency, ATS parseability, and writing quality. Run after generate, before you send.
---

## When to use

The user says "review the {Company} application", "QA the resume for {Company}", or
"/review-application". Runs after `generate`. Requires a per-application `{dir}` that
already contains `resume.tex`, `cover_letter.tex`, and `analysis.md`. If any of the
three is missing, tell the user to run `/generate` for that company first and stop.

## Flags

- `--fix` — after writing `review.md`, apply the unambiguous safe corrections
  (see "Output" below), then re-run every check **once** and rewrite `review.md`.
  Without `--fix` this skill only reports; it never edits `resume.tex` or
  `cover_letter.tex`.

## Inputs and paths

- All plugin-internal paths use `${CLAUDE_PLUGIN_ROOT}`: the config loader
  (`${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.ps1`), the plain-text cover-letter
  script (`${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.ps1`), the LaTeX
  compiler (`${CLAUDE_PLUGIN_ROOT}/scripts/compile_latex.ps1`), and `reference/`
  (`${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`,
  `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`).
- **Source-of-truth dir** and **output dir**: dot-source
  `${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.ps1`, call `Get-JobAppConfig`. Take
  `.SourceOfTruthDir` (default `resume_sections/`) and `.OutputDir` (default
  `applications/{Company}`). Resolve `{dir}` by substituting the literal token
  `{Company}` in `.OutputDir` with the company name, exactly as `jd-intake` and
  `generate` do (e.g. `applications/Testco`).

## Load context first

Read, before running any check:

- `{dir}/resume.tex`, `{dir}/cover_letter.tex`, `{dir}/analysis.md`, and
  `{dir}/cover_letter.txt` if it exists.
- `{sourceDir}/profile.yml` and `{sourceDir}/factual-bounds.md` — load
  `factual-bounds.md` **verbatim**; it is a hard constraint set, not a summary.
- The `{sourceDir}` section files that the résumé's claims should trace to
  (`companies/*.md`, `projects/*.md`, `introduction.md`, `skills.md`,
  `education.md`).
- `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md` (cover-letter §7, redundancy
  §3, no-hallucination §2) and `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`.

### Parsing `analysis.md`

- `## Essential` — a numbered list (`1.`, `2.`, …). Each item is one essential
  criterion with a stable ordinal. This list drives the **JD coverage** group.
- `## Criteria → Evidence` — the heading contains a literal U+2192 `→`. Table
  `Criterion | Evidence (file:line) | Status`, `Status` ∈ `met` / `partial` / `gap`.
  Treat every `gap` row as a claim the résumé and cover letter must **not** make.
- `## Fit` — first whitespace-delimited token of the first non-blank line under the
  heading, lower-cased. If it is `hard-mismatch`, note in `review.md` that the
  application should not have been generated and flag the whole thing.

## Checks — write `{dir}/review.md`

### 1. Compliance
- Every factual claim in `resume.tex` and `cover_letter.tex` (employers, titles,
  dates, technologies, projects, domains, metrics) traces to a specific
  source-of-truth line. Anything that does not is a **Flag**.
- No `factual-bounds.md` rule is violated. For each violation quote the rule
  verbatim **and** the offending text from the document.
- No numeric metric appears that is not recorded verbatim in `{sourceDir}`. A number
  in the résumé with no source-of-truth line is a **Flag** (or a **Fix** only if the
  safe correction is an unambiguous deletion of an adjective, not a number).

### 2. JD coverage
- For each numbered `## Essential` criterion in `analysis.md`, find at least one
  résumé bullet (or skills-line entry) that supports it. List every uncovered
  essential criterion.
- Cross-check against `## Criteria → Evidence`: a criterion marked `met` /
  `partial` there but absent from the résumé is a **Flag**; a criterion marked `gap`
  that the résumé nonetheless claims is a **compliance violation**, not coverage.

### 3. Consistency
- **Company / title / dates** in `resume.tex` match `{sourceDir}/profile.yml`
  `conventions.roles` **exactly, character for character**. Report every deviation
  with both strings (résumé vs `profile.yml`).
- Education institution / credential / dates match `profile.yml`
  `conventions.education` exactly.
- One tense throughout: past tense for finished work, present only for an ongoing
  duty in a current role, applied the same way in every entry. List every bullet
  that breaks the pattern.
- Résumé length matches the intended target (`--length` used by `generate`, else
  `profile.yml` `conventions.default_resume_length`). Recompile if needed:
  `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/compile_latex.ps1 -TexPath {dir}/resume.tex`
  and read the page count from the `OK:` line.

### 4. ATS & quality
- Single column; standard headings (`Introduction` / `Experience` / `Skills` /
  `Education` / `Projects`); no content locked in `tabular`/`minipage`/text boxes
  beyond the template's own heading rules; selectable text. Walk
  `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`.
- Every bullet is verb-first. Quantified where — and only where — a real
  source-of-truth number supports it.
- No two bullets in the résumé (or across résumé and cover letter) are
  near-duplicates (`reference/workflow-rules.md` §3).

### 5. Cover letter
- Follows `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md` §7: states total
  professional SDE experience duration; names the specific companies; names the
  specific business domains / sectors; names the company-tied tech stacks (each
  stack tied to the employer it belongs to, never blended).
- Obeys every `factual-bounds.md` cover-letter rule (e.g. no university named
  anywhere in `cover_letter.tex` if a bound says so).
- One page.
- `{dir}/cover_letter.txt` exists and is **current**: regenerate a scratch copy with
  `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.ps1 -TexPath {dir}/cover_letter.tex -OutPath <temp>`
  and diff it against the committed `cover_letter.txt`. Any difference (or a missing
  `.txt`) means the `.txt` is stale.

## Output — `{dir}/review.md`

Three sections, always in this order:

- `## Pass` — every check group that passed cleanly, one line each.
- `## Flag` — issues that need a **human judgement call**: possible unsupported
  claims, uncovered essential criteria, near-duplicate bullets, length overflow,
  weak cover-letter coverage, a `hard-mismatch` fit. For each: what, where
  (`file` + the line or bullet text), and why it matters. Never auto-fix these.
- `## Fix` — corrections that are **unambiguous and safe**. For each: the exact
  before/after.

Only these count as safe auto-fixes under `--fix`:

1. **Tense** — a past-role bullet written in present tense where every sibling
   bullet is past tense (and it is not an ongoing duty in a current role).
2. **`profile.yml` mismatch** — a company name, job title, employment date, or
   education field in the document that differs from `profile.yml`; rewrite the
   document to match `profile.yml` **verbatim** (`profile.yml` wins, always).
3. **Stale `cover_letter.txt`** — regenerate it with
   `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.ps1 -TexPath {dir}/cover_letter.tex`.

Anything touching the substance of a claim, the selection of evidence, or the
wording of an argument is a **Flag**, never a **Fix**.

## `--fix` behaviour

1. Write `review.md` from the first pass.
2. Apply every item in `## Fix` (and only those). If a fix edits `cover_letter.tex`,
   regenerate `cover_letter.txt` afterwards. If a fix edits `resume.tex` or
   `cover_letter.tex`, recompile the affected document
   (`${CLAUDE_PLUGIN_ROOT}/scripts/compile_latex.ps1`) and, on success, recompress
   (`${CLAUDE_PLUGIN_ROOT}/scripts/compress_pdf.ps1`). If a recompile fails, revert
   that edit, move the item to `## Flag`, and keep going.
3. Re-run every check **once**. Rewrite `review.md` with the new results and an
   `## Applied` note listing what was changed.
4. Do not loop a third time — remaining issues stay in `## Flag` / `## Fix` for the
   user.

## Guardrails

- This skill reads the source of truth and `{dir}`; it writes `{dir}/review.md`, and
  under `--fix` also `resume.tex` / `cover_letter.tex` / `cover_letter.txt` / the
  PDFs. It never edits `{sourceDir}` and never touches `jd.md` or `analysis.md`.
- `profile.yml` is authoritative for company names, titles, dates, and locations —
  on any mismatch the document is wrong, not `profile.yml`.
- `factual-bounds.md` is a hard constraint. A bounds violation is always a `## Flag`
  (or `## Fix` only when the safe correction is a verbatim `profile.yml` match).
- A genuine, honestly-stated gap is the expected outcome for some criteria — do not
  flag an application for *not* claiming something it has no basis to claim.
- English-only output. Full workflow rules:
  `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`.
