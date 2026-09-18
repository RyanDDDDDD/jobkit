# Integration-test assertions: `interview` skill

After running `interview` subcommands for a company whose per-application directory
`<dir>` already contains `jd.md`, `analysis.md`, and `tmp/resume.data.json`
(produced by `/job-application:apply` against `tests/fixtures/resume_sections/`,
candidate "Sample Dev"), the output must satisfy every assertion below. Assertions
are **structural** — file existence, heading presence/order, and substring checks,
not exact prose.

## research / prep paths

1. `interview research` writes `<dir>/interview/company_research.md` and leaves
   nothing at the old flat path `<dir>/company_research.md`.
2. `interview prep` writes `<dir>/interview/self_intro.md` and
   `<dir>/interview/hr_questions_prep.md`, and nothing at the old flat paths.

## mock — modes and records

3. `interview mock technical` writes exactly one file under
   `<dir>/interview/mock/technical/`, named `<YYYY-MM-DD>.md` for today's date, and
   creates nothing under `<dir>/interview/mock/behavioural/`.
4. `interview mock behavioural` writes exactly one file under
   `<dir>/interview/mock/behavioural/` and does not touch any `technical/` record.
5. A second `interview mock technical` run on the same day writes
   `<dir>/interview/mock/technical/<YYYY-MM-DD>-2.md`; the first run's file is
   byte-for-byte unchanged.
6. Every record file contains the headings `## Questions`, `## Debrief`, and
   `## Playbook`, in that order, each on its own line.
7. Under `## Questions`, every `### `-prefixed numbered block contains a line
   starting `- **Your answer:**`, one starting `- **Feedback:**`, and one starting
   `- **Stronger answer:**`.
8. In a `technical` record, every `### ` block additionally contains a line starting
   `- **Target:**`, and each Target value matches either a role `secondary` in
   `tmp/resume.data.json` or a project name from the résumé's Selected Projects
   section / a `tests/fixtures/resume_sections/projects/*.md` file.
9. In a `mock technical` run, every résumé bullet carrying a number is followed up
   on with at least one 'how was this measured / what are its bounds' question.

## grounding

10. No `interview/` output file (research, prep, or any mock record) contains the
    word `Rust` (case-insensitive) — Rust appears nowhere in
    `tests/fixtures/resume_sections/` and the fixture JD does not ask for it
    (zero-basis rule).
11. Every mock question and every **Stronger answer** is answerable from
    `tmp/resume.data.json` / the fixture source of truth: no employer, technology,
    or numeric metric appears that is absent from them.

## aborted run

12. If the operator is asked for the mock mode and does not supply one (the run is
    abandoned), no file is created under `<dir>/interview/mock/`.
