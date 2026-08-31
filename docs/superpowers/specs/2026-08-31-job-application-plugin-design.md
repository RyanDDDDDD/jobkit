# Job Application Plugin — Design Spec

**Date:** 2026-08-31
**Status:** Approved design, pre-implementation
**Type:** Architectural — new distributable Claude Code plugin

---

## 1. Purpose

Turn the ad-hoc résumé/cover-letter/interview workflow currently encoded as passive
rules in `.agents/AGENTS.md` (and demonstrated across ~90 folders in `all cv/`) into a
**distributable, open-source Claude Code plugin**: a generic "engine" of skills, scripts,
subagents and templates that operates on candidate data the user keeps in their own repo.

Non-goals:
- Not a web app, not a hosted service.
- The plugin never ships or requires the maintainer's personal history.
- No cross-platform guarantee in v1 — Windows + TinyTeX is the supported environment
  (documented); PRs can generalise later.

---

## 2. Key decisions (from brainstorming)

| # | Decision |
|---|----------|
| 1 | Packaged as a **distributable plugin**, not private project skills. |
| 2 | **Plugin = generic engine; user's repo = data.** Plugin reads candidate data from configurable paths, ships only example/placeholder data. |
| 3 | **5 skills**, merged from an initial 7: `ingest`, `jd-intake`, `generate`, `review-application`, `interview`. |
| 4 | **One design doc, one implementation plan**, with a checkpoint after each skill. |
| 5 | **Subagents for both** source-of-truth retrieval and web company-research. Two agent definitions bundled in the plugin. |
| 6 | Candidate contract is a **single self-contained `resume_sections/` directory** — no `.agents/` config. The plugin no longer depends on `.agents/AGENTS.md`: workflow → skills; factual bounds → `resume_sections/factual-bounds.md`; compiler path → auto-detected by script. The maintainer may keep a private `.agents/AGENTS.md` as personal notes, but it is not part of the plugin contract. |
| 7 | **The current directory becomes the public repo.** Personal data stays in place locally and is git-ignored. Add root `LICENSE` (MIT) + `README.md`. |

---

## 3. Repository layout

The current `Resume/` directory becomes the public repo root.

```
Resume/
├── .claude-plugin/
│   ├── plugin.json                 plugin manifest
│   └── marketplace.json            local install via `claude plugin`
├── LICENSE                         MIT
├── README.md                      what it is, install, the resume_sections/ contract, quickstart
├── .gitignore                     ignores every [PRIVATE] path below
│
├── skills/
│   ├── ingest/SKILL.md
│   ├── jd-intake/SKILL.md
│   ├── generate/SKILL.md
│   ├── review-application/SKILL.md
│   └── interview/SKILL.md
├── commands/                      slash-command shims → skills
│   ├── jd-intake.md  generate.md  review-application.md  interview.md  ingest.md
├── agents/
│   ├── sot-retriever.md           read-only source-of-truth retrieval
│   └── company-researcher.md      web research
├── scripts/
│   ├── compile_latex.ps1
│   ├── compress_pdf.ps1           (moved from templates/)
│   ├── cover_letter_to_txt.ps1    (moved from templates/)
│   └── extract_cv.ps1
├── templates/
│   ├── resume_1page.tex           {{PLACEHOLDER}} form (from current resume_template_1page.tex)
│   ├── resume_2page.tex
│   └── cover_letter.tex
├── reference/
│   ├── workflow-rules.md          generic half of today's AGENTS.md
│   ├── ats-checklist.md
│   └── interview-frameworks.md    generic starter (seed for interview_playbook.md)
├── example/
│   ├── resume_sections/           synthetic candidate "Sample Dev"
│   ├── raw_cvs/                    2 sample input CVs
│   └── sample-jd.md
├── tests/
│   └── run-pipeline.ps1           template/script smoke test (see §10)
│
├── .agents/AGENTS.md              [PRIVATE] maintainer's personal notes / pointer
├── resume_sections/              [PRIVATE] maintainer's real source-of-truth
│   ├── profile.yml
│   ├── factual-bounds.md
│   ├── companies/*.md  projects/*.md  education.md  introduction.md  skills.md
├── all cv/                       [PRIVATE] real applications + input CVs
├── interview_playbook.md         [PRIVATE] maintainer's evolving playbook
├── CVT/                          [PRIVATE]
└── "jobApplication - dont refer from this folder"/  [PRIVATE]
```

**Runtime rule:** the plugin always reads the *private* paths (or a configured override).
`example/` is documentation/fixtures only and is never read during normal operation.

---

## 4. The candidate contract

The only thing the plugin requires from a user is a **source-of-truth directory**
(default `resume_sections/`; override via `jobapp.config.yml`).

```
resume_sections/
├── profile.yml         structured identity — the one non-markdown file
├── factual-bounds.md   free-form "never claim" rules
├── companies/*.md      consolidated per-company experience
├── projects/*.md       consolidated per-project
├── education.md
├── introduction.md
└── skills.md
```

### 4.1 `profile.yml`

```yaml
name: "Sample Dev"
phone: "(+00) 000-000-000"
email: "sample.dev@example.com"
links:
  github: "sample-dev"
location: "Sydney, NSW, Australia"
working_rights: "full working rights in Australia"
conventions:
  roles:
    - company: "Acme Corp"
      title: "Software Engineer"
      start: "Jan. 2024"
      end: "Present"
      location: "Sydney, Australia"
    - company: "Globex Pty Ltd"
      title: "Junior Developer"
      start: "Feb. 2022"
      end: "Dec. 2023"
      location: "Sydney, Australia"
  education:
    - institution: "Example University"
      credential: "Bachelor of Computer Science"
      start: "2018"
      end: "2021"
      location: "Sydney, Australia"
  default_resume_length: 1        # 1 | 2
  default_include_projects: false
```

`output_dir` is **not** a `profile.yml` key — it is machine/repo config in
`jobapp.config.yml` (see §4.4), resolved by `Get-JobAppConfig` (plugin default
`applications/{Company}`).

Rationale for YAML (not markdown): résumé header substitution and cross-document
consistency (identical company names, titles, dates on every generated résumé) need
exact strings. `ingest` drafts this from the input CVs; the user corrects it once.

### 4.2 `factual-bounds.md`

Free-form markdown, loaded verbatim as **hard constraints** by `generate` and
`review-application`. Contains rules like: never claim Rust; Kafka is
personal-project only, never at Acme or Globex; never invent numeric metrics;
no university mention in cover letters; experienced-hire (no GPA); language-focus
rules.

`ingest` seeds it with a stub + any bounds inferable from CV inconsistencies. It **grows
over time** when the user corrects a generated draft (a wrong stack attribution appended
as a bound, or refined — e.g. a claim the bounds initially forbade that turned out to be
legitimate and was *added* to source-of-truth instead).

### 4.3 Consolidated sections

`companies/*.md`, `projects/*.md`, `education.md`, `introduction.md`, `skills.md` —
same shape as the current repo. De-duplicated bullet points that are the single source
of truth for all generated content.

### 4.4 Optional overrides

- `templates/` — if present in the user repo, overrides the plugin's bundled `.tex`.
- `interview_playbook.md` — if present, used and appended to; else plugin seeds from
  `reference/interview-frameworks.md`.
- `jobapp.config.yml` (repo root, optional) — machine settings: `pdflatex_path`,
  `source_of_truth_dir`, `output_dir`.

---

## 5. Skills

All skills operate on the shared per-application folder `all cv/{Company}/` as the
hand-off medium between pipeline stages.

### 5.1 `ingest` — build / refresh source-of-truth

- **Trigger:** "ingest my CVs", "build resume_sections", `/ingest <path>`.
- **Input:** a path containing `.docx` / `.pdf` / `.tex` / `.md` CVs.
- **Steps:**
  1. `scripts/extract_cv.ps1` on each file → plain text.
  2. Dispatch **`sot-retriever` subagent** to cluster content by company / project /
     education / skills / intro themes.
  3. De-duplicate against existing `resume_sections/` (merge, never clobber).
  4. Write/merge `companies/*.md`, `projects/*.md`, `education.md`, `introduction.md`,
     `skills.md`.
  5. Draft `profile.yml` (contact, links, canonical roles + dates from employment
     history).
  6. Seed `factual-bounds.md` stub if absent.
- **Output:** populated `resume_sections/` + a printed diff summary + an explicit
  "confirm these dates / titles / contact details" prompt.
- **Guardrail:** reorganises only what the CVs contain; never invents. Flags
  contradictions between CVs for the user to resolve.
- **Re-runnable:** incremental merge on subsequent runs.

### 5.2 `jd-intake` — analyze a job

- **Trigger:** pasting a JD, "analyze this JD for {Company}", `/jd-intake`.
- **Input:** JD text or file + company name.
- **Steps:**
  1. Create `all cv/{Company}/`, save raw JD as `jd.md`.
  2. Extract **essential criteria**, **desirable criteria**, **responsibilities**,
     **keywords**, **language/stack emphasis**.
  3. Dispatch **`sot-retriever` subagent** to map each criterion to a matching
     source-of-truth bullet, or mark it a gap.
  4. Classify fit: **strong** / **stretch** / **hard-mismatch** (e.g. a
     role requiring years of a platform the candidate has never used).
- **Output:** `all cv/{Company}/analysis.md` — criteria→evidence matrix, gap list, fit
  verdict, recommended framing. On hard-mismatch it recommends skipping before effort
  is spent.

### 5.3 `generate` — produce the documents

- **Trigger:** "generate the resume/cover letter for {Company}", `/generate`.
- **Precondition:** `all cv/{Company}/analysis.md` exists (else instruct to run
  `jd-intake`).
- **Flags:** `--length 1|2`, `--with-projects`, `--answers "Q1; Q2"`,
  `--order relevance|chronological`.
- **Steps:**
  1. Dispatch **`sot-retriever` subagent** for JD-relevant bullets (ranked, with source
     lines).
  2. Load `factual-bounds.md` as hard constraints. If the JD calls for something
     out-of-bounds → **stop and ask** (never silently comply); if the user supplies a
     new true fact, offer to add it to source-of-truth.
  3. Fill `templates/` → `resume.tex`, `cover_letter.tex` using `profile.yml` for the
     header and retrieved bullets for the body.
  4. `scripts/compile_latex.ps1` (twice) → `scripts/compress_pdf.ps1` →
     `scripts/cover_letter_to_txt.ps1` → clean `.aux/.log/.out`.
  5. Optional `answers.md` for free-text application-form questions.
- **Output:** `resume.{tex,pdf}`, `cover_letter.{tex,pdf,txt}`, optional `answers.md`.
- **Report:** every metric / skill used, each with its source-of-truth file:line.
  Deviations from `profile.yml` conventions are called out.

### 5.4 `review-application` — QA gate

- **Trigger:** "review the {Company} application", `/review-application`.
- **Input:** `all cv/{Company}/`.
- **Checks:**
  1. **Compliance** — every claim traceable to source-of-truth; no `factual-bounds.md`
     violation; no invented metrics.
  2. **JD coverage** — each essential criterion covered by ≥1 résumé bullet; list
     uncovered.
  3. **Consistency** — company / title / dates match `profile.yml`; uniform tense;
     length matches target; ATS-parseable (no tables/columns in machine-read text).
  4. **Quality** — bullets quantified where possible, verb-first, no near-duplicates.
  5. **Cover-letter rules** — no university mention; companies + domains + company-tied
     stacks named; `cover_letter.txt` present and current.
- **Output:** `all cv/{Company}/review.md` — **Pass / Flag / Fix** list.
- **Flag:** `--fix` applies the safe, unambiguous corrections to the working tree.

### 5.5 `interview` — prep + practice

- **Subcommands:**
  - `research` — dispatch **`company-researcher` subagent** (Glassdoor, Seek, Reddit,
    Whirlpool, 小红书, recent news, interview experiences) → `company_research.md`.
  - `prep` — generate `hr_questions_prep.md` and `self_intro.md` from the CV + JD +
    `interview_playbook.md`.
  - `mock` — conduct a mock interview with Q&A **strictly from the candidate's CV**;
    balanced feedback (strengths + concrete improvements, never purely positive); then
    append newly-observed recurring lessons to `interview_playbook.md`.
- **Output:** per-company prep files under `all cv/{Company}/` + playbook updates.

---

## 6. Subagents (`agents/`)

### 6.1 `sot-retriever`

- **Role:** read-only retrieval / clustering over `resume_sections/`.
- **Tools:** Read, Grep, Glob.
- **Contract in:** JD text (or "cluster this raw CV text") + source-of-truth path.
- **Contract out:** ranked relevant bullets per section, each with `file:line`; for
  `ingest`, a proposed section-file structure.
- **Used by:** `ingest`, `jd-intake`, `generate`.

### 6.2 `company-researcher`

- **Role:** web research on a target company + role.
- **Tools:** WebSearch, WebFetch, Read.
- **Contract in:** company name + role title + JD.
- **Contract out:** structured `company_research.md` — culture, products/clients,
  Glassdoor/Seek/Reddit/Whirlpool/小红书 signal (pros/cons), interview experiences and
  question topics, recent developments.
- **Used by:** `interview research`.

---

## 7. Scripts (`scripts/`, PowerShell)

| Script | Purpose |
|--------|---------|
| `compile_latex.ps1 <file.tex>` | Auto-detect `pdflatex` (TinyTeX `$APPDATA` path, then PATH). Run twice for refs. Return page count. Fail loud with log tail on error; leave `.tex` intact. |
| `compress_pdf.ps1 <file.pdf>` | Existing script, moved from `templates/`. |
| `cover_letter_to_txt.ps1 <file.tex>` | Existing script, moved from `templates/`. |
| `extract_cv.ps1 <file>` | Text extraction for `ingest`: pdftotext / pandoc / read-by-extension. |

Windows + TinyTeX assumption documented in `README.md`. `pdflatex_path` overridable via
`jobapp.config.yml`.

---

## 8. Templates (`templates/`)

Current `{{PLACEHOLDER}}` `.tex` files become the shipped defaults:
`resume_1page.tex`, `resume_2page.tex`, `cover_letter.tex`. A user's repo-level
`templates/` directory overrides. `profile.yml` fills header placeholders (`{{NAME}}`,
`{{PHONE}}`, `{{EMAIL}}`, `{{GITHUB_USERNAME}}`); skills fill body sections.

---

## 9. Error handling

| Situation | Behaviour |
|-----------|-----------|
| `resume_sections/` missing | `ingest` offers a guided walkthrough. |
| `generate` run without `analysis.md` | Stop; instruct to run `jd-intake` first. |
| LaTeX compile failure | Surface log tail, keep `.tex`, skip compression, do not claim success. |
| `factual-bounds.md` conflict | Stop, quote the specific rule, ask the user; never silently comply. If user supplies a new true fact, offer to update source-of-truth. |
| Résumé over target length | `review-application` flags it; `generate` warns and suggests trims. |
| Contradictory input CVs during `ingest` | List the conflicts, ask the user to resolve; do not pick silently. |

---

## 10. Testing

- **Fixture:** `example/` — synthetic candidate "Sample Dev", 2 sample input CVs,
  1 sample JD, an `example/factual-bounds.md` with a deliberately testable rule.
- **`tests/run-pipeline.ps1`:** a template/script **smoke test**, not a
  skill-execution pipeline. It does not run `ingest → jd-intake → generate →
  review-application` (those are LLM-driven skills). It:
  1. smoke-fills every `{{token}}` in the three shipped `templates/*.tex` and compiles
     each (asserting the 1-page résumé is exactly one page);
  2. exercises `cover_letter_to_txt.ps1` (asserts the hoisted `Subject:` line) and
     `Get-JobAppConfig`;
  3. runs each `tests/scripts/*.Tests.ps1` and folds its exit code into the total.
- The **skill-level** behavioural checks live in the `tests/skills/*.expected.md`
  prose checklists (`ingest`, `jd-intake`, `generate`, `review-application`), walked
  by an operator during manual verification — not executed by `run-pipeline.ps1`.
- CI-ready (GitHub Actions) once the repo is public — deferred, not in v1 plan.

---

## 11. Open-source polish

- Root `README.md`: what it is; `claude plugin` install; the `resume_sections/`
  contract; quickstart against `example/`; the Windows/TinyTeX prerequisite.
- `LICENSE`: MIT.
- `.gitignore`: every `[PRIVATE]` path from §3.
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`.
- Note: this directory is not yet a git repo; `git init` + first commit happen when the
  maintainer is ready to publish. The plugin is fully usable locally before then.

---

## 12. Implementation order (one plan, checkpoint per item)

1. **Scaffold** — `.claude-plugin/`, `README.md`, `LICENSE`, `.gitignore`, move
   `scripts/` + `templates/`, `reference/` extraction from `AGENTS.md`, `example/`
   fixture.
2. **`ingest`** skill + `sot-retriever` agent + `extract_cv.ps1`.
3. **`jd-intake`** skill.
4. **`generate`** skill + `compile_latex.ps1`.
5. **`review-application`** skill.
6. **`interview`** skill + `company-researcher` agent.
7. **`tests/run-pipeline.ps1`** + final `README` pass.

Migration of the maintainer's own `.agents/AGENTS.md` into `resume_sections/profile.yml`
+ `resume_sections/factual-bounds.md` happens alongside step 2, using the real data.
