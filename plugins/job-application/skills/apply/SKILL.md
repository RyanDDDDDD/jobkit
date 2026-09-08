---
name: apply
description: Turn a job description into a tailored resume, cover letter, and optional form answers, then self-check the result. Analyzes the JD, retrieves evidence from the source of truth, renders and compresses the PDFs, and writes a QA report.
---

## When to use

The user pastes a JD, uploads a JD file, or says "apply to {Company}", "tailor my
CV for {Company}", or "/job-application:apply". Requires a source-of-truth dir — if
missing, tell the user to run `/job-application:setup` first and stop.

## Flags

- `--lang en|zh` — default `en`. `zh` ⇒ `lang: "zh"` in both JSON files, Chinese
  section titles / salutation / closing, body strings translated from the English
  source of truth (never invented). See "`--lang zh`" below.
- `--density compact|standard` — résumé spacing. Default: `profile.yml`
  `conventions.density` if set, else `compact`. Sets `density` in
  `resume.data.json`; the template's `compact` class tightens spacing ~12%.
- `--answers "Q1; Q2; ..."` — also write `{dir}/answers.md`, one grounded answer
  per `;`-separated question.

## Inputs and paths

Resolve paths with `jobkit config` (JSON: `root`, `source_of_truth_dir`,
`output_dir`, `interview_playbook`, `browser_path`). `{sourceDir}` =
`<root>/<source_of_truth_dir>` — if it does not exist, tell the user to
run `/job-application:setup` first and stop. `{dir}` =
`<root>/<output_dir>` with the literal `{Company}` token replaced by the
application name. Create `{dir}` and `{dir}/tmp`. A repo-level
`<root>/templates/<name>.html` override, if present, is picked up
automatically by `jobkit render`. Machine artifacts
(`resume.data.json`, `cover_letter.data.json`) live in `{dir}/tmp/`; `jd.md`,
`analysis.md`, `review.md`, the PDFs, `cover_letter.txt`, and `answers.md` stay
flat in `{dir}`. Full tree: `jobkit doc output-layout`.

Commands below are `jobkit <sub>` (the plugin installs the `jobkit` CLI —
`pip install jobkit`). If `jobkit` is not on `PATH`, `python -m jobkit <sub>`
is exactly equivalent.

## Steps

1. **Resolve** `{Company}` (ask if unclear), then run `jobkit config` and
   derive `{dir}` / `{sourceDir}` as in *Inputs and paths*. Create `{dir}`
   and `{dir}/tmp`.

2. **JD source.** If the user supplied JD text / a file this run, write it
   **verbatim** to `{dir}/jd.md` (overwrite). Else if `{dir}/jd.md` exists, reuse
   it (the "regenerate after editing the source of truth" path). Else ask for the
   JD.

3. **Load context.** Read `{sourceDir}/profile.yml` and
   `{sourceDir}/factual-bounds.md` (verbatim — a hard constraint set).

4. **Analyse + retrieve.** Dispatch `sot-retriever` in `retrieve` mode
   `{ mode: "retrieve", jd: <text of {dir}/jd.md>, sourceDir: <resolved> }`. It
   returns ranked bullets per section (each with a `file:line`) plus a `## Gaps`
   block. Then write `{dir}/analysis.md` as a **working note** with these `##`
   sections in order: `## Essential` (numbered list — stable ordinals),
   `## Desirable`, `## Responsibilities`, `## Keywords`,
   `## Language / Stack emphasis`, `## Criteria → Evidence` (table
   `Criterion | Evidence (file:line) | Status`, Status ∈ `met` / `partial` /
   `gap`), `## Fit` (opens with `strong` / `stretch` / `hard-mismatch`, then ` — `
   and a one-sentence reason), `## Framing` (lead role(s), ordering decision,
   emphasis / de-emphasis, relevant `factual-bounds.md` rules). This file is
   written and consumed inside this run and read later by `interview` as prose —
   do not add strict-parse ceremony, just keep the headings.

   For `## Criteria → Evidence`: re-pivot the retriever output onto one row per
   essential criterion and assign Status yourself. A criterion with no supporting
   bullet and a matching entry in the retriever's `## Gaps` block is `gap`. Every
   `met` / `partial` row cites a real `file:line`. Never soften a `gap` to
   `partial` without concrete evidence.

5. **Hard-mismatch exit.** If `## Fit` is `hard-mismatch`: tell the user plainly
   in chat that the role is a hard mismatch and recommend skipping it. Write
   nothing further — no `.data.json`, no PDF, no `answers.md`. Stop.

6. **Build the data objects.** Assemble `{dir}/tmp/resume.data.json` and
   `{dir}/tmp/cover_letter.data.json` per "## Building the data files" below.
   Company / title / employment-date / location strings come from `profile.yml`
   **verbatim, never re-derived**. Include a Selected Projects section **only**
   when step 4 surfaced JD-relevant `projects/*.md` (else omit it). Experience
   order is reverse-chronological unless `## Framing` calls for relevance order.
   Read the `###` category headings in `{sourceDir}/skills.md` directly for the
   Skills section.

7. **Bounds check** (before writing files) — re-read every line you are about to
   place against `factual-bounds.md` and the `analysis.md` `gap` rows.
   Reframing / re-weighting / combining real material is fine (workflow-rules §2).
   Off-limits: `factual-bounds.md` violations and zero-basis claims — a
   technology, employer, domain, or number that appears **nowhere** in
   `{sourceDir}` (workflow-rules §3). On a conflict, **stop and ask the user**;
   if they give a new true fact, tell them which source-of-truth file to add it to
   and have them re-run — do not write it in from the chat alone.

8. **Render both PDFs in one call.** Emit each data object with `ConvertTo-Json`
   (see "## Building the data files"). Then render the résumé and the cover letter
   in a **single** `jobkit render` invocation — `--kind` / `--data` / `--out` are
   repeatable and zipped positionally, so one Chromium launch produces both:

   ```
   jobkit render \
     --kind resume       --data {dir}/tmp/resume.data.json       --out {dir}/resume.pdf \
     --kind cover_letter --data {dir}/tmp/cover_letter.data.json --out {dir}/cover_letter.pdf
   ```

   The command prints one `OK: <pdf> (N page[s])` line per document and exits 0
   only if **both** rendered. On a non-zero exit, apply the
   `jobkit doc render-contract` failure handling **per
   failed document** (surface its `Render failed [<pdf>]:` text, keep that
   `.data.json`, do not compress it, do not claim success); a document that
   rendered is still usable. On success, compress both in one call —
   `jobkit compress --pdf {dir}/resume.pdf --pdf {dir}/cover_letter.pdf`
   — then `jobkit cover-txt --data {dir}/tmp/cover_letter.data.json
   --out {dir}/cover_letter.txt`.

9. **Self-check → `{dir}/review.md`.**

   a. **Deterministic checks.** Run
      `jobkit verify --dir {dir} --source-dir {sourceDir} --json`. It
      reports `{ "pass": [...], "fail": [{id, detail}], "warn": [{id, detail}] }`
      and always exits 0 (exit 1 only means a required input file is missing —
      treat that as a render failure). The checks: `profile-roles-verbatim`,
      `profile-education-verbatim`, `resume-roundtrip`, `cover-roundtrip`,
      `page-budget`, `cover-txt-fresh`, `date-format`, and the advisory
      `bullet-dupes` (a `warn`).

   b. **Act on the report.** For each `fail[]` entry that matches a **safe
      auto-fix** (see "## Self-check → Safe auto-fixes"): a
      `profile-roles-verbatim` / `profile-education-verbatim` /
      `date-format` failure → rewrite the offending `.data.json` field to the
      `profile.yml` value verbatim; a `cover-txt-fresh` "stale" failure →
      regenerate `{dir}/cover_letter.txt`. After an edit to a `.data.json`,
      re-render **only that document** with a single-job `jobkit render` call and
      recompress it (and regenerate the `.txt` if it was the cover letter); if the
      re-render fails, revert the edit and move the item to `## Flag`. Every other
      `fail[]` entry, and every `warn[]` entry that is not obviously spurious, goes
      to `## Flag`.

   c. **Semantic checks (LLM).** Judge only what a script cannot:
      - **Compliance** — no `factual-bounds.md` rule violated (quote the rule + the
        offending JSON string).
      - **Zero-basis** — no technology, employer, domain, **or number** in either
        JSON that appears nowhere in `{sourceDir}` (`jobkit verify` does not
        judge this). Reframing real material to JD wording is not a violation.
      - **JD coverage** — each numbered `## Essential` criterion is supported by ≥1
        résumé bullet or skills-group entry; list every uncovered one. A criterion
        the `## Criteria → Evidence` table marks `gap` that the résumé nonetheless
        claims is a compliance violation.
      - **Cover letter content** — between the `paragraphs[]`: total professional
        SDE experience duration; the specific companies by name; the specific
        business domains; the company-tied tech stacks (each tied to its employer,
        never blended). Obeys every `factual-bounds.md` cover-letter rule.
      - **Style** — every bullet verb-first; section titles conventional (not
        creative renames).

   d. **Write `review.md`** with `## Pass`, `## Flag`, `## Fix (applied)`. **One
      pass only** — no second re-check loop. If `jobkit render` failed for a
      document, `review.md` must not claim the application passed.

10. **Answers** (only with `--answers`) — `{dir}/answers.md`, one `##` per
    question, grounded in the retrieved material, each with a compact
    one-to-two-sentence variant. No new facts.

11. **Clean up.** `jobkit render` removes each job's `.rendered.html`. End state:
    `{dir}/` has `jd.md`, `analysis.md`, `review.md`, `resume.pdf`,
    `cover_letter.pdf`, `cover_letter.txt`, optional `answers.md`; `{dir}/tmp/`
    has `resume.data.json`, `cover_letter.data.json`.

12. **Report.** Files written; résumé page count (from the `OK:` line) and cover
    letter page count; any `analysis.md` `gap` the documents honestly do not
    cover (expected — state it); the `--density` / `--lang` applied and whether
    Selected Projects was included; the experience ordering used; anything left in
    `review.md` `## Flag`.

## Building the data files

Build each file as a PowerShell hashtable / array and emit it with `ConvertTo-Json`:

```powershell
$data | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8NoBOM {dir}/tmp/resume.data.json
```

(Use `utf8NoBOM` on PowerShell 7. If you need Windows PowerShell 5.1 compatibility,
write with `[System.IO.File]::WriteAllText($path, $json)` instead — plain
`-Encoding utf8` there emits a BOM, which some JSON parsers choke on.)

`ConvertTo-Json` guarantees valid JSON and correct string escaping (quotes,
backslashes, newlines) — hand-writing nested JSON is error-prone. If you do hand-write
a file, you **must** validate it afterwards with
`Get-Content -Raw <path> | ConvertFrom-Json` and fix any parse error before
rendering. Every string is text-escaped by the renderer, so the only escaping
concern is producing valid JSON strings — which `ConvertTo-Json` handles.

### `{dir}/tmp/resume.data.json`

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
One item per role in `profile.yml` `conventions.roles`, reverse-chronological
(most recent first) unless `## Framing` calls for relevance order. Each item:
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
  role warrants (3–6; see "Length discipline" below).

**Selected Projects section** (only when step 4 surfaced JD-relevant
`projects/*.md`) — `{ "title": "Selected Projects", "type": "entries", "items": [...] }`.
One item per JD-relevant project: `primary` = project name; `metaRight` = tech
stack or `""` (use `metaRight`, **not** `dates`); `secondary` = the one-line
project description; `bullets` = retrieved project bullets.

**Education section** — `{ "title": "Education", "type": "education", "items": [...] }`.
One item per `profile.yml` `conventions.education` entry: `institution`, `dates` =
`"<start> – <end>"` (en-dash), `credential`, `location` — all verbatim. No GPA /
grades / distinctions (experienced-hire default).

**Skills section** — `{ "title": "Skills", "type": "skills", "groups": [...] }`.
Each group is `{ "label", "value" }` with `value` a comma-separated list. Read the
`###` category headings in `{sourceDir}/skills.md` **directly** for the grouping.
Take a JD-relevant subset within each group and keep the source file's category
structure.

**Extra sections** — any additional section the source of truth supports
(Publications, Certifications, Patents) → `{ "title", "type": "list", "items": [...] }`.

**Length discipline.** The résumé soft ceiling is a fixed **2** pages. When density
is `compact` and the goal is a 1-page résumé, aim well below the ceiling: ~3
bullets per role (the strongest, JD-relevant ones), a 3-item intro, and drop
de-emphasized skill groups. Render, check the page count, and if over the soft
ceiling WARN and list candidate trims — never silently trim content to fit.

### `{dir}/tmp/cover_letter.data.json`

| Key | Fill |
|---|---|
| `name` | `profile.yml` `name`. |
| `lang` | Same as the résumé. |
| `contact` | Same array shape as the résumé. |
| `date` | Today's date, long form, e.g. `"September 1, 2026"`. |
| `recipient` | Array of lines: `["Hiring Manager", "<Company> as the JD states it", "<City, Country>"]`. Use the named contact from the JD in place of `"Hiring Manager"` if it gives one. Drop the location line if the JD gives no location. Fall back to the `{Company}` argument if the JD names no company. |
| `subject` | `"Application for the Position of <role title from the JD>"`. If the JD carries a requisition / reference ID, append it naturally (e.g. `" (Ref: <id>)"`); **if the JD has none, no `"Ref:"` dangle**. |
| `salutation` | `"Dear Hiring Manager,"` (or `"Dear <contact name>,"`). |
| `paragraphs` | Array of body paragraphs, any count (typically intro, body1, body2, outro). Between them they must: (1) state the total professional software-engineering experience duration; (2) name the specific companies; (3) name the specific business domains / sectors; (4) name the company-tied tech stacks, each tied to the company it was used at (workflow-rules §9). Draw only on retrieved material; no overclaiming of `gap` criteria. |
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

## Self-check

Step 9 runs this in two halves: `jobkit verify` (step 9a) covers every
mechanical check; the LLM (step 9c) judges only what a script cannot.

### Mechanical — `jobkit verify` (step 9a)

These are the script's check ids, not a separate manual pass:

- `profile-roles-verbatim` / `profile-education-verbatim` — every `type: "entries"`
  role item (`primary` / `secondary` / `location` / `dates`) and every
  `type: "education"` item matches `profile.yml` `conventions.*` **verbatim**
  (`dates` == `"<start> – <end>"`, space–en-dash–space).
- `date-format` — every `dates` string uses ` – ` (space, U+2013, space).
- `resume-roundtrip` / `cover-roundtrip` — the render/`jobkit extract-cv` silent-failure
  guard against the PDFs already on disk: no `Invalid resume JSON` /
  `Invalid cover letter JSON`; candidate `name` and a company name (résumé) or the
  `subject` (cover letter) appear in the extracted text.
- `page-budget` — résumé ≤ 2 pages, cover letter == 1.
- `cover-txt-fresh` — `{dir}/cover_letter.txt` exists, byte-matches a fresh
  regeneration from `cover_letter.data.json`, and leads with its `Subject:` line.
- `bullet-dupes` (`warn`) — no near-duplicate bullet within or across the two
  documents (workflow-rules §10).

### Semantic — LLM (step 9c)

- **Compliance** — no `factual-bounds.md` rule violated (quote the rule + the
  offending JSON string). No technology / employer / domain / **number** in either
  JSON that appears **nowhere** in `{sourceDir}` (zero-basis — a `## Flag`).
  Reframing real material to JD wording is not a violation.
- **JD coverage** — for each numbered `## Essential` criterion, at least one résumé
  bullet or skills-group entry supports it — list every uncovered one. A criterion
  the `## Criteria → Evidence` table marks `gap` that the résumé nonetheless claims
  is a compliance violation.
- **Cover letter content** — between the `paragraphs[]`: total professional SDE
  experience duration; the specific companies by name; the specific business
  domains; the company-tied tech stacks (each tied to its employer, never blended)
  (workflow-rules §9). Obeys every `factual-bounds.md` cover-letter rule.
- **ATS & style** — section titles are conventional (not creative renames); every
  bullet is verb-first; one tense throughout each `bullets[]` (past for finished
  work, present only for an ongoing duty in a current role). Walk
  `jobkit doc ats-checklist`.
- **Length** — page count over the soft ceiling of 2 ⇒ `## Flag` with the count and
  candidate trims. Never a `## Fix`.

### Safe auto-fixes
The only `## Fix (applied)` items: (1) a past-role bullet in present tense where
every sibling is past; (2) a `.data.json` company / title / date / location /
education field that differs from `profile.yml` — rewrite to match `profile.yml`
verbatim; (3) a stale / missing `cover_letter.txt` — regenerate. Anything touching
the substance of a claim, evidence selection, or argument wording is a `## Flag`.

If `jobkit render` fails, surface the failure under `## Flag` and do not claim the
application passed.

## Guardrails

- Company names / titles / dates / locations from `profile.yml` verbatim.
- The one prohibition is zero-basis additions (workflow-rules §3).
- `factual-bounds.md` is hard — on conflict stop and ask.
- English by default; `--lang zh` faithfully translated.
- Machine artifacts in `{dir}/tmp/`, deliverables flat.
- `jd.md` stays (workflow-rules §7).
- `jobkit doc workflow-rules` and `jobkit doc render-contract`.
