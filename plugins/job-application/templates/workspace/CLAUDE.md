# Job-hunt workspace (private)

This folder is the **working directory** for the `job-application` (jobkit) plugin.
The plugin is installed separately (`~/.claude/plugins/…`, or a local marketplace).
Nothing here is part of the plugin — this is all personal data and generated output.

## Contents

- `private/` — everything personal, in one subtree so the workspace root stays clean
  and the folder is easy to exclude when sharing the setup.
  - `private/resume_sections/` — **the source of truth.** `profile.yml` (identity +
    canonical company names / job titles / employment dates — used verbatim),
    `factual-bounds.md` (the "never claim" rules — a hard constraint on every
    generated document), plus `companies/`, `projects/`, `education.md`,
    `introduction.md`, `skills.md`. Location set by `source_of_truth_dir` in
    `jobapp.config.yml`.
  - `private/interview_playbook.md` — accumulated interview lessons; the `interview`
    skill only ever appends to it. Location set by `interview_playbook` in
    `jobapp.config.yml`.
  - `private/questions_to_ask.md` — questions to ask interviewers.
- `applications/` — one folder per application (`jd.md`, `analysis.md`, `resume.*`,
  `cover_letter.*`, optional `answers.md`, `interview/`). Location set by `output_dir`
  in `jobapp.config.yml`.
- `jobapp.config.yml` — resolves `source_of_truth_dir`, `output_dir`, and
  `interview_playbook`.

## Workflow

One-time: `/job-application:init` scaffolds this folder. Then fill in
`private/resume_sections/profile.yml` and `private/resume_sections/factual-bounds.md`.

Populate the source of truth — either:
- `/job-application:ingest <folder of your old CVs>` to build `resume_sections/`
  automatically, or
- hand-fill `introduction.md` / `skills.md` / `education.md` / `companies/*.md`.

Then one pass per job:
`/job-application:jd-intake` → `/job-application:generate` →
`/job-application:review-application` → `/job-application:interview`.

## Preferences

Résumé length, whether to include a projects section, and similar conventions live
in `private/resume_sections/profile.yml` (`conventions:` block). Per-application
"never claim" rules live in `private/resume_sections/factual-bounds.md`.
