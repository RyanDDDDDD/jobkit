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
| `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` | plugin manifests — one per host | plugin format |
| `../.claude-plugin/marketplace.json` / `../.cursor-plugin/marketplace.json` | marketplace entries — one per host, both `source: ./plugins/job-application` | marketplace |
| `.mcp.json` / `mcp.json` | optional Tavily MCP server — Claude Code / Cursor | ours |
| `skills/` | the three skills — `setup`, `apply`, `interview` | plugin format |
| `agents/` | subagents the skills dispatch — `sot-retriever`, `company-researcher` | plugin format |
| `src/jobkit/` | the installable `jobkit` package — `config`, `render`, `report` (the render Report block), `compress`, `cover_txt`, `extract_cv`, `init_workspace`, `scaffold` (pre-fills the `.data.json` files from `profile.yml`), `docs`, `cli`; templates + reference ship as package data | ours |
| `pyproject.toml` | `pip` / `hatchling` packaging (`playwright`, `pikepdf`, `pymupdf`, `python-docx`, `pyyaml`; no `uv`) | ours |
| `tests/` | `pytest` script tests under `tests/scripts/`, `skills/*.expected.md`, `fixtures/` (synthetic candidate) | ours |
| `example/` | rendered sample PDFs — the default theme's résumé + cover letter (EN + ZH), plus one EN résumé + cover letter per non-default theme (`resume.<theme>.pdf` / `cover_letter.<theme>.pdf`) | ours |

Reference docs live at `src/jobkit/reference/` and are printed by `jobkit doc <name>`.
Templates live at `src/jobkit/templates/` — shared `fonts/` (CN/EN pack), five
theme packs (`dossier` / `classic` / `modern-sans` / `signal` / `slate`, each with
résumé + cover letter), workspace scaffold, and section skeletons.

There is no `commands/` directory; Claude Code lists plugin skills directly in the `/`
picker as `/job-application:<skill>`.

**Two hosts, one tree.** `skills/` and `agents/` are shared: Claude Code and
Cursor each autodiscover them from the plugin root. The only per-host files
are the two manifest dirs and the two MCP filenames (`.mcp.json` for Claude
Code, `mcp.json` for Cursor). `tests/test_manifests.py` asserts the two
manifests keep the same name and version.

## Working on the plugin

Follow `jobkit doc workflow-rules`. Specs and plans go in `docs/` (git-ignored).
Run `python -m pytest` (in a venv: `python -m venv .venv && pip install -e ".[dev]"`)
before opening a PR. Render checks skip cleanly (not fail) if
`jobkit install-browser` hasn't been run yet.

Skills call `jobkit <sub>`; reference docs are `jobkit doc <name>`; skills and
agents contain no host-specific path variables (enforced by
`tests/test_portability_lint.py`).

## Using the plugin (not from this repo)

Install it, then run Claude Code from a **separate private folder**. Install the
engine with `pip install jobkit` (or `pip install -e .` from a checkout) then
`jobkit install-browser`. Run `/job-application:setup` once there to scaffold
`jobapp.config.yml`, `CLAUDE.md`, the `private/` source-of-truth templates, and
`applications/`. `jobkit config` resolves the source-of-truth directory (default
`resume_sections/`, `private/resume_sections/` after `setup`) and the per-application
output directory from that working directory (walking up for `jobapp.config.yml`).
Flow: `setup` → `apply` → `interview`. The structure inside each
`applications/{Company}/` directory (flat deliverables, `tmp/` for machine artifacts,
`interview/` for prep) is fixed — see `jobkit doc output-layout`. Everything under
the plugin install is read-only; nothing is ever written back into the plugin. See
`README.md` § Setup.
