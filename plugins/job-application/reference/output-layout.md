# Per-application directory layout (generic)

Every generated application for one job lives in one directory, `{dir}` — by
default `<root>/applications/{Company}/`, where `<root>` is the directory holding
`jobapp.config.yml` (or the working directory) and `{Company}` is the application
name. `config.py` resolves `{dir}`; the structure **inside** it is fixed and is not
configurable.

    {dir}/
    ├── jd.md                       verbatim job description            (jd-intake)
    ├── analysis.md                 criteria -> evidence, fit, framing  (jd-intake)  analysis.md is a working note the `apply` run writes and `interview` later reads as prose — not a strictly-parsed contract.
    ├── review.md                   QA report                          (review-application)
    ├── resume.pdf                  deliverable                        (generate)
    ├── cover_letter.pdf            deliverable                        (generate)
    ├── cover_letter.txt            email-ready deliverable             (generate)
    ├── answers.md                  optional, with --answers            (generate)
    ├── interview/
    │   ├── company_research.md                                        (interview research)
    │   ├── self_intro.md                                              (interview prep)
    │   ├── hr_questions_prep.md                                       (interview prep)
    │   └── mock/
    │       ├── behavioural/<YYYY-MM-DD>[-N].md                        (interview mock)
    │       └── technical/<YYYY-MM-DD>[-N].md                          (interview mock)
    └── tmp/                        regenerable - safe to delete
        ├── resume.data.json                                           (generate)
        ├── cover_letter.data.json                                     (generate)
        ├── resume.rendered.html    only with --keep-html              (generate)
        └── cover_letter.rendered.html

## Placement rules

| Location | Holds | Why |
|---|---|---|
| `{dir}/` (flat) | `jd.md`, `analysis.md`, `review.md`, the three PDFs/txt, `answers.md` | Read by a human or sent to an employer. |
| `{dir}/interview/` | research report, self-intro, HR prep, `mock/` | Interview-stage collateral. |
| `{dir}/interview/mock/<mode>/` | one `.md` per mock session | Separated by mode (`behavioural` / `technical`); one file per session so history is never lost. |
| `{dir}/tmp/` | `*.data.json`, `*.rendered.html` | Machine artifacts. Every one is rebuilt by re-running `generate`. Never put anything here that cannot be regenerated. |

## Session-file naming

`{dir}/interview/mock/<mode>/<YYYY-MM-DD>.md` for the day's first run of that mode;
a second run the same day writes `<YYYY-MM-DD>-2.md`, a third `-3.md`, and so on.
Existing session files are never appended to or overwritten.

## Which skill creates which subdirectory

Each skill creates only the subtree it writes (`mkdir -p` semantics): `jd-intake` ->
`{dir}`; `generate` -> `{dir}` + `{dir}/tmp`; `review-application` -> `{dir}` (reads
`{dir}/tmp`, may rewrite it under `--fix`); `interview research`/`prep` ->
`{dir}/interview`; `interview mock` -> `{dir}/interview/mock/<mode>`.
