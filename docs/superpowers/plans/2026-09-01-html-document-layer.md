# HTML Document Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the plugin's LaTeX rendering layer with browser-rendered HTML — one
data-driven `resume.html` / `cover_letter.html` template per document type, rendered to
PDF by headless Chromium, flowing to any page count, with bilingual (EN/ZH) support.

**Architecture:** Each template is a self-contained HTML file: bundled `@font-face`
fonts, a direction-A stylesheet, a `<script type="application/json">` data block, and a
~90-line inline vanilla-JS renderer. `generate` writes only the JSON; `render_pdf.ps1`
injects it and runs `msedge --headless=new --print-to-pdf`. No Node, no build step, no
network at render time.

**Tech Stack:** HTML5 + print CSS, vanilla ES5 JS (runs in the print browser),
PowerShell 7, headless Microsoft Edge / Google Chrome, WOFF2 fonts (Newsreader + Source
Serif 4, OFL).

**Spec:** `docs/superpowers/specs/2026-09-01-html-document-layer-design.md`
(amends `docs/superpowers/specs/2026-08-31-job-application-plugin-design.md`)

## Global Constraints

- Branch: `build/job-application-plugin` (continues from the v0.1 commits / PR #1).
- Plugin version → `0.2.0` in `.claude-plugin/plugin.json`.
- No new machine dependency beyond a Chromium browser (Edge/Chrome/Chromium). No Node,
  no npm, no Tailwind, no CDN, no network at render time.
- Tests are plain-PowerShell assertion scripts run via `pwsh -File` (no Pester) — same
  as v0.1.
- Plugin-internal paths in skill/command/agent markdown use `${CLAUDE_PLUGIN_ROOT}`.
- `Get-JobAppConfig` keeps returning `@{ Root; PdflatexPath?; SourceOfTruthDir; OutputDir }`
  — rename `PdflatexPath` → `BrowserPath`; add `GhostscriptPath` stays as-is if present.
- Every generated claim traces to a source-of-truth `file:line`; `factual-bounds.md` is
  a hard STOP-and-ask constraint. Company/title/date strings come from `profile.yml`
  verbatim. (All unchanged from v0.1.)
- All JSON strings are text-escaped by the renderer — no HTML in the data.
- `${CLAUDE_PLUGIN_ROOT}/templates/` is overridable by a repo-level `templates/` dir.
- Unchanged and NOT to be touched: `skills/ingest`, `skills/jd-intake`, `skills/interview`,
  `agents/sot-retriever.md`, `agents/company-researcher.md`, `reference/workflow-rules.md`,
  `reference/interview-frameworks.md`, `example/resume_sections/**`, `scripts/extract_cv.ps1`,
  `scripts/compress_pdf.ps1`.
- A working prototype exists at
  `<scratchpad>/resume.html` + `<scratchpad>/data_1page.json` +
  `<scratchpad>/data_4page.json` (the controller will hand these to Task 1).

---

## File Structure

**Created:**

| Path | Responsibility |
|------|----------------|
| `templates/resume.html` | Data-driven résumé template (direction A, JSON block + inline renderer) |
| `templates/cover_letter.html` | Data-driven cover-letter template |
| `templates/fonts/Newsreader.woff2` | Display face (variable, OFL) |
| `templates/fonts/SourceSerif4.woff2` | Body face (variable, OFL) |
| `templates/fonts/OFL.txt` | SIL Open Font License + source URLs |
| `scripts/render_pdf.ps1` | Inject JSON → temp HTML → headless-Chromium print-to-pdf |
| `tests/scripts/render_pdf.Tests.ps1` | Plain-PS assertions for `render_pdf.ps1` |
| `tests/skills/review-application.expected.md` | (if not already present from v0.1 final wave — verify) |
| `example/resume.data.json` | Sample Dev résumé JSON (English) |
| `example/resume.zh.data.json` | Sample Dev résumé JSON (Chinese) |
| `example/cover_letter.data.json` | Sample Dev cover-letter JSON |
| `README.zh-CN.md` | Chinese README |

**Modified:**

| Path | Change |
|------|--------|
| `scripts/lib/config.ps1` | `Resolve-Pdflatex` → `Resolve-Browser`; config key `pdflatex_path` → `browser_path`; hashtable key `PdflatexPath` → `BrowserPath` |
| `scripts/cover_letter_to_txt.ps1` | Rewrite: `cover_letter.data.json` → email `.txt` (no LaTeX/HTML parsing) |
| `tests/scripts/config.Tests.ps1` | `Resolve-Browser` assertion; key rename |
| `tests/run-pipeline.ps1` | Render both templates via `render_pdf.ps1`; drop LaTeX checks |
| `skills/generate/SKILL.md` | JSON contract, render step, `--density`/`--max-pages`/`--lang` flags |
| `commands/generate.md` | New flag list |
| `tests/skills/generate.expected.md` | Assertions target `.data.json` + rendered PDF |
| `skills/review-application/SKILL.md` | Checks vs `.data.json` + PDF text extraction; render-failure path |
| `README.md` | Prereq = Chromium browser; `--lang zh` note; switcher line |
| `jobapp.config.example.yml` | `pdflatex_path` → `browser_path` |
| `reference/ats-checklist.md` | Drop LaTeX lines; note single-column + text-extractable |
| `.claude-plugin/plugin.json` | `version` → `0.2.0` |
| `docs/superpowers/specs/2026-08-31-…-design.md` | Pointer to the amendment (§7/§8/§10) |

**Deleted:**

| Path | Reason |
|------|--------|
| `scripts/compile_latex.ps1` | Replaced by `render_pdf.ps1` |
| `tests/scripts/compile_latex.Tests.ps1` | Replaced by `render_pdf.Tests.ps1` |
| `templates/resume_1page.tex`, `templates/resume_2page.tex`, `templates/cover_letter.tex` | Replaced by `.html` |

---

## Task 1: Bundled fonts + `templates/resume.html`

**Files:**
- Create: `templates/fonts/Newsreader.woff2`, `templates/fonts/SourceSerif4.woff2`, `templates/fonts/OFL.txt`
- Create: `templates/resume.html`
- Delete: `templates/resume_1page.tex`, `templates/resume_2page.tex`
- Test: manual render of two fixture JSONs

**Interfaces:**
- Produces: `templates/resume.html` — single placeholder `{{RESUME_JSON}}` inside
  `<script type="application/json" id="resume-data">`. Renderer reads the schema in
  spec §3.1: `{ name, lang, density, contact[], introTitle?, intro[{lead,text}],
  sections[{title, type, ...}] }`; section `type` ∈ `entries|education|skills|list`.
  Renderer text-escapes every value; catches JSON parse errors and prints
  `Invalid resume JSON: <msg>` into `#resume`.

- [ ] **Step 1: Fetch the fonts**

```bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
mkdir -p templates/fonts
# Google Fonts css2 returns variable woff2 for a wght range when called with a modern UA
curl -s -A "$UA" 'https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400..600&family=Source+Serif+4:opsz,wght@8..60,400..600&display=swap' -o /tmp/gf.css
# extract the two woff2 URLs (latin subset)
grep -oE 'https://fonts.gstatic.com/[^)]+\.woff2' /tmp/gf.css | sort -u
```
Download the Newsreader latin woff2 → `templates/fonts/Newsreader.woff2`, the Source
Serif 4 latin woff2 → `templates/fonts/SourceSerif4.woff2`. If `css2` returns multiple
subsets, take the `/* latin */` block's URL for each. Each file should be < 200 KB.

- [ ] **Step 2: Write `templates/fonts/OFL.txt`** — the SIL Open Font License 1.1 full
  text, preceded by:
  ```
  Newsreader — Production Type — https://github.com/productiontype/Newsreader
  Source Serif 4 — Adobe — https://github.com/adobe-fonts/source-serif
  Both licensed under the SIL Open Font License, Version 1.1.
  ```

- [ ] **Step 3: Write `templates/resume.html`** — start from the controller-provided
  prototype `<scratchpad>/resume.html`, with these finalizations:
  - Replace the Google Fonts `@import` line with:
    ```css
    @font-face { font-family: "Newsreader"; src: url("fonts/Newsreader.woff2") format("woff2");
      font-weight: 400 600; font-display: swap; }
    @font-face { font-family: "Source Serif 4"; src: url("fonts/SourceSerif4.woff2") format("woff2");
      font-weight: 400 600; font-display: swap; }
    ```
  - Add CJK fallbacks to the font stacks and a lang rule:
    ```css
    :root {
      --body: "Source Serif 4", Georgia, "Times New Roman", "Noto Serif CJK SC", "Songti SC", serif;
      --display: "Newsreader", Georgia, "Noto Serif CJK SC", "Songti SC", serif;
    }
    :lang(zh) { --body: "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "SimSun", "PingFang SC", "Microsoft YaHei", serif;
                --display: "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "PingFang SC", "Microsoft YaHei", serif; }
    ```
  - Keep the prototype's `.edu-item { break-inside: avoid }`, `p, li { orphans: 2; widows: 2 }`,
    `h2 { break-after: avoid }`, `.entry { break-inside: avoid }`, `body.compact { … }`.
  - Keep the inline renderer exactly as in the prototype (header, intro, the four
    section renderers, `data.density`/`data.lang` handling).
  - `<title>` = `Resume`.

- [ ] **Step 4: Render the two fixture JSONs**

```bash
BROWSER="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
[ -f "$BROWSER" ] || BROWSER="/c/Program Files/Google/Chrome/Application/chrome.exe"
SP="$(pwd)"   # run from repo root
for d in 1page 4page; do
  python -c "t=open('templates/resume.html',encoding='utf-8').read(); import json,sys; j=open('/tmp/data_$d.json',encoding='utf-8').read(); open('/tmp/r_$d.html','w',encoding='utf-8').write(t.replace('{{RESUME_JSON}}', j))"
  WIN=$(cygpath -w /tmp/r_$d.html 2>/dev/null || echo "C:/tmp/r_$d.html")
  "$BROWSER" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=5000 --print-to-pdf="C:/tmp/r_$d.pdf" "file:///${WIN//\\//}"
done
```
(controller provides `/tmp/data_1page.json` and `/tmp/data_4page.json` from the prototype.)

Expected: `r_1page.pdf` is 1 page; `r_4page.pdf` is ≥ 3 pages; `pdftotext -enc UTF-8
r_1page.pdf -` contains `Sample Dev` and both company names; no page-break splits a
role or an education entry mid-block (eyeball the multi-page PDF). Record the page
counts and the extraction check in the report.

- [ ] **Step 5: Delete the LaTeX résumé templates**

```bash
git rm templates/resume_1page.tex templates/resume_2page.tex
```

- [ ] **Step 6: Commit**

```bash
git add templates/fonts templates/resume.html
git rm templates/resume_1page.tex templates/resume_2page.tex
git commit -m "feat: data-driven HTML resume template with bundled fonts"
```

---

## Task 2: `templates/cover_letter.html`

**Files:**
- Create: `templates/cover_letter.html`
- Delete: `templates/cover_letter.tex`
- Test: manual render of a fixture JSON

**Interfaces:**
- Consumes: `templates/fonts/*` (Task 1).
- Produces: `templates/cover_letter.html` — single placeholder `{{COVER_LETTER_JSON}}`.
  Schema (spec §3.2): `{ name, lang, contact[], date, recipient[], subject, salutation,
  paragraphs[], closing, signature }`. Renderer text-escapes every value.

- [ ] **Step 1: Write `templates/cover_letter.html`** — same `@font-face` + `:root` /
  `:lang(zh)` blocks as `resume.html`. Layout:
  - centered `.name` + `.contact` header (same as résumé)
  - `.meta` block: `Date: <date>` then the `recipient[]` lines
  - `.subject` — bold, `Subject: <subject>`
  - `.salutation`
  - `.body` — one `<p>` per `paragraphs[]` entry, `margin-bottom: 10pt`, `line-height: 1.5`
  - `.closing` then a 30pt gap then `.signature`
  - `@page { size: Letter; margin: 18mm 18mm }`, body 11pt
  - inline renderer (~40 lines) mirroring the résumé renderer's helpers (`el`, escape via
    `textContent`); parse-error → `Invalid cover letter JSON: <msg>`.

- [ ] **Step 2: Render a fixture JSON**

```bash
# controller provides /tmp/cover_letter.data.json
python -c "t=open('templates/cover_letter.html',encoding='utf-8').read(); j=open('/tmp/cover_letter.data.json',encoding='utf-8').read(); open('/tmp/cl.html','w',encoding='utf-8').write(t.replace('{{COVER_LETTER_JSON}}', j))"
"$BROWSER" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="C:/tmp/cl.pdf" "file:///C:/tmp/cl.html"
```
Expected: 1 page; `pdftotext -enc UTF-8` shows `Subject:` line, the recipient, all
paragraphs, the signature. Record in the report.

- [ ] **Step 3: Commit**

```bash
git add templates/cover_letter.html
git rm templates/cover_letter.tex
git commit -m "feat: data-driven HTML cover-letter template"
```

---

## Task 3: `render_pdf.ps1` + `Resolve-Browser` + tests

**Files:**
- Create: `scripts/render_pdf.ps1`, `tests/scripts/render_pdf.Tests.ps1`
- Modify: `scripts/lib/config.ps1`, `tests/scripts/config.Tests.ps1`, `jobapp.config.example.yml`
- Delete: `scripts/compile_latex.ps1`, `tests/scripts/compile_latex.Tests.ps1`

**Interfaces:**
- Consumes: `templates/*.html` (Tasks 1–2), `Get-JobAppConfig` (`BrowserPath`).
- Produces:
  - `Resolve-Browser [-Hint <path>]` in `config.ps1` → absolute path to a Chromium
    binary; throws `"No Chromium browser found. Set browser_path in jobapp.config.yml."`
    if none. Candidate order: `$Hint`; `${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe`;
    `$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe`;
    `$env:ProgramFiles\Google\Chrome\Application\chrome.exe`;
    `${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe`;
    `Get-Command msedge|chrome|chromium|chromium-browser`.
  - `Get-JobAppConfig` returns `@{ Root; BrowserPath; SourceOfTruthDir; OutputDir }`
    (was `PdflatexPath`). Reads `browser_path` (was `pdflatex_path`) from `jobapp.config.yml`.
  - `scripts/render_pdf.ps1 -TemplatePath <html> -DataPath <json> -OutPath <pdf> [-Placeholder <token>] [-KeepHtml] [-AsModule]`
    → `Invoke-RenderPdf` returns `[pscustomobject]@{ Pdf; Pages; Ok; Log; Html }`.
    `-Placeholder` default `{{RESUME_JSON}}`; the cover-letter caller passes
    `{{COVER_LETTER_JSON}}`. Reads the template, replaces the placeholder with the raw
    file bytes of `-DataPath`, writes `<OutPath dir>/<name>.rendered.html`, runs the
    browser headless print-to-pdf into `-OutPath`. `Pages` = count of `/Type\s*/Page\b`
    (not `/Pages`) matches in the PDF bytes. `Ok=$false` when the browser exit code is
    non-zero OR `-OutPath` is missing/zero-byte; `Log` = last ~25 lines of the browser's
    stderr/stdout. Removes the `.rendered.html` unless `-KeepHtml`. CLI mode
    (`-not $AsModule`): print `OK: <pdf> (<n> page[s])` or `Write-Error` + `exit 1`;
    require all three of `-TemplatePath -DataPath -OutPath` (`exit 2` if missing).

- [ ] **Step 1: Write the failing test `tests/scripts/render_pdf.Tests.ps1`**

```powershell
# plain PowerShell assertions, no Pester
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/render_pdf.ps1" -AsModule
$fail = 0
function Assert($n,[bool]$c){ if($c){Write-Host "PASS  $n" -f Green}else{Write-Host "FAIL  $n" -f Red;$script:fail++} }
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
$work = Join-Path ([IO.Path]::GetTempPath()) "render_pdf-test-$(Get-Random)"
New-Item -ItemType Directory $work | Out-Null
try {
  $tpl = Join-Path $repo "templates/resume.html"
  $small = Join-Path $work "s.json"
  Set-Content $small '{"name":"Testy McTest","contact":["x@example.com"],"sections":[{"title":"Skills","type":"skills","groups":[{"label":"Languages","value":"Python"}]}]}'
  $r = Invoke-RenderPdf -TemplatePath $tpl -DataPath $small -OutPath (Join-Path $work "s.pdf")
  Assert "small: Ok"        $r.Ok
  Assert "small: 1 page"    ($r.Pages -eq 1)
  Assert "small: pdf exists" (Test-Path $r.Pdf)

  $big = Join-Path $work "b.json"
  Set-Content $big (Get-Content (Join-Path $repo "example/resume.data.json") -Raw)   # ← may not exist yet at test-authoring time; see Step 2 note
  # (Task 6 authors example/resume.data.json; until then use a locally-built large JSON)

  $bad = Join-Path $work "bad.json"
  Set-Content $bad '{ this is not json'
  $rb = Invoke-RenderPdf -TemplatePath $tpl -DataPath $bad -OutPath (Join-Path $work "bad.pdf")
  Assert "bad json: still renders a pdf" $rb.Ok
  $txt = & pdftotext -enc UTF-8 $rb.Pdf - 2>$null
  Assert "bad json: page shows the error" ("$txt" -match "Invalid resume JSON")
}
finally { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }
if ($fail) { Write-Error "$fail assertion(s) failed"; exit 1 }
Write-Host "all assertions passed" -f Green
```
Note: the "big JSON ≥3 pages" assertion is deferred to `run-pipeline.ps1` (Task 6) once
`example/resume.data.json` exists; keep this file to the small + bad-json cases plus a
locally-constructed 5-role JSON asserting `Pages -ge 3`.

- [ ] **Step 2: Run it — expect failure** (`Invoke-RenderPdf` undefined).
Run: `pwsh -File tests/scripts/render_pdf.Tests.ps1` → FAIL.

- [ ] **Step 3: Modify `scripts/lib/config.ps1`** — rename `Resolve-Pdflatex` →
  `Resolve-Browser` with the candidate list above; in `Get-JobAppConfig` rename the
  `pdflatex_path` case to `browser_path` and the hashtable key `PdflatexPath` →
  `BrowserPath`. Leave `Root`, `SourceOfTruthDir`, `OutputDir`, `Resolve-Ghostscript`
  untouched.

- [ ] **Step 4: Write `scripts/render_pdf.ps1`**

```powershell
param(
  [string]$TemplatePath,
  [string]$DataPath,
  [string]$OutPath,
  [string]$Placeholder = '{{RESUME_JSON}}',
  [switch]$KeepHtml,
  [switch]$AsModule
)
$PSNativeCommandUseErrorActionPreference = $false
. "$PSScriptRoot/lib/config.ps1"

function Invoke-RenderPdf {
  param(
    [Parameter(Mandatory)][string]$TemplatePath,
    [Parameter(Mandatory)][string]$DataPath,
    [Parameter(Mandatory)][string]$OutPath,
    [string]$Placeholder = '{{RESUME_JSON}}',
    [switch]$KeepHtml
  )
  $TemplatePath = (Resolve-Path $TemplatePath).Path
  $DataPath     = (Resolve-Path $DataPath).Path
  $outDir = Split-Path $OutPath -Parent
  if (-not (Test-Path $outDir)) { New-Item -ItemType Directory $outDir -Force | Out-Null }

  $tpl  = Get-Content -Raw -LiteralPath $TemplatePath
  $json = Get-Content -Raw -LiteralPath $DataPath
  $html = $tpl.Replace($Placeholder, $json)
  $renderedHtml = [IO.Path]::ChangeExtension($OutPath, '.rendered.html')
  Set-Content -LiteralPath $renderedHtml -Value $html -Encoding utf8

  $cfg     = Get-JobAppConfig
  $browser = Resolve-Browser -Hint $cfg.BrowserPath
  $fileUrl = 'file:///' + ($renderedHtml -replace '\\','/')
  $out = & $browser --headless=new --disable-gpu --no-pdf-header-footer `
                    --virtual-time-budget=5000 --print-to-pdf="$OutPath" $fileUrl 2>&1
  $exit = $LASTEXITCODE

  $ok = ($exit -eq 0) -and (Test-Path $OutPath) -and ((Get-Item $OutPath).Length -gt 0)
  $pages = 0
  if ($ok) {
    $bytes = [IO.File]::ReadAllText($OutPath, [Text.Encoding]::Latin1)
    $pages = ([regex]::Matches($bytes, '/Type\s*/Page\b')).Count
  }
  if (-not $KeepHtml) { Remove-Item $renderedHtml -ErrorAction SilentlyContinue }

  [pscustomobject]@{
    Pdf   = $OutPath
    Pages = $pages
    Ok    = $ok
    Log   = if ($ok) { '' } else { (($out | Select-Object -Last 25) -join "`n") }
    Html  = if ($KeepHtml) { $renderedHtml } else { $null }
  }
}

if (-not $AsModule) {
  if (-not $TemplatePath -or -not $DataPath -or -not $OutPath) {
    Write-Error "render_pdf.ps1: -TemplatePath, -DataPath and -OutPath are required"; exit 2
  }
  $r = Invoke-RenderPdf -TemplatePath $TemplatePath -DataPath $DataPath -OutPath $OutPath -Placeholder $Placeholder -KeepHtml:$KeepHtml
  if ($r.Ok) { Write-Host "OK: $($r.Pdf) ($($r.Pages) page$(if($r.Pages -ne 1){'s'}))" }
  else { Write-Error "Render failed:`n$($r.Log)"; exit 1 }
}
```

- [ ] **Step 5: Run tests → pass.** `pwsh -File tests/scripts/render_pdf.Tests.ps1`
Expected: PASS (small + bad-json + local-big cases). If Edge/Chrome absent, the whole
file `exit`s early with a `SKIP` message (mirror the pattern; a Chromium browser is a
global constraint so a skip is acceptable but note it).

- [ ] **Step 6: Update `tests/scripts/config.Tests.ps1`** — replace any `PdflatexPath`
  reference with `BrowserPath`; add: `Resolve-Browser` returns a path that exists, OR
  (if none installed) throws with "browser_path". Keep the `Root` assertions.

- [ ] **Step 7: Update `jobapp.config.example.yml`** — `pdflatex_path:` line → `browser_path:`
  with a Windows Edge example path, commented.

- [ ] **Step 8: Delete the LaTeX compile script + test**

```bash
git rm scripts/compile_latex.ps1 tests/scripts/compile_latex.Tests.ps1
```

- [ ] **Step 9: Commit**

```bash
git add scripts/render_pdf.ps1 scripts/lib/config.ps1 tests/scripts/render_pdf.Tests.ps1 tests/scripts/config.Tests.ps1 jobapp.config.example.yml
git rm scripts/compile_latex.ps1 tests/scripts/compile_latex.Tests.ps1
git commit -m "feat: render_pdf.ps1 via headless Chromium; retire compile_latex.ps1"
```

---

## Task 4: `cover_letter_to_txt.ps1` rewrite

**Files:**
- Modify: `scripts/cover_letter_to_txt.ps1`
- Create: `tests/scripts/cover_letter_to_txt.Tests.ps1`

**Interfaces:**
- Produces: `scripts/cover_letter_to_txt.ps1 -DataPath <cover_letter.data.json> [-OutPath <txt>] [-AsModule]`
  → `ConvertTo-CoverLetterText` returns the text and writes it to `-OutPath` (default:
  `<DataPath dir>/cover_letter.txt`). Output layout, in order:
  ```
  Subject: <subject>
  <blank>
  <name>
  <contact joined by "  |  ">
  <blank>
  <date>
  <blank>
  <each recipient[] line>
  <blank>
  <salutation>
  <blank>
  <each paragraph, separated by a blank line>
  <blank>
  <closing>
  <blank>
  <signature>
  ```
  Plain UTF-8, `\n` line endings, no trailing whitespace, single trailing newline.

- [ ] **Step 1: Write the failing test**

```powershell
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/cover_letter_to_txt.ps1" -AsModule
$fail = 0
function Assert($n,[bool]$c){ if($c){Write-Host "PASS  $n" -f Green}else{Write-Host "FAIL  $n" -f Red;$script:fail++} }
$work = Join-Path ([IO.Path]::GetTempPath()) "cl2txt-$(Get-Random)"; New-Item -ItemType Directory $work | Out-Null
try {
  $j = Join-Path $work "cl.json"
  Set-Content $j '{"name":"Sample Dev","contact":["x@example.com","github.com/s"],"date":"September 1, 2026","recipient":["Hiring Manager","Acme Corp"],"subject":"Application for the Position of X","salutation":"Dear Hiring Manager,","paragraphs":["Para one.","Para two."],"closing":"Sincerely,","signature":"Sample Dev"}'
  $out = Join-Path $work "cl.txt"
  ConvertTo-CoverLetterText -DataPath $j -OutPath $out | Out-Null
  $t = Get-Content -Raw $out
  Assert "file written"           (Test-Path $out)
  Assert "first line is Subject"  (($t -split "`n")[0] -eq 'Subject: Application for the Position of X')
  Assert "has salutation"         ($t -match 'Dear Hiring Manager,')
  Assert "paragraphs separated"   ($t -match 'Para one\.\r?\n\r?\nPara two\.')
  Assert "ends with signature"    ($t.TrimEnd() -match 'Sample Dev$')
}
finally { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }
if ($fail) { Write-Error "$fail failed"; exit 1 }; Write-Host "all assertions passed" -f Green
```

- [ ] **Step 2: Run → FAIL** (`ConvertTo-CoverLetterText` undefined).

- [ ] **Step 3: Rewrite `scripts/cover_letter_to_txt.ps1`**

```powershell
param([string]$DataPath, [string]$OutPath, [switch]$AsModule)
$ErrorActionPreference = 'Stop'

function ConvertTo-CoverLetterText {
  param([Parameter(Mandatory)][string]$DataPath, [string]$OutPath)
  $d = Get-Content -Raw -LiteralPath $DataPath | ConvertFrom-Json
  if (-not $OutPath) { $OutPath = Join-Path (Split-Path (Resolve-Path $DataPath)) 'cover_letter.txt' }

  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add("Subject: $($d.subject)"); $lines.Add('')
  $lines.Add($d.name)
  $contact = @($d.contact | ForEach-Object { if ($_ -is [string]) { $_ } else { $_.text } })
  if ($contact.Count) { $lines.Add(($contact -join '  |  ')) }
  $lines.Add('')
  if ($d.date) { $lines.Add([string]$d.date); $lines.Add('') }
  foreach ($r in @($d.recipient)) { $lines.Add([string]$r) }
  if (@($d.recipient).Count) { $lines.Add('') }
  if ($d.salutation) { $lines.Add([string]$d.salutation); $lines.Add('') }
  $paras = @($d.paragraphs)
  for ($i = 0; $i -lt $paras.Count; $i++) { $lines.Add([string]$paras[$i]); if ($i -lt $paras.Count - 1) { $lines.Add('') } }
  $lines.Add('')
  if ($d.closing)   { $lines.Add([string]$d.closing);   $lines.Add('') }
  if ($d.signature) { $lines.Add([string]$d.signature) }

  $text = (($lines -join "`n") -replace '[ \t]+(\r?\n)', '$1').TrimEnd() + "`n"
  Set-Content -LiteralPath $OutPath -Value $text -Encoding utf8 -NoNewline
  $text
}

if (-not $AsModule) {
  if (-not $DataPath) { Write-Error "cover_letter_to_txt.ps1: -DataPath is required"; exit 2 }
  ConvertTo-CoverLetterText -DataPath $DataPath -OutPath $OutPath | Out-Null
  Write-Host "Wrote $(if($OutPath){$OutPath}else{'cover_letter.txt'})"
}
```

- [ ] **Step 4: Run tests → pass.**

- [ ] **Step 5: Commit**

```bash
git add scripts/cover_letter_to_txt.ps1 tests/scripts/cover_letter_to_txt.Tests.ps1
git commit -m "feat: cover_letter_to_txt.ps1 builds email text from cover_letter.data.json"
```

---

## Task 5: `generate` skill rewrite

**Files:**
- Modify: `skills/generate/SKILL.md`, `commands/generate.md`, `tests/skills/generate.expected.md`

**Interfaces:**
- Consumes: `templates/resume.html`, `templates/cover_letter.html`, `scripts/render_pdf.ps1`,
  `scripts/cover_letter_to_txt.ps1`, `scripts/compress_pdf.ps1`, `Get-JobAppConfig`,
  `agents/sot-retriever.md` (`retrieve`), `{dir}/analysis.md` (from `jd-intake`),
  `profile.yml`, `factual-bounds.md`.
- Produces: `{dir}/resume.data.json`, `{dir}/resume.pdf`, `{dir}/cover_letter.data.json`,
  `{dir}/cover_letter.pdf`, `{dir}/cover_letter.txt`, optional `{dir}/answers.md`,
  optional `*.rendered.html` (with `--keep-html`).

- [ ] **Step 1: Rewrite `skills/generate/SKILL.md`** keeping the v0.1 frontmatter,
  "when to use", the bounds STOP-and-ask (step 5), the `## Fit` hard-mismatch stop, the
  source-of-truth `file:line` citation requirement, and the `profile.yml`-verbatim rule.
  Replace the rendering half:
  - **Flags:** `--density compact|standard` (default: `profile.yml` `default_density`
    if present, else `compact` when `default_resume_length == 1`, else `standard`);
    `--max-pages N` (default 2, soft); `--lang en|zh` (default `en`);
    `--with-projects`; `--order relevance|chronological`; `--answers "…"`;
    `--keep-html`.
  - **Step: build `{dir}/resume.data.json`** per spec §3.1. Enumerate: `name`, `lang`,
    `density`, `contact` (from `profile.yml`), `intro` (`{lead,text}` from retrieved
    introduction content), `sections`:
    - `Industrial Experience` — `type: entries`, one item per `profile.yml.conventions.roles`
      (primary=title, dates, secondary=company, location — all verbatim; stack + bullets
      from `sot-retriever` `retrieve`). Order per `--order`.
    - `Selected Projects` — `type: entries` — only if `--with-projects`.
    - `Education` — `type: education` from `conventions.education`.
    - `Skills` — `type: skills`, `groups` from retrieved skills.
    - Any extra section the source-of-truth supports (Publications, Certifications) →
      `type: list`.
  - **`--lang zh`:** section `title`s are the Chinese equivalents
    (工作经验 / 教育背景 / 技能 / …), `lang: "zh"`, and body strings are Chinese — the
    skill translates the retrieved English source-of-truth content. This is the ONLY
    place translation occurs; the `factual-bounds` / no-invention rules still apply to
    the translated text.
  - **Step: render** — `pwsh ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.ps1
    -TemplatePath <resume.html> -DataPath {dir}/resume.data.json -OutPath {dir}/resume.pdf`.
    Non-zero exit ⇒ surface the `Render failed:` text, keep the `.json`, do NOT compress,
    do NOT claim success. Parse pages from the `OK: … (N page…)` line.
    `pages > --max-pages` ⇒ warn and list candidate trims (shortest-impact bullets
    first); never edit content to force-fit without telling the user.
  - **Step: compress** — `pwsh …/compress_pdf.ps1 -PdfPath {dir}/resume.pdf` on success.
  - **Cover letter:** build `{dir}/cover_letter.data.json` per §3.2 (rules from
    `${CLAUDE_PLUGIN_ROOT}/reference/workflow-rules.md`: experience duration, name
    companies, name business domains, name company-tied stacks; obey `factual-bounds.md`
    cover-letter rules e.g. no university). Render with
    `-TemplatePath <cover_letter.html> -DataPath … -Placeholder '{{COVER_LETTER_JSON}}'`.
    Then `pwsh …/cover_letter_to_txt.ps1 -DataPath {dir}/cover_letter.data.json`.
  - **Answers:** unchanged (`{dir}/answers.md`).
  - **Report:** every metric / named skill with its source-of-truth `file:line`;
    call out deviations from `profile.yml`; state the final page count for résumé and
    cover letter.
  - Template override: check repo `./templates/<name>.html` before
    `${CLAUDE_PLUGIN_ROOT}/templates/<name>.html`.

- [ ] **Step 2: Rewrite `commands/generate.md`** — the new flag list; one line each.

- [ ] **Step 3: Rewrite `tests/skills/generate.expected.md`** — assertions for a
  `/generate` on the fixture (`Testco`, defaults):
  - `resume.data.json` parses as JSON; `.name` == `profile.yml` name; every
    `sections[].items[].primary/secondary/dates` for the experience section matches a
    `profile.yml.conventions.roles` entry verbatim
  - `resume.pdf` exists, `Ok`, `Pages == 1` for the fixture
  - `pdftotext -enc UTF-8 resume.pdf -` contains the name and both company names
  - `resume.data.json` and `resume.pdf` text contain no `Rust` (fixture bound)
  - `cover_letter.pdf` exists; `cover_letter.txt` first non-blank line starts `Subject:`
  - `cover_letter.data.json` / `.txt` contain no `Example University` (bound: no
    university in cover letters)
  - no `.rendered.html` left in `{dir}` (no `--keep-html`)
  - the generate report cites a `file:line` for every metric / named skill

- [ ] **Step 4: Manual walkthrough** — you cannot run `/generate` as a slash command.
  Walk the SKILL.md by hand for `example/sample-jd.md` → `Testco`: build
  `resume.data.json` + `cover_letter.data.json` into a temp dir (retrieve against
  `example/resume_sections/`), run the REAL `render_pdf.ps1` + `compress_pdf.ps1` +
  `cover_letter_to_txt.ps1`, check every `generate.expected.md` assertion (record the
  real page count + the `pdftotext` output). Delete the temp dir; do NOT commit it.

- [ ] **Step 5: Commit**

```bash
git add skills/generate/SKILL.md commands/generate.md tests/skills/generate.expected.md
git commit -m "feat: generate skill produces resume/cover-letter JSON, renders via render_pdf.ps1"
```

---

## Task 6: `review-application` + `run-pipeline.ps1` + example JSONs + README (EN/ZH) + version + docs

**Files:**
- Modify: `skills/review-application/SKILL.md`, `tests/run-pipeline.ps1`, `README.md`,
  `reference/ats-checklist.md`, `.claude-plugin/plugin.json`,
  `docs/superpowers/specs/2026-08-31-job-application-plugin-design.md`
- Create: `example/resume.data.json`, `example/resume.zh.data.json`,
  `example/cover_letter.data.json`, `README.zh-CN.md`

**Interfaces:**
- Consumes: everything from Tasks 1–5.

- [ ] **Step 1: `example/resume.data.json`** — the Sample Dev fixture rendered as the
  §3.1 schema: `name` "Sample Dev", contact, a 3-bullet `intro`, `Industrial Experience`
  (`entries`, 2 roles = Acme Corp + Globex, verbatim from
  `example/resume_sections/profile.yml`, bullets from `companies/*.md`), `Education`,
  `Skills`. Must round-trip: rendering it produces exactly 1 page; contains no `Rust`.

- [ ] **Step 2: `example/resume.zh.data.json`** — same person, `lang: "zh"`, Chinese
  section titles (工作经验 / 教育背景 / 技能) and Chinese body text (a faithful
  translation of the English fixture — this is fixture data, not a generated claim).
  Contact + company names may stay Latin. Renders to 1 page with the CJK font fallback.

- [ ] **Step 3: `example/cover_letter.data.json`** — §3.2 schema, Sample Dev applying to
  a plausible role; 4 `paragraphs`; no university mention.

- [ ] **Step 4: Update `skills/review-application/SKILL.md`** — the checks now read
  `{dir}/resume.data.json` (not `.tex`):
  - Compliance: every string in `resume.data.json` traces to source-of-truth; no
    `factual-bounds.md` violation; no metric absent from source-of-truth.
  - Consistency: `sections` experience items' `primary`/`secondary`/`dates`/`location`
    == `profile.yml` verbatim; education likewise.
  - ATS: render the PDF (or read an existing `{dir}/resume.pdf`), run `pdftotext -enc
    UTF-8`, assert the name + each company appear in the extracted text; confirm
    single-column (the template is) and standard headings.
  - Length: `Pages` from `render_pdf` vs `--max-pages` ⇒ `## Flag` (never `## Fix`).
  - Cover letter: `cover_letter.data.json` follows `reference/workflow-rules.md`;
    `cover_letter.txt` exists and its `Subject:` matches `cover_letter.data.json.subject`;
    obey `factual-bounds.md` cover-letter rules.
  - Render-failure path: browser, not pdflatex.
  - `--fix`: unchanged scope (tense, `profile.yml` mismatches, regenerate a stale `.txt`
    from the `.data.json`).

- [ ] **Step 5: Update `tests/run-pipeline.ps1`** — replace the LaTeX-template checks:
  - render `templates/resume.html` with `example/resume.data.json` via
    `Invoke-RenderPdf` → `Ok`, `Pages == 1`, `pdftotext -enc UTF-8` contains `Sample Dev`
  - render `templates/resume.html` with `example/resume.zh.data.json` → `Ok`,
    `pdftotext -enc UTF-8` contains a Chinese section title (e.g. `工作经验`)
  - render `templates/cover_letter.html` with `example/cover_letter.data.json`
    (`-Placeholder '{{COVER_LETTER_JSON}}'`) → `Ok`, `Pages == 1`
  - `cover_letter_to_txt.ps1 -DataPath example/cover_letter.data.json` → `.txt` first
    non-blank line starts `Subject:`
  - `Get-JobAppConfig` → `BrowserPath` key present; `SourceOfTruthDir == 'resume_sections'`
  - run `tests/scripts/render_pdf.Tests.ps1`, `config.Tests.ps1`,
    `cover_letter_to_txt.Tests.ps1`, `extract_cv.Tests.ps1` — each `exit 0`
  - wrap the body in `try { } finally { Remove-Item $work }`; `Get-Content` only after a
    `Test-Path` guard (keep the v0.1-final-wave fixes)

- [ ] **Step 6: `README.md`** — prerequisites: "**A Chromium browser** — Microsoft Edge
  (preinstalled on Windows), Google Chrome, or Chromium. Optional: Ghostscript for
  `compress_pdf`." Remove TinyTeX / XeLaTeX / LaTeX everywhere. Add `--lang zh` to the
  daily-use flow. Add `[English](README.md) | [中文](README.zh-CN.md)` as the first
  line. Keep the `resume_sections/` contract table and the `pwsh tests/run-pipeline.ps1`
  quickstart.

- [ ] **Step 7: `README.zh-CN.md`** — full Chinese translation of `README.md` (same
  sections, same structure), first line `[English](README.md) | [中文](README.zh-CN.md)`.

- [ ] **Step 8: `reference/ats-checklist.md`** — drop LaTeX-specific lines; add: the
  bundled template is single-column with standard headings; generated PDFs are
  text-extractable (`pdftotext -enc UTF-8` round-trips, CJK included); avoid multi-column
  or text-in-images.

- [ ] **Step 9: `.claude-plugin/plugin.json`** — `"version": "0.2.0"`. Update
  `description` if it names LaTeX.

- [ ] **Step 10: Pointer in the v0.1 spec** — add to
  `docs/superpowers/specs/2026-08-31-job-application-plugin-design.md` §7, §8, §10 a
  line: "**Superseded for the rendering layer by
  `docs/superpowers/specs/2026-09-01-html-document-layer-design.md`.**"

- [ ] **Step 11: Run `pwsh tests/run-pipeline.ps1`** — all checks green. Paste output.

- [ ] **Step 12: Commit**

```bash
git add skills/review-application/SKILL.md tests/run-pipeline.ps1 README.md README.zh-CN.md reference/ats-checklist.md .claude-plugin/plugin.json docs/superpowers/specs/2026-08-31-job-application-plugin-design.md example/resume.data.json example/resume.zh.data.json example/cover_letter.data.json
git commit -m "feat: HTML-layer review-application + integration test + bilingual README (v0.2.0)"
```

---

## Self-Review

**1. Spec coverage**

| Spec §  | Task |
|---------|------|
| §2.1 render engine (headless Chromium, resolver) | T3 (`Resolve-Browser`, `render_pdf.ps1`) |
| §2.2 template = HTML + JSON + inline renderer | T1 (résumé), T2 (cover letter) |
| §2.3 multi-page / `--density` / `--max-pages` | T1 (CSS `body.compact`, break rules), T5 (flags) |
| §2.4 bilingual, one template + `:lang(zh)` | T1 (`:lang(zh)` font rule), T5 (`--lang`), T6 (`resume.zh.data.json`) |
| §2.5 bundled fonts | T1 (`templates/fonts/`, `@font-face`) |
| §2.6 direction A visual | T1 (from prototype) |
| §2.8 version 0.2.0 | T6 |
| §3.1 `resume.data.json` schema | T1 (renderer), T5 (producer), T6 (example) |
| §3.2 `cover_letter.data.json` schema | T2 (renderer), T4 (`to_txt`), T5 (producer), T6 (example) |
| §4 templates + fonts | T1, T2 |
| §5 scripts (`render_pdf`, `config`, `cover_letter_to_txt`, deletions) | T3, T4 |
| §6 `generate` rewrite | T5 |
| §7 `review-application` delta | T6 |
| §8 tests | T3, T4 (unit), T6 (`run-pipeline.ps1`) |
| §9 docs (README EN/ZH, ats-checklist, spec pointer, example JSONs) | T6 |
| §10 migration / branch / version | Global Constraints + T6 |

No gaps.

**2. Placeholder scan** — code steps carry full script/CSS/JS content or exact
finalization deltas against the named prototype file; prose files (SKILL.md rewrites,
README, ats-checklist, example JSON *content*) are specified by required
sections/fields/assertions, appropriate for prose+fixture. No "TBD", no "handle edge
cases", no "similar to Task N".

**3. Type consistency**

- `Get-JobAppConfig` → `@{ Root; BrowserPath; SourceOfTruthDir; OutputDir }` — the
  `PdflatexPath`→`BrowserPath` rename is applied in T3 and consumed only in T3/T5/T6.
- `Invoke-RenderPdf` → `@{ Pdf; Pages; Ok; Log; Html }` — defined T3, consumed T3 test,
  T5 (generate), T6 (`run-pipeline.ps1`, `review-application`).
- `Resolve-Browser` — defined T3, used inside `render_pdf.ps1` only.
- `ConvertTo-CoverLetterText -DataPath -OutPath` — defined T4, consumed T4 test, T5, T6.
- `render_pdf.ps1 -Placeholder` default `{{RESUME_JSON}}`; cover-letter callers (T5, T6)
  pass `{{COVER_LETTER_JSON}}` — matches the template placeholders authored in T1/T2.
- JSON schema keys (`sections[].type` ∈ `entries|education|skills|list`; `intro[{lead,text}]`;
  cover letter `paragraphs[]`, `recipient[]`, `subject`) — defined in spec §3, authored
  in the T1/T2 renderers, produced in T5, exemplified in T6, asserted in T3/T4/T6 tests.
  Consistent.

No mismatches found.
