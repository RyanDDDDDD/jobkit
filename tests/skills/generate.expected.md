# Integration-test assertions: `generate` skill

After running the `generate` skill for company `Testco` with `--length 1`, against
the `example/resume_sections/` source of truth (candidate "Sample Dev") and the
`applications/Testco/analysis.md` produced by `jd-intake` from `example/sample-jd.md`
(the synthetic "Integration Developer" JD), the produced output must satisfy every
assertion below.

The fixture ships no `jobapp.config.yml`, so `Get-JobAppConfig` returns the plugin
default `output_dir` of `applications/{Company}`; the resolved directory is therefore
`applications/Testco/`. There is no repo-level `templates/` override in the fixture,
so the bundled `templates/resume_1page.tex` and `templates/cover_letter.tex` are
used. Assertions are **structural** — file existence, section presence, page count,
and substring checks, not exact prose.

1. **All five artefacts exist.** `applications/Testco/resume.tex`,
   `applications/Testco/resume.pdf`, `applications/Testco/cover_letter.tex`,
   `applications/Testco/cover_letter.pdf`, and `applications/Testco/cover_letter.txt`
   all exist.

2. **`resume.pdf` is exactly 1 page.** The page count reported by
   `compile_latex.ps1` (parsed from the LaTeX `.log` "Output written on … (N page…)"
   line) is exactly `1` for `--length 1`.

3. **`resume.tex` uses the `profile.yml` role strings verbatim.** It contains the
   literal string `Sample Dev` and both company names exactly as written in
   `example/resume_sections/profile.yml` `conventions.roles` — `Acme Corp` and
   `Globex Pty Ltd`.

4. **`resume.tex` has one experience `\resumeSubheading` per role.** The count of
   `\resumeSubheading` occurrences inside the `Industrial Experience` section
   (between `\section{Industrial Experience}` and the next `\section{…}`) equals the
   number of entries in `profile.yml` `conventions.roles` (fixture: 2).

5. **`resume.tex` Education section lists every institution.** For each entry in
   `profile.yml` `conventions.education`, the entry's `institution` string appears in
   `resume.tex` within the `Education` section (fixture: `Example University`).

6. **No forbidden technology.** Neither `resume.tex` nor `cover_letter.tex` contains
   the word `Rust` (case-insensitive). `example/resume_sections/factual-bounds.md`
   forbids claiming Rust and the JD does not ask for it.

7. **`cover_letter.tex` names no university.** `cover_letter.tex` does not contain
   `Example University` (or any other `conventions.education` institution string) —
   `factual-bounds.md`: no university mention in cover letters.

8. **`cover_letter.txt` leads with the subject.** The first non-empty line of
   `applications/Testco/cover_letter.txt` starts with `Subject:`.

9. **`cover_letter.tex` subject line has no dangling reference.** The synthetic JD
   carries no requisition ID, so the subject line contains neither the literal
   `{{REQ_ID}}` placeholder nor an empty `Ref / Req ID:` / `Ref:` fragment.

10. **No aux files left.** After the skill finishes, `applications/Testco/` contains
    no `.aux`, `.log`, or `.out` file.

11. **The `generate` report cites a `file:line` for every metric/skill claim.** The
    skill's step-12 report contains a table (or list) in which every metric and every
    named skill used in `resume.tex` / `cover_letter.tex` is paired with a
    source-of-truth citation of the form `<relative/path>:<line>` that resolves to a
    real line under `example/resume_sections/` (e.g. `introduction.md:5`,
    `companies/acme.md:11`). No metric appears in the résumé that is not recorded in
    the source of truth (in particular, the résumé introduces no numeric performance
    figure beyond the "4+ years" experience statement traceable to
    `introduction.md`).

12. **`analysis.md` was honoured, not overridden.** `analysis.md` `## Fit` for this
    JD is `stretch` (not `hard-mismatch`), so generation proceeds. The healthcare
    interoperability (HL7/FHIR) gap and the named-iPaaS-platform gap from
    `analysis.md` `## Criteria → Evidence` are **not** papered over: `resume.tex` and
    `cover_letter.tex` do not claim HL7, FHIR, MuleSoft, Dell Boomi, or Workato
    experience.
