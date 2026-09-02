---
name: generate
description: Produce a tailored resume, cover letter, and optional application-form answers for a job already analyzed by jd-intake. Renders and compresses the PDFs.
---

## When to use

The user says "generate the resume/cover letter for {Company}", "tailor my CV for
{Company}", or "/job-application:generate". Requires `{dir}/analysis.md` from the
`jd-intake` skill — if it is absent, tell the user to run `/job-application:jd-intake`
first and stop.

## Flags

- `--density compact|standard` — résumé spacing. Default: `profile.yml`
  `conventions.default_density` if that key is present; else `compact` when
  `conventions.default_resume_length == 1`, `standard` when `== 2`, and `standard`
  if neither key is set. Sets `density` in `resume.data.json` — the template's
  `compact` class tightens spacing ~12%.
- `--max-pages N` — **soft** page ceiling. Default `2`. If the rendered résumé
  exceeds it, WARN the user and list candidate trims (drop the lowest-ranked bullet
  per role, shorten the intro, drop a de-emphasized skill group). NEVER silently
  trim content to fit.
- `--lang en|zh` — output language. Default `en`. `zh` ⇒ `lang: "zh"` in both JSON
  files, Chinese résumé section titles and cover-letter subject / salutation /
  closing, and body strings translated from the English source of truth (see
  "`--lang zh`" under "Building the data files").
- `--with-projects` — add a `Selected Projects` section built from the JD-relevant
  `projects/<slug>.md` entries. Default: `profile.yml`
  `conventions.default_include_projects` (fixture: `false`). There is one template
  now — this no longer changes any page target.
- `--order relevance|chronological` — experience-entry ordering. Default
  `chronological` (reverse-chronological, most recent role first). `relevance` uses
  the ordering decision recorded in `analysis.md` `## Framing`.
- `--answers "Q1; Q2; ..."` — also write `{dir}/answers.md`, one grounded answer per
  `;`-separated question.
- `--keep-html` — pass `--keep-html` to `render_pdf.py` so the `{dir}/*.rendered.html`
  files are kept instead of being cleaned up.

## Inputs and paths

- All plugin-internal paths use `${CLAUDE_PLUGIN_ROOT}`: scripts
  (`${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py`,
  `${CLAUDE_PLUGIN_ROOT}/scripts/compress_pdf.py`,
  `${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.py`, run via `uv run
  --project ${CLAUDE_PLUGIN_ROOT}`), templates
  (`${CLAUDE_PLUGIN_ROOT}/templates/*.html`), the retriever agent
  (`${CLAUDE_PLUGIN_ROOT}/agents/sot-retriever.md`), and `reference/`
  (`${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`,
  `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`).
- **Template override:** before using a bundled template, check for a repo-level
  override. If `./templates/<name>.html` exists in the user's working repo, use it
  instead of `${CLAUDE_PLUGIN_ROOT}/templates/<name>.html`. `<name>` is `resume` or
  `cover_letter`.
- **Source-of-truth dir** and **output dir**: run `uv run --project
  ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.py`, which prints
  the resolved config as JSON. It returns `root` (the directory where
  `jobapp.config.yml` was found by walking up from the current working directory, or
  the current directory if none), `browser_path` (a machine hint, may be `null`),
  `source_of_truth_dir` (default `resume_sections/`), and `output_dir` (default
  `applications/{Company}`). The source-of-truth dir is
  `<root>/<source_of_truth_dir>`. `profile.yml` has **no** `output_dir` key — resolve
  `{dir}` by substituting the literal token `{Company}` in `output_dir` with the
  company name and joining onto `root` (e.g. `<root>/applications/Testco`), exactly
  as `jd-intake` does.
- `{dir}/analysis.md` must already exist. If not: "run `/job-application:jd-intake`
  for {Company} first" and stop.

## Reading `analysis.md` (Task 6 output)

Parse it with these exact rules:

- `## Fit` — the classification is the **first whitespace-delimited token** of the
  first non-blank line under the `## Fit` heading, lower-cased, trailing punctuation
  stripped. It is one of `strong` / `stretch` / `hard-mismatch`. The line has the
  form `<token> — <reason>`.
  **If the token is `hard-mismatch`, STOP.** Tell the user the role is a hard
  mismatch, that `jd-intake` already flagged it, and generate nothing (no
  `.data.json`, no PDF, no `answers.md`).
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

3. **Resolve templates and options.**
   - Résumé template: repo `./templates/resume.html` if it exists, else
     `${CLAUDE_PLUGIN_ROOT}/templates/resume.html`. Cover-letter template: repo
     `./templates/cover_letter.html` if it exists, else the bundled one. There is
     one résumé template — no `--length` variant selection.
   - Resolve `--density` (per the default rule in Flags), `--order`, `--lang`,
     `--with-projects`, and `--max-pages`.
   - Read the `###` category headings in `<root>/<source_of_truth_dir>/skills.md`
     directly — you need them for the Skills section and `sot-retriever` `retrieve`
     mode returns flat bullets, not `###` categories.

4. **Build the résumé data object.** Assemble `{dir}/resume.data.json` per
   "Building the data files" below — `name` / `lang` / `density` / `contact` /
   `intro` / `sections` (Experience, optional Selected Projects, Education, Skills,
   any extra source-of-truth section). Company / title / employment-date / location
   strings come from `profile.yml` **verbatim, never re-derived**; tech stack and
   bullets come from the retriever.

5. **Bounds check (before writing anything).** Re-read every line you are about to
   place against `factual-bounds.md` and the `analysis.md` `gap` rows:
   - Reframing and re-weighting real `resume_sections/` experience to match JD
     language is expected — mapping a bullet onto JD keywords, leading with a
     transferable angle, describing a recorded pipeline in more JD-aligned wording, or
     combining two real bullets into one is **not** a bounds violation. Only
     `factual-bounds.md` violations and zero-basis claims (a tool, domain, employer,
     or metric with no grounding in any real experience) are off-limits.
   - No bullet may claim a technology, employer, project, metric, or scope that a
     bound forbids or that the source of truth does not support.
   - Keep every tech stack tied to the employer/project it belongs to — no blending.
   - No numeric metric appears that is not recorded verbatim in the source of truth.
   - If the JD or `analysis.md` pushes for content that would violate a bound, **STOP
     and ask the user.** Do not silently comply and do not silently omit. If the user
     supplies a new true fact, tell them which source-of-truth file to add it to
     (`companies/<slug>.md`, `skills.md`, `profile.yml`, etc.) and have them re-run
     after updating — do not write it into the résumé from the chat alone.

6. **Write and render the résumé.** Emit the data object with `ConvertTo-Json`
   (see "Building the data files" — this guarantees valid JSON). Then:
   `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py --template-path <resume.html override-resolved> --data-path {dir}/resume.data.json --out-path {dir}/resume.pdf`
   (add `--keep-html` when `--keep-html` was passed). CLI contract: on success it
   prints `OK: <pdf> (N page…)` to stdout and exits 0; on failure it prints
   `Render failed:` plus the log tail to stderr and exits 1; it exits 2 if a required
   parameter is missing.
   - **Non-zero exit ⇒ failure:** surface the `Render failed:` text, keep the
     `.data.json`, do **not** compress, do **not** claim success. Fix the data
     (usually an invalid JSON string or a wrong shape) and re-render.
   - **Silent-failure guard:** the renderer exits 0 even when the data is unusable —
     it draws a visible "Invalid resume JSON: …" page for a JSON scalar / `null`, and
     a near-empty page for a valid-JSON-but-wrong-shape object (no `sections`). After
     a successful render, extract the PDF text
     (`uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/extract_cv.py {dir}/resume.pdf`)
     and confirm **both**: it does not contain `Invalid resume JSON`, **and** it
     contains the candidate's `name` plus at least one company name from the
     experience section. If either check fails, treat it exactly like a render
     failure: surface it, keep the `.data.json`, do not compress, do not claim
     success — fix the data and re-render.
   - **Page count** is the integer in the `OK: … (N page…)` line. If it exceeds
     `--max-pages`: WARN the user and list candidate trims (drop the lowest-ranked
     bullet from each role, shorten the intro, drop a de-emphasized skill group). Do
     not ship an over-length résumé silently and never edit content to force-fit
     without telling the user.

7. **Compress.** On success:
   `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/compress_pdf.py --pdf-path {dir}/resume.pdf`.

8. **Cover letter.** Build `{dir}/cover_letter.data.json` per "Building the data
   files". Content must follow the cover-letter rules in
   `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md` §7:
   1. state the total professional software-engineering experience duration;
   2. name the specific companies worked at;
   3. name the specific business domains / sectors;
   4. name the specific tech stacks, each tied to the company where it was used.
   Obey every `factual-bounds.md` cover-letter rule (e.g. no university mention).
   Emit with `ConvertTo-Json`, then render:
   `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py --template-path <cover_letter.html override-resolved> --data-path {dir}/cover_letter.data.json --out-path {dir}/cover_letter.pdf --placeholder '{{COVER_LETTER_JSON}}'`
   (add `--keep-html` with `--keep-html`). Same CLI contract — non-zero exit ⇒
   failure; the `OK: … (N page…)` line should report 1 page. Apply the same
   silent-failure guard as step 6 (via `extract_cv.py`): after a
   successful render, extract the PDF text and confirm it does **not** contain
   `Invalid cover letter JSON` and **does** contain the candidate's `name` and the
   `subject` text. If either check fails, keep the `.data.json`, do not compress,
   do not claim success — fix the data and re-render. Then
   `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/compress_pdf.py --pdf-path {dir}/cover_letter.pdf`.

9. **Plain-text cover letter.**
   `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.py --data-path {dir}/cover_letter.data.json`
   → `{dir}/cover_letter.txt` (the script hoists the `Subject:` / `主题：` line to
   the first line and formats the structured data directly). Regenerate it any time
   `cover_letter.data.json` changes.

10. **Answers (only if `--answers`).** Write `{dir}/answers.md`: one `##` heading per
    question, each answer grounded in the same retrieved bullets (cite the
    `file:line` inline), followed by a compact one-to-two-sentence variant for
    short-field forms. No new facts beyond the source of truth.

11. **Clean up.** There are no `.aux` / `.log` / `.out` files any more.
    `render_pdf.py` removes its own `.rendered.html` unless `--keep-html` was passed.
    So there is nothing to clean unless `--keep-html` was passed — in which case
    `{dir}/resume.rendered.html` and `{dir}/cover_letter.rendered.html` are
    intentionally kept. Files left in `{dir}`: `jd.md`, `analysis.md`,
    `resume.data.json`, `resume.pdf`, `cover_letter.data.json`, `cover_letter.pdf`,
    `cover_letter.txt`, optional `answers.md`, optional `*.rendered.html`.

12. **Report.** Output:
    - every file written, with the résumé's real page count from the
      `render_pdf.py` `OK:` line and the cover letter's page count;
    - a table of every metric and every named skill used in the résumé or cover
      letter, each with its source-of-truth `file:line` (Ruling: no claim without a
      citation);
    - any deviation from `profile.yml` conventions (and why);
    - any `analysis.md` `gap` the documents do not paper over (expected — state it);
    - the ordering decision used, the `--density` / `--lang` applied, and whether
      `--with-projects` added the Selected Projects section.

## Building the data files

Build each file as a PowerShell hashtable / array and emit it with `ConvertTo-Json`:

```powershell
$data | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8NoBOM {dir}/resume.data.json
```

(Use `utf8NoBOM` on PowerShell 7. If you need Windows PowerShell 5.1 compatibility,
write with `[System.IO.File]::WriteAllText($path, $json)` instead — plain
`-Encoding utf8` there emits a BOM, which some JSON parsers choke on.)

`ConvertTo-Json` guarantees valid JSON and correct string escaping (quotes,
backslashes, newlines) — hand-writing nested JSON is error-prone. If you do hand-write
a file, you **must** validate it afterwards with
`Get-Content -Raw <path> | ConvertFrom-Json` and fix any parse error before
rendering. There is no LaTeX escaping any more: every string is text-escaped by the
renderer, so the only escaping concern is producing valid JSON strings — which
`ConvertTo-Json` handles.

### `{dir}/resume.data.json` (design amendment §3.1)

| Key | Fill |
|---|---|
| `name` | `profile.yml` `name`, verbatim. |
| `lang` | `"en"` or `"zh"` per `--lang` (default `"en"`). |
| `density` | `"compact"` or `"standard"` per `--density` (see Flags for the default). |
| `contact` | Array from `profile.yml`: `phone` as a plain string; `email` as `{ "text": "<email>", "href": "mailto:<email>" }`; and, only if `links.github` is set, `{ "text": "github.com/<handle>", "href": "https://github.com/<handle>" }`. Omit the GitHub entry entirely when `links.github` is absent. |
| `introTitle` | Optional. Omit for the default `"Introduction"`; set it to `"简介"` for `--lang zh`. |
| `intro` | Array of `{ "lead", "text" }` — 3–5 items distilled from retrieved `introduction.md` content. `lead` is the short topic phrase (the renderer bolds it and appends the trailing period — `.` for `lang: "en"`, `。` for `lang: "zh"`); `text` is the rest of the clause. |
| `sections` | Array, in this order: Experience, [Selected Projects], Education, Skills, [extra source-of-truth sections]. |

**Experience section** — `{ "title": "Industrial Experience", "type": "entries", "items": [...] }`.
One item per role in `profile.yml` `conventions.roles`, ordered per `--order`
(chronological = most recent role first). Each item:
- `primary` = role `title` — **verbatim from `profile.yml`**.
- `dates` = `"<start> – <end>"` — an en-dash (U+2013) with a space on each side;
  `start` and `end` **verbatim from `profile.yml`** (e.g. `"Jan. 2024 – Present"`).
- `secondary` = role `company` — **verbatim from `profile.yml`**.
- `location` = role `location` — **verbatim from `profile.yml`**.
- `stack` = the retrieved "Integrated Tech Stack" line for **that** company
  (`companies/<slug>.md`); a JD-relevant subset is allowed, never blended with
  another company's stack. `stackLabel` is optional (default `"Stack"`).
- `bullets` = the retrieved bullets for that role, best-first, verb-first, past
  tense (present only for an ongoing duty in a current role). Emit as many as the
  role warrants (3–6; see "Length discipline" below when targeting one compact
  page); every bullet traces to a retriever `file:line`.

**Selected Projects section** (only with `--with-projects`) —
`{ "title": "Selected Projects", "type": "entries", "items": [...] }`. One item per
JD-relevant `projects/<slug>.md`: `primary` = project name; `metaRight` = tech stack
or `""` (use `metaRight`, **not** `dates`); `secondary` = the one-line project
description; `bullets` = retrieved project bullets.

**Education section** — `{ "title": "Education", "type": "education", "items": [...] }`.
One item per `profile.yml` `conventions.education` entry: `institution`, `dates` =
`"<start> – <end>"` (en-dash), `credential`, `location` — all verbatim. No GPA /
grades / distinctions (experienced-hire default).

**Skills section** — `{ "title": "Skills", "type": "skills", "groups": [...] }`.
Each group is `{ "label", "value" }` with `value` a comma-separated list. Read the
`###` category headings in `<root>/<source_of_truth_dir>/skills.md` **directly** for the
grouping (the retriever returns flat bullets, not `###` categories). Take a
JD-relevant subset within each group and keep the source file's category structure.

**Extra sections** — any additional section the source of truth supports
(Publications, Certifications, Patents) → `{ "title", "type": "list", "items": [...] }`.

**Length discipline.** `--max-pages` is the upper bound, not the target. When the
density is `compact` and the goal is a 1-page résumé, aim well below the ceiling:
~3 bullets per role (the strongest, JD-relevant ones), a 3-item intro, and drop
de-emphasized skill groups. Render, check the page count, and if it is over target
trim the lowest-ranked bullet from each role and re-render — the soft-trim loop in
step 6 applies here too.

### `{dir}/cover_letter.data.json` (design amendment §3.2)

| Key | Fill |
|---|---|
| `name` | `profile.yml` `name`. |
| `lang` | Same as the résumé. |
| `contact` | Same array shape as the résumé. |
| `date` | Today's date, long form, e.g. `"September 1, 2026"`. |
| `recipient` | Array of lines: `["Hiring Manager", "<Company> as the JD states it", "<City, Country>"]`. Use the named contact from the JD in place of `"Hiring Manager"` if it gives one. Drop the location line if the JD gives no location. Fall back to the `{Company}` argument if the JD names no company. |
| `subject` | `"Application for the Position of <role title from the JD>"`. If the JD carries a requisition / reference ID, append it naturally (e.g. `" (Ref: <id>)"`); **if the JD has none, no `"Ref:"` dangle**. |
| `salutation` | `"Dear Hiring Manager,"` (or `"Dear <contact name>,"`). |
| `paragraphs` | Array of body paragraphs, any count (typically intro, body1, body2, outro). Between them they must: (1) state the total professional software-engineering experience duration; (2) name the specific companies; (3) name the specific business domains / sectors; (4) name the company-tied tech stacks, each tied to the company it was used at (workflow-rules §7). Draw only on retrieved material; no overclaiming of `gap` criteria. |
| `closing` | `"Sincerely,"`. |
| `signature` | `profile.yml` `name`. |

`factual-bounds.md` still applies to the letter — e.g. "Do not mention the university
in cover letters" means no `conventions.education` institution string appears anywhere
in `cover_letter.data.json`.

### `--lang zh`

When `--lang zh`:
- `lang: "zh"` in both JSON files.
- Résumé section `title`s are the Chinese equivalents — e.g. 简介 / 工作经验 /
  精选项目 / 教育背景 / 技能 — as are `introTitle` and any `stackLabel`.
- Cover-letter `subject` / `salutation` / `closing` are Chinese (the script prefixes
  the `主题：` / `日期：` labels itself).
- Every body string (`intro` `lead`/`text`, `bullets`, `stack`, cover-letter
  `paragraphs`) is translated from the English source-of-truth content. **This is
  the only place in the whole workflow where translation happens.**
- `factual-bounds.md` and the no-invention rules apply to the translated text exactly
  as they do to English — do not invent a detail to make a smoother Chinese sentence.

## Guardrails

- Company names, job titles, employment dates, and locations come from `profile.yml`
  **verbatim** — never re-derived from the JD or the conversation.
- No skill, tool, employer, project, or metric appears that has no grounding anywhere
  in the source-of-truth directory (a zero-basis claim). A genuine gap stated honestly
  is the expected outcome for some criteria; papering over it is a bounds violation.
- Reframing and re-weighting real `resume_sections/` experience to match JD language
  is expected. Only `factual-bounds.md` violations and zero-basis claims (a tool,
  domain, employer, or metric with no grounding in any real experience) are
  off-limits — the source of truth not phrasing something the JD's way is not a
  reason to drop it.
- Every metric and every named skill in either document is paired with a
  source-of-truth `file:line` citation in the report (Ruling: no claim without a
  citation).
- `factual-bounds.md` is a hard constraint. On any conflict: STOP and ask.
- English by default; `--lang zh` produces Chinese, faithfully translated from the
  English source of truth — never invented.
- `jd.md` stays in `{dir}` (workflow-rules §5) — this skill never deletes it.
- Full workflow rules: `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`.
  ATS checklist: `${CLAUDE_PLUGIN_ROOT}/reference/ats-checklist.md`.
