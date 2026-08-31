---
name: ingest
description: Build or refresh the resume_sections/ source-of-truth from a folder of the user's past CVs (.docx/.pdf/.tex/.md). Use when setting up the plugin or after adding a new CV/role.
---

## When to use

User says "ingest my CVs", "build resume_sections", "/ingest <path>", or a
source-of-truth directory does not exist yet.

## Steps

1. **Resolve directories.**
   - Source-of-truth dir: dot-source `${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.ps1`
     and call `Get-JobAppConfig`; use `.SourceOfTruthDir` (default `resume_sections/`),
     resolved relative to the user's project root. Create it if absent.
   - Input dir: the folder path the user supplied (the `/ingest` argument). It must
     be a directory containing past CVs. If the user gave a single file, use its
     parent and process only that file.

2. **Extract text from every CV.** For each `.md/.tex/.txt/.pdf/.docx` file in the
   input folder, run:

   ```
   pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/extract_cv.ps1 -Path <file>
   ```

   Collect each file's text, labelled by filename (so contradictions can be cited as
   `sample-cv-a.md` vs `sample-cv-b.md`). `.pdf` needs `pdftotext` (poppler); `.docx`
   needs `pandoc` — if a call throws, tell the user which tool to install and skip
   that file.

3. **Cluster.** Dispatch the `sot-retriever` subagent
   (`${CLAUDE_PLUGIN_ROOT}/agents/sot-retriever.md`) in `cluster` mode with
   `{ mode: "cluster", text: <combined labelled text>, sourceDir: <source-of-truth dir> }`.
   It returns a proposed mapping of employers / projects / education / skills /
   introduction points to destination files, with `[NEW]` vs `[DUP of file:line]`
   tags and a contradictions list.

4. **Create or MERGE section files (never overwrite).** For each cluster the
   subagent proposes, write to the source-of-truth dir:
   - `companies/<slug>.md` — one file per employer. `<slug>` is the lower-cased
     company name, alphanumerics and hyphens only (`Globex Pty Ltd` -> `globex`).
   - `projects/<slug>.md` — one file per personal/side project (only if the CVs
     contain projects).
   - `education.md` — all credentials.
   - `introduction.md` — the distilled summary points.
   - `skills.md` — the flat de-duplicated skill list.

   Follow the existing file style (see `${CLAUDE_PLUGIN_ROOT}/example/resume_sections/`):
   company files have a `### Company Overview` block (Company Name, Role Titles,
   Business Domain, Integrated Tech Stack) then `### Unique Bullet Points` with `- `
   bullets. **Merge is additive**: keep every existing bullet, append only
   `[NEW]` bullets, never delete. A re-run with one extra CV must not remove
   anything already present. Collapse near-duplicate bullets into one canonical
   bullet rather than listing both.

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
     output_dir: "applications/{Company}"
   ```

   - `links` is an inline map; today only `github` is used. Omit the key entirely
     if the CV shows no GitHub handle.
   - `conventions.roles` comes from the employment history, most recent first, and
     must match the companies you wrote in step 4. `conventions.education` mirrors
     `education.md`.
   - `default_resume_length` (pages, integer) and `default_include_projects`
     (boolean) are workflow defaults — use `1` and `false` unless the user says
     otherwise. `output_dir` stays `"applications/{Company}"` unless the user
     overrides it.
   - Dates: use the CV's own format normalised to `Mon. YYYY` (e.g. `Jan. 2024`),
     `Present` for a current role.
   - If a field is ambiguous or missing from the CVs, still write the key with your
     best guess and append a `# TODO confirm` comment on that line. Never invent a
     phone number or email.
   - If `profile.yml` already exists, do not clobber user edits: fill only missing
     keys and report what you changed.

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
   - the subagent's "Coverage notes" (existing material the new CVs did not mention),
     so the user knows nothing was dropped.

## Guardrails

- Only reorganise what the CVs contain. Never add skills, employers, projects,
  tools, metrics, or dates that are not in the extracted text.
- Every line you write to `skills.md` must be a case-insensitive substring of the
  ingest input text or of a company/project file you just produced. If it is not,
  drop it.
- Merges are additive; a re-run with one new CV must not delete existing bullets.
- Do not touch anything outside the source-of-truth dir. Do not run LaTeX or
  generate resumes here — that is the `generate` skill.
- Full workflow rules: `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`.
