---
name: setup
description: Scaffold a job-application workspace and, given a folder of past CVs, build the resume_sections/ source of truth from them. Run once per workspace, before apply.
---

## When to use

The user says "set up jobkit", "initialise a job-hunt workspace", "ingest my CVs",
"/job-application:setup", "/job-application:setup <folder>", or a skill was run in
a directory with no `jobapp.config.yml`.

## Steps

Commands are `jobkit <sub>` (the plugin installs the `jobkit` CLI —
`pip install jobkit`). If `jobkit` is not on `PATH`, `python -m jobkit <sub>`
is exactly equivalent.

1. **Declare language + theme + GPA, then scaffold.** Ask the user (if not already
   stated) for three workspace-level choices — do not guess:

   - **Output language** `en` or `zh` — every apply / interview artifact defaults
     to this language (resume, cover letter, interview prep).
   - **Resume template** `dossier` (default Engineering Dossier), `classic`
     (conservative ATS serif), `modern-sans` (all-sans, A4-friendly), `signal`
     (Space Grotesk + DM Sans, cyan-to-purple accent), or `slate` (single-accent,
     compact card-style layout).
   - **Show GPA?** yes or no — workspace default for whether an education entry's
     `gpa` appears on the résumé (default: no, matching the experienced-hire
     default). Written to `conventions.include_gpa` (see step 5) after scaffolding.

   If the working directory already has a top-level `resume_sections/`
   or `interview_playbook.md` and no `jobapp.config.yml`, it is a v0.3.x flat-layout
   workspace. Tell the user that setup introduces the `private/` layout: after it
   runs they must move that existing content under `private/` (or hand-write
   `jobapp.config.yml` with the flat paths and skip scaffolding). Get their
   go-ahead before continuing.

   Run, in the current working directory (substitute the chosen values):

   ```
   jobkit init --lang <en|zh> --template <dossier|classic|modern-sans|signal|slate> --json
   ```

   Both `--lang` and `--template` are **required**. The command writes them into
   `jobapp.config.yml` and creates any of these that are absent (never touches one
   that exists): `jobapp.config.yml`, `CLAUDE.md`, `applications/`,
   `private/resume_sections/{profile.yml, introduction.md, skills.md,
   education.md}`, `private/resume_sections/{companies,projects}/`,
   `private/interview_playbook.md` (seeded from `jobkit doc interview-frameworks`),
   `private/questions_to_ask.md`, and `example/<theme>/{resume,cover_letter}[.zh].pdf`
   — sample output for all five bundled themes, so the user can see what jobkit
   produces before filling in their own data.

   Parse `{"created": [...], "skipped": [...], "warnings": [...]}`; show a short
   created-vs-skipped list. If `warnings` is non-empty, show every warning
   prominently and stop until the user resolves it.

   If the user answered "yes" to **Show GPA?**, `Edit`
   `private/resume_sections/profile.yml`'s `conventions.include_gpa` line from
   `false` to `true` (it scaffolds as `false`). Skip this edit if they answered "no"
   — the scaffolded default is already correct.

2. **If no CV folder argument was given:** stop. Tell the user, in order: fill
   `private/resume_sections/profile.yml` (identity, canonical company names /
   titles / dates) and, if they have any "never claim" rules, add them straight to
   the workspace `CLAUDE.md` (or an `AGENTS.md`) — every skill run loads it
   automatically; then either re-run `/job-application:setup <folder of your old
   CVs>` or hand-fill `introduction.md` / `skills.md` / `education.md` and one
   `companies/<slug>.md` per employer — start from the bundled section skeletons:
   a `### Company Overview` block (Company Name, Role Titles, Business Domain,
   Integrated Tech Stack) then `### Unique Bullet Points` with `- ` bullets;
   projects use `### Project Overview` + `### Unique Bullet Points`; then
   `/job-application:apply`.

3. **If a CV folder was given** — continue with ingest:

   1. **Resolve directories.** Resolve `{sourceDir}` with `jobkit config`
      (`{sourceDir}` = `<root>/<source_of_truth_dir>`). Create `{sourceDir}`
      if absent. Input dir: the folder path the user supplied. It must be a
      directory containing past CVs. If the user gave a single file, use its parent
      and process only that file.

   2. **Extract text from every CV.** For each `.md/.tex/.txt/.pdf/.docx` file in
      the input folder, run:

      ```
      jobkit extract-cv <file>
      ```

      Collect each file's text, labelled by filename (so contradictions can be
      cited as `sample-cv-a.md` vs `sample-cv-b.md`). `.pdf` and `.docx`
      extraction has no external tool dependency (PyMuPDF / python-docx ship with
      `jobkit`) — if a call still fails (a corrupt or
      encrypted file), tell the user and skip that file.

   3. **Cluster.** Dispatch the `sot-retriever` subagent in `cluster` mode with
      `{ mode: "cluster", text: <combined labelled text>, sourceDir: <resolved> }`.
      It returns a proposed mapping of employers / projects / education / skills /
      introduction points to destination files, with `[NEW]` vs `[DUP of file:line]`
      tags and a contradictions list.

   4. **Create or MERGE section files (never overwrite).** For each cluster the
      subagent proposes, write to `{sourceDir}`:
      - `companies/<slug>.md` — one file per employer. Derive `<slug>`: strip
        legal-entity suffixes (Corp, Corporation, Pty Ltd, Ltd, Inc, LLC, GmbH, Co,
        and similar), then lower-case and replace runs of non-alphanumerics with a
        single hyphen, and trim leading/trailing hyphens. Examples: `Acme Corp` ->
        `acme`, `Globex Pty Ltd` -> `globex`.
      - `projects/<slug>.md` — one file per personal/side project (only if the CVs
        contain projects); same slug rule.
      - `education.md` — all credentials.
      - `introduction.md` — the distilled summary points.
      - `skills.md` — the de-duplicated skill list.

      Start each new `companies/<slug>.md` / `projects/<slug>.md` from the matching
      skeleton shape (companies: `### Company Overview` then `### Unique Bullet
      Points`; projects: `### Project Overview` then `### Unique Bullet Points`):
      - Company files have a `### Company Overview` block (Company Name, Role Titles,
        Business Domain, Integrated Tech Stack) then `### Unique Bullet Points` with
        `- ` bullets. Derive **Business Domain** only from how the CV text itself
        describes the employer (its sector / what it does); do not invent one. If the
        CV text says nothing about the employer's sector, write `not stated in source`
        and list it in the confirmation items for the user to fill in.
      - Preserve the `- **Bold lead-in:** sentence.` bullet style: when a source
        bullet (or its existing source-of-truth counterpart) has a bold topic
        lead-in, keep/emit one; use a plain sentence bullet only when the source has
        no natural topic phrase.
      - `skills.md` keeps its grouped `###` category headers (e.g. `### Core
        Languages`, `### Frameworks & Libraries`, `### Tools, DevOps & Cloud`,
        `### Concepts, Protocols & Data`). Add each skill under the right existing
        category; do not flatten the file into one list.

      **Merge is additive**: keep every existing bullet, append only `[NEW]` bullets,
      never delete. A re-run with one extra CV must not remove anything already
      present. Collapse near-duplicate bullets into one canonical bullet rather than
      listing both.

   5. **Draft `profile.yml`.** Write it to `{sourceDir}` with EXACTLY this key
      structure (do not add or rename keys):

      ```yaml
      name: "<full name from CV header>"
      phone: "<phone from CV header>"
      email: "<email from CV header>"
      links: { github: "<github handle only, not a URL>" }
      location: "<City, Region, Country>"
      working_rights: "<e.g. full working rights in Australia>"
      conventions:
        roles:
          - { company: "<name>", title: "<title>", start: "<Mon. YYYY>", end: "<Mon. YYYY | Present>", location: "<City, Country>", ticker: "<optional, e.g. NZX/ASX: FBU>" }
        education:
          - { institution: "<name>", credential: "<degree>", start: "<YYYY>", end: "<YYYY>", location: "<City, Country>", rank: "<optional, e.g. QS 2027 世界第19 / 澳大利亚第1>", gpa: "<optional, only shown when include_gpa is true>" }
        density: compact
        include_projects: false
        include_gpa: <true if the user said yes in step 1, else false>
      ```

      - `links` is an inline map; today only `github` is used. Omit the key entirely
        if the CV shows no GitHub handle.
      - `conventions.roles` comes from the employment history, most recent first, and
        must match the companies you wrote in step 4. `conventions.education` mirrors
        `education.md`.
      - `conventions.roles[].ticker` and `conventions.education[].rank` are
        optional. For each role's company and each education entry's institution,
        search whether it is publicly listed (and its ticker, e.g.
        `"NZX/ASX: FBU"`) and its most recent QS / U.S. News / THE ranking (e.g.
        `"QS 2027 世界第19 / 澳大利亚第1"`). Write a clear, specific, confident
        finding verbatim; leave the field `""` if nothing specific and
        clearly-matching turns up — never guess, and never blend in a
        similarly-named company or institution. List every finding (including
        "not found") in the confirmation summary (step 7) for the user to verify.
        On a re-run, only research a role/education entry whose `ticker`/`rank` is
        still missing (absent, `""`, or a `# TODO` line) — never re-research or
        silently overwrite a value the user already set or corrected.
      - `density` (`compact` | `standard`), `include_projects` (boolean), and
        `include_gpa` (boolean) are workflow defaults — use `compact`, `false`, and
        whatever the user answered for **Show GPA?** in step 1 (default `false`)
        unless told otherwise.
      - `conventions.education[].gpa` is optional. Only fill it when
        `include_gpa` is `true` for this workspace: extract the GPA verbatim if a
        CV states one for that credential; otherwise leave `""` with a
        `# TODO confirm` comment, same as `phone`/`email` — never invent a GPA
        figure. When `include_gpa` is `false`, leave `gpa: ""` with no `# TODO`
        (there is nothing to confirm — it will not be shown).
      - `output_dir` is NOT part of `profile.yml` — it is machine/repo config in
        `jobapp.config.yml`. Do not write it here.
      - Dates: use the CV's own format normalised to `Mon. YYYY` (e.g. `Jan. 2024`),
        `Present` for a current role.
      - If a field is ambiguous or missing from the CVs, still write the key with your
        best guess and append a `# TODO confirm` comment on that line. Never invent a
        phone number or email.
      - If `profile.yml` already exists, do not clobber user edits: fill only missing
        keys and report what you changed. A key counts as **missing** when it is
        absent, its value is an empty string, or its line carries a `# TODO` comment
        (the state setup leaves the template in) — fill those from the CVs. A key
        already set to a real value is left untouched. An all-empty placeholder entry
        in `conventions.roles` / `conventions.education` (every field `""`) is
        **replaced** by the real entries derived from the CVs, never appended to.
        `phone` and `email` are still never invented; if the CVs contain none, leave
        the `# TODO` line as it is.

   6. **Print a confirmation summary.** List:
      - every file created vs merged (with counts of new bullets added);
      - an explicit table of the dates / titles / company names / contact details you
        wrote to `profile.yml`, for the user to confirm;
      - every CV contradiction the subagent flagged — ask the user to resolve each one,
        do NOT choose silently;
      - any company file whose Business Domain is `not stated in source`, so the user
        can supply the sector;
      - every ticker / ranking found (or explicitly not found) for a role or
        education entry, for the user to verify or correct;
      - the subagent's "Coverage notes" (existing material the new CVs did not mention),
        so the user knows nothing was dropped.

## Guardrails

- **Never overwrites** on scaffold: the script only creates files that are absent.
  Safe to re-run.
- Merges are additive; a re-run with one new CV must not delete existing bullets.
- Only reorganise what the CVs contain. Never add skills, employers, projects,
  tools, metrics, or dates that are not in the extracted text.
- Never invent a `ticker` or `rank` — only write one a web search clearly and
  specifically confirms for that exact employer/institution; leave the field
  blank otherwise.
- Ground every `skills.md` entry. For each list item, strip any trailing
  parenthetical `(...)`; the remaining text must be a case-insensitive substring of
  the concatenation of the ingest input CV text and the `companies/*.md` /
  `projects/*.md` files you just produced. If it is not, reword the entry to a
  phrase that does appear (prefer the CV's own wording), or drop it. Never invent a
  skill the CVs do not support.
- Do not touch anything outside the working directory. Do not run `apply` or render
  anything.
- Full workflow rules: `jobkit doc workflow-rules`.
