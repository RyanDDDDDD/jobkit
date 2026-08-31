# Integration-test assertions: `review-application` skill

After running the `review-application` skill for a company whose per-application
directory — referred to below as `<dir>` — already contains `resume.data.json`,
`cover_letter.data.json`, `analysis.md`, and `cover_letter.txt` (produced by `generate`
against the `example/resume_sections/` source of truth, candidate "Sample Dev"), the
result must satisfy every assertion below.

`<dir>` is whatever directory the operator points the skill at (e.g. a temp
`applications/Testco/`). Assertions are phrased relative to it. They are
**structural** — file existence, heading presence and order, and substring checks,
not exact prose.

1. **`review.md` exists with the three sections, in order.** `<dir>/review.md`
   exists and contains the headings `## Pass`, `## Flag`, and `## Fix`, in that
   order (each on its own line, `## Pass` before `## Flag` before `## Fix`).

2. **A factual-bounds violation is flagged with the rule quoted.** If
   `resume.data.json` contains a claim that violates a rule in
   `example/resume_sections/factual-bounds.md` — the canonical test case is the word
   `Rust` (case-insensitive) anywhere in `resume.data.json` (a `stack` entry or a
   `bullets[]` string), which the bound "Never claim Rust. Sample Dev has never used
   Rust." forbids and the JD does not ask for — then `review.md` reports it under
   `## Flag` (not `## Pass`, not `## Fix`), and the offending text **and** the
   violated bound (quoted verbatim from `factual-bounds.md`) both appear in the
   `## Flag` section.

3. **A `profile.yml` disagreement is listed under `## Fix`.** If a company name, job
   title, or employment date in `resume.data.json` disagrees with
   `example/resume_sections/profile.yml` `conventions.roles` (canonical test case: a
   role's end date changed, e.g. `items[].dates` ending `Nov. 2023` where
   `profile.yml` says `Dec. 2023`), then `review.md` lists it under `## Fix` with an
   explicit before/after that rewrites the JSON string to match `profile.yml`
   verbatim (`profile.yml` wins).

4. **A stale `cover_letter.txt` is reported.** If `<dir>/cover_letter.txt` is older
   than `<dir>/cover_letter.data.json` (its modification time precedes the
   `.data.json`'s), or a freshly regenerated scratch copy differs from it,
   `review.md` reports it (under `## Fix` or `## Flag`) as needing regeneration and
   names `scripts/cover_letter_to_txt.ps1` as the fix.

## Manual walkthrough (recorded 2026-09-01)

Performed once, by hand, against a throwaway `applications/Testco/` temp dir (deleted
afterward):

1. Regenerated `resume.data.json` / `cover_letter.data.json` / `cover_letter.txt` for
   company `Testco` from `example/resume_sections/` and an `analysis.md` whose
   `## Fit` is `stretch` (essentials 1–3 `met`, 4 and 5 `gap` — dedicated iPaaS and
   HL7/FHIR). Both PDFs rendered to exactly 1 page via `scripts/render_pdf.ps1`.
2. Seeded two defects into `resume.data.json`: (a) a `Rust` entry in the Globex
   `stack` plus a "Built high-throughput claims-reconciliation components in Rust"
   bullet under Globex; (b) the Globex `dates` end changed from `Dec. 2023` to
   `Nov. 2023`. Edited one word in `cover_letter.data.json` and left
   `cover_letter.txt` untouched, making the `.txt` stale by both mtime and content.
3. Walked `skills/review-application/SKILL.md` by hand and wrote `<dir>/review.md`.

Result — all four assertions held:

| # | Assertion | Result |
|---|---|---|
| 1 | `review.md` has `## Pass` → `## Flag` → `## Fix` in order | PASS |
| 2 | Rust flagged under `## Flag`, bound "Never claim Rust. Sample Dev has never used Rust." quoted alongside both offending lines | PASS |
| 3 | Globex `Nov. 2023` vs `profile.yml` `Dec. 2023` under `## Fix` with before/after | PASS |
| 4 | `cover_letter.txt` reported stale (mtime older than `.data.json` and regenerated copy differs) under `## Fix` with the `cover_letter_to_txt.ps1` command | PASS |

Temp dir deleted; nothing committed from it.
