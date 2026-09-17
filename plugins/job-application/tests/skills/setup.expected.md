# Integration-test assertions: `setup` skill

## Part A — scaffold

After running `/job-application:setup` in an empty directory `<ws>` (no
`jobapp.config.yml`, no `private/`), having declared `--lang` and `--template`,
the result must satisfy every assertion below.
Assertions are **structural** — file / directory existence and substring checks.

### fresh workspace

1. `<ws>/jobapp.config.yml` exists and contains all of
   `source_of_truth_dir: "private/resume_sections"`,
   `output_dir: "applications/{Company}"`,
   `interview_playbook: "private/interview_playbook.md"`,
   a `lang: "en"` or `lang: "zh"` line matching what setup asked for, and a
   `resume_template:` of `dossier`, `classic`, `modern-sans`, `signal`, or `slate`.
2. `<ws>/CLAUDE.md` exists.
3. `<ws>/private/resume_sections/` contains `profile.yml`, `factual-bounds.md`,
   `introduction.md`, `skills.md`, and `education.md`.
4. `<ws>/private/resume_sections/companies/` and
   `<ws>/private/resume_sections/projects/` exist as directories.
5. `<ws>/private/interview_playbook.md` exists and is byte-for-byte identical to the
   plugin's `reference/interview-frameworks.md`.
6. `<ws>/private/questions_to_ask.md` exists.
7. `<ws>/applications/` exists as a directory.
8. `<ws>/example/` contains one subdirectory per bundled theme (`dossier`, `classic`,
   `modern-sans`, `signal`, `slate`); `<ws>/example/dossier/` has `resume.pdf`,
   `resume.zh.pdf`, `cover_letter.pdf`, and `cover_letter.zh.pdf`; each other theme's
   subdirectory has `resume.pdf` and `cover_letter.pdf`.
9. `<ws>/private/resume_sections/profile.yml` still contains the `# TODO` markers —
   setup does not fill them in. It uses `density:` / `include_projects:` (not
   `default_density`, `default_resume_length`, or `default_include_projects`).
10. `<ws>/private/resume_sections/skills.md` contains the four headings
   `### Core Languages`, `### Frameworks & Libraries`, `### Tools, DevOps & Cloud`,
   and `### Concepts, Protocols & Data`.

### idempotent re-run

11. Running `/job-application:setup` a second time in `<ws>` creates no new file and
    modifies none — every path is reported as already present, and the content of
    `jobapp.config.yml` and every `private/` file is unchanged.

### non-destructive

12. If `<ws>/jobapp.config.yml` exists with custom content before the run, it is
    reported as skipped and its content is byte-for-byte unchanged; the rest of the
    scaffold is still created.

### flat-layout guard

13. If `<ws>` contained a top-level `resume_sections/` directory and no
    `jobapp.config.yml` before the run, the `jobkit init` JSON output's
    `warnings` array is non-empty and names both `resume_sections` and `private/`.

## Part B — ingest

After running `/job-application:setup tests/fixtures/raw_cvs` against a scaffolded
workspace (two synthetic CVs for "Sample Dev": Acme Corp SWE Jan 2024–Present,
Globex Pty Ltd Junior Developer Feb 2022–Dec 2023, Example University BCS), the
produced source-of-truth directory — referred to below as `<OUTPUT_DIR>` — must
satisfy every assertion.

`<OUTPUT_DIR>` is whatever directory the test points the skill at. Assertions are
phrased relative to it, not to a fixed folder.

1. `<OUTPUT_DIR>/companies/acme.md` exists and contains at least one line that
   starts with `- ` (a bullet). Company files use the `### Company Overview` /
   `### Unique Bullet Points` structure.

2. `<OUTPUT_DIR>/companies/globex.md` exists (same structure).

3. `<OUTPUT_DIR>/profile.yml` exists and parses as YAML, with:
   - `name` equal to `Sample Dev`
   - `conventions.roles` a non-empty list whose entries each have
     `company`, `title`, `start`, `end`, `location`, and match the companies written
   - `conventions.education` a non-empty list
   - `conventions.density` / `conventions.include_projects` present (not
     `default_*` keys)

4. `<OUTPUT_DIR>/factual-bounds.md` exists (seeded, heading present; body may be
   just the "add rules as you correct drafts" comment).

5. No duplicated bullet text across the two company files: no identical bullet
   sentence (normalised: trimmed, lower-cased, leading `- ` removed) appears in both
   `<OUTPUT_DIR>/companies/acme.md` and `<OUTPUT_DIR>/companies/globex.md`. The two
   source CVs describe the same roles in overlapping wording; the skill must
   collapse, not duplicate.

6. No-hallucination check: for every non-blank list item in
   `<OUTPUT_DIR>/skills.md` (a line starting with `- `, ignoring the `###` category
   headers), strip any trailing parenthetical `(...)` and trim; the remaining text
   must be a case-insensitive substring of the concatenation of the ingest input
   CV files (`tests/fixtures/raw_cvs/*.md`) and the produced `<OUTPUT_DIR>/companies/*.md`
   + `<OUTPUT_DIR>/projects/*.md` files. Nothing in `skills.md` may be invented
   beyond what the CVs and produced company/project files contain. `skills.md` keeps
   its `###` category headers.

7. Merges are additive on re-run: a second `/job-application:setup` against the same
   CV folder must not delete existing bullets. Contradictions are surfaced to the
   user, not silently resolved.
