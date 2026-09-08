# Per-application directory layout (generic)

Every generated application for one job lives in one directory, `{dir}` — by
default `<root>/applications/{Company}/`, where `<root>` is the directory holding
`jobapp.config.yml` (or the working directory) and `{Company}` is the application
name. `config.py` resolves `{dir}`; the structure **inside** it is fixed and is not
configurable. `analysis.md` is a working note the `apply` run writes and `interview`
later reads as prose — not a strictly-parsed contract.

    {dir}/
    ├── jd.md                       verbatim job description            (apply)
    ├── analysis.md                 criteria -> evidence, fit, framing  (apply)
    ├── review.md                   QA report                          (apply)
    ├── resume.pdf                  deliverable                        (apply)
    ├── cover_letter.pdf            deliverable                        (apply)
    ├── cover_letter.txt            email-ready deliverable             (apply)
    ├── answers.md                  optional, with --answers            (apply)
    ├── interview/
    │   ├── company_research.md                                        (interview research)
    │   ├── self_intro.md                                              (interview prep)
    │   ├── hr_questions_prep.md                                       (interview prep)
    │   └── mock/
    │       ├── behavioural/<YYYY-MM-DD>[-N].md                        (interview mock)
    │       └── technical/<YYYY-MM-DD>[-N].md                          (interview mock)
    └── tmp/                        regenerable - safe to delete
        ├── resume.data.json                                           (apply)
        ├── cover_letter.data.json                                     (apply)
        ├── resume.rendered.html    transient during render             (apply)
        └── cover_letter.rendered.html

## Placement rules

| Location | Holds | Why |
|---|---|---|
| `{dir}/` (flat) | `jd.md`, `analysis.md`, `review.md`, the three PDFs/txt, `answers.md` | Read by a human or sent to an employer. |
| `{dir}/interview/` | research report, self-intro, HR prep, `mock/` | Interview-stage collateral. |
| `{dir}/interview/mock/<mode>/` | one `.md` per mock session | Separated by mode (`behavioural` / `technical`); one file per session so history is never lost. |
| `{dir}/tmp/` | `*.data.json`, `*.rendered.html` | Machine artifacts. Every one is rebuilt by re-running `apply`. Never put anything here that cannot be regenerated. |

## Session-file naming

`{dir}/interview/mock/<mode>/<YYYY-MM-DD>.md` for the day's first run of that mode;
a second run the same day writes `<YYYY-MM-DD>-2.md`, a third `-3.md`, and so on.
Existing session files are never appended to or overwritten.

## Which skill creates which subdirectory

Each skill creates only the subtree it writes (`mkdir -p` semantics): `apply` ->
`{dir}` + `{dir}/tmp`; `interview research`/`prep` -> `{dir}/interview`;
`interview mock` -> `{dir}/interview/mock/<mode>`.
