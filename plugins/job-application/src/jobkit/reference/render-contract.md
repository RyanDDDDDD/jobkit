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

This guard is available via `jobkit verify`'s `resume-roundtrip` / `cover-roundtrip`
checks against the PDFs already on disk — no re-render — for anyone who wants to
double-check a rendered application by hand; `apply` does not run it automatically.
A failure there is treated exactly like a render failure (surface it, keep the
`.data.json`, do not compress, do not claim success).

Ligature clusters (`ft`, `fi`) and a leading `+` do not survive text extraction on
the bundled fonts — do not assert on strings that contain them.

## Page count

The integer in the `OK: … (N page[s])` line. The résumé's soft ceiling is **2**. If
it renders longer: WARN the user and list candidate trims (drop the lowest-ranked
bullet per role, shorten the intro, drop a de-emphasized skill group). Never
silently trim content to fit. `jobkit verify` can also check this by hand
(`page-budget`: résumé ≤ 2, cover letter == 1).
