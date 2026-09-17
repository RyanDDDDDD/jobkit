---
name: apply
description: Turn a job description into a tailored resume and cover letter. Analyzes the JD, retrieves evidence from the source of truth, and renders and compresses the PDFs.
---

## When to use

The user pastes a JD, uploads a JD file, or says "apply to {Company}", "tailor my
CV for {Company}", or "/job-application:apply". Requires a source-of-truth dir — if
missing, tell the user to run `/job-application:setup` first and stop.

## Flags

- `--lang en|zh` — default from `jobapp.config.yml` `lang` (set at setup). If the
  flag is omitted, read `lang` from `jobkit config`. `zh` ⇒ `lang: "zh"` in both
  JSON files, Chinese section titles / salutation / closing, body strings
  translated from the English source of truth (never invented). See "`--lang zh`"
  below. Override only when this one application must differ from the workspace
  default.
- `--density compact|standard` — résumé spacing. Default: `profile.yml`
  `conventions.density` if set, else `compact`. Sets `density` in
  `resume.data.json`; the template's `compact` class tightens spacing ~12%.

## Inputs and paths

Resolve paths with `jobkit config` (JSON: `root`, `source_of_truth_dir`,
`output_dir`, `interview_playbook`, `browser_path`, `lang`, `resume_template`).
`{sourceDir}` = `<root>/<source_of_truth_dir>` — if it does not exist, tell the
user to run `/job-application:setup` first and stop. `{dir}` =
`<root>/<output_dir>` with the literal `{Company}` token replaced by the
application name. Create `{dir}` and `{dir}/tmp`. The bundled theme is
`resume_template` from config (`dossier` | `classic` | `modern-sans` | `signal` | `slate`);
`jobkit render` picks `templates/<theme>/{resume,cover_letter}.html` automatically.
A repo-level `<root>/templates/resume.html` / `cover_letter.html` override, if
present, still wins. Machine artifacts (`resume.data.json`,
`cover_letter.data.json`) live in `{dir}/tmp/`; `jd.md`, `analysis.md`,
the PDFs, and `cover_letter.txt` stay flat in `{dir}`.
Full tree: `jobkit doc output-layout`.

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

5. **Scaffold, then build the data objects.** Run `jobkit scaffold-data` (see
   "## Building the data files" below) to write `{dir}/tmp/resume.data.json` and
   `{dir}/tmp/cover_letter.data.json` with every `profile.yml`-derived field
   already filled in — name, contact, lang, density, today's date, each
   Experience item's `primary`/`dates`/`secondary`/`location`, and the whole
   Education section. These are correct as scaffolded and **you never edit them**,
   **except** that for `--lang zh` you translate Experience `primary`, Education
   `institution`/`credential`, and both sections' `location` into Chinese — see
   "`--lang zh`" below for exactly which fields and why. `dates` is never your job
   to touch in either language — `scaffold-data` already reformats it for
   `--lang zh`. Then `Edit` in the judgment content: `intro`, each Experience
   item's `stack`/`bullets`/`summary`, the Skills `groups` (read the `###`
   category headings in `{sourceDir}/skills.md` directly), a Selected Projects
   section **only** when step 4 surfaced JD-relevant `projects/*.md` (insert it
   between Experience and Education; else omit it entirely), and the cover
   letter's `recipient`/`subject`/`paragraphs` (and, for `--lang zh`,
   `salutation`/`closing`). Experience order is reverse-chronological by default
   (matching `profile.yml` `conventions.roles` file order); reorder the
   scaffolded `items[]` array via `Edit` if `## Framing` calls for relevance
   order instead.

6. **Render both PDFs in one call.** Both `.data.json` files are already on disk
   from step 5 (see "## Building the data files"). Render the résumé and the cover
   letter in a **single** `jobkit render` invocation — `--kind` / `--data` / `--out`
   are repeatable and zipped positionally, so one Chromium launch produces both,
   and the call itself compresses each successfully-rendered PDF, writes
   `{dir}/cover_letter.txt` for the `cover_letter` job, cleans up its own
   `.rendered.html` temp files, and prints a `Report:` block — there is nothing
   left to run after it:

   ```
   jobkit render \
     --kind resume       --data {dir}/tmp/resume.data.json       --out {dir}/resume.pdf \
     --kind cover_letter --data {dir}/tmp/cover_letter.data.json --out {dir}/cover_letter.pdf
   ```

   The command prints one `OK: <pdf> (N page[s])` line per document and exits 0
   only if **both** rendered. On a non-zero exit, apply the
   `jobkit doc render-contract` failure handling **per failed document**
   (surface its `Render failed [<pdf>]:` text, keep that `.data.json`, do not
   claim success); a document that rendered is still usable — it is compressed
   and (if it's the cover letter) converted to `.txt` regardless of whether its
   sibling job failed. A `WARN: compress failed …` or `WARN: cover-txt failed …`
   line does not mean the render failed — the PDF itself is still a valid
   deliverable, just not compressed (or, for the cover letter, missing its
   `.txt`).

   End state: `{dir}/` has `jd.md`, `analysis.md`, `resume.pdf`,
   `cover_letter.pdf`, `cover_letter.txt`; `{dir}/tmp/` has `resume.data.json`,
   `cover_letter.data.json`.

7. **Report.** Relay the `Report:` block `jobkit render` already printed to the
   user — page counts, `--density`/`--lang`, whether Selected Projects was
   included, the experience ordering used, and any `analysis.md` gap the
   documents honestly do not cover (expected — state it, do not paper over it).
   Reformatting for chat is fine; inventing or omitting a line is not.

## Building the data files

Run the scaffolder, then edit in the judgment content:

```
jobkit scaffold-data --dir {dir} --source-dir {sourceDir} --lang <en|zh> --density <compact|standard>
```

This writes both `.data.json` files, already valid JSON, with every field
`profile.yml` (plus `--lang`/`--density`) determines pre-filled. When `--lang`
is omitted, `scaffold-data` uses workspace `jobapp.config.yml` `lang`:

| Key | Value |
|---|---|
| `name` | `profile.yml` `name`, verbatim. |
| `lang` | `"en"` or `"zh"` per `--lang`. |
| `density` | `"compact"` or `"standard"` per `--density` (`profile.yml` `conventions.density` if the flag is omitted, else `"compact"`). |
| `contact` (both files) | Array from `profile.yml`: `phone` as a plain string; `email` as `{ "text": "<email>", "href": "mailto:<email>" }`; and, only if `links.github` is set, `{ "text": "github.com/<handle>", "href": "https://github.com/<handle>" }`. |
| `introTitle` | Only set (to `"简介"`) for `--lang zh`; omitted for `--lang en` (renderer default `"Introduction"`). |
| Experience items | One per `profile.yml` `conventions.roles` entry, in file order: `primary` = role `title`, `dates` = `"<start> – <end>"` (en-dash, U+2013; reformatted to Chinese for `--lang zh` by `scaffold-data`), `secondary` = role `company` (plus `" (ticker)"` when the role has one) — always verbatim, `location` = role `location`. `stack: ""`, `bullets: []`, and `summary: ""` are left for you. For `--lang zh`, translate `primary` and `location` after scaffolding (see "`--lang zh`" below); for `--lang en` leave them verbatim. |
| Education section | Fully filled — one item per `conventions.education` entry: `institution`, `dates` (reformatted to Chinese for `--lang zh`), `credential`, `location`, plus `note` (from the entry's `rank`, if any) and `gpa` (from the entry's `gpa`, only when `conventions.include_gpa` is `true`) — all pre-filled by `scaffold-data`. For `--lang zh`, translate `institution`, `credential`, and `location` after scaffolding (see "`--lang zh`" below); for `--lang en` leave them verbatim. Nothing else to add here. |
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
| Experience items' `summary` | 1–2 sentences distilling that company's Company Overview (`companies/<slug>.md` — the Business Domain line, optionally plus the role's scope within it). Leave `""` (omit) if Business Domain is `"not stated in source."` `summaryLabel` is optional (default `"Summary"`). |
| Experience items' `bullets` | The retrieved bullets for that role, best-first, verb-first, past tense (present only for an ongoing duty in a current role). Emit as many as the role warrants (3–6; see "Length discipline" below). Follow the **bullet format rule** below. |
| `sections` — Selected Projects | Insert `{ "title": "Selected Projects", "type": "entries", "items": [...] }` between Experience and Education **only** when step 4 surfaced JD-relevant `projects/*.md` (else leave it out). One item per JD-relevant project: `primary` = project name; `metaRight` = tech stack or `""` (use `metaRight`, **not** `dates`); `summary` = 1–2 sentences distilling that project's Project Overview (`projects/<slug>.md`); `bullets` = retrieved project bullets. Leave `secondary` unset — there is no org line for a personal project. |
| Skills `groups` | Each group is `{ "label", "value" }` with `value` a comma-separated list. Read the `###` category headings in `{sourceDir}/skills.md` **directly** for the grouping. Take a JD-relevant subset within each group and keep the source file's category structure. |
| Extra sections | Any additional section the source of truth supports (Publications, Certifications, Patents) → `{ "title", "type": "list", "items": [...] }`. |

**Bullet format rule.** Every experience bullet must follow the pattern:

```
**Category keyword:** Action verb + technical detail + quantified result (where available).
```

- The **category keyword** is a short noun phrase (2–4 words) that labels what kind of work the bullet describes — e.g. `Performance Tuning`, `Architecture Refactoring`, `Service Integration`, `CI/CD Automation`. It is rendered bold.
- The body starts with a **past-tense action verb** (e.g. *Profiled*, *Refactored*, *Engineered*, *Integrated*).
- Include **specific technologies** and a **quantified result** wherever the source of truth provides one (e.g. "reducing memory footprint by 40%", "cutting startup time by 50%").
- Do **not** start with "Responsible for", "Worked on", or other weak openers.
- For `--lang zh` résumés the keyword is Chinese (e.g. `性能调优：`、`架构重构：`) and rendered bold via `<strong>` in the HTML template — the pattern is otherwise identical.

Example (en): `**Performance Tuning:** Utilized perf and Valgrind for bottleneck analysis and memory profiling, ensuring zero-leak execution for industrial-grade components.`
Example (zh): `**性能调优：** 使用 perf、Valgrind 进行瓶颈分析与内存剖析，确保工业级组件零泄漏运行。`

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
  `"精选项目"` for Selected Projects — as does any `stackLabel` / `summaryLabel`
  override.
- Translate, after scaffolding: each Experience item's `primary` (job title) and
  `location`; each Education item's `institution`, `credential`, and `location` — to
  the standard/official Chinese rendering (e.g. a well-known university's official
  Chinese name). `secondary` (company name, plus its `ticker` if any) is a proper
  noun and is never translated. `dates` is never your job either —
  `scaffold-data` already reformatted it (e.g. `"Jan. 2024"` → `"2024年1月"`,
  `"Present"` → `"至今"`).
- Cover-letter `subject` / `salutation` / `closing` are Chinese (the script prefixes
  the `主题：` / `日期：` labels itself); the scaffolder leaves `salutation` and
  `closing` empty for `--lang zh` since translating them is your job.
- Every body string (`intro` `lead`/`text`, `bullets`, `stack`, `summary`, Skills
  `groups`' `label`/`value`, cover-letter `paragraphs`) is translated from the
  English source-of-truth content — along with the structural fields named above
  (job title, institution, credential, location). Keep tool/language/framework/
  product proper nouns (e.g. `PostgreSQL`, `React`, `Modern C++`, `Linux`, `Git`) in
  their standard form; translate the surrounding descriptive language. This, plus
  the structural-field translations above, is the only place in the whole workflow
  where translation happens.
- `factual-bounds.md` and the no-invention rules apply to the translated text exactly
  as they do to English — do not invent a detail to make a smoother Chinese sentence.
  Translating a correctly-recorded job title, institution name, or location into
  Chinese is expected, not a zero-basis addition.

## Guardrails

- Company names, tickers, and dates from `profile.yml` verbatim in both languages.
  Job titles, institution/credential names, and locations are verbatim for
  `--lang en`, translated to Chinese for `--lang zh` (never invented — a faithful
  translation of a recorded fact, not a new one).
- The one prohibition is zero-basis additions (workflow-rules §3).
- `factual-bounds.md` is hard — on conflict stop and ask.
- Follows workspace `lang` (or `--lang` override); `zh` faithfully translated.
- Machine artifacts in `{dir}/tmp/`, deliverables flat.
- `jd.md` stays (workflow-rules §7).
- `jobkit doc workflow-rules` and `jobkit doc render-contract`.
