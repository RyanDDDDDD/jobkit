# Job-hunt workspace (private)

This folder is the **working directory** for the `job-application` (jobkit) plugin.
The plugin is installed separately (`claude plugin install`), and its engine via `pip install jobkit` + `jobkit install-browser`.
Nothing here is part of the plugin — this is all personal data and generated output.

## Contents

- `private/` — everything personal, in one subtree so the workspace root stays clean
  and the folder is easy to exclude when sharing the setup.
  - `private/resume_sections/` — **the source of truth.** `profile.yml` (identity +
    canonical company names / job titles / employment dates — used verbatim), plus
    `companies/`, `projects/`, `education.md`, `introduction.md`, `skills.md`.
    Location set by `source_of_truth_dir` in `jobapp.config.yml`. Your own "never
    claim" rules (technologies never used, per-employer stack scoping, whether the
    university may be named, etc.) don't need a dedicated file here — add them
    directly to this `CLAUDE.md` (or an `AGENTS.md`), which every skill run already
    loads.
  - `private/interview_playbook.md` — accumulated interview lessons; the `interview`
    skill only ever appends to it. Location set by `interview_playbook` in
    `jobapp.config.yml`.
  - `private/questions_to_ask.md` — questions to ask interviewers.
- `applications/` — one folder per application (`jd.md`, `analysis.md`, `resume.*`,
  `cover_letter.*`, `interview/`). Location set by `output_dir`
  in `jobapp.config.yml`.
- `jobapp.config.yml` — resolves `source_of_truth_dir`, `output_dir`,
  `interview_playbook`, plus workspace `lang` (`en`|`zh`) and `resume_template`
  (`dossier`|`classic`|`modern-sans`|`signal`|`slate`) chosen at setup.

## Workflow

One-time: `/job-application:setup` scaffolds this folder; `/job-application:setup <folder of your old CVs>` also builds the source of truth.
Then fill in `private/resume_sections/profile.yml` (and, if you have any, your own
"never claim" rules — see Preferences below).

Populate the source of truth — either:
- `/job-application:setup <folder of your old CVs>` to build `private/resume_sections/`
  automatically, or
- hand-fill `introduction.md` / `skills.md` / `education.md` / `companies/*.md`.

Then one pass per job:
`/job-application:apply` → `/job-application:interview`.

## Preferences

Workspace language and résumé theme are set once at setup (`lang`,
`resume_template` in `jobapp.config.yml`). Résumé density (`compact` | `standard`)
and whether to include a Selected Projects section live in
`private/resume_sections/profile.yml` (`conventions.density` /
`conventions.include_projects`). jobkit does not manage a separate "never claim"
rules file — write your own constraints (technologies never used, per-employer
stack scoping, whether the university may be named in cover letters, metrics not
to invent, …) straight into this `CLAUDE.md` or an `AGENTS.md`; every skill run
loads it automatically, and on a conflict with the JD you'll be asked, not
silently overridden.
