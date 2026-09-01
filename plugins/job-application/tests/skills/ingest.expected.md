# Integration-test assertions: `ingest` skill

After running the `ingest` skill against `tests/fixtures/raw_cvs/` (two synthetic CVs for
"Sample Dev": Acme Corp SWE Jan 2024–Present, Globex Pty Ltd Junior Developer
Feb 2022–Dec 2023, Example University BCS), the produced source-of-truth directory
— referred to below as `<OUTPUT_DIR>` — must satisfy every assertion.

`<OUTPUT_DIR>` is whatever directory the test points the skill at (Task 8 wires a
real temp path). Assertions are phrased relative to it, not to a fixed folder.

1. `<OUTPUT_DIR>/companies/acme.md` exists and contains at least one line that
   starts with `- ` (a bullet).

2. `<OUTPUT_DIR>/companies/globex.md` exists.

3. `<OUTPUT_DIR>/profile.yml` exists and parses as YAML, with:
   - `name` equal to `Sample Dev`
   - `conventions.roles` a non-empty list whose entries each have
     `company`, `title`, `start`, `end`, `location`
   - `conventions.education` a non-empty list

4. `<OUTPUT_DIR>/factual-bounds.md` exists (seeded, heading present; body may be
   just the "add rules as you correct drafts" comment).

5. No duplicated bullet text across the two company files: no identical bullet
   sentence (normalised: trimmed, lower-cased, leading `- ` removed) appears in both
   `<OUTPUT_DIR>/companies/acme.md` and `<OUTPUT_DIR>/companies/globex.md`. The two
   source CVs describe the same roles in overlapping wording; the skill must
   collapse, not duplicate.

6. No-hallucination check: for every non-blank list item in
   `<OUTPUT_DIR>/skills.md` (a line starting with `- `, ignoring the `###` category
   headers), strip any trailing parenthetical `(...)` and trim; the remaining text
   must be a case-insensitive substring of the concatenation of the ingest input
   CV files (`tests/fixtures/raw_cvs/*.md`) and the produced `<OUTPUT_DIR>/companies/*.md`
   + `<OUTPUT_DIR>/projects/*.md` files. Nothing in `skills.md` may be invented
   beyond what the CVs and produced company/project files contain.
