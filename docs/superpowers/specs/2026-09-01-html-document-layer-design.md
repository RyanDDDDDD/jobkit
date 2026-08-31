# HTML Document Layer — Design Amendment

**Date:** 2026-09-01
**Status:** Approved design, pre-implementation
**Amends:** `docs/superpowers/specs/2026-08-31-job-application-plugin-design.md` §7 (scripts),
§8 (templates), §5.3 (`generate`), §5.4 (`review-application`)
**Type:** Architectural — replaces the LaTeX rendering layer with browser-rendered HTML

---

## 1. Why

The LaTeX layer requires TinyTeX (~200 MB) on the user's machine — a heavier and less
universal dependency than a browser. Chinese résumés compound it (xelatex + `ctex` +
CJK fonts). The v0.1 plugin "does not just work on load."

**Every user has a Chromium browser** (Edge ships with Windows; Chrome/Edge/Safari on
macOS; Chromium on Linux desktops). `msedge --headless=new --print-to-pdf` renders HTML
to PDF with:
- correct `@page` size/margins, print CSS, `break-inside: avoid`
- **CJK that both renders and extracts as Unicode text** (verified: `pdftotext -enc
  UTF-8` round-trips `软件工程师，负责 REST API 与 SQL 优化。`)
- sub-second, ~30–260 KB output
- **natural multi-page flow** — a 5-page résumé prints 5 pages with no template change

Spike confirmed on the dev machine (Edge + Chrome both present).

## 2. Key decisions

| # | Decision |
|---|----------|
| 1 | **Render engine:** headless Chromium (`msedge` / `chrome`), resolved from Program Files + PATH. No Node, no build step, no CDN. |
| 2 | **Document format:** a single self-contained HTML template per document type. The template embeds a `<script type="application/json" id="resume-data">` block + a ~90-line inline vanilla-JS renderer. `generate` writes **only the JSON**; the browser renders it at print time. |
| 3 | **Multi-page:** solved by HTML flow. `resume_1page.tex` + `resume_2page.tex` collapse into one `resume.html`. `--length 1\|2` → `--density compact\|standard` (a CSS class) + `--max-pages N` (a *soft* warning in `generate` and `review-application`, never a truncation). |
| 4 | **Bilingual:** one template each, not per-language files. The template's font stack has CJK fallbacks and a `:lang(zh)` rule that puts a CJK face first. `generate` sets `lang` and the section titles in the JSON. A `example/resume.zh.data.json` demonstrates Chinese output. |
| 5 | **Fonts bundled:** Newsreader (display) + Source Serif 4 (body) as `.woff2` under `templates/fonts/`, referenced via `@font-face` — identical output on every OS / CI, no network. CJK falls back to system fonts (`PingFang SC` / `Microsoft YaHei` / `Noto Serif CJK SC`). |
| 6 | **Visual direction:** "Editorial serif" (design direction A) — Newsreader name + small-caps section headings, Source Serif 4 body, hairline rules, old-style figures. This is the default stylesheet; a theme is just a different `<style>` block. |
| 7 | **Unchanged:** `ingest`, `jd-intake`, `interview`, `sot-retriever`, `company-researcher`, `reference/workflow-rules.md`, `reference/interview-frameworks.md`, the `example/resume_sections/` fixture, `Get-JobAppConfig`'s `Root`/`SourceOfTruthDir`/`OutputDir` contract, `compress_pdf.ps1`. |
| 8 | **Version:** bump `plugin.json` to `0.2.0`. |

## 3. The JSON contract

`generate` produces `{dir}/resume.data.json` and `{dir}/cover_letter.data.json`.

### 3.1 `resume.data.json`

```jsonc
{
  "name": "Sample Dev",
  "lang": "en",                       // "en" | "zh" — sets <html lang> and the :lang() font rule
  "density": "standard",              // "standard" | "compact"
  "contact": [                        // array of strings or {text, href}
    "(+61) 400 000 000",
    { "text": "sample.dev@example.com", "href": "mailto:sample.dev@example.com" },
    { "text": "github.com/sample-dev", "href": "https://github.com/sample-dev" }
  ],
  "introTitle": "Introduction",       // optional; default "Introduction"
  "intro": [                          // optional
    { "lead": "Full-Stack Software Engineer",
      "text": "Bachelor of Computer Science with 4+ years ..." }
  ],
  "sections": [
    {
      "title": "Industrial Experience",
      "type": "entries",              // experience AND projects use this
      "items": [
        {
          "primary": "Software Engineer",     // role / project name
          "dates": "Jan. 2024 – Present",     // OR "metaRight" for non-date right text
          "secondary": "Acme Corp",           // company / one-line project description
          "location": "Sydney, Australia",    // optional
          "stack": "Python, C#/.NET, ...",    // optional
          "stackLabel": "Stack",              // optional; default "Stack"
          "bullets": ["...", "..."]           // plain text, any count
        }
      ]
    },
    { "title": "Education", "type": "education", "items": [
        { "institution": "Example University", "dates": "2018 – 2021",
          "credential": "Bachelor of Computer Science", "location": "Sydney, Australia" } ] },
    { "title": "Skills", "type": "skills", "groups": [
        { "label": "Languages & Data", "value": "Python, JavaScript, ..." } ] },
    { "title": "Patents & Publications", "type": "list", "items": ["...", "..."] }
  ]
}
```

- **Section `type`s:** `entries`, `education`, `skills`, `list`. Unknown types fall back
  to `entries`. Add a type = add one render function + document one JSON shape.
- **All strings are text-escaped by the renderer.** No HTML in the JSON. The only rich
  affordance is the `{lead, text}` split (renderer bolds the lead).
- **Company/title/date strings come from `profile.yml` verbatim** — same rule as v0.1.
- **No metric appears that is not in the source-of-truth dir** — unchanged.

### 3.2 `cover_letter.data.json`

```jsonc
{
  "name": "Sample Dev",
  "lang": "en",
  "contact": [ ... ],                 // same shape as resume
  "date": "September 1, 2026",
  "recipient": ["Hiring Manager", "Rivkin Securities Pty Ltd", "Rushcutters Bay, Sydney NSW, Australia"],
  "subject": "Application for the Position of Junior Software Engineer",
  "salutation": "Dear Hiring Manager,",
  "paragraphs": ["...", "...", "...", "..."],   // body, any count
  "closing": "Sincerely,",
  "signature": "Sample Dev"
}
```

## 4. Templates (`templates/`)

| File | Replaces |
|------|----------|
| `templates/resume.html` | `resume_1page.tex` + `resume_2page.tex` |
| `templates/cover_letter.html` | `cover_letter.tex` |
| `templates/fonts/*.woff2` | — (new: Newsreader + Source Serif 4) |

Each template: `@font-face` (local `fonts/`), the direction-A `<style>`, the
`<script type="application/json" id="…-data">{{JSON}}</script>` block (single placeholder
`{{RESUME_JSON}}` / `{{COVER_LETTER_JSON}}`), and the inline renderer `<script>`.

A repo-level `templates/` override still wins over the plugin's bundled one (unchanged).

## 5. Scripts (`scripts/`)

| Script | Change |
|--------|--------|
| `render_pdf.ps1` | **new — replaces `compile_latex.ps1`.** `render_pdf.ps1 -TemplatePath <html> -DataPath <json> -OutPath <pdf>` → injects the JSON into the template's placeholder, writes a temp rendered `.html`, runs `& $browser --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=5000 --print-to-pdf=<out> file:///<temp>`, returns `@{ Pdf; Pages; Ok; Log; Html }`. `Pages` parsed by counting `/Type /Page` objects in the PDF. Non-zero exit or missing/zero-byte PDF ⇒ `Ok=$false`. Optionally `-KeepHtml` to keep the flat rendered file. |
| `lib/config.ps1` | `Resolve-Pdflatex` → `Resolve-Browser` (candidates: `jobapp.config.yml` `browser_path`; `%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe`; `%ProgramFiles%\...\msedge.exe`; `%ProgramFiles%\Google\Chrome\Application\chrome.exe`; PATH `msedge`/`chrome`/`chromium`). `Resolve-Ghostscript` unchanged. `Root` unchanged. |
| `cover_letter_to_txt.ps1` | **rewrite** — takes `cover_letter.data.json`, emits the email-ready `.txt` (Subject line first, blank line, recipient block, salutation, paragraphs, closing, signature). No HTML/LaTeX parsing — it formats the structured data directly. |
| `compress_pdf.ps1` | unchanged. |
| `compile_latex.ps1` | **deleted.** |
| `jobapp.config.example.yml` | `pdflatex_path` → `browser_path`. |

## 6. `generate` skill (§5.3 replacement)

Steps that change:
- **3 (template select):** pick `templates/resume.html` / `cover_letter.html` (repo
  override first). No `--length` variant selection.
- **4 (fill):** build the JSON object per §3, not HTML/LaTeX. Roles from
  `profile.yml.conventions.roles` verbatim + retrieved bullets. Education from
  `conventions.education`. `lang` from `--lang` (default `en`); when `zh`, section
  titles are the Chinese equivalents and body text is Chinese (the skill translates the
  retrieved English source-of-truth bullets — the ONLY place translation happens).
- **6 (render):** `pwsh render_pdf.ps1 -TemplatePath … -DataPath {dir}/resume.data.json
  -OutPath {dir}/resume.pdf`. `Ok=$false` ⇒ surface `Log`, keep the `.json` + `.html`,
  do not compress, do not claim success. `Pages > --max-pages` ⇒ warn + list candidate
  trims; never truncate.
- **9 (txt):** `pwsh cover_letter_to_txt.ps1 -DataPath {dir}/cover_letter.data.json`.
- **11 (clean):** remove the temp rendered `.html` unless `--keep-html`; there are no
  `.aux/.log/.out`.
- Flags: `--density compact|standard` (default from `profile.yml`
  `default_resume_length`: 1 ⇒ compact, 2 ⇒ standard — or a new `default_density` key),
  `--max-pages N`, `--lang en|zh`, `--with-projects`, `--order`, `--answers`.
- **Bounds check, source-of-truth citation, `## Fit` hard-mismatch stop:** unchanged.

Outputs: `resume.{data.json,pdf}`, `cover_letter.{data.json,pdf,txt}`, optional
`answers.md`, optional `*.html`.

## 7. `review-application` skill (§5.4 delta)

- Reads `resume.data.json` (not `.tex`) — checks are now against structured data + the
  rendered PDF's extracted text.
- ATS check: single-column (the template is), headings present, **text extraction
  round-trips** (render the PDF, `pdftotext -enc UTF-8`, assert the name + each company
  appear).
- Render-failure path: browser, not pdflatex.
- `--max-pages` overage is a `## Flag`, not `## Fix`.

## 8. Tests

- `tests/scripts/render_pdf.Tests.ps1` (replaces `compile_latex.Tests.ps1`): render
  `templates/resume.html` with a fixture JSON → PDF exists, `Ok=$true`, `Pages == 1`;
  render with a large fixture JSON → `Pages >= 3`; a deliberately broken JSON → `Ok`
  still true but the rendered page shows the error string (renderer catches parse
  errors) — assert the PDF text contains "Invalid resume JSON".
- `tests/scripts/config.Tests.ps1`: add a `Resolve-Browser` assertion (skip-if-none).
- `tests/run-pipeline.ps1`: render both templates via `render_pdf.ps1` with
  `example/*.data.json`; assert PDF + `pdftotext -enc UTF-8` contains the candidate name;
  assert `cover_letter.txt` first non-blank line starts `Subject:`. Drop the LaTeX
  checks. Keep the 3 (now 2 + render) `tests/scripts/*.Tests.ps1` invocations.

## 9. Docs

- `README.md`: prerequisite becomes **"a Chromium browser (Microsoft Edge, Google
  Chrome, or Chromium — preinstalled on Windows and macOS)"** + optional Ghostscript for
  `compress_pdf`. Remove TinyTeX / XeLaTeX. Add a line on `--lang zh`.
- **`README.zh-CN.md`** (new): full Chinese translation. Both files get a
  `[English](README.md) | [中文](README.zh-CN.md)` switcher line at the top.
- `reference/ats-checklist.md`: note that the HTML template is single-column and that
  generated PDFs are text-extractable; drop LaTeX-specific lines.
- `docs/superpowers/specs/2026-08-31-…-design.md` §7/§8/§10: add a pointer to this
  amendment.
- `example/resume.data.json` + `example/resume.zh.data.json` + `example/cover_letter.data.json`
  (new): the schema, filled from the Sample Dev fixture, one English + one Chinese.

## 10. Migration / PR

Same `build/job-application-plugin` branch, on top of the v0.1 commits (PR #1). The v0.1
LaTeX commits stay as history; the branch's net diff vs `master` ends up HTML. Bump to
`0.2.0`. The maintainer's ~90 existing `.tex` résumés in `all cv/` are unaffected —
they're historical output, not plugin inputs.

## 11. Out of scope

- Multiple visual themes (the architecture supports it; only direction A ships).
- Market-specific Chinese résumé conventions (photo, personal-info block) — same
  template, Chinese content.
- A `--format tex` fallback — LaTeX is removed, not kept as an option.
