# Integration-test assertions: `jd-intake` skill

After running the `jd-intake` skill on `example/sample-jd.md` (the synthetic
"Integration Developer" JD for Meridian Integration Partners) with company `Testco`,
retrieving against the `example/resume_sections/` source of truth (candidate "Sample
Dev"), the produced output must satisfy every assertion below.

The fixture ships no `jobapp.config.yml`, so `Get-JobAppConfig` returns the plugin
default `output_dir` of `applications/{Company}`; the resolved directory is therefore
`applications/Testco/`. Assertions are **structural** — they check file existence,
section presence, and table shape, not exact prose.

1. **Raw JD saved verbatim.** `applications/Testco/jd.md` exists and its content is
   byte-for-byte equal to `example/sample-jd.md` (no reformatting, no trimming).

2. **`analysis.md` has all eight `##` sections, in order.**
   `applications/Testco/analysis.md` exists and contains, in this order, exactly
   these level-2 headings:
   `## Essential`, `## Desirable`, `## Responsibilities`, `## Keywords`,
   `## Language / Stack emphasis`, `## Criteria → Evidence`, `## Fit`, `## Framing`.

3. **`## Criteria → Evidence` table is honest about the gaps.** The table under
   `## Criteria → Evidence` has a `Criterion | Evidence (file:line) | Status` header
   and one row per essential criterion, and:
   - (a) The row for essential criterion 5 (working knowledge of HL7 v2 / FHIR
     healthcare-interoperability standards) has Status `gap`. This is the one hard,
     unbridgeable gap — nothing in `example/resume_sections/` touches healthcare
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
     actually exists under `example/resume_sections/` (e.g. `companies/acme.md:11`,
     `companies/globex.md:12`, `introduction.md:6`). No `met`/`partial` row has an
     empty or invented evidence cell.
   - (e) No row is marked `met` for a technology absent from the source of truth. In
     particular, nothing referencing Rust appears as a `met` criterion
     (`example/resume_sections/factual-bounds.md` forbids claiming Rust, and the JD
     does not ask for it).

4. **`## Fit` is `stretch`.** The `## Fit` section's classification token is exactly
   `stretch` (lowercase) — not `strong`, not `hard-mismatch`. Three of five
   essentials are met and only one criterion is a true gap, but the iPaaS shortfall
   and the healthcare-interop gap keep it below `strong`; the candidate's four-plus
   years of hands-on systems-integration work (REST APIs, message pipelines,
   third-party carrier/ERP integration) is a credible transferable story, so it is
   not a `hard-mismatch`.
