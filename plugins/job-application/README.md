[English](README.md) | [中文](README.zh-CN.md)

# job-application

## What it is

`job-application` is a Claude Code plugin that turns a folder of your past CVs into a
tailored application for every job you apply to. It bundles five skills — `ingest`,
`jd-intake`, `generate`, `review-application`, and `interview` — plus supporting
scripts, HTML templates, and subagents. `ingest` consolidates your historical CVs into
a structured source-of-truth directory; `jd-intake` analyses a job description against
it; `generate` produces a tailored resume and cover letter; `review-application` runs a
QA gate over the result; and `interview` handles company research, question prep, and
mock interviews. The plugin is a generic engine: your candidate data lives in your own
repo and is never shipped with the plugin.

## Prerequisites

- Windows with PowerShell 7 (`pwsh`).
- **A Chromium browser** — Microsoft Edge (preinstalled on Windows), Google Chrome, or
  Chromium — used by `scripts/render_pdf.ps1` to render the HTML templates to PDF.
  Auto-detected from Program Files / PATH, or set `browser_path` in
  `jobapp.config.yml`.
- [Ghostscript](https://www.ghostscript.com/) (`gs` / `gswin64c` on the path) — used
  by `scripts/compress_pdf.ps1` to shrink the rendered PDFs. This step needs
  Ghostscript; a full TinyTeX install also satisfies it because it bundles a `ps2pdf`
  wrapper around Ghostscript, which the script will use as a fallback.
- `pdftotext` (Poppler) — used by `generate` and `review-application` to verify the
  rendered PDF's text, and by `ingest` for `.pdf` source CVs.
- Optional: `pandoc` for ingesting `.docx` source CVs. Plain `.tex` / `.md` CVs need
  neither it nor `pdftotext`.

## Install

The `jobkit` repository is a Claude Code marketplace; this plugin lives in
`plugins/job-application/`. Add the marketplace and install:

```
claude plugin marketplace add RyanDDDDDD/jobkit
claude plugin install job-application@job-application-marketplace
```

Or from a local checkout of `jobkit` (point at the repo root, not this subdirectory):

```
claude plugin marketplace add /path/to/jobkit
claude plugin install job-application@job-application-marketplace
```

## Setup

The plugin holds no candidate data. It reads its assets from where it is installed
(`${CLAUDE_PLUGIN_ROOT}`, read-only) and reads/writes **everything else — your source
of truth and every generated document — in the directory you run Claude Code from**,
resolved by `Get-JobAppConfig` walking up for `jobapp.config.yml`.

1. Make a private working folder (e.g. `~/job-hunt/`) and run Claude Code there. Keep
   it separate from this repo; nothing you generate belongs in the plugin.
2. Optional: copy `jobapp.config.example.yml` into it as `jobapp.config.yml` if you
   want non-default paths — `browser_path`, `ghostscript_path`, `source_of_truth_dir`,
   `output_dir`. Skip it to use the defaults (`resume_sections/`,
   `applications/{Company}/`).
3. Run `/ingest <path to your CVs>` (pointing at a folder of your past CVs) to build
   `resume_sections/` in that folder.
4. Review `resume_sections/profile.yml` — confirm your contact details, canonical
   company names, job titles, and employment dates.
5. Review `resume_sections/factual-bounds.md` — the "never claim" rules that constrain
   every generated document.

### Try it against the bundled fixture

Before pointing the plugin at your own data, run it against the synthetic candidate in
`tests/fixtures/`: `/ingest tests/fixtures/raw_cvs` to build the source of truth, then
`/jd-intake` on `tests/fixtures/sample-jd.md` and name the company `Testco` (the sample
JD is written for a fictional "Meridian Integration Partners"; you name the application
`Testco`), then `/generate` — you get a full resume + cover letter for a fictional
"Sample Dev" and can see the whole pipeline end to end.

`example/` holds a rendered sample of that output — nothing but the four PDFs:
résumé and cover letter, English and Chinese (`resume.pdf` / `resume.zh.pdf` /
`cover_letter.pdf` / `cover_letter.zh.pdf`). The `*.data.json` they were rendered from
live in `tests/fixtures/`.

## Daily use

One pass per job, in order:

```
/ingest <folder>                       # once (or after adding a new CV): build resume_sections/
/jd-intake                             # paste the job description, name the company
/generate [--density compact|standard] [--lang en|zh] [--with-projects]   # resume.data.json/pdf + cover_letter.data.json/pdf/txt
/review-application [--fix]            # QA gate: writes review.md (Pass / Flag / Fix)
/interview research|prep|mock          # company research | self-intro + HR prep | mock interview
```

- `/generate` flags: `--density compact|standard` sets the résumé spacing (default
  from `profile.yml`); `--lang zh` produces a Chinese résumé and cover letter (body
  text translated from your English source of truth); `--with-projects` adds a
  Selected Projects section built from the JD-relevant `projects/*.md`;
  `--max-pages N` is a soft page ceiling (a warning, never a truncation);
  `--order relevance|chronological` sets experience ordering; `--answers "Q1; Q2"`
  also writes `answers.md`.
- `/review-application --fix` applies only unambiguous safe corrections (present-tense
  bullets in past roles, fields that disagree with `profile.yml`, a stale
  `cover_letter.txt`), re-renders, and re-runs the checks once.
- `/interview` subcommands: `research` dispatches the `company-researcher` subagent to
  `{dir}/company_research.md`; `prep` writes `{dir}/self_intro.md` and
  `{dir}/hr_questions_prep.md`; `mock` runs a résumé-grounded mock interview with
  balanced feedback and appends new recurring lessons to `interview_playbook.md` at
  your repo root (seeded on first use from the plugin's `interview-frameworks.md`).

Every application's files land in one directory — `applications/{Company}/` by
default (`jd.md`, `analysis.md`, `resume.data.json/pdf`,
`cover_letter.data.json/pdf/txt`, `review.md`, and the interview-prep files).
Override the location with `output_dir` in `jobapp.config.yml`.

## The `resume_sections/` contract

The only thing the plugin requires from you is a source-of-truth directory (default
`resume_sections/`, overridable via `jobapp.config.yml`).
It contains:

| Path | Purpose |
|------|---------|
| `profile.yml` | Structured identity — the one non-markdown file. Name, contact, links, location, working rights, and canonical roles / education (exact company names, titles, and dates used verbatim on every generated document). Also holds conventions like default resume length and whether to include a projects section. |
| `factual-bounds.md` | Free-form "never claim" rules, loaded verbatim as hard constraints by `generate` and `review-application` (e.g. technologies you have never used, which stacks belong to which employer, no invented metrics, no university in cover letters). Grows over time as you correct generated drafts. |
| `companies/*.md` | Consolidated, de-duplicated per-company experience — the source of truth for all achievement bullets. |
| `projects/*.md` | Consolidated per-project achievements. |
| `education.md` | Education history. |
| `introduction.md` | Reusable personal summary / positioning statement. |
| `skills.md` | Consolidated skills inventory. |

## Running the tests

All mechanical tests run from one entry point — plain PowerShell, no Pester:

```
pwsh tests/run-pipeline.ps1
```

It renders the bundled HTML templates with the `tests/fixtures/*.data.json` fixtures
(asserting the résumé is one page), exercises `cover_letter_to_txt.ps1` and
`Get-JobAppConfig`, and then runs each `tests/scripts/*.Tests.ps1`, folding their
exit codes into the pass/fail count. Exit 0 means every check passed. The render
checks skip cleanly on a machine with no Chromium browser.

The synthetic candidate fixture the skills' expected-output checklists
(`tests/skills/*.expected.md`) are written against lives under `tests/fixtures/`
(`tests/fixtures/raw_cvs/`, `tests/fixtures/resume_sections/`,
`tests/fixtures/sample-jd.md`).
