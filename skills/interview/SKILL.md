---
name: interview
description: Interview preparation and practice for a specific application — company research, HR question prep, self-introduction, and mock interviews with balanced feedback. Subcommands research / prep / mock.
---

## When to use

The user says "prep me for the {Company} interview", "mock interview for {Company}",
"research {Company}", or "/interview research|prep|mock". Runs after `generate` (and
usually `review-application`) for that company.

## Subcommand is the first argument

`/interview research` · `/interview prep` · `/interview mock`. If no subcommand is
given, ask which of the three the user wants. All three operate on one company's
per-application directory.

## Inputs and paths

- **Plugin-internal paths use `${CLAUDE_PLUGIN_ROOT}`**: the config loader
  (`${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.ps1`), the research agent
  (`${CLAUDE_PLUGIN_ROOT}/agents/company-researcher.md`), and the generic frameworks
  (`${CLAUDE_PLUGIN_ROOT}/reference/interview-frameworks.md`).
- **`{dir}` (per-application directory):** dot-source
  `${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.ps1`, call `Get-JobAppConfig`, take
  `.OutputDir` (default `applications/{Company}`), substitute the literal `{Company}`
  token with the company name, then join onto `.Root`: `{dir}` is
  `<Root>/<OutputDir with {Company} substituted>`. `{dir}` must already contain
  `jd.md`, `analysis.md`, and `resume.tex` — if not, tell the user to run
  `/jd-intake` and `/generate` first and stop.
- **`interview_playbook.md` lives at the USER's repo root** — `Get-JobAppConfig`'s
  `Root` key (the directory containing `jobapp.config.yml` found by walking up from
  the current working directory, or `(Get-Location).Path` if there is none). It is
  **not** a plugin file and **never** lives under `${CLAUDE_PLUGIN_ROOT}`. If it does
  not exist yet, seed it by
  copying `${CLAUDE_PLUGIN_ROOT}/reference/interview-frameworks.md` to
  `<repo-root>/interview_playbook.md`, then tell the user it was created and that
  it is theirs to extend.

## Subcommand: research

1. Resolve `{dir}`. Read `{dir}/jd.md` and (if present) `{dir}/analysis.md`,
   `{dir}/resume.tex`.
2. Dispatch the `company-researcher` agent
   (`${CLAUDE_PLUGIN_ROOT}/agents/company-researcher.md`) with
   `{ company: <name>, role: <title from jd.md>, jd: <text of {dir}/jd.md>, dir: <{dir}> }`.
3. Save its report **verbatim** to `{dir}/company_research.md`. Print a short summary
   (2–4 lines) and the source count.

## Subcommand: prep

Read `{dir}/analysis.md`, `{dir}/resume.tex`, `{dir}/company_research.md` (if
present), and `<repo-root>/interview_playbook.md` (seed it first if absent). Then
write two files:

- **`{dir}/self_intro.md`** — a spoken-length self-introduction (about 45–60
  seconds read aloud) that hits anchor points, structured for delivery not
  memorisation: current role and focus → one or two relevant threads from the
  résumé → why this company / role. Every fact traces to `resume.tex` /
  `analysis.md` / `company_research.md`. Mark the 3–4 anchor points as a bullet list
  at the top so the user can rehearse the beats, not the words.
- **`{dir}/hr_questions_prep.md`** — the likely behavioural / motivation / gap
  questions for this application, each with a bullet-point answer grounded in the
  résumé:
  - Motivation: "why this company", "why this role" — must use real company facts
    from `company_research.md`, not generic industry language.
  - Gap questions: for each `gap` / `partial` row in `analysis.md`
    `## Criteria → Evidence`, a one-clean-sentence framing plus the transferable
    bridge (never a claim the source of truth does not support).
  - Behavioural: 3–5 "tell me about a time…" prompts answerable from `resume.tex`
    bullets, each mapped to the specific bullet(s) it draws on.
  Apply the answer-structuring principles from `interview_playbook.md` §2.

## Subcommand: mock

Conduct a live mock interview in the chat.

1. Read `{dir}/resume.tex`, `{dir}/analysis.md`, `{dir}/company_research.md` (if
   present), and `<repo-root>/interview_playbook.md`.
2. Ask questions **one at a time**, strictly answerable from `resume.tex` (and the
   JD's own responsibilities). Never assume experience, a technology, an employer, or
   a metric absent from the résumé.
3. After each answer give **balanced** feedback: exactly one genuine strength and one
   concrete, specific improvement ("you said 'we' — the question asked for your
   personal action"; "the example proved you're fast, but the question was about
   absorbing domain knowledge"). Never purely positive. Reference
   `interview_playbook.md` framings where they apply.
4. At the end, produce a short debrief: recurring patterns across answers, strongest
   answer, weakest answer.
5. **Playbook update.** If the mock surfaced a *new, recurring* lesson (a pattern the
   user hit more than once that is not already covered), append it to
   `<repo-root>/interview_playbook.md` under the most relevant existing `##` section
   (or a new one). Before appending, check the file — if an equivalent point already
   exists, do **not** duplicate it; say so instead. A one-off slip is not a playbook
   entry.

## Guardrails

- Mock questions and prep answers never assume experience absent from `resume.tex` /
  the source of truth.
- Feedback is specific and balanced — never generic praise, never purely positive
  (`${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md` §8).
- `interview_playbook.md` is the user's file: additive edits only, no deletions, no
  duplicate entries, and it stays at the repo root — never copied into the plugin.
- `research` writes only `{dir}/company_research.md`; `prep` writes only
  `{dir}/self_intro.md` and `{dir}/hr_questions_prep.md`; `mock` writes only
  (appends to) `interview_playbook.md`. None of them touch `{sourceDir}`, `jd.md`,
  `analysis.md`, `resume.tex`, or `cover_letter.tex`.
- English-only output regardless of the conversation language.
