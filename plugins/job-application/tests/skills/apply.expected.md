# Integration-test assertions: `apply` skill

After running `/job-application:apply` for company `Testco` against
`tests/fixtures/resume_sections/` (candidate "Sample Dev") with the synthetic JD
`tests/fixtures/sample-jd.md` and default flags, the produced output must satisfy
every assertion below.

The fixture ships no `jobapp.config.yml`, so `config.py` returns the plugin
default `output_dir` of `applications/{Company}`; the resolved directory is
`applications/Testco/`. Machine artifacts land in `applications/Testco/tmp/`;
deliverables are flat in `applications/Testco/`. With no `--density` flag and
`profile.yml` `conventions.density: compact`, the résumé renders with
`density: "compact"`. Assertions are **structural**.

## Analysis (working note)

1. **Raw JD saved verbatim.** `applications/Testco/jd.md` exists and its content is
   byte-for-byte equal to `tests/fixtures/sample-jd.md` (no reformatting, no trimming).

2. **`analysis.md` has all eight `##` sections, in order.**
   `applications/Testco/analysis.md` exists and contains, in this order, exactly
   these level-2 headings:
   `## Essential`, `## Desirable`, `## Responsibilities`, `## Keywords`,
   `## Language / Stack emphasis`, `## Criteria → Evidence`, `## Fit`, `## Framing`.
   The `## Essential` section is a numbered list (`1.`, `2.`, …), giving each
   essential criterion a stable ordinal the table rows and later sections refer to.

3. **`## Criteria → Evidence` table is honest about the gaps.** The table under
   `## Criteria → Evidence` has a `Criterion | Evidence (file:line) | Status` header
   and one row per essential criterion, and:
   - (a) The row for essential criterion 5 (working knowledge of HL7 v2 / FHIR
     healthcare-interoperability standards) has Status `gap`. This is the one hard,
     unbridgeable gap — nothing in `tests/fixtures/resume_sections/` touches healthcare
     interoperability.
   - (b) The row for essential criterion 4 (2+ years hands-on with a dedicated
     iPaaS / integration platform — MuleSoft Anypoint, Dell Boomi, or Workato) has
     Status `partial` **or** `gap` — either is acceptable. Sample Dev has
     systems-integration experience but no named iPaaS-platform experience in the
     source of truth.
   - (c) The rows for essential criteria 1–3 (RESTful APIs; relational DB / complex
     SQL in PostgreSQL or SQL Server; commercial Python or C#/.NET backend) are
     `met` or `partial`, never `gap`.
   - (d) Every row with Status `met` or `partial` cites a concrete `file:line` that
     actually exists under `tests/fixtures/resume_sections/` (e.g. `companies/acme.md:11`,
     `companies/globex.md:12`, `introduction.md:6`). No `met`/`partial` row has an
     empty or invented evidence cell.
   - (e) No row is marked `met` for a technology absent from the source of truth. In
     particular, nothing referencing Rust appears as a `met` criterion
     (`tests/fixtures/resume_sections/factual-bounds.md` forbids claiming Rust, and the JD
     does not ask for it).

4. **`## Fit` is `stretch`.** Take the first non-blank line of the `## Fit` section
   body, split it on whitespace; the first token, lowercased and stripped of
   trailing punctuation, is exactly `stretch` — not `strong`, not `hard-mismatch`.
   The line follows the form `<token> — <one-sentence reason>` with nothing before
   the token (no bullet, no bold, no `Fit:` prefix). Three of five essentials are
   met and only one criterion is a true gap, but the iPaaS shortfall and the
   healthcare-interop gap keep it below `strong`; the candidate's four-plus years of
   hands-on systems-integration work (REST APIs, message pipelines, third-party
   carrier/ERP integration) is a credible transferable story, so it is not a
   `hard-mismatch`.

## Deliverables

5. **All five artefacts exist.** `applications/Testco/tmp/resume.data.json`,
   `applications/Testco/resume.pdf`, `applications/Testco/tmp/cover_letter.data.json`,
   `applications/Testco/cover_letter.pdf`, and `applications/Testco/cover_letter.txt`
   all exist.

6. **`resume.data.json` parses and carries the right identity.**
   `Get-Content -Raw tmp/resume.data.json | ConvertFrom-Json` succeeds. `.name` equals
   the `name` in `tests/fixtures/resume_sections/profile.yml` exactly (`Sample Dev`).
   `.lang` is `en` and `.density` is `compact`.

7. **The experience section uses the `profile.yml` role strings verbatim.** The
   section with `type == "entries"` whose `title` is the experience heading has one
   `items[]` entry per `profile.yml` `conventions.roles` entry (fixture: 2). For each
   item, matched to its role:
   - `primary` == role `title` (`Software Engineer`, `Junior Developer`);
   - `secondary` == role `company` (`Acme Corp`, `Globex Pty Ltd`);
   - `dates` == `"<start> – <end>"` built from the role's `start` / `end` verbatim,
     joined by a space-padded en-dash U+2013 (`Jan. 2024 – Present`,
     `Feb. 2022 – Dec. 2023`).

8. **`resume.pdf` renders within the page budget.** `render_pdf.py` prints an
   `OK: <path> (N page…)` line (exit 0), the file exists and is non-empty, and the
   page count `N` satisfies `1 <= N <= 2`. A compact fixture résumé of this size
   *should* be 1 page — the skill's "Length discipline" guidance aims well below
   the ceiling — and 2 is the tolerated soft ceiling. The extracted text of
   `resume.pdf` must **not** contain `Invalid resume JSON`.

9. **`resume.pdf` text round-trips.** Extracted text contains `Sample Dev` and both
   company names (`Acme Corp` and `Globex Pty Ltd`).

10. **No forbidden technology.** Neither `tmp/resume.data.json` (raw text) nor the
    extracted text of `resume.pdf` contains the word `Rust` (case-insensitive).
    `tests/fixtures/resume_sections/factual-bounds.md` forbids claiming Rust and the
    JD does not ask for it.

11. **`cover_letter.pdf` exists** and `render_pdf.py` reports it as 1 page.

12. **`cover_letter.txt` leads with the subject.** The first non-empty line of
    `applications/Testco/cover_letter.txt` starts with `Subject:`.

13. **`tmp/cover_letter.data.json` subject has no dangling reference.** The synthetic
    JD carries no requisition ID, so `.subject` is exactly
    `Application for the Position of Integration Developer` — no `Ref:` / `Req ID:`
    fragment and no `{{...}}` placeholder.

14. **No university in the cover letter.** Neither `tmp/cover_letter.data.json` (raw
    text) nor `cover_letter.txt` contains `Example University` (or any other
    `profile.yml` `conventions.education` institution string) —
    `factual-bounds.md`: no university mention in cover letters.

15. **No stray rendered HTML.** `applications/Testco/` contains no `*.rendered.html`
    at any depth — in particular none in `applications/Testco/tmp/`.

16. **Zero-basis / numeric discipline (replaces citation-table gating).** No
    technology, employer, or numeric figure appears in `tmp/resume.data.json` or the
    extracted `resume.pdf` text that is absent from
    `tests/fixtures/resume_sections/` (concatenated). In particular no numeric
    performance figure beyond the experience-duration statement traceable to
    `introduction.md`.

17. **`analysis.md` was honoured, not overridden.** `analysis.md` `## Fit` for this
    JD is `stretch` (not `hard-mismatch`), so generation proceeds. The healthcare
    interoperability (HL7/FHIR) gap and the named-iPaaS-platform gap from
    `analysis.md` `## Criteria → Evidence` are **not** papered over: neither
    `tmp/resume.data.json` nor `tmp/cover_letter.data.json` claims HL7, FHIR,
    MuleSoft, Dell Boomi, or Workato experience.

## Self-check

18. **`review.md` exists with the expected sections.**
    `applications/Testco/review.md` exists with `## Pass`, `## Flag`, and (if any
    fix applied) `## Fix (applied)` sections. It does not assert the application
    "passed" if the render failed.

19. **The deterministic self-check ran and its `pass` checks are not re-flagged.**
    `verify_application.py --dir applications/Testco --source-dir tests/fixtures/resume_sections --json`
    exits 0. For the default fixture run it reports `fail == []` (the fixture
    `profile.yml`, once rendered verbatim, matches; dates use ` – `; the fresh
    `cover_letter.txt` is on disk). `review.md` contains no `## Fix (applied)`
    item whose cause is a check `verify_application.py` reports under `pass`.
