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

- **Windows, macOS, or Linux** — the plugin has no OS-specific dependency.
- [`uv`](https://docs.astral.sh/uv/) — manages the plugin's Python environment.
  One-time install: see uv's own install instructions for your OS.
- A one-time browser download: `uv run --project ${CLAUDE_PLUGIN_ROOT} playwright
  install chromium` (downloads a Chromium binary Playwright manages itself — no
  system browser install needed).

No Ghostscript, Poppler, or `pandoc` install is required — PDF compression and
`.pdf`/`.docx` text extraction are pure-Python (`pikepdf`, `pymupdf`,
`python-docx`), installed automatically the first time a script runs via `uv run`.

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
resolved by `config.py` walking up for `jobapp.config.yml`.

1. Make a private working folder (e.g. `~/job-hunt/`) and run Claude Code there. Keep
   it separate from this repo; nothing you generate belongs in the plugin.
2. Optional: copy `jobapp.config.example.yml` into it as `jobapp.config.yml` if you
   want non-default paths — `browser_path`, `source_of_truth_dir`, `output_dir`,
   `interview_playbook`. Skip it to use the defaults (`resume_sections/`,
   `applications/{Company}/`, `interview_playbook.md`).
3. Run `/job-application:ingest <path to your CVs>` (pointing at a folder of your past
   CVs) to build `resume_sections/` in that folder.
4. Review `resume_sections/profile.yml` — confirm your contact details, canonical
   company names, job titles, and employment dates.
5. Review `resume_sections/factual-bounds.md` — the "never claim" rules that constrain
   every generated document.

### Try it against the bundled fixture

Before pointing the plugin at your own data, run it against the synthetic candidate in
`tests/fixtures/`: `/job-application:ingest tests/fixtures/raw_cvs` to build the source
of truth, then `/job-application:jd-intake` on `tests/fixtures/sample-jd.md` and name
the company `Testco` (the sample JD is written for a fictional "Meridian Integration
Partners"; you name the application `Testco`), then `/job-application:generate` — you
get a full resume + cover letter for a fictional "Sample Dev" and can see the whole
pipeline end to end.

`example/` holds a rendered sample of that output — nothing but the four PDFs:
résumé and cover letter, English and Chinese (`resume.pdf` / `resume.zh.pdf` /
`cover_letter.pdf` / `cover_letter.zh.pdf`). The `*.data.json` they were rendered from
live in `tests/fixtures/`.

## Daily use

One pass per job, in order:

```
/job-application:ingest <folder>                       # once (or after adding a new CV): build resume_sections/
/job-application:jd-intake                             # paste the job description, name the company
/job-application:generate [--density compact|standard] [--lang en|zh] [--with-projects]   # tmp/*.data.json + resume.pdf + cover_letter.pdf/txt
/job-application:review-application [--fix]            # QA gate: writes review.md (Pass / Flag / Fix)
/job-application:interview research|prep|mock [behavioural|technical] [--lang en|zh]   # research | self-intro + HR prep | mock interview
```

- `/job-application:generate` flags: `--density compact|standard` sets the résumé
  spacing (default from `profile.yml`); `--lang zh` produces a Chinese résumé and
  cover letter (body text translated from your English source of truth);
  `--with-projects` adds a Selected Projects section built from the JD-relevant
  `projects/*.md`; `--max-pages N` is a soft page ceiling (a warning, never a
  truncation); `--order relevance|chronological` sets experience ordering;
  `--answers "Q1; Q2"` also writes `answers.md`.
- `/job-application:review-application --fix` applies only unambiguous safe corrections
  (present-tense bullets in past roles, fields that disagree with `profile.yml`, a
  stale `cover_letter.txt`), re-renders, and re-runs the checks once.
- `/job-application:interview` subcommands: `research` dispatches the
  `company-researcher` subagent — it judges whether the company's hiring is
  domestic-China, overseas, or both, and searches accordingly (Glassdoor/Seek/
  Indeed/LinkedIn overseas; 牛客网/脉脉/看准网/知乎/BOSS直聘 domestically) — to
  `{dir}/interview/company_research.md`; `prep` writes
  `{dir}/interview/self_intro.md` and `{dir}/interview/hr_questions_prep.md`; `mock
  behavioural|technical` runs a résumé-grounded mock interview (a behavioural round,
  or a role-by-role / project-by-project technical deep-dive), gives balanced
  feedback, writes a dated session record to
  `{dir}/interview/mock/<mode>/<date>.md` (never overwritten — a same-day re-run
  gets `-2`, `-3`, …), and appends new recurring lessons to the interview playbook
  (`interview_playbook.md` at your working-directory root by default; override with
  `interview_playbook` in `jobapp.config.yml`, e.g. `private/interview_playbook.md`).
  It is seeded on first use, always in English, from the plugin's
  `interview-frameworks.md`. `mock technical` also takes `--focus "<role or
  project>"`. `--lang en|zh` sets the language for everything this subcommand writes
  (research report, prep files, mock chat and record, new playbook entries); default
  is whatever `--lang` `generate` used for this application's résumé.

Every application's files land in one directory — `applications/{Company}/` by
default. Deliverables and working notes sit flat (`jd.md`, `analysis.md`,
`review.md`, `resume.pdf`, `cover_letter.pdf`, `cover_letter.txt`); machine
artifacts (`resume.data.json`, `cover_letter.data.json`) sit under `tmp/` and are
regenerable; interview-prep files sit under `interview/` (with mock-interview
records at `interview/mock/<behavioural|technical>/<date>.md`). Full tree:
`reference/output-layout.md`. Override the directory location with `output_dir` in
`jobapp.config.yml`.

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

From `plugins/job-application/`:

```
uv run pytest
```

Render checks skip cleanly (not fail) if `uv run playwright install chromium` hasn't
been run yet.

The synthetic candidate fixture the skills' expected-output checklists
(`tests/skills/*.expected.md`) are written against lives under `tests/fixtures/`
(`tests/fixtures/raw_cvs/`, `tests/fixtures/resume_sections/`,
`tests/fixtures/sample-jd.md`).
