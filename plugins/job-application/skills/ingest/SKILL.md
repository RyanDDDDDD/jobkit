---
name: ingest
description: Build or refresh the resume_sections/ source-of-truth from a folder of the user's past CVs (.docx/.pdf/.tex/.txt/.md). Use when setting up the plugin or after adding a new CV/role.
---

## When to use

User says "ingest my CVs", "build resume_sections", "/job-application:ingest <path>",
or a source-of-truth directory does not exist yet. If the working directory has not
been set up at all (no `jobapp.config.yml`), run `/job-application:init` first.

## Steps

1. **Resolve directories.**
   - Source-of-truth dir: run
     `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.py`
     (prints the resolved config as JSON) and resolve the directory by joining its
     `root` key
     onto `source_of_truth_dir` (default `resume_sections/`) — i.e.
     `<root>/<source_of_truth_dir>`. `root` is the directory where `jobapp.config.yml`
     was found by walking up from the current working directory, or
     the current directory if none is found. Create the directory if absent.
   - Input dir: the folder path the user supplied (the `/job-application:ingest`
     argument). It must
     be a directory containing past CVs. If the user gave a single file, use its
     parent and process only that file.

2. **Extract text from every CV.** For each `.md/.tex/.txt/.pdf/.docx` file in the
   input folder, run:

   ```
   uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/extract_cv.py <file>
   ```

   Collect each file's text, labelled by filename (so contradictions can be cited as
   `sample-cv-a.md` vs `sample-cv-b.md`). `.pdf` and `.docx` extraction has no
   external tool dependency (PyMuPDF / python-docx are part of the plugin's own `uv`
   environment) — if a call still fails (a corrupt or encrypted file), tell the user
   and skip that file.

3. **Cluster.** Dispatch the `sot-retriever` subagent
   (`${CLAUDE_PLUGIN_ROOT}/agents/sot-retriever.md`) in `cluster` mode with
   `{ mode: "cluster", text: <combined labelled text>, sourceDir: <source-of-truth dir> }`.
   It returns a proposed mapping of employers / projects / education / skills /
   introduction points to destination files, with `[NEW]` vs `[DUP of file:line]`
   tags and a contradictions list.

4. **Create or MERGE section files (never overwrite).** For each cluster the
   subagent proposes, write to the source-of-truth dir:
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

   Follow the existing file style (see `${CLAUDE_PLUGIN_ROOT}/tests/fixtures/resume_sections/`):
   - Company files have a `### Company Overview` block (Company Name, Role Titles,
     Business Domain, Integrated Tech Stack) then `### Unique Bullet Points` with
     `- ` bullets. Derive **Business Domain** only from how the CV text itself
     describes the employer (its sector / what it does); do not invent one. If the
     CV text says nothing about the employer's sector, write `not stated in source`
     and list it in the step-7 confirmation items for the user to fill in.
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

5. **Draft `profile.yml`.** Write it to the source-of-truth dir with EXACTLY this
   key structure (this is what Task 7's `generate` consumes — do not add or rename
   keys):

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
     default_resume_length: 1
     default_include_projects: false
   ```

   - `links` is an inline map; today only `github` is used. Omit the key entirely
     if the CV shows no GitHub handle.
   - `conventions.roles` comes from the employment history, most recent first, and
     must match the companies you wrote in step 4. `conventions.education` mirrors
     `education.md`.
   - `default_resume_length` (pages, integer) and `default_include_projects`
     (boolean) are workflow defaults — use `1` and `false` unless the user says
     otherwise.
   - `output_dir` is NOT part of `profile.yml` — it is machine/repo config in
     `jobapp.config.yml` (resolved by `config.py`, default
     `applications/{Company}`). Do not write it here.
   - Dates: use the CV's own format normalised to `Mon. YYYY` (e.g. `Jan. 2024`),
     `Present` for a current role.
   - If a field is ambiguous or missing from the CVs, still write the key with your
     best guess and append a `# TODO confirm` comment on that line. Never invent a
     phone number or email.
   - If `profile.yml` already exists, do not clobber user edits: fill only missing
     keys and report what you changed. A key counts as **missing** when it is
     absent, its value is an empty string, or its line carries a `# TODO` comment
     (the state `/job-application:init` leaves the template in) — fill those from
     the CVs. A key already set to a real value is left untouched. `phone` and
     `email` are still never invented; if the CVs contain none, leave the `# TODO`
     line as it is.

6. **Seed `factual-bounds.md`.** If it is absent in the source-of-truth dir, create
   it:

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

- Only reorganise what the CVs contain. Never add skills, employers, projects,
  tools, metrics, or dates that are not in the extracted text.
- Ground every `skills.md` entry. For each list item, strip any trailing
  parenthetical `(...)`; the remaining text must be a case-insensitive substring of
  the concatenation of the ingest input CV text and the `companies/*.md` /
  `projects/*.md` files you just produced. If it is not, reword the entry to a
  phrase that does appear (prefer the CV's own wording), or drop it. Never invent a
  skill the CVs do not support.
- Merges are additive; a re-run with one new CV must not delete existing bullets.
- Do not touch anything outside the source-of-truth dir. Do not run LaTeX or
  generate resumes here — that is the `generate` skill.
- Full workflow rules: `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`.
