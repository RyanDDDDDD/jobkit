---
name: interview
description: Interview preparation and practice for a specific application - company research, HR question prep, self-introduction, and mock interviews with balanced feedback. Subcommands research / prep / mock.
---

## When to use

The user says "prep me for the {Company} interview", "mock interview for {Company}",
"research {Company}", or "/job-application:interview research|prep|mock". Runs after
`apply` for that company.

## Subcommand is the first argument

`/job-application:interview research` · `/job-application:interview prep` ·
`/job-application:interview mock`. If no subcommand is given, ask which of the three
the user wants. All three operate on one company's per-application directory.

## Flags

- `--lang en|zh` — language for every artifact this skill writes this session:
  `interview/company_research.md`, `interview/self_intro.md`,
  `interview/hr_questions_prep.md`, the mock chat and its session record, and any
  `{playbook}` entries appended this run. Default, in order: (1) explicit `--lang`;
  (2) `{dir}/tmp/resume.data.json`'s `lang` if present; (3) workspace
  `jobapp.config.yml` `lang`. Override when the interview language differs from the
  résumé (e.g. English résumé, Chinese interview). This does **not** affect the
  initial `{playbook}` seed copy (see Inputs and paths), which always stays
  English.
- `--focus "<role or project name>"` — `mock technical` only: restrict the deep-dive
  to the single matching grill target (one role or one project). Ignored by
  `mock behavioural` and the other subcommands.

## Inputs and paths

- Commands are `jobkit <sub>` (`python -m jobkit <sub>` if not on PATH).
- Resolve `{dir}` / `{sourceDir}` with `jobkit config` (see the `apply`
  skill's *Inputs and paths* for the derivation). `{dir}` must already
  contain `jd.md`, `analysis.md`, `tmp/resume.data.json` — else tell the
  user to run `/job-application:apply` first and stop.
  This skill writes under `{dir}/interview/` (create it, `mkdir -p` semantics);
  layout: `jobkit doc output-layout`.
- **`tmp/resume.data.json`** follows the shape in the `apply` skill's *Building the
  data files* section (`name`, `contact`, `intro[]`, `sections[]` with `type` ∈
  `entries` | `education` | `skills` | `list`). All strings are plain text — the
  résumé's claims live in `intro[]`, the `sections[].items[].bullets[]`, and the
  `skills` groups' `value` strings.
- **`{playbook}` (the interview playbook):** `<root>/<interview_playbook>` where
  `<root>` is `jobkit config`'s `root` key (the directory containing `jobapp.config.yml`
  found by walking up from the current working directory, or the current directory
  if there is none) and `<interview_playbook>` is `jobkit config`'s `interview_playbook`
  key (default `interview_playbook.md`, override with `interview_playbook` in
  `jobapp.config.yml` — e.g. `private/interview_playbook.md`). It is **not** a plugin
  file. If it does not exist yet,
  seed it by writing the output of `jobkit doc interview-frameworks` to
  `{playbook}` (creating parent directories as needed), then tell the user it was
  created and that it is theirs to extend.

## Subcommand: research

1. Resolve `{dir}` and `--lang` (see Flags — default from
   `{dir}/tmp/resume.data.json`'s `lang` field). Read `{dir}/jd.md` and (if present)
   `{dir}/analysis.md` (treat `analysis.md` as prose — read `## Criteria → Evidence`,
   `## Fit`, `## Framing`, use the `gap` / `partial` rows for gap questions; tolerate
   formatting variation), `{dir}/tmp/resume.data.json`. Create `{dir}/interview/`.
2. Dispatch the `company-researcher` subagent with
   `{ company: <name>, role: <title from jd.md>, jd: <text of {dir}/jd.md>, dir: <{dir}>, lang: <resolved --lang> }`.
3. Save its report **verbatim** to `{dir}/interview/company_research.md`. Print a short summary
   (2–4 lines) and the source count.

## Subcommand: prep

Resolve `--lang` (see Flags) — both files below are written in that language. Read
`{dir}/analysis.md` (treat as prose — read `## Criteria → Evidence`, `## Fit`,
`## Framing`, use the `gap` / `partial` rows for gap questions; tolerate formatting
variation), `{dir}/tmp/resume.data.json`,
`{dir}/interview/company_research.md` (if present), and
`{playbook}` (seed it first if absent). Create
`{dir}/interview/`. Then write two files:

- **`{dir}/interview/self_intro.md`** — a spoken-length self-introduction (about 45–60
  seconds read aloud) that hits anchor points, structured for delivery not
  memorisation: current role and focus → one or two relevant threads from the
  résumé → why this company / role. Every fact traces to `tmp/resume.data.json`
  (`intro[]`, the `sections[]` entries) / `analysis.md` / `company_research.md`. Mark
  the 3–4 anchor points as a bullet list
  at the top so the user can rehearse the beats, not the words.
- **`{dir}/interview/hr_questions_prep.md`** — the likely behavioural / motivation / gap
  questions for this application, each with a bullet-point answer grounded in the
  résumé:
  - Motivation: "why this company", "why this role" — must use real company facts
    from `company_research.md`, not generic industry language.
  - Gap questions: for each `gap` / `partial` row in `analysis.md`
    `## Criteria → Evidence`, a one-clean-sentence framing plus the transferable
    bridge (never a claim the source of truth does not support).
  - Behavioural: 3–5 "tell me about a time…" prompts answerable from
    `tmp/resume.data.json` (`bullets[]`, `intro[]`, the `sections[]` entries), each
    mapped to the specific bullet(s) it draws on.
  Apply the answer-structuring principles from `{playbook}` §2.

## Subcommand: mock

A live mock interview in the chat, in one of two modes.

**Mode is the second argument:** `/job-application:interview mock behavioural` or
`/job-application:interview mock technical`. If it is omitted, ask the user which
they want — one question, the two options, no default — **before reading any file**,
so an aborted mock writes nothing.

- **behavioural** — behavioural / motivation / gap / "why this company" questions.
- **technical** — a deep-dive ("拷打"): relentless follow-ups on each role and each
  project in turn.

### Both modes

1. Resolve `{dir}`, `--lang` (see Flags), the mode, and (technical only) `--focus`.
   Read `{dir}/tmp/resume.data.json`, `{dir}/analysis.md` (treat as prose — read
   `## Criteria → Evidence`, `## Fit`, `## Framing`, use the `gap` / `partial` rows
   for gap questions; tolerate formatting variation),
   `{dir}/interview/company_research.md` (if present), and
   `{playbook}` (seed it first if absent). A `technical` mock
   also resolves `{sourceDir}` with `jobkit config` and reads, for the projects
   fallback, `{sourceDir}/projects/*.md`.
2. Ask questions **one at a time**, strictly answerable from `tmp/resume.data.json`
   (`bullets[]`, `intro[]`, the `sections[]` entries), `analysis.md`, and the JD's
   own responsibilities. Never presume an experience, a technology, an employer, or
   a metric absent from the résumé / source of truth. A `technical` follow-up may
   push for depth the résumé does not spell out — that is the point of the exercise
   — but still may not presume a specific tool, employer, or metric that is not
   recorded.
3. After each answer give **balanced** feedback: exactly one genuine strength and
   one concrete, specific improvement ("you said 'we' — the question asked for your
   personal action"). Never purely positive. Reference `{playbook}`
   framings where they apply.
4. At the end, produce a short debrief: recurring patterns across answers, strongest
   answer, weakest answer, and the 2–3 threads to go rehearse.
5. **Playbook update.** If the mock surfaced a *new, recurring* lesson (a pattern
   the user hit more than once that is not already covered), append it to
   `{playbook}` under the most relevant existing `##` section
   (or a new one). Check the file first — if an equivalent point already exists, do
   **not** duplicate it; say so instead. A one-off slip is not a playbook entry.
6. **Write the session record** — see "Session record" below. Do this last, once,
   so it can report the debrief and the playbook outcome.

### behavioural mode

6–10 questions, adapting to the answers: motivation ("why this company", "why this
role" — using real facts from `company_research.md`, never generic industry
language), the `gap` / `partial` rows in `analysis.md` `## Criteria → Evidence`
(one clean framing plus the transferable bridge, never a claim the source of truth
does not support), and "tell me about a time…" prompts answerable from
`tmp/resume.data.json`. Apply the answer-structuring principles from
`{playbook}` §2.

### technical mode

1. Build the ordered list of **grill targets**: each experience `items[]` entry in
   `tmp/resume.data.json` (most recent first), then each project. Projects come from
   the résumé's Selected Projects section if it has one; otherwise from every
   `{sourceDir}/projects/*.md`. If neither yields a project, grill the roles only.
   With `--focus "<name>"`, the list is just the one target whose role `secondary`
   / `primary` or project name matches.
2. Announce the plan up front ("we'll go through Acme, then Globex, then the
   price-tracker project").
3. For each target, ask **3–6 relentless follow-ups, one at a time**, going deeper
   where the answers are thin. Cover, as the target warrants: the design decision
   and the alternatives rejected; the hardest bug or failure and how it was
   diagnosed; scale and bottlenecks (what breaks at 10×); the candidate's personal
   contribution vs. the team's; what they would do differently now. **For every
   number and every claim on the résumé**, the follow-ups MUST cover: how it was
   measured; its boundaries; what breaks at 10×; the candidate's personal
   contribution vs the team's. This is the pressure test that replaces
   generation-time citation gating
   (`jobkit doc workflow-rules` §5).

### Session record

Write `{dir}/interview/mock/<mode>/<YYYY-MM-DD>.md` (`<mode>` is `behavioural` or
`technical`; create the directory). If that file already exists — a re-run of the
same mode on the same day — write `<YYYY-MM-DD>-2.md`, then `-3.md`, and so on.
Never append to or overwrite an existing session file. Write it once, at the end of
the run, in the resolved `--lang`, with this structure:

    # Mock interview — <Company> — <mode> — <YYYY-MM-DD>[ (run N)]

    - Role: <title from jd.md>
    - Language: <en|zh>
    - Focus: <grill target, or "full — all roles + projects">   (technical only)

    ## Questions

    ### 1. <question as asked>
    - **Target:** <role / project this drilled>          (technical only)
    - **Your answer:** <1–2 sentence condensation of what the candidate said>
    - **Feedback:** <the one strength + one concrete fix given live>
    - **Stronger answer:** <a short model paragraph the candidate can study —
      grounded in tmp/resume.data.json, no invented facts>

    ### 2. …

    ## Debrief

    - **Recurring patterns:** …
    - **Strongest answer:** Q<n> — <why>
    - **Weakest answer:** Q<n> — <why>
    - **Rehearse next:** <2–3 threads>

    ## Playbook

    - <"Appended '<lesson>' to the interview playbook § <section>", or "No new
      recurring lesson — nothing appended.">

Every fact in a **Stronger answer** traces to `tmp/resume.data.json` / the source of
truth — it may reframe and sharpen, never invent (see
`jobkit doc workflow-rules`).

## Guardrails

- Mock questions and prep answers never assume experience absent from
  `tmp/resume.data.json` / the source of truth.
- Feedback is specific and balanced — never generic praise, never purely positive
  (`jobkit doc workflow-rules` §11).
- `{playbook}` is the user's file: additive edits only, no deletions, no
  duplicate entries, and it stays at `{playbook}`
  — never copied into the plugin.
- `research` writes only `{dir}/interview/company_research.md`; `prep` writes only
  `{dir}/interview/self_intro.md` and `{dir}/interview/hr_questions_prep.md`; `mock`
  writes its session record under `{dir}/interview/mock/<mode>/` and appends to
  `{playbook}`. None of them touch `{sourceDir}`, `jd.md`, `analysis.md`,
  `tmp/resume.data.json` / `resume.pdf`, or `tmp/cover_letter.data.json` /
  `cover_letter.pdf`.
- `mock` asks behavioural-or-technical (if not given as the second argument) before
  reading any file, so an aborted mock writes nothing. The session record is written
  once at the end; an existing `<date>.md` is never overwritten — the next run of
  that mode/day gets `-2`, `-3`, ….
- This skill's own output (`interview/company_research.md`, `interview/self_intro.md`,
  `interview/hr_questions_prep.md`, the mock chat and its session record,
  `{playbook}` entries appended this run) follows the resolved `--lang`
  (see Flags), not necessarily the conversation language. The initial
  `{playbook}` seed copy is the one exception — it always stays English,
  since it is the plugin's own bundled reference content, not this skill's output.
