# Render contract + silent-failure guard (generic)

`render_pdf.py` renders an HTML template + a JSON data file to a PDF. The template
splices the data at the single token `{{DATA_JSON}}` (both bundled templates use it;
there is no `--placeholder` argument).

Invocation:

    uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py \
        --template-path <resolved template> --data-path <dir>/tmp/<name>.data.json \
        --out-path <dir>/<name>.pdf \
        [--template-path … --data-path … --out-path …]

The three path flags are repeatable and zipped positionally; one browser launch
renders every job.

## CLI contract

- **Success:** prints `OK: <pdf> (N page[s])` to stdout, exits 0.
- **Failure:** prints `Render failed [<pdf>]:\n<log tail>` to stderr, exits 1.
- **Batch:** exits 0 only if every job succeeded; one `OK:` / `Render failed [<pdf>]:`
  line per job, in input order. **Flag-count mismatch:** exits 2.
- **Missing required argument:** exits 2.

Non-zero exit ⇒ failure. Surface the `Render failed [<pdf>]:` text, keep the
`.data.json`, do **not** run `compress_pdf.py`, do **not** claim success. Fix the
data (usually an invalid JSON string or a wrong shape) and re-render.

## Silent-failure guard

`render_pdf.py` exits 0 even when the data is unusable — it draws a visible
"Invalid resume JSON: …" / "Invalid cover letter JSON: …" page for a JSON scalar or
`null`, and a near-empty page for valid-JSON-but-wrong-shape (no `sections`).

This guard is now `verify_application.py`'s `resume-roundtrip` / `cover-roundtrip`
checks, run in step 9a against the PDFs already on disk — no re-render. A failure
there is treated exactly like a render failure (surface it, keep the `.data.json`,
do not compress, do not claim success).

Ligature clusters (`ft`, `fi`) and a leading `+` do not survive text extraction on
the bundled fonts — do not assert on strings that contain them.

## Page count

The integer in the `OK: … (N page[s])` line. The résumé's soft ceiling is **2**. If
it renders longer: WARN the user and list candidate trims (drop the lowest-ranked
bullet per role, shorten the intro, drop a de-emphasized skill group). Never
silently trim content to fit. `verify_application.py` also enforces this
(`page-budget`: résumé ≤ 2, cover letter == 1).
