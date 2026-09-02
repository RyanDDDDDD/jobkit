---
name: review-application
description: QA a generated application (resume + cover letter) against factual bounds, JD coverage, internal consistency, ATS parseability, and writing quality. Run after generate, before you send.
---

## When to use

The user says "review the {Company} application", "QA the resume for {Company}", or
"/job-application:review-application". Runs after `generate`. Requires a
per-application `{dir}` that already contains `tmp/resume.data.json`,
`tmp/cover_letter.data.json`, and `analysis.md`. If any of the three is missing, tell
the user to run `/job-application:generate` for that company first and stop.

## Flags

- `--fix` — after writing `review.md`, apply the unambiguous safe corrections
  (see "Output" below), then re-run every check **once** and rewrite `review.md`.
  Without `--fix` this skill only reports; it never edits `tmp/resume.data.json` or
  `tmp/cover_letter.data.json`.

## Inputs and paths

- All plugin-internal paths use `${CLAUDE_PLUGIN_ROOT}`: the config loader
  (`${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.py`), the plain-text cover-letter
  script (`${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.py`), the HTML→PDF
  renderer (`${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py`) — all run via `uv run
  --project ${CLAUDE_PLUGIN_ROOT}` — the bundled templates
  (`${CLAUDE_PLUGIN_ROOT}/templates/resume.html`,
  `${CLAUDE_PLUGIN_ROOT}/templates/cover_letter.html`), and `reference/`
  (`${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`,
  `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`).
- **Source-of-truth dir** and **output dir**: run `uv run --project
  ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.py`, which prints
  the resolved config as JSON. It returns `root` (the directory where
  `jobapp.config.yml` was found by walking up from the current working directory, or
  the current directory if none), `browser_path` (a machine hint, may be `null`),
  `source_of_truth_dir` (default `resume_sections/`), and `output_dir` (default
  `applications/{Company}`). The source-of-truth dir is `<root>/<source_of_truth_dir>`.
  `profile.yml` has **no** `output_dir` key — resolve `{dir}` by substituting the
  literal token `{Company}` in `output_dir` with the company name and joining onto
  `root` (e.g. `<root>/applications/Testco`), exactly as `jd-intake` and `generate` do.
- **Layout:** the résumé / cover-letter `.data.json` files this skill reads (and,
  under `--fix`, edits) live in `{dir}/tmp/`; `review.md`, `cover_letter.txt`, and
  the PDFs are flat in `{dir}`. See
  `${CLAUDE_PLUGIN_ROOT}/reference/output-layout.md`.
- If a repo-level `templates/` dir exists under `root`, its `resume.html` /
  `cover_letter.html` override the plugin's bundled ones — use the resolved path for
  the render check.

## Load context first

Read, before running any check:

- `{dir}/tmp/resume.data.json`, `{dir}/tmp/cover_letter.data.json`,
  `{dir}/analysis.md`, and `{dir}/cover_letter.txt` if it exists.
- `{sourceDir}/profile.yml` and `{sourceDir}/factual-bounds.md` — load
  `factual-bounds.md` **verbatim**; it is a hard constraint set, not a summary.
- The `{sourceDir}` section files that the résumé's claims should trace to
  (`companies/*.md`, `projects/*.md`, `introduction.md`, `skills.md`,
  `education.md`).
- `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md` (cover-letter §7, redundancy
  §3, no-hallucination §2) and `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`.

Both `.data.json` files follow design amendment §3: `name` / `lang` / `contact`,
the résumé's `intro[]` (`{lead, text}`) and `sections[]` (each `type` ∈
`entries` | `education` | `skills` | `list`), and the letter's `recipient[]` /
`subject` / `paragraphs[]`. All strings are plain text (the renderer escapes them);
there is no markup to parse.

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
- Every factual string in `resume.data.json` and `cover_letter.data.json` (employers,
  titles, dates, locations, technologies in `stack` / `groups[].value`, project
  names, domains, metrics, and every `bullets[]` / `paragraphs[]` claim) traces to a
  specific source-of-truth line. Anything that does not is a **Flag**.
- "Traces to" allows reframing. A bullet that re-languages, re-weights, or combines
  real source-of-truth material to match JD wording is supported as long as the
  underlying claim is rooted in a real line — do not flag it merely for being phrased
  differently than the source file, leading with a transferable angle, or mapping
  real evidence onto JD keywords. Flag only claims with **no** such root: a
  `factual-bounds.md` violation, or a zero-basis claim (a tool, domain, employer, or
  metric with no grounding in any real experience).
- No `factual-bounds.md` rule is violated. For each violation quote the rule
  verbatim **and** the offending text (the exact JSON string value).
- No numeric metric appears that is not recorded verbatim in `{sourceDir}`. A number
  in the résumé with no source-of-truth line is a **Flag** (or a **Fix** only if the
  safe correction is an unambiguous deletion of an adjective, not a number).

### 2. JD coverage
- For each numbered `## Essential` criterion in `analysis.md`, find at least one
  résumé bullet (or `skills` group entry) that supports it. List every uncovered
  essential criterion.
- Cross-check against `## Criteria → Evidence`: a criterion marked `met` /
  `partial` there but absent from the résumé is a **Flag**; a criterion marked `gap`
  that the résumé nonetheless claims is a **compliance violation**, not coverage.

### 3. Consistency
- **Experience items.** For every `sections[]` entry of `type: "entries"` that
  represents a role, `items[].primary`, `items[].secondary`, `items[].location`,
  and `items[].dates` match `{sourceDir}/profile.yml` `conventions.roles`
  **verbatim, character for character** — `primary` == role `title`, `secondary` ==
  role `company`, `location` == role `location`, `dates` == `"<start> – <end>"`
  (space–en-dash–space, `start`/`end` verbatim). Report every deviation with both
  strings (JSON vs `profile.yml`).
- **Education items.** Each `type: "education"` `items[]` entry matches `profile.yml`
  `conventions.education` verbatim — `institution`, `credential`, `location`, and
  `dates` == `"<start> – <end>"`.
- One tense throughout `bullets[]`: past tense for finished work, present only for
  an ongoing duty in a current role, applied the same way in every entry. List every
  bullet that breaks the pattern.
- Résumé length: see **Length** below.

### 4. ATS & quality
- Render the résumé (or read an existing `{dir}/resume.pdf`):
  `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py
  --template-path <resume.html> --data-path {dir}/tmp/resume.data.json --out-path
  <temp>.pdf`. Then run `uv run --project ${CLAUDE_PLUGIN_ROOT}
  ${CLAUDE_PLUGIN_ROOT}/scripts/extract_cv.py <temp>.pdf` and assert the candidate
  `name` **and** every
  company name (`items[].secondary`) appear in the extracted text — these round-trip
  cleanly. (Some ligature clusters — `ft`, `fi` — and a leading `+` do not survive
  text extraction on the bundled fonts; do not assert on strings that contain them.
  Also assert the PDF text does **not** contain `Invalid resume JSON` — that string
  is the renderer's fallback when the JSON is the wrong shape.)
- The bundled template is single-column with standard headings (`Introduction` /
  the experience title / `Skills` / `Education` / `Projects`) **by construction** —
  confirm the section `title`s in the JSON are conventional, not creative renames.
- Every bullet is verb-first. Quantified where — and only where — a real
  source-of-truth number supports it.
- No two bullets in the résumé (or across résumé and cover letter) are
  near-duplicates (`reference/workflow-rules.md` §3).
- Walk `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md` for anything else.

### 5. Length
- Take `Pages` from the render above (the `OK: <pdf> (N page[s])` line, or the
  `.Pages` field). Compare against `--max-pages` (the value `generate` used, else
  default **2**). Over the ceiling ⇒ `## Flag` with the page count and candidate
  trims. **Never a `## Fix`** — trimming evidence is a human judgement call.

### 6. Cover letter
- `cover_letter.data.json` follows `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`
  §7: between the `paragraphs[]` it states total professional SDE experience
  duration; names the specific companies; names the specific business domains /
  sectors; names the company-tied tech stacks (each stack tied to the employer it
  belongs to, never blended).
- Obeys every `factual-bounds.md` cover-letter rule — e.g. if a bound says so, no
  `conventions.education` institution string appears anywhere in
  `cover_letter.data.json` **or** `cover_letter.txt`.
- The rendered letter is one page (render `cover_letter.html` with
  `-Placeholder '{{COVER_LETTER_JSON}}'` if you need to confirm).
- `{dir}/cover_letter.txt` exists and is **current**: regenerate a scratch copy with
  `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.py
  --data-path {dir}/tmp/cover_letter.data.json --out-path <temp>` and diff it against the committed
  `cover_letter.txt`. Any difference (or a missing `.txt`, or a `.txt` whose
  modification time precedes `cover_letter.data.json`'s) means the `.txt` is stale.
  Its first `Subject:` line must match `cover_letter.data.json.subject`.

### Render failure
If `render_pdf.py` returns `ok=False` (or the CLI prints `Render failed:`), surface
the `log` — this is a **browser** render failure (missing Chromium, malformed
template), not a LaTeX compile. Report it under `## Flag` and skip the checks that
depend on the PDF; do not claim the application passed.

## Output — `{dir}/review.md`

Three sections, always in this order:

- `## Pass` — every check group that passed cleanly, one line each.
- `## Flag` — issues that need a **human judgement call**: possible unsupported
  claims, uncovered essential criteria, near-duplicate bullets, length overflow,
  weak cover-letter coverage, a `hard-mismatch` fit, a render failure. For each:
  what, where (`file` + the JSON path or bullet text), and why it matters. Never
  auto-fix these.
- `## Fix` — corrections that are **unambiguous and safe**. For each: the exact
  before/after.

Only these count as safe auto-fixes under `--fix`:

1. **Tense** — a past-role bullet written in present tense where every sibling
   bullet is past tense (and it is not an ongoing duty in a current role).
2. **`profile.yml` mismatch** — a company name, job title, employment date,
   location, or education field in a `.data.json` that differs from `profile.yml`;
   rewrite the JSON string to match `profile.yml` **verbatim** (`profile.yml` wins,
   always).
3. **Stale `cover_letter.txt`** — regenerate it with
   `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.py
   --data-path {dir}/tmp/cover_letter.data.json --out-path {dir}/cover_letter.txt`.

Anything touching the substance of a claim, the selection of evidence, or the
wording of an argument is a **Flag**, never a **Fix**.

## `--fix` behaviour

1. Write `review.md` from the first pass.
2. Apply every item in `## Fix` (and only those). If a fix edits
   `{dir}/tmp/cover_letter.data.json`, regenerate `cover_letter.txt` afterwards
   (`uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.py
   --data-path {dir}/tmp/cover_letter.data.json --out-path {dir}/cover_letter.txt`).
   If a fix edits `{dir}/tmp/resume.data.json`, re-render it
   (`uv run --project ${CLAUDE_PLUGIN_ROOT}
   ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py --template-path <resume.html>
   --data-path {dir}/tmp/resume.data.json --out-path {dir}/resume.pdf`) and, on
   success, recompress (`uv run --project ${CLAUDE_PLUGIN_ROOT}
   ${CLAUDE_PLUGIN_ROOT}/scripts/compress_pdf.py --pdf-path {dir}/resume.pdf`). If a
   re-render fails, revert that edit, move the item to `## Flag`, and keep going.
3. Re-run every check **once**. Rewrite `review.md` with the new results and an
   `## Applied` note listing what was changed.
4. Do not loop a third time — remaining issues stay in `## Flag` / `## Fix` for the
   user.

## Guardrails

- This skill reads the source of truth and `{dir}`; it writes `{dir}/review.md`, and
  under `--fix` also `{dir}/tmp/resume.data.json` / `{dir}/tmp/cover_letter.data.json`
  / `{dir}/cover_letter.txt` / the flat PDFs. It never edits `{sourceDir}` and never
  touches `jd.md` or `analysis.md`.
- `profile.yml` is authoritative for company names, titles, dates, and locations —
  on any mismatch the document is wrong, not `profile.yml`.
- `factual-bounds.md` is a hard constraint. A bounds violation is always a `## Flag`
  (or `## Fix` only when the safe correction is a verbatim `profile.yml` match).
- A genuine, honestly-stated gap is the expected outcome for some criteria — do not
  flag an application for *not* claiming something it has no basis to claim.
- Reframing and re-weighting real `resume_sections/` experience to match JD language
  is expected — do not flag a bullet as an unsupported claim merely because it maps
  real evidence onto JD keywords, leads with a transferable angle, or describes a
  recorded pipeline in more JD-aligned wording than the source file uses. Only
  `factual-bounds.md` violations and zero-basis claims (a tool, domain, employer, or
  metric with no grounding in any real experience) are off-limits.
- This skill's own `review.md` report text is English-only, regardless of the
  conversation language. The résumé / cover-letter language is `generate`'s call
  (`--lang zh` is a sanctioned Chinese output); when reviewing a `lang: "zh"`
  application, check the translated strings, do not flag them for being Chinese.
  Full workflow rules: `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`.
