# job-application (jobkit) — plugin source

This directory is the `job-application` Claude Code plugin: a generic engine for
JD analysis, tailored résumé + cover-letter generation, and interview prep. It ships
**no personal data** — the candidate's source of truth and all generated output live
in the user's own working directory, never here.

The repository root one level up is the **marketplace** (`../.claude-plugin/marketplace.json`,
which points its one plugin `source` at `./plugins/job-application`). The plugin lives in
this subdirectory — not at the repo root — so a marketplace checkout is never itself
mistaken for a second copy of the plugin.

## Layout (within `plugins/job-application/`)

| Path | Purpose | Required by |
|---|---|---|
| `.claude-plugin/plugin.json` | plugin manifest | plugin format |
| `skills/` | the five skills — `ingest`, `jd-intake`, `generate`, `review-application`, `interview` (the actual logic) | plugin format |
| `commands/` | the `/slash` entrypoints — thin shims that forward args to the skills | plugin format |
| `agents/` | subagents the skills dispatch — `sot-retriever`, `company-researcher` | plugin format |
| `scripts/` | PowerShell helpers — `render_pdf.ps1`, `compress_pdf.ps1`, `cover_letter_to_txt.ps1`, `extract_cv.ps1`, `lib/config.ps1` | ours |
| `templates/` | HTML résumé / cover-letter templates + bundled fonts (OFL) | ours |
| `reference/` | prose shared across skills — `workflow-rules.md`, `ats-checklist.md`, `interview-frameworks.md` | ours |
| `tests/` | `run-pipeline.ps1` (single entry point), `scripts/*.Tests.ps1`, `skills/*.expected.md`, `fixtures/` (synthetic candidate) | ours |
| `example/` | four rendered sample PDFs (résumé + cover letter, EN + ZH) | ours |

## Working on the plugin

Follow `reference/workflow-rules.md`. Specs and plans go in `docs/` (git-ignored).
Run `pwsh tests/run-pipeline.ps1` before opening a PR — plain PowerShell assertions,
no Pester; render checks skip cleanly with no Chromium.

## Using the plugin (not from this repo)

Install it, then run Claude Code from a **separate private folder**. `Get-JobAppConfig`
resolves `resume_sections/` and the per-application output directory from that working
directory (walking up for `jobapp.config.yml`). Everything under `${CLAUDE_PLUGIN_ROOT}`
is read-only; nothing is ever written back into the plugin. See `README.md` § Setup.
