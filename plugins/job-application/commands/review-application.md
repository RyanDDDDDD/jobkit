---
description: QA a generated application - factual bounds, JD coverage, consistency, ATS, cover letter. Writes review.md
---

Invoke the `review-application` skill
(`${CLAUDE_PLUGIN_ROOT}/skills/review-application/SKILL.md`).

Give the company name (the same one used with `/jd-intake` and `/generate`). The
skill requires `{dir}/resume.data.json`, `{dir}/cover_letter.data.json`, and
`{dir}/analysis.md` to already exist — if any is missing, run `/generate` for that company first.

Flag (`$ARGUMENTS`):

- `--fix` — after reporting, apply the unambiguous safe corrections (present-tense
  bullets in past roles, company/title/date/education fields that disagree with
  `profile.yml`, a stale `cover_letter.txt`), re-render the affected documents, then
  re-run every check once. Without `--fix` the skill only reports.

The skill resolves `{dir}` from `Get-JobAppConfig`, loads `factual-bounds.md` and
`profile.yml` verbatim, parses the numbered `## Essential` list and the
`## Criteria → Evidence` table from `analysis.md`, and runs five check groups —
Compliance, JD coverage, Consistency, ATS & quality, Cover letter. It writes
`{dir}/review.md` with `## Pass`, `## Flag` (human judgement calls), and `## Fix`
(safe corrections). `--fix` also adds an `## Applied` note.
