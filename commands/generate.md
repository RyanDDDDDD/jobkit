---
description: Produce a tailored resume, cover letter, and optional answers for an analyzed job — renders and compresses the PDFs
---

Invoke the `generate` skill (`${CLAUDE_PLUGIN_ROOT}/skills/generate/SKILL.md`).

Give the company name (the same one used with `/jd-intake`). The skill requires
`{dir}/analysis.md` to already exist — if it does not, run `/jd-intake` for that
company first.

Flags (`$ARGUMENTS`):

- `--density compact|standard` — résumé spacing. Default: `profile.yml` `conventions.default_density`, else `compact` when `default_resume_length == 1`, else `standard`.
- `--max-pages N` — soft page ceiling (default `2`); overage warns and lists trims, never truncates.
- `--lang en|zh` — output language (default `en`); `zh` renders Chinese titles and body text translated from the English source of truth.
- `--with-projects` — add the Selected Projects section. Default: `profile.yml` `conventions.default_include_projects`.
- `--order relevance|chronological` — experience ordering. Default `chronological`.
- `--answers "Q1; Q2; ..."` — also write `answers.md`, one grounded answer per `;`-separated question.
- `--keep-html` — keep the intermediate `{dir}/*.rendered.html` files.

The skill resolves the per-application directory from `Get-JobAppConfig`, dispatches
the `sot-retriever` subagent in `retrieve` mode for JD-relevant bullets, builds
`resume.data.json` and `cover_letter.data.json` (a repo-level `templates/` overrides
the bundled `resume.html` / `cover_letter.html`) from `profile.yml` (verbatim
company/title/date strings) plus the retrieved evidence, checks every line against
`factual-bounds.md`, renders the JSON to `resume.pdf` and `cover_letter.pdf` via
`render_pdf.ps1`, compresses them, writes `cover_letter.txt`, and reports every metric
and named skill with its source-of-truth `file:line`. If `analysis.md` `## Fit` is
`hard-mismatch`, the skill stops and generates nothing.
