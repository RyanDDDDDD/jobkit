# Integration-test assertions: `generate` skill

After running the `generate` skill for company `Testco` with **default flags**,
against the `tests/fixtures/resume_sections/` source of truth (candidate "Sample Dev") and
the `applications/Testco/analysis.md` produced by `jd-intake` from
`tests/fixtures/sample-jd.md` (the synthetic "Integration Developer" JD), the produced
output must satisfy every assertion below.

The fixture ships no `jobapp.config.yml`, so `Get-JobAppConfig` returns the plugin
default `output_dir` of `applications/{Company}`; the resolved directory is therefore
`applications/Testco/`. There is no repo-level `templates/` override in the fixture,
so the bundled `templates/resume.html` and `templates/cover_letter.html` are used.
With no `--density` flag and `profile.yml` `conventions.default_resume_length: 1`
(and no `default_density` key), the résumé renders with `density: "compact"`.
Assertions are **structural** — file existence, JSON shape, page count, and substring
checks, not exact prose.

1. **All five artefacts exist.** `applications/Testco/resume.data.json`,
   `applications/Testco/resume.pdf`, `applications/Testco/cover_letter.data.json`,
   `applications/Testco/cover_letter.pdf`, and `applications/Testco/cover_letter.txt`
   all exist.

2. **`resume.data.json` parses and carries the right identity.**
   `Get-Content -Raw resume.data.json | ConvertFrom-Json` succeeds. `.name` equals
   the `name` in `tests/fixtures/resume_sections/profile.yml` exactly (`Sample Dev`).
   `.lang` is `en` and `.density` is `compact`.

3. **The experience section uses the `profile.yml` role strings verbatim.** The
   section with `type == "entries"` whose `title` is the experience heading has one
   `items[]` entry per `profile.yml` `conventions.roles` entry (fixture: 2). For each
   item, matched to its role:
   - `primary` == role `title` (`Software Engineer`, `Junior Developer`);
   - `secondary` == role `company` (`Acme Corp`, `Globex Pty Ltd`);
   - `dates` == `"<start> – <end>"` built from the role's `start` / `end` verbatim,
     joined by a space-padded en-dash U+2013 (`Jan. 2024 – Present`,
     `Feb. 2022 – Dec. 2023`).

4. **`resume.pdf` renders within the page budget.** `render_pdf.ps1` prints an
   `OK: <path> (N page…)` line (exit 0), the file exists and is non-empty, and the
   page count `N` satisfies `1 <= N <= 2` (the default `--max-pages`). A compact
   fixture résumé of this size *should* be 1 page — the skill's "Length discipline"
   guidance aims well below the ceiling — and 2 is the tolerated soft ceiling, not a
   pass by luck. The `pdftotext -enc UTF-8` output of `resume.pdf` must **not**
   contain `Invalid resume JSON` (the renderer's wrong-shape fallback page).

5. **`resume.pdf` text round-trips.** `pdftotext -enc UTF-8 resume.pdf -` output
   contains `Sample Dev` and both company names (`Acme Corp` and `Globex Pty Ltd`).

6. **No forbidden technology.** Neither `resume.data.json` (raw text) nor the
   `pdftotext -enc UTF-8` output of `resume.pdf` contains the word `Rust`
   (case-insensitive). `tests/fixtures/resume_sections/factual-bounds.md` forbids claiming
   Rust and the JD does not ask for it.

7. **`cover_letter.pdf` exists** and `render_pdf.ps1` reports it as 1 page.

8. **`cover_letter.txt` leads with the subject.** The first non-empty line of
   `applications/Testco/cover_letter.txt` starts with `Subject:`.

9. **`cover_letter.data.json` subject has no dangling reference.** The synthetic JD
   carries no requisition ID, so `.subject` is exactly
   `Application for the Position of Integration Developer` — no `Ref:` / `Req ID:`
   fragment and no `{{...}}` placeholder.

10. **No university in the cover letter.** Neither `cover_letter.data.json` (raw
    text) nor `cover_letter.txt` contains `Example University` (or any other
    `profile.yml` `conventions.education` institution string) —
    `factual-bounds.md`: no university mention in cover letters.

11. **No stray rendered HTML.** `--keep-html` was not passed, so `applications/Testco/`
    contains no `resume.rendered.html` or `cover_letter.rendered.html` (and no other
    `*.rendered.html`).

12. **The `generate` report cites a `file:line` for every metric/skill claim.** The
    skill's step-12 report contains a table (or list) in which every metric and every
    named skill used in `resume.data.json` / `cover_letter.data.json` is paired with
    a source-of-truth citation of the form `<relative/path>:<line>` that resolves to a
    real line under `tests/fixtures/resume_sections/` (e.g. `introduction.md:5`,
    `companies/acme.md:11`). No metric appears in the résumé that is not recorded in
    the source of truth (in particular, no numeric performance figure beyond the
    "4+ years" experience statement traceable to `introduction.md`).

13. **`analysis.md` was honoured, not overridden.** `analysis.md` `## Fit` for this
    JD is `stretch` (not `hard-mismatch`), so generation proceeds. The healthcare
    interoperability (HL7/FHIR) gap and the named-iPaaS-platform gap from
    `analysis.md` `## Criteria → Evidence` are **not** papered over: neither
    `resume.data.json` nor `cover_letter.data.json` claims HL7, FHIR, MuleSoft, Dell
    Boomi, or Workato experience.
