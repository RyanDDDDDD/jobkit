# Render contract + silent-failure guard (generic)

`jobkit render` renders an HTML template + a JSON data file to a PDF. The template
splices the data at the single token `{{DATA_JSON}}` (both bundled templates use it;
there is no `--placeholder` argument).

Invocation:

    jobkit render \
        --kind <resume|cover_letter> --data <dir>/tmp/<name>.data.json --out <dir>/<name>.pdf \
        [--kind … --data … --out …]

    (`--template <path>` per job overrides the theme; otherwise the workspace
    `resume_template` from `jobapp.config.yml` selects
    `templates/<theme>/{resume,cover_letter}.html`. A repo-level
    `<root>/templates/resume.html` / `cover_letter.html` is picked up
    automatically and wins over the bundled theme.)

The `--kind` / `--data` / `--out` flags are repeatable and zipped positionally; one
browser launch renders every job.

## CLI contract

- **Success:** prints `OK: <pdf> (N page[s])` to stdout, exits 0.
- **Failure:** prints `Render failed [<pdf>]:\n<log tail>` to stderr, exits 1.
- **Batch:** exits 0 only if every job succeeded; one `OK:` / `Render failed [<pdf>]:`
  line per job, in input order. **Flag-count mismatch:** exits 2.
- **Missing required argument:** exits 2.

Non-zero exit ⇒ failure. Surface the `Render failed [<pdf>]:` text, keep the
`.data.json`, do **not** run `jobkit compress`, do **not** claim success. Fix the
data (usually an invalid JSON string or a wrong shape) and re-render.

## Silent-failure guard

`jobkit render` exits 0 even when the data is unusable — it draws a visible
"Invalid resume JSON: …" / "Invalid cover letter JSON: …" page for a JSON scalar or
`null`, and a near-empty page for valid-JSON-but-wrong-shape (no `sections`).

There is no separate roundtrip check anymore — a corrupted render still shows up
as the visible error page inside the PDF itself; open the PDF (or run
`jobkit extract-cv <pdf>`) to confirm.

Ligature clusters (`ft`, `fi`) and a leading `+` do not survive text extraction on
the bundled fonts — do not assert on strings that contain them.

## Page count

The integer in the `OK: … (N page[s])` line. The résumé's soft ceiling is **2**. If
it renders longer: WARN the user and list candidate trims (drop the lowest-ranked
bullet per role, shorten the intro, drop a de-emphasized skill group). Never
silently trim content to fit.

## Compress + cover-txt + Report (automatic)

A successfully-rendered job is compressed in place (`jobkit compress`'s
algorithm, run internally — never touches a PDF that failed to render). A
`cover_letter` job additionally gets a sibling `.txt` (same directory, same
basename, `.txt` extension) written from its `.data.json`. Both are
best-effort: a `WARN: compress failed for <pdf>: …` or `WARN: cover-txt failed
for <pdf>: …` line on stderr does not change the job's `OK`/`Render failed`
status or the command's exit code — the PDF is still a valid deliverable.

After processing every job, `jobkit render` prints a plain-text `Report:`
block to stdout: each job's status/page-count/lang/density, whether the
résumé's `sections` include a "Selected Projects" title, the résumé's
experience order, and any `## Criteria → Evidence` row in the sibling
`analysis.md` (found by walking up from the `.data.json`'s directory) whose
Status is `gap`. This replaces the deleted `jobkit verify` as the place a
`page-budget`-style summary comes from — it is descriptive, not a gate.
