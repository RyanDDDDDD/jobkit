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
| `skills/` | the three skills — `setup`, `apply`, `interview` | plugin format |
| `agents/` | subagents the skills dispatch — `sot-retriever`, `company-researcher` | plugin format |
| `scripts/` | Python helpers, run via `uv run` — `render_pdf.py` (one or many jobs per launch), `compress_pdf.py`, `cover_letter_to_txt.py`, `verify_application.py`, `extract_cv.py`, `init_workspace.py`, `lib/config.py` | ours |
| `pyproject.toml`, `uv.lock` | `uv`-managed dependencies (`playwright`, `pikepdf`, `pymupdf`, `python-docx`, `pyyaml`) | ours |
| `templates/` | HTML résumé / cover-letter templates + bundled fonts (OFL) | ours |
| `templates/workspace/` | files `/job-application:setup` scaffolds into a new working directory | ours |
| `templates/section-skeletons/` | per-entry section skeletons (`companies.md`, `projects.md`) `setup` copies to start a new `companies/<slug>.md` / `projects/<slug>.md`; kept out of `templates/workspace/` so `init_workspace.py` never places them in the workspace | ours |
| `reference/` | prose shared across skills — `workflow-rules.md`, `config-resolution.md`, `render-contract.md`, `output-layout.md`, `ats-checklist.md`, `interview-frameworks.md` | ours |
| `tests/` | `pytest` script tests under `tests/scripts/`, `skills/*.expected.md`, `fixtures/` (synthetic candidate) | ours |
| `example/` | four rendered sample PDFs (résumé + cover letter, EN + ZH) | ours |

There is no `commands/` directory; Claude Code lists plugin skills directly in the `/`
picker as `/job-application:<skill>`.

## Working on the plugin

Follow `reference/workflow-rules.md`. Specs and plans go in `docs/` (git-ignored).
Run `uv run pytest` before opening a PR. Render checks skip cleanly (not fail) if
`uv run playwright install chromium` hasn't been run yet.

## Using the plugin (not from this repo)

Install it, then run Claude Code from a **separate private folder**. Run
`/job-application:setup` once there to scaffold `jobapp.config.yml`, `CLAUDE.md`, the
`private/` source-of-truth templates, and `applications/`. `config.py`
resolves the source-of-truth directory (default `resume_sections/`, `private/resume_sections/`
after `setup`) and the per-application output directory from that working
directory (walking up for `jobapp.config.yml`). Flow: `setup` → `apply` → `interview`.
The structure inside each `applications/{Company}/` directory (flat deliverables, `tmp/`
for machine artifacts, `interview/` for prep) is fixed — see `reference/output-layout.md`.
Everything under `${CLAUDE_PLUGIN_ROOT}` is read-only; nothing is ever written back into
the plugin. See `README.md` § Setup.
