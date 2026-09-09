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

6. **Scaffold, then build the data objects.** Run `jobkit scaffold-data` (see
   "## Building the data files" below) to write `{dir}/tmp/resume.data.json` and
   `{dir}/tmp/cover_letter.data.json` with every `profile.yml`-derived field
   already filled in verbatim — name, contact, lang, density, today's date, each
   Experience item's `primary`/`dates`/`secondary`/`location`, and the whole
   Education section. **Never edit those fields** — they are already correct.
   Then `Edit` in the judgment content: `intro`, each Experience item's
   `stack`/`bullets`, the Skills `groups` (read the `###` category headings in
   `{sourceDir}/skills.md` directly), a Selected Projects section **only** when
   step 4 surfaced JD-relevant `projects/*.md` (insert it between Experience and
   Education; else omit it entirely), and the cover letter's
   `recipient`/`subject`/`paragraphs` (and, for `--lang zh`,
   `salutation`/`closing`). Experience order is reverse-chronological by default
   (matching `profile.yml` `conventions.roles` file order); reorder the
   scaffolded `items[]` array via `Edit` if `## Framing` calls for relevance
   order instead.

7. **Bounds check** (before writing files) — re-read every line you are about to
   place against `factual-bounds.md` and the `analysis.md` `gap` rows.
   Reframing / re-weighting / combining real material is fine (workflow-rules §2).
   Off-limits: `factual-bounds.md` violations and zero-basis claims — a
   technology, employer, domain, or number that appears **nowhere** in
   `{sourceDir}` (workflow-rules §3). On a conflict, **stop and ask the user**;
   if they give a new true fact, tell them which source-of-truth file to add it to
   and have them re-run — do not write it in from the chat alone.

8. **Render both PDFs in one call.** Both `.data.json` files are already on disk
   from step 6 (see "## Building the data files"). Render the résumé and the cover
   letter in a **single** `jobkit render` invocation — `--kind` / `--data` / `--out`
   are repeatable and zipped positionally, so one Chromium launch produces both:

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

Run the scaffolder, then edit in the judgment content:

```
jobkit scaffold-data --dir {dir} --source-dir {sourceDir} --lang <en|zh> --density <compact|standard>
```

This writes both `.data.json` files, already valid JSON, with every field
`profile.yml` (plus `--lang`/`--density`) determines pre-filled:

| Key | Value |
|---|---|
| `name` | `profile.yml` `name`, verbatim. |
| `lang` | `"en"` or `"zh"` per `--lang`. |
| `density` | `"compact"` or `"standard"` per `--density` (`profile.yml` `conventions.density` if the flag is omitted, else `"compact"`). |
| `contact` (both files) | Array from `profile.yml`: `phone` as a plain string; `email` as `{ "text": "<email>", "href": "mailto:<email>" }`; and, only if `links.github` is set, `{ "text": "github.com/<handle>", "href": "https://github.com/<handle>" }`. |
| `introTitle` | Only set (to `"简介"`) for `--lang zh`; omitted for `--lang en` (renderer default `"Introduction"`). |
| Experience items | One per `profile.yml` `conventions.roles` entry, in file order: `primary` = role `title`, `dates` = `"<start> – <end>"` (en-dash, U+2013), `secondary` = role `company`, `location` = role `location` — all verbatim. `stack: ""` and `bullets: []` are left for you. |
| Education section | Fully filled — one item per `conventions.education` entry: `institution`, `dates`, `credential`, `location`, all verbatim. No GPA / grades / distinctions (experienced-hire default). Nothing left to edit here. |
| Skills section shell | `{ "title": "Skills", "type": "skills", "groups": [] }` — `groups` is left for you. |
| Cover letter `date` | Today, long form, e.g. `"September 1, 2026"`. |
| Cover letter `signature` | `profile.yml` `name`. |
| Cover letter `salutation` / `closing` | `--lang en`: `"Dear Hiring Manager,"` / `"Sincerely,"`. `--lang zh`: left empty (translation is your job — see "`--lang zh`" below). |

**Never edit the fields above** — they are already correct, verbatim from
`profile.yml`. Everything else is left empty (`""` / `[]`) for you to fill in with
`Edit`, one field at a time — the file stays valid JSON at every intermediate step,
so there is no escaping step and no ad-hoc script to write.

### `{dir}/tmp/resume.data.json` — fields you fill in

| Key | Fill |
|---|---|
| `intro` | Array of `{ "lead", "text" }` — 3–5 items distilled from retrieved `introduction.md` content. `lead` is the short topic phrase (the renderer bolds it and appends the trailing period — `.` for `lang: "en"`, `。` for `lang: "zh"`); `text` is the rest of the clause. |
| Experience items' `stack` | The retrieved "Integrated Tech Stack" line for **that** company (`companies/<slug>.md`); a JD-relevant subset is allowed, never blended with another company's stack. `stackLabel` is optional (default `"Stack"`). |
| Experience items' `bullets` | The retrieved bullets for that role, best-first, verb-first, past tense (present only for an ongoing duty in a current role). Emit as many as the role warrants (3–6; see "Length discipline" below). |
| `sections` — Selected Projects | Insert `{ "title": "Selected Projects", "type": "entries", "items": [...] }` between Experience and Education **only** when step 4 surfaced JD-relevant `projects/*.md` (else leave it out). One item per JD-relevant project: `primary` = project name; `metaRight` = tech stack or `""` (use `metaRight`, **not** `dates`); `secondary` = the one-line project description; `bullets` = retrieved project bullets. |
| Skills `groups` | Each group is `{ "label", "value" }` with `value` a comma-separated list. Read the `###` category headings in `{sourceDir}/skills.md` **directly** for the grouping. Take a JD-relevant subset within each group and keep the source file's category structure. |
| Extra sections | Any additional section the source of truth supports (Publications, Certifications, Patents) → `{ "title", "type": "list", "items": [...] }`. |

**Length discipline.** The résumé soft ceiling is a fixed **2** pages. When density
is `compact` and the goal is a 1-page résumé, aim well below the ceiling: ~3
bullets per role (the strongest, JD-relevant ones), a 3-item intro, and drop
de-emphasized skill groups. Render, check the page count, and if over the soft
ceiling WARN and list candidate trims — never silently trim content to fit.

### `{dir}/tmp/cover_letter.data.json` — fields you fill in

| Key | Fill |
|---|---|
| `recipient` | Array of lines: `["Hiring Manager", "<Company> as the JD states it", "<City, Country>"]`. Use the named contact from the JD in place of `"Hiring Manager"` if it gives one. Drop the location line if the JD gives no location. Fall back to the `{Company}` argument if the JD names no company. |
| `subject` | `"Application for the Position of <role title from the JD>"`. If the JD carries a requisition / reference ID, append it naturally (e.g. `" (Ref: <id>)"`); **if the JD has none, no `"Ref:"` dangle**. |
| `paragraphs` | Array of body paragraphs, any count (typically intro, body1, body2, outro). Between them they must: (1) state the total professional software-engineering experience duration; (2) name the specific companies; (3) name the specific business domains / sectors; (4) name the company-tied tech stacks, each tied to the company it was used at (workflow-rules §9). Draw only on retrieved material; no overclaiming of `gap` criteria. |
| `salutation` (override) | Scaffolded to `"Dear Hiring Manager,"` for `--lang en` — override only if the JD names a contact (`"Dear <contact name>,"`). |

`factual-bounds.md` still applies to the letter — e.g. "Do not mention the university
in cover letters" means no `conventions.education` institution string appears anywhere
in `cover_letter.data.json`.

### `--lang zh`

When `--lang zh`:
- Pass `--lang zh` to `jobkit scaffold-data` — it sets `lang: "zh"` in both JSON files
  and fills in the Chinese section titles (工作经验 / 教育背景 / 技能) and
  `introTitle` (简介) for you.
- Résumé section `title`s you add yourself follow the same convention — e.g.
  `"精选项目"` for Selected Projects — as does any `stackLabel` override.
- Cover-letter `subject` / `salutation` / `closing` are Chinese (the script prefixes
  the `主题：` / `日期：` labels itself); the scaffolder leaves `salutation` and
  `closing` empty for `--lang zh` since translating them is your job.
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
