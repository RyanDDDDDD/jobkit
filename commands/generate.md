---
description: Produce a tailored resume, cover letter, and optional answers for an analyzed job — compiles and compresses the PDFs
---

Invoke the `generate` skill (`${CLAUDE_PLUGIN_ROOT}/skills/generate/SKILL.md`).

Give the company name (the same one used with `/jd-intake`). The skill requires
`{dir}/analysis.md` to already exist — if it does not, run `/jd-intake` for that
company first.

Flags (`$ARGUMENTS`):

- `--length 1|2` — résumé page target. Default: `profile.yml`
  `conventions.default_resume_length`.
- `--with-projects` — include the Personal Projects section (implies `--length 2`).
  Default: `profile.yml` `conventions.default_include_projects`.
- `--order relevance|chronological` — experience ordering. Default `chronological`.
- `--answers "Q1; Q2; ..."` — also write `answers.md`, one grounded answer per
  `;`-separated question.

The skill resolves the per-application directory from `Get-JobAppConfig`, dispatches
the `sot-retriever` subagent in `retrieve` mode for JD-relevant bullets, fills the
résumé and cover-letter templates (a repo-level `templates/` overrides the bundled
one) from `profile.yml` (header, verbatim company/title/date strings) plus the
retrieved evidence, checks every line against `factual-bounds.md`, compiles and
compresses `resume.pdf` and `cover_letter.pdf`, writes `cover_letter.txt`, cleans the
`.aux`/`.log`/`.out` files, and reports every metric and named skill with its
source-of-truth `file:line`. If `analysis.md` `## Fit` is `hard-mismatch`, the skill
stops and generates nothing.
