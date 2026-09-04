# Integration-test assertions: `init` skill

After running `/job-application:init` in an empty directory `<ws>` (no
`jobapp.config.yml`, no `private/`), the result must satisfy every assertion below.
Assertions are **structural** — file / directory existence and substring checks.

## fresh workspace

1. `<ws>/jobapp.config.yml` exists and contains all three of
   `source_of_truth_dir: "private/resume_sections"`,
   `output_dir: "applications/{Company}"`, and
   `interview_playbook: "private/interview_playbook.md"`.
2. `<ws>/CLAUDE.md` exists.
3. `<ws>/private/resume_sections/` contains `profile.yml`, `factual-bounds.md`,
   `introduction.md`, `skills.md`, and `education.md`.
4. `<ws>/private/resume_sections/companies/` and
   `<ws>/private/resume_sections/projects/` exist as directories.
5. `<ws>/private/interview_playbook.md` exists and is byte-for-byte identical to the
   plugin's `reference/interview-frameworks.md`.
6. `<ws>/private/questions_to_ask.md` exists.
7. `<ws>/applications/` exists as a directory.
8. `<ws>/private/resume_sections/profile.yml` still contains the `# TODO` markers —
   `init` does not fill them in.
9. `<ws>/private/resume_sections/skills.md` contains the four headings
   `### Core Languages`, `### Frameworks & Libraries`, `### Tools, DevOps & Cloud`,
   and `### Concepts, Protocols & Data`.

## idempotent re-run

10. Running `/job-application:init` a second time in `<ws>` creates no new file and
    modifies none — every path is reported as already present, and the content of
    `jobapp.config.yml` and every `private/` file is unchanged.

## non-destructive

11. If `<ws>/jobapp.config.yml` exists with custom content before the run, it is
    reported as skipped and its content is byte-for-byte unchanged; the rest of the
    scaffold is still created.

## flat-layout guard

12. If `<ws>` contained a top-level `resume_sections/` directory and no
    `jobapp.config.yml` before the run, the `init_workspace.py` JSON output's
    `warnings` array is non-empty and names both `resume_sections` and `private/`.
