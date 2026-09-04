---
name: init
description: Scaffold a fresh working directory for the plugin - jobapp.config.yml, CLAUDE.md, the private/ source-of-truth templates, a seeded interview_playbook.md, and applications/. Run once per workspace, before ingest.
---

## When to use

The user says "set up jobkit", "initialise a job-hunt workspace",
"/job-application:init", or runs a plugin skill in a directory that has no
`jobapp.config.yml`. Run once per working directory, before `ingest`.

## Steps

1. **Check for an existing flat layout.** If the working directory already has a
   top-level `resume_sections/` or `interview_playbook.md` and no `jobapp.config.yml`,
   it is a v0.3.x flat-layout workspace. Tell the user that `init` introduces the
   `private/` layout: after it runs they must move that existing content under
   `private/` (or hand-write `jobapp.config.yml` with the flat paths and skip
   `init`). Get their go-ahead before continuing.

2. **Scaffold.** Run, in the current working directory:

   ```
   uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/init_workspace.py --json
   ```

   It creates any of these that are absent, and never touches one that exists:
   `jobapp.config.yml`, `CLAUDE.md`, `applications/`,
   `private/resume_sections/{profile.yml, factual-bounds.md, introduction.md,
   skills.md, education.md}`, `private/resume_sections/{companies,projects}/`,
   `private/interview_playbook.md` (seeded from the plugin's
   `reference/interview-frameworks.md`), and `private/questions_to_ask.md`.

3. **Report.** Parse the JSON (`{"created": [...], "skipped": [...], "warnings": [...]}`)
   and show the user a short list — what was created vs already present. If `created`
   is empty, say the workspace is already initialised. If the JSON `warnings` array is
   non-empty, show every warning prominently and do not move on to the next steps until
   the user has resolved it.

4. **Next steps.** Tell the user, in order:
   - Fill in `private/resume_sections/profile.yml` (identity, canonical company
     names / titles / dates) and `private/resume_sections/factual-bounds.md` (the
     "never claim" rules).
   - Then **either** `/job-application:ingest <folder of your old CVs>` to populate
     `private/resume_sections/` and the blank `profile.yml` keys automatically,
     **or** hand-fill `introduction.md`, `skills.md`, `education.md`, and
     `companies/<employer>.md`.
   - Then `/job-application:jd-intake` to analyse your first job description.

## Guardrails

- **Never overwrites.** The script only creates files that are absent; an existing
  `jobapp.config.yml`, `CLAUDE.md`, or source-of-truth file is left byte-for-byte
  untouched. Safe to re-run.
- Does not run `ingest`, `generate`, or any other skill, and writes nothing outside
  the working directory.
- Uses no network and no candidate data — every value written is a static template
  placeholder.
- The scaffolded `jobapp.config.yml` sets the `private/` layout
  (`source_of_truth_dir: private/resume_sections`,
  `interview_playbook: private/interview_playbook.md`). A user who wants the flat
  default layout can edit or delete those keys.
