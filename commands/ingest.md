---
description: Build/refresh resume_sections/ from a folder of past CVs
---

Invoke the `ingest` skill (`${CLAUDE_PLUGIN_ROOT}/skills/ingest/SKILL.md`).

Argument (`$ARGUMENTS`): path to a folder containing the user's past CVs
(`.docx` / `.pdf` / `.tex` / `.md`). If omitted, ask the user for the folder path.

The skill extracts each CV, clusters the material with the `sot-retriever` subagent,
then creates or additively merges `companies/*.md`, `projects/*.md`, `education.md`,
`introduction.md`, `skills.md`, drafts `profile.yml`, and seeds `factual-bounds.md`
in the source-of-truth directory. It finishes by printing a summary of dates,
titles, and contact details for you to confirm, plus any contradictions between CVs.
