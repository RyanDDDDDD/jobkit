---
description: Analyze a job description - save it, extract criteria, map to evidence, classify fit
---

Invoke the `jd-intake` skill (`${CLAUDE_PLUGIN_ROOT}/skills/jd-intake/SKILL.md`).

Paste the job description (or give the path to a JD file) and provide the company
name. If the company name is missing, the skill will ask.

The skill resolves the per-application output directory from `Get-JobAppConfig`,
saves the JD verbatim to `jd.md`, then writes `analysis.md` with the essential and
desirable criteria, responsibilities, ATS keywords, language/stack emphasis, a
`Criteria → Evidence` table (each criterion mapped to a `file:line` in the
source-of-truth directory via the `sot-retriever` subagent in `retrieve` mode), a
`Fit` classification (`strong` / `stretch` / `hard-mismatch`), and `Framing` notes.
If the fit is `hard-mismatch`, the skill says so and recommends skipping the role
rather than generating anything.
