[English](README.md) | [中文](README.zh-CN.md)

# job-application

## What it is

`job-application` is a Claude Code plugin that turns a folder of your past CVs into a
tailored application for every job you apply to. It bundles three skills — `setup`,
`apply`, and `interview` — plus supporting scripts, HTML templates, and subagents.
`setup` scaffolds a working directory and (given a folder of past CVs) builds the
source of truth; `apply` analyses a job description, generates a tailored résumé and
cover letter, and self-checks the result; `interview` handles company research,
question prep, and mock interviews. The plugin is a generic engine: your candidate
data lives in your own repo and is never shipped with the plugin.

## Prerequisites

- **Windows, macOS, or Linux** — the plugin has no OS-specific dependency.
- **Python ≥ 3.10** and `pip`. Install the engine: `pip install jobkit` (until PyPI:
  `pip install "git+https://github.com/RyanDDDDDD/jobkit#subdirectory=plugins/job-application"`).
  Then one-time `jobkit install-browser` (downloads the Playwright-managed Chromium).

No Ghostscript, Poppler, or `pandoc` install is required — PDF compression and
`.pdf`/`.docx` text extraction are pure-Python (`pikepdf`, `pymupdf`,
`python-docx`), installed automatically with `jobkit`.

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

The plugin holds no candidate data. It reads its assets from the installed
`jobkit` package (read-only) and reads/writes **everything else — your source
of truth and every generated document — in the directory you run Claude Code from**,
resolved by `jobkit config` walking up for `jobapp.config.yml`.

1. Make a private working folder (e.g. `~/job-hunt/`) and run Claude Code there. Keep
   it separate from this repo; nothing you generate belongs in the plugin.
2. Run `/job-application:setup`. It scaffolds the folder — `jobapp.config.yml`,
   `CLAUDE.md`, a `private/` subtree with the `resume_sections/` templates and a
   seeded `interview_playbook.md`, and an `applications/` output directory. It never
   overwrites an existing file, so it is safe to re-run. Run
   `/job-application:setup <folder of your old CVs>` to also build
   `private/resume_sections/` from them.
3. Fill in `private/resume_sections/profile.yml` (identity, canonical company names /
   titles / dates) and `private/resume_sections/factual-bounds.md` (the "never
   claim" rules that constrain every generated document). If you skipped the CV
   folder argument, either re-run setup with a folder or hand-fill the section files.

`jobapp.config.yml` keys — `source_of_truth_dir`, `output_dir`, `interview_playbook`,
`browser_path` — override the built-in defaults (`resume_sections/`,
`applications/{Company}/`, `interview_playbook.md`); `setup` writes the first three to
the `private/` layout. See `jobapp.config.example.yml`.

### Try it against the bundled fixture

Before pointing the plugin at your own data, run it against the synthetic candidate in
`tests/fixtures/`: `/job-application:setup tests/fixtures/raw_cvs` to build the source
of truth, then `/job-application:apply` on `tests/fixtures/sample-jd.md` naming the
company `Testco` (the sample JD is written for a fictional "Meridian Integration
Partners"; you name the application `Testco`) — you get a full resume + cover letter
for a fictional "Sample Dev" and can see the whole pipeline end to end.

`example/` holds a rendered sample of that output — nothing but the four PDFs:
résumé and cover letter, English and Chinese (`resume.pdf` / `resume.zh.pdf` /
`cover_letter.pdf` / `cover_letter.zh.pdf`). The `*.data.json` they were rendered from
live in `tests/fixtures/`.

## Daily use

One pass per job:

```
/job-application:setup [<folder>]     # once: scaffold + build the source of truth
/job-application:apply [--density compact|standard] [--lang en|zh] [--answers "Q1; Q2"]
/job-application:interview research|prep|mock [behavioural|technical] [--lang en|zh]
```

- `/job-application:apply` runs analysis → generate → self-check in one pass, writing
  `jd.md`, `analysis.md`, `review.md`, and the deliverables (`resume.pdf`,
  `cover_letter.pdf` / `cover_letter.txt`, optional `answers.md`). Flags:
  `--density compact|standard` sets résumé spacing (default from `profile.yml`
  `conventions.density`); `--lang zh` produces a Chinese résumé and cover letter
  (body text translated from your English source of truth); `--answers "Q1; Q2"`
  also writes `answers.md`. Selected Projects is included automatically when the JD
  makes projects relevant.
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
  It is seeded on first use, always in English, from
  `jobkit doc interview-frameworks`. `mock technical` also takes `--focus "<role or
  project>"`. `--lang en|zh` sets the language for everything this subcommand writes
  (research report, prep files, mock chat and record, new playbook entries); default
  is whatever `--lang` `apply` used for this application's résumé.

Every application's files land in one directory — `applications/{Company}/` by
default. Deliverables and working notes sit flat (`jd.md`, `analysis.md`,
`review.md`, `resume.pdf`, `cover_letter.pdf`, `cover_letter.txt`); machine
artifacts (`resume.data.json`, `cover_letter.data.json`) sit under `tmp/` and are
regenerable; interview-prep files sit under `interview/` (with mock-interview
records at `interview/mock/<behavioural|technical>/<date>.md`). Full tree:
`jobkit doc output-layout`. Override the directory location with `output_dir` in
`jobapp.config.yml`.

## The `resume_sections/` contract

The only thing the plugin requires from you is a source-of-truth directory (default
`resume_sections/`, overridable via `jobapp.config.yml`).
It contains:

| Path | Purpose |
|------|---------|
| `profile.yml` | Structured identity — the one non-markdown file. Name, contact, links, location, working rights, and canonical roles / education (exact company names, titles, and dates used verbatim on every generated document). Also holds résumé density and whether to include a projects section (`conventions.density` / `conventions.include_projects`). |
| `factual-bounds.md` | Free-form "never claim" rules, loaded verbatim as hard constraints by `apply` (e.g. technologies you have never used, which stacks belong to which employer, no invented metrics, no university in cover letters). Grows over time as you correct generated drafts. |
| `companies/*.md` | Consolidated, de-duplicated per-company experience — the source of truth for all achievement bullets. |
| `projects/*.md` | Consolidated per-project achievements. |
| `education.md` | Education history. |
| `introduction.md` | Reusable personal summary / positioning statement. |
| `skills.md` | Consolidated skills inventory. |

`setup` scaffolds the flat files (`profile.yml`, `factual-bounds.md`,
`introduction.md`, `skills.md`, `education.md`) and leaves `companies/` and
`projects/` empty. Each new `companies/<slug>.md` / `projects/<slug>.md` starts from
the skeleton shape under the bundled `templates/section-skeletons/` — `setup` uses it during
CV ingest, and you can mirror it yourself when hand-filling.

## Running the tests

From `plugins/job-application/`:

```
python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && python -m pytest
```

Render checks skip cleanly (not fail) if `jobkit install-browser` hasn't been run yet.

The synthetic candidate fixture the skills' expected-output checklists
(`tests/skills/*.expected.md` — `setup` / `apply` / `interview`) are written against
lives under `tests/fixtures/` (`tests/fixtures/raw_cvs/`,
`tests/fixtures/resume_sections/`, `tests/fixtures/sample-jd.md`).
