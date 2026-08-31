# job-application

## What it is

`job-application` is a Claude Code plugin that turns a folder of your past CVs into a
tailored application for every job you apply to. It bundles five skills — `ingest`,
`jd-intake`, `generate`, `review-application`, and `interview` — plus supporting
scripts, LaTeX templates, and subagents. `ingest` consolidates your historical CVs into
a structured source-of-truth directory; `jd-intake` analyses a job description against
it; `generate` produces a tailored resume and cover letter; `review-application` runs a
QA gate over the result; and `interview` handles company research, question prep, and
mock interviews. The plugin is a generic engine: your candidate data lives in your own
repo and is never shipped with the plugin.

## Prerequisites

- Windows with PowerShell 7 (`pwsh`).
- [TinyTeX](https://yihui.org/tinytex/) with `pdflatex` on the path (or configured via
  `jobapp.config.yml`).
- [Ghostscript](https://www.ghostscript.com/) — required by `scripts/compress_pdf.ps1`.
- Optional: `pdftotext` (Poppler) and/or `pandoc` for ingesting `.pdf` and `.docx`
  source CVs. Plain `.tex` / `.md` CVs need neither.

## Install

Add this repository as a plugin marketplace and install:

```
claude plugin marketplace add <this repo>
claude plugin install job-application
```

Or add a local checkout as a marketplace:

```
claude plugin marketplace add ./path/to/job-application
claude plugin install job-application
```

## Setup

1. Run `/ingest ./raw_cvs` (pointing at a folder of your past CVs) to build
   `resume_sections/`.
2. Review `resume_sections/profile.yml` — confirm your contact details, canonical
   company names, job titles, and employment dates.
3. Review `resume_sections/factual-bounds.md` — the "never claim" rules that constrain
   every generated document.

## Daily use

```
/jd-intake                 # paste the job description, name the company
/generate                  # produce resume.tex/pdf + cover_letter.tex/pdf/txt
/review-application         # QA gate: Pass / Flag / Fix
/interview research         # web research on the company
/interview prep             # HR question prep + self-intro
/interview mock             # mock interview from your CV, with balanced feedback
```

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

## Quickstart against `example/`

A synthetic candidate fixture lives under `example/`. Run the end-to-end pipeline against
it with:

```
pwsh tests/run-pipeline.ps1
```
