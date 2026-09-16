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

1. **Declare language + theme, then scaffold.** Ask the user (if not already
   stated) for two workspace-level choices — do not guess:

   - **Output language** `en` or `zh` — every apply / interview artifact defaults
     to this language (resume, cover letter, interview prep).
   - **Resume template** `dossier` (default Engineering Dossier), `classic`
     (conservative ATS serif), `modern-sans` (all-sans, A4-friendly), `signal`
     (Space Grotesk + DM Sans, cyan-to-purple accent), or `slate` (single-accent,
     compact card-style layout).

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
   `private/resume_sections/{profile.yml, factual-bounds.md, introduction.md,
   skills.md, education.md}`, `private/resume_sections/{companies,projects}/`,
   `private/interview_playbook.md` (seeded from `jobkit doc interview-frameworks`),
   and `private/questions_to_ask.md`.

   Parse `{"created": [...], "skipped": [...], "warnings": [...]}`; show a short
   created-vs-skipped list. If `warnings` is non-empty, show every warning
   prominently and stop until the user resolves it.

2. **If no CV folder argument was given:** stop. Tell the user, in order: fill
   `private/resume_sections/profile.yml` (identity, canonical company names /
   titles / dates) and `private/resume_sections/factual-bounds.md` (the "never
   claim" rules); then either re-run `/job-application:setup <folder of your old
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
          - { company: "<name>", title: "<title>", start: "<Mon. YYYY>", end: "<Mon. YYYY | Present>", location: "<City, Country>" }
        education:
          - { institution: "<name>", credential: "<degree>", start: "<YYYY>", end: "<YYYY>", location: "<City, Country>" }
        density: compact
        include_projects: false
      ```

      - `links` is an inline map; today only `github` is used. Omit the key entirely
        if the CV shows no GitHub handle.
      - `conventions.roles` comes from the employment history, most recent first, and
        must match the companies you wrote in step 4. `conventions.education` mirrors
        `education.md`.
      - `density` (`compact` | `standard`) and `include_projects` (boolean) are
        workflow defaults — use `compact` and `false` unless the user says otherwise.
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

   6. **Seed `factual-bounds.md`.** If it is absent in `{sourceDir}`, create it:

      ```markdown
      # Factual Bounds — <name>

      <!-- Add one rule per line as you correct drafts. These are hard constraints the
           resume/cover-letter steps must never violate: technologies never used,
           per-employer stack scoping, metrics that must not be invented, whether the
           university may be named in cover letters, etc. -->
      ```

      If it already exists, leave it completely untouched.

   7. **Print a confirmation summary.** List:
      - every file created vs merged (with counts of new bullets added);
      - an explicit table of the dates / titles / company names / contact details you
        wrote to `profile.yml`, for the user to confirm;
      - every CV contradiction the subagent flagged — ask the user to resolve each one,
        do NOT choose silently;
      - any company file whose Business Domain is `not stated in source`, so the user
        can supply the sector;
      - the subagent's "Coverage notes" (existing material the new CVs did not mention),
        so the user knows nothing was dropped.

## Guardrails

- **Never overwrites** on scaffold: the script only creates files that are absent.
  Safe to re-run.
- Merges are additive; a re-run with one new CV must not delete existing bullets.
- Only reorganise what the CVs contain. Never add skills, employers, projects,
  tools, metrics, or dates that are not in the extracted text.
- Ground every `skills.md` entry. For each list item, strip any trailing
  parenthetical `(...)`; the remaining text must be a case-insensitive substring of
  the concatenation of the ingest input CV text and the `companies/*.md` /
  `projects/*.md` files you just produced. If it is not, reword the entry to a
  phrase that does appear (prefer the CV's own wording), or drop it. Never invent a
  skill the CVs do not support.
- Do not touch anything outside the working directory. Do not run `apply` or render
  anything.
- Full workflow rules: `jobkit doc workflow-rules`.
