---
description: Interview prep for an application — research | prep | mock
---

Invoke the `interview` skill (`${CLAUDE_PLUGIN_ROOT}/skills/interview/SKILL.md`).

First argument (`$ARGUMENTS`) is the subcommand; also give the company name (the same
one used with `/jd-intake` and `/generate`). The skill resolves the per-application
directory from `Get-JobAppConfig` and needs `{dir}/jd.md`, `{dir}/analysis.md`, and
`{dir}/resume.tex` to exist.

Subcommands:

- `/interview research` — dispatches the `company-researcher` subagent (web research
  on the company, role, culture, reviews, and interview process) and saves the report
  to `{dir}/company_research.md`.
- `/interview prep` — writes `{dir}/self_intro.md` (a spoken-length,
  anchor-point self-introduction) and `{dir}/hr_questions_prep.md` (likely
  behavioural / motivation / gap questions with résumé-grounded bullet answers),
  using `analysis.md`, `resume.tex`, `company_research.md`, and your
  `interview_playbook.md`.
- `/interview mock` — conducts a mock interview with questions answerable only from
  `resume.tex`, gives balanced feedback after each answer (one strength, one concrete
  improvement — never purely positive), and appends any genuinely new recurring
  lesson to your `interview_playbook.md`.

`interview_playbook.md` lives at your repo root. On first use the skill seeds it from
the plugin's generic `reference/interview-frameworks.md`; after that it is yours to
extend and the skill only ever appends to it.
