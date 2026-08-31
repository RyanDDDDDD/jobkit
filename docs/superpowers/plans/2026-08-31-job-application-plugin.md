# Job Application Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a distributable, open-source Claude Code plugin that turns the current
résumé / cover-letter / interview workflow into five invokable skills operating on
candidate data the user keeps in their own repo.

**Architecture:** A generic "engine" (skills + scripts + subagents + LaTeX templates)
lives at the repo root and is git-tracked; the maintainer's personal job-hunt data
(`resume_sections/`, `all cv/`, `interview_playbook.md`, `.agents/`) stays in place
locally and is git-ignored. Skills read a single self-contained source-of-truth
directory (`resume_sections/` by default) and hand work between pipeline stages through
per-application folders (`all cv/{Company}/`).

**Tech Stack:** Claude Code plugin format (`.claude-plugin/plugin.json`, `skills/`,
`commands/`, `agents/`), PowerShell 7 scripts, LaTeX (TinyTeX / `pdflatex`), YAML config,
Markdown skill definitions.

**Spec:** `docs/superpowers/specs/2026-08-31-job-application-plugin-design.md`

## Global Constraints

- Plugin name: `job-application`. Version starts at `0.1.0`.
- Supported environment: Windows + PowerShell 7 + TinyTeX. Documented as a prerequisite;
  no cross-platform requirement in v1.
- The plugin MUST NOT read `example/` during normal skill operation — it is fixtures /
  docs only. Skills always read the configured source-of-truth path (default
  `resume_sections/`).
- The plugin MUST NOT contain the maintainer's personal data. Personal facts live only
  in git-ignored paths.
- Skills never invent facts. Every generated claim traces to a source-of-truth line.
  `factual-bounds.md` is loaded verbatim as a hard constraint; a conflict stops
  generation and asks the user.
- All generated résumé / cover-letter / answer content is in English regardless of
  conversation language.
- Plugin default `output_dir` is `applications/{Company}`; the maintainer's
  `jobapp.config.yml` overrides it to `all cv/{Company}`.
- Markdown skill files: YAML frontmatter with `name` and `description` keys; body is the
  instruction set. Keep each SKILL.md focused; put long reference material in the
  skill's own `reference/` subdir or the top-level `reference/`.

---

## File Structure

**Created by this plan (git-tracked, public):**

| Path | Responsibility |
|------|----------------|
| `.claude-plugin/plugin.json` | Plugin manifest |
| `.claude-plugin/marketplace.json` | Local/marketplace install descriptor |
| `README.md` | What it is, install, the `resume_sections/` contract, quickstart |
| `LICENSE` | MIT |
| `.gitignore` | Ignores every private path |
| `jobapp.config.example.yml` | Documented machine-settings override sample |
| `scripts/compile_latex.ps1` | Detect pdflatex, compile twice, report page count |
| `scripts/compress_pdf.ps1` | (moved) Ghostscript PDF compression |
| `scripts/cover_letter_to_txt.ps1` | (moved) LaTeX cover letter → email plain text |
| `scripts/extract_cv.ps1` | Extract text from `.docx/.pdf/.tex/.md` for ingest |
| `scripts/lib/config.ps1` | Shared: locate source-of-truth dir + read `jobapp.config.yml` |
| `templates/resume_1page.tex` | (moved/renamed) 1-page résumé, `{{PLACEHOLDER}}` form |
| `templates/resume_2page.tex` | (moved/renamed) 2-page résumé |
| `templates/cover_letter.tex` | (moved/renamed) cover letter |
| `agents/sot-retriever.md` | Read-only source-of-truth retrieval / clustering subagent |
| `agents/company-researcher.md` | Web company-research subagent |
| `skills/ingest/SKILL.md` | Build/refresh `resume_sections/` from raw CVs |
| `skills/jd-intake/SKILL.md` | Analyze a JD → `analysis.md` |
| `skills/generate/SKILL.md` | Produce résumé + cover letter + answers |
| `skills/review-application/SKILL.md` | QA gate → `review.md` |
| `skills/interview/SKILL.md` | Research + prep + mock interview |
| `commands/ingest.md` … `commands/interview.md` | Slash-command shims → skills |
| `reference/workflow-rules.md` | Generic workflow rules (extracted from `AGENTS.md`) |
| `reference/ats-checklist.md` | ATS / résumé quality checklist |
| `reference/interview-frameworks.md` | Generic interview frameworks (playbook seed) |
| `example/resume_sections/**` | Synthetic candidate "Sample Dev" |
| `example/raw_cvs/**` | 2 sample input CVs |
| `example/sample-jd.md` | Sample job description |
| `tests/run-pipeline.ps1` | Integration test over `example/` |

**Modified:**

| Path | Change |
|------|--------|
| `templates/compress_pdf.ps1` → `scripts/compress_pdf.ps1` | Move only |
| `templates/cover_letter_to_txt.ps1` → `scripts/cover_letter_to_txt.ps1` | Move; fix internal default-path assumptions |
| `templates/resume_template_1page.tex` → `templates/resume_1page.tex` | Rename |
| `templates/resume_template_2page.tex` → `templates/resume_2page.tex` | Rename |
| `templates/cover_letter_template.tex` → `templates/cover_letter.tex` | Rename |

**Left untouched (git-ignored private data):** `resume_sections/`, `all cv/`,
`interview_playbook.md`, `.agents/`, `CVT/`, `jobApplication - dont refer from this folder/`,
`docs/` (specs/plans are tracked — see `.gitignore` task).

---

## Task 1: Scaffold the plugin + repo hygiene

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `README.md`
- Create: `jobapp.config.example.yml`
- Move: `templates/compress_pdf.ps1` → `scripts/compress_pdf.ps1`
- Move: `templates/cover_letter_to_txt.ps1` → `scripts/cover_letter_to_txt.ps1`
- Move+rename: `templates/resume_template_1page.tex` → `templates/resume_1page.tex`
- Move+rename: `templates/resume_template_2page.tex` → `templates/resume_2page.tex`
- Move+rename: `templates/cover_letter_template.tex` → `templates/cover_letter.tex`

**Interfaces:**
- Produces: the plugin directory structure; `scripts/` and `templates/` at their final
  paths; `.gitignore` semantics that later tasks rely on (private paths never committed).

- [ ] **Step 1: Create `.claude-plugin/plugin.json`**

```json
{
  "name": "job-application",
  "version": "0.1.0",
  "description": "JD analysis, tailored resume + cover letter generation, and interview prep — operating on candidate data you keep in your own repo.",
  "author": { "name": "RyanDDDDDD" },
  "license": "MIT",
  "keywords": ["resume", "cv", "cover-letter", "job-application", "interview", "ats"]
}
```

- [ ] **Step 2: Create `.claude-plugin/marketplace.json`**

```json
{
  "name": "job-application-marketplace",
  "owner": { "name": "RyanDDDDDD" },
  "plugins": [
    { "name": "job-application", "source": "./", "description": "Job application engine: JD analysis, resume/cover-letter generation, interview prep." }
  ]
}
```

- [ ] **Step 3: Create `.gitignore`**

```gitignore
# --- Private candidate data (never committed) ---
/resume_sections/
/all cv/
/CVT/
/jobApplication - dont refer from this folder/
/interview_playbook.md
/.agents/
/jobapp.config.yml

# --- Build artefacts ---
*.aux
*.log
*.out
*.synctex.gz

# --- Keep tracked ---
!/docs/
!/example/
```

- [ ] **Step 4: Create `LICENSE`** — standard MIT License text, copyright holder
  `RyanDDDDDD`, year `2026`.

- [ ] **Step 5: Create `jobapp.config.example.yml`**

```yaml
# Copy to jobapp.config.yml (git-ignored) to override machine/repo defaults.
# All keys optional.
pdflatex_path: "%APPDATA%/TinyTeX/bin/windows/pdflatex.exe"
source_of_truth_dir: "resume_sections"
output_dir: "applications/{Company}"
```

- [ ] **Step 6: Create `README.md`** with these sections (real prose, not placeholders):
  - **What it is** — one paragraph: a Claude Code plugin of 5 skills (`ingest`,
    `jd-intake`, `generate`, `review-application`, `interview`) that turn a folder of
    your past CVs into a tailored application per job.
  - **Prerequisites** — Windows, PowerShell 7, TinyTeX with `pdflatex`, Ghostscript
    (for `compress_pdf.ps1`), optional `pdftotext`/`pandoc` for `.pdf`/`.docx` ingest.
  - **Install** — `claude plugin marketplace add <this repo>` then
    `claude plugin install job-application`, or add the local path as a marketplace.
  - **Setup** — run `/ingest ./raw_cvs` to build `resume_sections/`, then review
    `resume_sections/profile.yml` and `resume_sections/factual-bounds.md`.
  - **Daily use** — `/jd-intake` (paste JD) → `/generate` → `/review-application` →
    `/interview research|prep|mock`.
  - **The `resume_sections/` contract** — table of the files and their purpose (copy
    from spec §4).
  - **Quickstart against `example/`** — `pwsh tests/run-pipeline.ps1`.

- [ ] **Step 7: Move scripts and templates**

```bash
mkdir -p scripts templates
git_mv() { mkdir -p "$(dirname "$2")"; mv "$1" "$2"; }
mv "templates/compress_pdf.ps1" "scripts/compress_pdf.ps1"
mv "templates/cover_letter_to_txt.ps1" "scripts/cover_letter_to_txt.ps1"
mv "templates/resume_template_1page.tex" "templates/resume_1page.tex"
mv "templates/resume_template_2page.tex" "templates/resume_2page.tex"
mv "templates/cover_letter_template.tex" "templates/cover_letter.tex"
```

- [ ] **Step 8: Verify plugin loads**

Run: `claude plugin validate .` (or `claude plugin marketplace add ./ && claude plugin list`)
Expected: `job-application` plugin recognised, no manifest errors. If `claude plugin
validate` is unavailable, assert the JSON files parse: `pwsh -c "Get-Content .claude-plugin/plugin.json | ConvertFrom-Json"`.

- [ ] **Step 9: Commit**

```bash
git init
git add .claude-plugin LICENSE README.md .gitignore jobapp.config.example.yml scripts templates docs
git commit -m "chore: scaffold job-application plugin, move scripts and templates"
```

---

## Task 2: `scripts/lib/config.ps1` + `scripts/compile_latex.ps1`

**Files:**
- Create: `scripts/lib/config.ps1`
- Create: `scripts/compile_latex.ps1`
- Create: `tests/scripts/compile_latex.Tests.ps1`
- Test: `tests/scripts/compile_latex.Tests.ps1`

**Interfaces:**
- Produces:
  - `Get-JobAppConfig` — returns a hashtable `@{ PdflatexPath; SourceOfTruthDir;
    OutputDir }` merging `jobapp.config.yml` (if present, walking up from CWD) over
    built-in defaults.
  - `scripts/compile_latex.ps1 -TexPath <path> [-Runs 2]` — compiles, returns an object
    `@{ Pdf = <path>; Pages = <int>; Ok = <bool>; LogTail = <string> }`; exit code 0 on
    success, 1 on LaTeX error.
- Consumes: nothing from earlier tasks.

- [ ] **Step 1: Write the failing test**

```powershell
# tests/scripts/compile_latex.Tests.ps1
BeforeAll { . "$PSScriptRoot/../../scripts/compile_latex.ps1" -AsModule }

Describe "compile_latex" {
  It "compiles a minimal document and reports 1 page" {
    $dir = Join-Path $TestDrive "doc"; New-Item -ItemType Directory $dir | Out-Null
    $tex = Join-Path $dir "min.tex"
    Set-Content $tex "\documentclass{article}\begin{document}hello\end{document}"
    $r = Invoke-LatexCompile -TexPath $tex
    $r.Ok | Should -BeTrue
    $r.Pages | Should -Be 1
    Test-Path $r.Pdf | Should -BeTrue
  }
  It "fails loud on a broken document and keeps the .tex" {
    $dir = Join-Path $TestDrive "bad"; New-Item -ItemType Directory $dir | Out-Null
    $tex = Join-Path $dir "bad.tex"
    Set-Content $tex "\documentclass{article}\begin{document}\undefinedmacro"
    $r = Invoke-LatexCompile -TexPath $tex
    $r.Ok | Should -BeFalse
    $r.LogTail | Should -Match "Undefined control sequence|Emergency stop"
    Test-Path $tex | Should -BeTrue
  }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pwsh -c "Invoke-Pester tests/scripts/compile_latex.Tests.ps1"`
Expected: FAIL — `Invoke-LatexCompile` not defined / file not found.

- [ ] **Step 3: Implement `scripts/lib/config.ps1`**

```powershell
function Get-JobAppConfig {
    $defaults = @{
        PdflatexPath     = $null
        SourceOfTruthDir = "resume_sections"
        OutputDir        = "applications/{Company}"
    }
    $dir = (Get-Location).Path
    while ($dir) {
        $cfg = Join-Path $dir "jobapp.config.yml"
        if (Test-Path $cfg) {
            foreach ($line in Get-Content $cfg) {
                if ($line -match '^\s*#' -or $line -notmatch ':') { continue }
                $k, $v = $line -split ':', 2
                $v = $v.Trim().Trim('"').Trim("'")
                switch ($k.Trim()) {
                    'pdflatex_path'       { $defaults.PdflatexPath = [Environment]::ExpandEnvironmentVariables($v) }
                    'source_of_truth_dir' { $defaults.SourceOfTruthDir = $v }
                    'output_dir'          { $defaults.OutputDir = $v }
                }
            }
            break
        }
        $parent = Split-Path $dir -Parent
        if ($parent -eq $dir) { break }
        $dir = $parent
    }
    return $defaults
}

function Resolve-Pdflatex {
    param([string]$Hint)
    $candidates = @()
    if ($Hint) { $candidates += $Hint }
    $candidates += (Join-Path $env:APPDATA "TinyTeX/bin/windows/pdflatex.exe")
    $cmd = Get-Command pdflatex -ErrorAction SilentlyContinue
    if ($cmd) { $candidates += $cmd.Source }
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    throw "pdflatex not found. Set pdflatex_path in jobapp.config.yml."
}
```

- [ ] **Step 4: Implement `scripts/compile_latex.ps1`**

```powershell
param(
    [Parameter(Mandatory)][string]$TexPath,
    [int]$Runs = 2,
    [switch]$AsModule
)
. "$PSScriptRoot/lib/config.ps1"

function Invoke-LatexCompile {
    param([Parameter(Mandatory)][string]$TexPath, [int]$Runs = 2)
    $TexPath = (Resolve-Path $TexPath).Path
    $dir = Split-Path $TexPath -Parent
    $cfg = Get-JobAppConfig
    $engine = Resolve-Pdflatex -Hint $cfg.PdflatexPath
    $ok = $true; $logTail = ""
    for ($i = 1; $i -le $Runs; $i++) {
        $out = & $engine -interaction=nonstopmode -halt-on-error -output-directory $dir $TexPath 2>&1
        if ($LASTEXITCODE -ne 0) { $ok = $false; $logTail = ($out | Select-Object -Last 25) -join "`n"; break }
    }
    $pdf = [IO.Path]::ChangeExtension($TexPath, ".pdf")
    $pages = 0
    if ($ok -and (Test-Path $pdf)) {
        $log = [IO.Path]::ChangeExtension($TexPath, ".log")
        if (Test-Path $log) {
            $m = Select-String -Path $log -Pattern 'Output written on .*\((\d+) page' | Select-Object -Last 1
            if ($m) { $pages = [int]$m.Matches[0].Groups[1].Value }
        }
    }
    foreach ($ext in '.aux', '.out') {
        $f = [IO.Path]::ChangeExtension($TexPath, $ext); if (Test-Path $f) { Remove-Item $f }
    }
    return [pscustomobject]@{ Pdf = $pdf; Pages = $pages; Ok = $ok; LogTail = $logTail }
}

if (-not $AsModule) {
    $r = Invoke-LatexCompile -TexPath $TexPath -Runs $Runs
    if ($r.Ok) { Write-Host "OK: $($r.Pdf) ($($r.Pages) page$(if($r.Pages -ne 1){'s'}))" }
    else { Write-Error "LaTeX failed:`n$($r.LogTail)"; exit 1 }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pwsh -c "Invoke-Pester tests/scripts/compile_latex.Tests.ps1"`
Expected: PASS (2 tests). If TinyTeX is absent in the environment, the test is
`-Skip`ped with a message — add `-Skip:(-not (Get-Command pdflatex -ErrorAction SilentlyContinue) -and -not (Test-Path (Join-Path $env:APPDATA 'TinyTeX/bin/windows/pdflatex.exe')))` to the `Describe`.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/config.ps1 scripts/compile_latex.ps1 tests/scripts/compile_latex.Tests.ps1
git commit -m "feat: add config loader and compile_latex script"
```

---

## Task 3: `scripts/extract_cv.ps1`

**Files:**
- Create: `scripts/extract_cv.ps1`
- Create: `tests/scripts/extract_cv.Tests.ps1`
- Test: `tests/scripts/extract_cv.Tests.ps1`

**Interfaces:**
- Produces: `scripts/extract_cv.ps1 -Path <file>` → writes plain text to stdout;
  dispatches by extension: `.md`/`.tex` = read raw; `.pdf` = `pdftotext -layout` (fallback
  error if missing); `.docx` = `pandoc -t plain` (fallback error if missing).
- Consumes: nothing.

- [ ] **Step 1: Write the failing test**

```powershell
# tests/scripts/extract_cv.Tests.ps1
Describe "extract_cv" {
  It "reads a .md file verbatim" {
    $f = Join-Path $TestDrive "a.md"; Set-Content $f "# Ryan`nC++ engineer"
    $text = & "$PSScriptRoot/../../scripts/extract_cv.ps1" -Path $f
    ($text -join "`n") | Should -Match "C\+\+ engineer"
  }
  It "reads a .tex file verbatim" {
    $f = Join-Path $TestDrive "a.tex"; Set-Content $f "\section{Experience} RBS"
    (& "$PSScriptRoot/../../scripts/extract_cv.ps1" -Path $f) -join "`n" | Should -Match "RBS"
  }
  It "errors clearly for an unsupported extension" {
    $f = Join-Path $TestDrive "a.rtf"; Set-Content $f "x"
    { & "$PSScriptRoot/../../scripts/extract_cv.ps1" -Path $f } | Should -Throw "*Unsupported*"
  }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pwsh -c "Invoke-Pester tests/scripts/extract_cv.Tests.ps1"`
Expected: FAIL — script not found.

- [ ] **Step 3: Implement `scripts/extract_cv.ps1`**

```powershell
param([Parameter(Mandatory)][string]$Path)
$ErrorActionPreference = 'Stop'
$Path = (Resolve-Path $Path).Path
$ext = [IO.Path]::GetExtension($Path).ToLower()
switch ($ext) {
    { $_ -in '.md', '.tex', '.txt' } { Get-Content -Raw -LiteralPath $Path }
    '.pdf' {
        if (-not (Get-Command pdftotext -ErrorAction SilentlyContinue)) { throw "pdftotext not found; install poppler to ingest PDFs." }
        & pdftotext -layout $Path -
    }
    '.docx' {
        if (-not (Get-Command pandoc -ErrorAction SilentlyContinue)) { throw "pandoc not found; install pandoc to ingest .docx." }
        & pandoc -t plain $Path
    }
    default { throw "Unsupported file type: $ext" }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pwsh -c "Invoke-Pester tests/scripts/extract_cv.Tests.ps1"`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/extract_cv.ps1 tests/scripts/extract_cv.Tests.ps1
git commit -m "feat: add extract_cv script for ingest"
```

---

## Task 4: `reference/` docs + `example/` fixture

**Files:**
- Create: `reference/workflow-rules.md`
- Create: `reference/ats-checklist.md`
- Create: `reference/interview-frameworks.md`
- Create: `example/resume_sections/profile.yml`
- Create: `example/resume_sections/factual-bounds.md`
- Create: `example/resume_sections/companies/acme.md`
- Create: `example/resume_sections/companies/globex.md`
- Create: `example/resume_sections/skills.md`
- Create: `example/resume_sections/introduction.md`
- Create: `example/resume_sections/education.md`
- Create: `example/raw_cvs/sample-cv-a.md`
- Create: `example/raw_cvs/sample-cv-b.md`
- Create: `example/sample-jd.md`

**Interfaces:**
- Produces: a complete synthetic candidate the integration test (Task 8) and skill
  authors reference. `reference/*.md` is stable prose the skills link to.

- [ ] **Step 1: Write `reference/workflow-rules.md`** — extract the generic, non-personal
  rules from the current `.agents/AGENTS.md`: source-of-truth is authoritative;
  redundancy control; English-only output; no hallucinated skills/metrics; save the JD;
  experienced-hire (omit GPA) as a *configurable default*, not hard-coded; the cover
  letter core-content structure (duration, companies, domains, company-tied stacks).
  Personal bounds (WPF, React-at-Fletcher, cloud scopes) are explicitly NOT here — they
  belong in each user's `factual-bounds.md`.

- [ ] **Step 2: Write `reference/ats-checklist.md`** — single-column layout, standard
  section headings, no text in tables/text-boxes, real dates, quantified verb-first
  bullets, keyword alignment to the JD, consistent tense, file naming.

- [ ] **Step 3: Write `reference/interview-frameworks.md`** — the general frameworks from
  the current `interview_playbook.md` §1, §4, §5 (self-rating template, answer-structuring
  principles, pre-call checklist), rewritten candidate-agnostic. This is the seed copied
  into a user's `interview_playbook.md` on first `interview` run.

- [ ] **Step 4: Write `example/resume_sections/profile.yml`**

```yaml
name: "Sample Dev"
phone: "(+00) 000-000-000"
email: "sample.dev@example.com"
links: { github: "sample-dev" }
location: "Sydney, NSW, Australia"
working_rights: "full working rights in Australia"
conventions:
  roles:
    - { company: "Acme Corp", title: "Software Engineer", start: "Jan. 2024", end: "Present", location: "Sydney, Australia" }
    - { company: "Globex Pty Ltd", title: "Junior Developer", start: "Feb. 2022", end: "Dec. 2023", location: "Sydney, Australia" }
  education:
    - { institution: "Example University", credential: "Bachelor of Computer Science", start: "2018", end: "2021", location: "Sydney, Australia" }
  default_resume_length: 1
  default_include_projects: false
  output_dir: "applications/{Company}"
```

- [ ] **Step 5: Write `example/resume_sections/factual-bounds.md`**

```markdown
# Factual Bounds — Sample Dev

- Never claim Rust. Sample Dev has never used Rust.
- Kafka experience is personal-project only, never at Acme or Globex.
- Do not mention the university in cover letters.
- Do not invent numeric metrics not recorded in this directory.
```

- [ ] **Step 6: Write the two company files and remaining sections** — `acme.md` and
  `globex.md` each with a tech-stack line and 4–5 de-duplicated bullets (Python, C#,
  REST APIs, SQL, CI/CD, incident response; Kafka appears ONLY as a note that it was a
  personal project). `skills.md`, `introduction.md`, `education.md` consistent with
  `profile.yml`.

- [ ] **Step 7: Write `example/raw_cvs/sample-cv-a.md` and `sample-cv-b.md`** — two
  overlapping prior résumés for Sample Dev (one backend-leaning, one full-stack-leaning)
  with slightly different wording of the same jobs, so `ingest` de-duplication has
  something real to collapse.

- [ ] **Step 8: Write `example/sample-jd.md`** — a plausible "Integration Developer"
  JD with 5 essential criteria, 3 of which Sample Dev clearly meets, 1 partial, 1 a
  genuine gap (so `jd-intake` fit-classification and `review-application` coverage have
  signal). Must NOT require Rust (so the bounds rule is testable as *not* violated).

- [ ] **Step 9: Commit**

```bash
git add reference example
git commit -m "docs: add reference guides and synthetic example fixture"
```

---

## Task 5: `sot-retriever` agent + `ingest` skill

**Files:**
- Create: `agents/sot-retriever.md`
- Create: `skills/ingest/SKILL.md`
- Create: `commands/ingest.md`
- Create: `tests/skills/ingest.expected.md` (assertion notes for the integration test)

**Interfaces:**
- Consumes: `scripts/extract_cv.ps1` (Task 3); `example/` fixture (Task 4).
- Produces:
  - Agent `sot-retriever` — input: `{ mode: "cluster" | "retrieve", text|jd, sourceDir }`;
    output: for `cluster`, a proposed mapping of raw text spans → section files with
    de-dupe notes; for `retrieve`, ranked bullets per section each with `file:line`.
  - Skill `ingest` — CLI shape `/ingest <path-to-cvs>`; writes/merges
    `<sourceDir>/{companies,projects}/*.md`, `education.md`, `introduction.md`,
    `skills.md`, drafts `profile.yml`, seeds `factual-bounds.md`.

- [ ] **Step 1: Write `agents/sot-retriever.md`**

```markdown
---
name: sot-retriever
description: Read-only retrieval and clustering over a candidate source-of-truth directory. Use for resume_sections ingestion clustering and for JD-driven bullet retrieval.
tools: Read, Grep, Glob
---

You retrieve and organise résumé source material. You NEVER write files and NEVER
invent facts.

## Mode: cluster
Input: raw text extracted from one or more past CVs + the target source-of-truth dir.
Output (markdown): for each distinct employer / project / education entry found,
propose the destination file and the bullet points, marking which are duplicates of
material already present in the source-of-truth dir (cite `file:line`) and which are
new. Flag any contradictions between CVs (different dates/titles for the same role).

## Mode: retrieve
Input: a job description + the source-of-truth dir.
Output (markdown): the most relevant bullets per section, ranked, each annotated with
its `file:line`. Note coverage gaps where the JD asks for something absent.
```

- [ ] **Step 2: Write `skills/ingest/SKILL.md`**

```markdown
---
name: ingest
description: Build or refresh the resume_sections/ source-of-truth from a folder of the user's past CVs (.docx/.pdf/.tex/.md). Use when setting up the plugin or after adding a new CV/role.
---

## When to use
User says "ingest my CVs", "build resume_sections", "/ingest <path>", or a
source-of-truth directory does not exist yet.

## Steps
1. Resolve the source-of-truth dir via `scripts/lib/config.ps1` `Get-JobAppConfig`
   (default `resume_sections/`). Resolve the input path from the user (a folder).
2. For each file in the input folder, run
   `pwsh scripts/extract_cv.ps1 -Path <file>` and collect the text.
3. Dispatch the `sot-retriever` subagent in `cluster` mode with the combined text and
   the source-of-truth dir path.
4. From its output, create or MERGE (never overwrite) these files:
   `companies/<slug>.md`, `projects/<slug>.md`, `education.md`, `introduction.md`,
   `skills.md`. Keep the existing de-duplicated bullet style.
5. Draft `profile.yml` — contact details and links from the CV headers; `conventions.roles`
   from the employment history (company, title, start, end, location). If a field is
   ambiguous, leave a `# TODO confirm` comment.
6. If `factual-bounds.md` is absent, create it with a heading and a short "add rules as
   you correct drafts" comment. If present, leave it untouched.
7. Print a summary: files created/merged, and an explicit list of dates/titles/contact
   details for the user to confirm. List any CV contradictions the subagent flagged and
   ask the user to resolve them — do not choose silently.

## Guardrails
- Only reorganise what the CVs contain. Never add skills, employers, or metrics.
- Merges are additive; a re-run with one new CV must not delete existing bullets.
```

- [ ] **Step 3: Write `commands/ingest.md`**

```markdown
---
description: Build/refresh resume_sections/ from a folder of past CVs
---

Invoke the `ingest` skill. Argument: path to a folder containing the user's past CVs.
```

- [ ] **Step 4: Write `tests/skills/ingest.expected.md`** — a checklist the integration
  test asserts against after running `ingest` on `example/raw_cvs/`:
  - `example-run/resume_sections/companies/acme.md` exists and contains a bullet
  - `.../companies/globex.md` exists
  - `.../profile.yml` exists and parses as YAML with `name: "Sample Dev"`
  - `.../factual-bounds.md` exists
  - no duplicate bullet text across the two company files (same sentence twice)

- [ ] **Step 5: Manual verification run**

Run: in a scratch copy, `/ingest example/raw_cvs` targeting a temp source-of-truth dir.
Expected: `companies/acme.md`, `companies/globex.md`, `profile.yml`, `factual-bounds.md`
created; summary lists dates/titles to confirm; the two source CVs' overlapping wording
is collapsed, not duplicated.

- [ ] **Step 6: Commit**

```bash
git add agents/sot-retriever.md skills/ingest commands/ingest.md tests/skills/ingest.expected.md
git commit -m "feat: add sot-retriever agent and ingest skill"
```

---

## Task 6: `jd-intake` skill

**Files:**
- Create: `skills/jd-intake/SKILL.md`
- Create: `commands/jd-intake.md`
- Create: `tests/skills/jd-intake.expected.md`

**Interfaces:**
- Consumes: `sot-retriever` agent (Task 5, `retrieve` mode); `Get-JobAppConfig` for
  `output_dir`.
- Produces: `{output_dir}/jd.md` (raw JD) and `{output_dir}/analysis.md` with a fixed
  structure later tasks parse: `## Essential`, `## Desirable`, `## Responsibilities`,
  `## Criteria → Evidence` (table: Criterion | Evidence (file:line) | Status), `## Fit`
  (one of `strong` / `stretch` / `hard-mismatch` + reason), `## Framing`.

- [ ] **Step 1: Write `skills/jd-intake/SKILL.md`**

```markdown
---
name: jd-intake
description: Analyze a job description — save it, extract essential/desirable criteria, map each to source-of-truth evidence, and classify fit. Run before generate.
---

## When to use
The user pastes a job description or says "analyze this JD for {Company}" / "/jd-intake".

## Steps
1. Determine `{Company}` (ask if unclear). Resolve `output_dir` from `Get-JobAppConfig`,
   substitute `{Company}`, create the folder.
2. Save the raw JD verbatim to `{dir}/jd.md`.
3. Extract, into `{dir}/analysis.md`:
   - `## Essential` — bulleted, verbatim where possible
   - `## Desirable`
   - `## Responsibilities`
   - `## Keywords` — the terms an ATS would scan for
   - `## Language / Stack emphasis` — what this role leads with
4. Dispatch `sot-retriever` in `retrieve` mode (JD + source-of-truth dir). Build
   `## Criteria → Evidence` — a table with columns Criterion | Evidence (file:line) |
   Status (met / partial / gap).
5. Write `## Fit`: `strong` (most essentials met), `stretch` (gaps but a credible
   transferable story), or `hard-mismatch` (an essential requires years of something
   absent from source-of-truth). One sentence of reasoning.
6. Write `## Framing`: which roles to lead with, ordering (relevance vs chronological),
   language emphasis, which bounds from `factual-bounds.md` are relevant.
7. If `hard-mismatch`, tell the user plainly and recommend skipping before they invest
   effort. Do not generate anything.

## Guardrails
- Every "met"/"partial" row must cite a real `file:line` in the source-of-truth dir.
- Never soften a `gap` to `partial` without evidence.
```

- [ ] **Step 2: Write `commands/jd-intake.md`** — shim: "Invoke the `jd-intake` skill.
  Paste the job description; provide the company name."

- [ ] **Step 3: Write `tests/skills/jd-intake.expected.md`** — after running on
  `example/sample-jd.md` with company `Testco`:
  - `applications/Testco/jd.md` equals the input file content
  - `applications/Testco/analysis.md` has all six `##` sections
  - the `Criteria → Evidence` table has one `gap` row (the deliberate gap) and no Rust row marked "met"
  - `## Fit` is `stretch` (not `strong`, not `hard-mismatch`)

- [ ] **Step 4: Manual verification run**

Run: `/jd-intake` with `example/sample-jd.md`, company `Testco`.
Expected: folder + `jd.md` + `analysis.md`; fit = `stretch`; the gap criterion shows as
`gap` with no invented evidence.

- [ ] **Step 5: Commit**

```bash
git add skills/jd-intake commands/jd-intake.md tests/skills/jd-intake.expected.md
git commit -m "feat: add jd-intake skill"
```

---

## Task 7: `generate` skill

**Files:**
- Create: `skills/generate/SKILL.md`
- Create: `commands/generate.md`
- Create: `tests/skills/generate.expected.md`

**Interfaces:**
- Consumes: `{dir}/analysis.md` (Task 6 structure); `sot-retriever` `retrieve` mode;
  `templates/resume_1page.tex`, `templates/resume_2page.tex`, `templates/cover_letter.tex`
  (a repo-level `templates/` overrides); `scripts/compile_latex.ps1`,
  `scripts/compress_pdf.ps1`, `scripts/cover_letter_to_txt.ps1`; `profile.yml`;
  `factual-bounds.md`.
- Produces: `{dir}/resume.{tex,pdf}`, `{dir}/cover_letter.{tex,pdf,txt}`, optional
  `{dir}/answers.md`.

- [ ] **Step 1: Write `skills/generate/SKILL.md`**

```markdown
---
name: generate
description: Produce a tailored resume, cover letter, and optional application-form answers for a job already analyzed by jd-intake. Compiles and compresses the PDFs.
---

## When to use
"Generate the resume/cover letter for {Company}" / "/generate". Requires
`{dir}/analysis.md` — if absent, tell the user to run `jd-intake` first.

## Flags
`--length 1|2` (default from `profile.yml` `default_resume_length`),
`--with-projects` (default from `default_include_projects`),
`--order relevance|chronological` (default `chronological`),
`--answers "Q1; Q2; ..."`.

## Steps
1. Load `{dir}/analysis.md`, `profile.yml`, and `factual-bounds.md` (verbatim).
2. Dispatch `sot-retriever` `retrieve` mode for JD-relevant bullets (ranked, with
   `file:line`).
3. Select résumé template by `--length`. Choose an override at repo `templates/` over
   the plugin's bundled one.
4. Fill the header from `profile.yml` (`{{NAME}}`, `{{PHONE}}`, `{{EMAIL}}`,
   `{{GITHUB_USERNAME}}`). Fill Industrial Experience from `profile.yml.conventions.roles`
   (exact company/title/date strings) + the retrieved bullets. Skills + Introduction
   from retrieved content. Include a Projects section only if `--with-projects`.
5. **Bounds check:** before writing, verify no bullet violates `factual-bounds.md`. If
   the JD pushes for something out of bounds, STOP and ask the user; if they supply a
   new true fact, offer to add it to the source-of-truth dir (and note the file to edit).
6. Write `{dir}/resume.tex`. Run `pwsh scripts/compile_latex.ps1 -TexPath {dir}/resume.tex`.
   If `-not Ok`, surface the log tail, keep the `.tex`, do not compress, do not claim
   success. If pages > target length, warn and list candidate trims.
7. On success: `pwsh scripts/compress_pdf.ps1 -PdfPath {dir}/resume.pdf`.
8. Repeat 4–7 for `cover_letter.tex` using `templates/cover_letter.tex`. Cover-letter
   content rules from `reference/workflow-rules.md`: state experience duration, name the
   companies, name the business domains, name company-tied stacks; obey any
   `factual-bounds.md` cover-letter rule (e.g. no university).
9. `pwsh scripts/cover_letter_to_txt.ps1 -TexPath {dir}/cover_letter.tex`.
10. If `--answers`, write `{dir}/answers.md` — one answer per question, grounded in the
    same retrieved bullets, plus a compact variant each.
11. Clean `.aux/.log/.out` from `{dir}`.
12. Report: every metric and named skill used, each with its source-of-truth `file:line`;
    call out any deviation from `profile.yml` conventions.

## Guardrails
- Company names / titles / dates come from `profile.yml` verbatim — never re-derived.
- No metric appears that is not in the source-of-truth dir.
```

- [ ] **Step 2: Write `commands/generate.md`** — shim listing the flags.

- [ ] **Step 3: Write `tests/skills/generate.expected.md`** — after `/generate` for
  `Testco` (fixture, `--length 1`):
  - `resume.tex`, `resume.pdf`, `cover_letter.tex`, `cover_letter.pdf`, `cover_letter.txt` exist
  - `resume.pdf` is 1 page (via `compile_latex` page count)
  - `resume.tex` contains `Sample Dev` and both company names exactly as in `profile.yml`
  - neither `resume.tex` nor `cover_letter.tex` contains the word `Rust`
  - `cover_letter.txt` first non-empty line starts with `Subject:`
  - `cover_letter.tex` does not contain `Example University` (bounds: no university in cover letter)
  - no `.aux`/`.log`/`.out` left in the folder

- [ ] **Step 4: Manual verification run**

Run: `/generate` for `Testco`, `--length 1`.
Expected: all five files; résumé 1 page; report cites source lines for each metric; no
bounds violation.

- [ ] **Step 5: Commit**

```bash
git add skills/generate commands/generate.md tests/skills/generate.expected.md
git commit -m "feat: add generate skill"
```

---

## Task 8: `review-application` skill, `interview` skill + `company-researcher` agent, integration test

**Files:**
- Create: `skills/review-application/SKILL.md`
- Create: `commands/review-application.md`
- Create: `agents/company-researcher.md`
- Create: `skills/interview/SKILL.md`
- Create: `commands/interview.md`
- Create: `tests/run-pipeline.ps1`
- Modify: `README.md` (final pass — real command examples, fixture output paths)

**Interfaces:**
- Consumes: everything from Tasks 1–7.
- Produces:
  - Skill `review-application` → `{dir}/review.md` with `## Pass`, `## Flag`, `## Fix`
    sections; `--fix` applies safe corrections.
  - Agent `company-researcher` → structured research markdown.
  - Skill `interview` with subcommands `research` / `prep` / `mock`.
  - `tests/run-pipeline.ps1` — runs the whole chain against `example/` and asserts the
    four `tests/skills/*.expected.md` checklists mechanically where possible.

- [ ] **Step 1: Write `skills/review-application/SKILL.md`**

```markdown
---
name: review-application
description: QA a generated application (resume + cover letter) against factual bounds, JD coverage, internal consistency, ATS parseability, and writing quality.
---

## When to use
"Review the {Company} application" / "/review-application". Requires `{dir}` with
`resume.tex`, `cover_letter.tex`, `analysis.md`.

## Checks → write {dir}/review.md
### Compliance
- Every claim in `resume.tex` / `cover_letter.tex` traces to a source-of-truth line.
- No `factual-bounds.md` rule violated (quote the rule + the offending text).
- No numeric metric absent from the source-of-truth dir.
### JD coverage
- Each `## Essential` criterion in `analysis.md` is supported by at least one résumé
  bullet. List any uncovered.
### Consistency
- Company / title / dates match `profile.yml` exactly.
- One tense throughout; résumé length matches the intended target.
- ATS: single column, standard headings, no content locked in tables/text-boxes.
### Quality
- Bullets verb-first; quantified where the source-of-truth supports it; no two bullets
  that are near-duplicates.
### Cover letter
- Follows `reference/workflow-rules.md` core structure; obeys `factual-bounds.md`
  cover-letter rules; `cover_letter.txt` exists and matches the current `.tex`.

## Output
`{dir}/review.md` with `## Pass` / `## Flag` / `## Fix`. With `--fix`, apply the
unambiguous corrections (tense, date/title mismatches vs `profile.yml`, regenerate a
stale `.txt`) and re-run the checks once.
```

- [ ] **Step 2: Write `agents/company-researcher.md`**

```markdown
---
name: company-researcher
description: Web research on a target company and role for interview preparation. Compiles culture, products, reviews, and interview experiences.
tools: WebSearch, WebFetch, Read
---

Given a company name, role title, and the JD, produce a single markdown report:

## Company
Products / clients / business model; size; recent news (last ~12 months).
## Culture & reviews
Glassdoor / Seek / Reddit / Whirlpool / 小红书 signal — balanced pros and cons, dated
where possible.
## Interview process
Reported stages, formats, and specific question topics for this or adjacent roles.
## Angles for the candidate
Where the JD and the candidate's likely background intersect with what the company
actually values.

Cite sources inline. Distinguish widely-corroborated points from single-source anecdotes.
```

- [ ] **Step 3: Write `skills/interview/SKILL.md`**

```markdown
---
name: interview
description: Interview preparation and practice for a specific application — company research, HR question prep, self-introduction, and mock interviews with feedback.
---

## Subcommands

### research
Dispatch `company-researcher` (company + role + JD). Save to
`{dir}/company_research.md`.

### prep
Using `{dir}/analysis.md`, `resume.tex`, `company_research.md` (if present), and the
user's `interview_playbook.md` (seed from `reference/interview-frameworks.md` if
absent), write:
- `{dir}/self_intro.md` — a spoken-length intro hitting anchor points, not memorised.
- `{dir}/hr_questions_prep.md` — likely behavioural / motivation / gap questions with
  bullet-point answers grounded in the résumé.

### mock
Conduct a mock interview. Questions strictly answerable from `resume.tex`. After each
answer give balanced feedback — one genuine strength, one concrete improvement — never
purely positive. At the end, append any *new recurring* lesson to the user's
`interview_playbook.md` (do not duplicate existing entries).

## Guardrails
- Mock questions never assume experience absent from the résumé.
- Feedback is specific ("you said 'we' — the question wanted your personal action"),
  not generic praise.
```

- [ ] **Step 4: Write `commands/review-application.md` and `commands/interview.md`** —
  shims. `interview.md` documents the three subcommands.

- [ ] **Step 5: Write the failing integration test `tests/run-pipeline.ps1`**

```powershell
#requires -Version 7
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$work = Join-Path ([IO.Path]::GetTempPath()) "jobapp-pipeline-$(Get-Random)"
Copy-Item (Join-Path $root "example/resume_sections") (Join-Path $work "resume_sections") -Recurse -Force
$fail = 0
function Check($name, $cond) {
    if ($cond) { Write-Host "PASS  $name" -f Green } else { Write-Host "FAIL  $name" -f Red; $script:fail++ }
}

# 1. compile the shipped 1-page template with placeholder values filled
$tex = Join-Path $work "resume_sections/../smoke.tex"
(Get-Content (Join-Path $root "templates/resume_1page.tex") -Raw).
    Replace('{{NAME}}','Sample Dev').Replace('{{PHONE}}','(+00) 0').
    Replace('{{EMAIL}}','s@example.com').Replace('{{GITHUB_USERNAME}}','sample-dev').
    Replace('{{INTRODUCTION_BULLETS}}','Test.').Replace('{{JOB_TITLE}}','Software Engineer').
    Replace('{{EMPLOYMENT_DATES}}','Jan. 2024 -- Present').Replace('{{COMPANY_NAME}}','Acme Corp').
    Replace('{{LOCATION}}','Sydney').Replace('{{TECH_STACK}}','Python').
    Replace('{{BULLET_POINT_1}}','Did a thing.').Replace('{{BULLET_POINT_2}}','Did another.').
    Replace('{{BULLET_POINT_3}}','And another.').Replace('{{LANGUAGES_LIST}}','Python').
    Replace('{{FRAMEWORKS_AND_TOOLS_LIST}}','Django') | Set-Content $tex
$r = & (Join-Path $root "scripts/compile_latex.ps1") -TexPath $tex
Check "template compiles" ($LASTEXITCODE -eq 0)

# 2. cover_letter_to_txt hoists Subject
$cl = Join-Path $work "cl.tex"
Copy-Item (Join-Path $root "templates/cover_letter.tex") $cl
(Get-Content $cl -Raw).Replace('{{SUBJECT}}','Application for X').Replace('{{NAME}}','Sample Dev') | Set-Content $cl
# (fill remaining placeholders minimally) ...
& (Join-Path $root "scripts/cover_letter_to_txt.ps1") -TexPath $cl
$txt = [IO.Path]::ChangeExtension($cl, ".txt")
Check "txt produced" (Test-Path $txt)

# 3. config loader default
. (Join-Path $root "scripts/lib/config.ps1")
Check "config default sot dir" ((Get-JobAppConfig).SourceOfTruthDir -eq 'resume_sections')

Remove-Item $work -Recurse -Force
if ($fail) { Write-Error "$fail check(s) failed"; exit 1 } else { Write-Host "all checks passed" -f Green }
```

- [ ] **Step 6: Run it, expect failure, then make it pass**

Run: `pwsh tests/run-pipeline.ps1`
Expected first run: FAIL if any placeholder set is incomplete or a script path is wrong.
Fix the script (fill every placeholder the templates actually contain — enumerate them
with `Select-String '{{.*?}}' templates/*.tex`), re-run until "all checks passed".

- [ ] **Step 7: README final pass** — replace any earlier provisional command text with
  the real invocations and the real `example/` output paths; add a "Running the tests"
  line (`pwsh tests/run-pipeline.ps1`, `Invoke-Pester tests/`).

- [ ] **Step 8: Commit**

```bash
git add skills/review-application skills/interview agents/company-researcher.md commands tests/run-pipeline.ps1 README.md
git commit -m "feat: add review-application and interview skills, integration test"
```

---

## Self-Review

**1. Spec coverage**

| Spec section | Task |
|---|---|
| §3 repo layout | Task 1 (scaffold, moves), Task 4 (`reference/`, `example/`) |
| §4.1 `profile.yml` | Task 4 (example), Task 5 (`ingest` drafts it), Task 7 (consumed) |
| §4.2 `factual-bounds.md` | Task 4 (example), Task 5 (seeded), Task 7 + Task 8 (enforced) |
| §4.3 consolidated sections | Task 4 (example), Task 5 (`ingest` writes) |
| §4.4 overrides (`templates/`, `interview_playbook.md`, `jobapp.config.yml`) | Task 2 (`config.ps1`), Task 7 (template override), Task 8 (playbook seed) |
| §5.1 `ingest` | Task 5 |
| §5.2 `jd-intake` | Task 6 |
| §5.3 `generate` | Task 7 |
| §5.4 `review-application` | Task 8 |
| §5.5 `interview` | Task 8 |
| §6.1 `sot-retriever` | Task 5 |
| §6.2 `company-researcher` | Task 8 |
| §7 scripts | Task 1 (moves), Task 2 (`compile_latex`), Task 3 (`extract_cv`) |
| §8 templates | Task 1 (rename), Task 7 (fill logic) |
| §9 error handling | Task 2 (loud LaTeX fail), Task 6 (missing analysis), Task 7 (bounds stop, length warn) |
| §10 testing | Task 2/3 (Pester), Task 5/6/7 (expected checklists), Task 8 (`run-pipeline.ps1`) |
| §11 open-source polish | Task 1 (`LICENSE`, `README`, `.gitignore`, manifests), Task 8 (README final) |
| §12 implementation order | This plan's task order |

No gaps.

**2. Placeholder scan** — the plan contains illustrative-but-complete file contents for
JSON/PS1/agent/skill files; prose-heavy files (`README.md`, `reference/*.md`, the
`example/` company files, `analysis.md` structure) are specified by required sections
and required properties rather than full text, which is appropriate for
documentation/fixture content. No "TBD", no "handle edge cases", no "similar to Task N".

**3. Type consistency**

- `Get-JobAppConfig` returns `@{ PdflatexPath; SourceOfTruthDir; OutputDir }` — used
  consistently in Tasks 2, 5, 6, 7.
- `Invoke-LatexCompile` / `compile_latex.ps1` returns `@{ Pdf; Pages; Ok; LogTail }` —
  consumed in Task 7 step 6 and Task 8.
- `sot-retriever` modes `cluster` / `retrieve` — named identically in Task 5 (agent def),
  Task 5 (`ingest` uses `cluster`), Task 6 + Task 7 (use `retrieve`).
- `analysis.md` sections (`## Essential`, `## Criteria → Evidence`, `## Fit`, `## Framing`)
  — defined in Task 6, consumed in Tasks 7 and 8 with the same names.
- `review.md` sections (`## Pass` / `## Flag` / `## Fix`) — Task 8 only, consistent.

No mismatches found.
