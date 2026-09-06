# Render contract + silent-failure guard (generic)

`render_pdf.py` renders an HTML template + a JSON data file to a PDF. The template
splices the data at the single token `{{DATA_JSON}}` (both bundled templates use it;
there is no `--placeholder` argument).

Invocation:

    uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py \
        --template-path <resolved template> --data-path <dir>/tmp/<name>.data.json \
        --out-path <dir>/<name>.pdf

## CLI contract

- **Success:** prints `OK: <pdf> (N page[s])` to stdout, exits 0.
- **Failure:** prints `Render failed:\n<log tail>` to stderr, exits 1.
- **Missing required argument:** exits 2.

Non-zero exit ⇒ failure. Surface the `Render failed:` text, keep the `.data.json`,
do **not** run `compress_pdf.py`, do **not** claim success. Fix the data (usually an
invalid JSON string or a wrong shape) and re-render.

## Silent-failure guard

`render_pdf.py` exits 0 even when the data is unusable — it draws a visible
"Invalid resume JSON: …" / "Invalid cover letter JSON: …" page for a JSON scalar or
`null`, and a near-empty page for valid-JSON-but-wrong-shape (no `sections`). After
every successful render, extract the PDF text:

    uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/extract_cv.py <dir>/<name>.pdf

and confirm **both**:
- it does **not** contain `Invalid resume JSON` / `Invalid cover letter JSON`; and
- it **does** contain the candidate `name`, plus — for the résumé — at least one
  company name from the experience section, or — for the cover letter — the
  `subject` text.

Ligature clusters (`ft`, `fi`) and a leading `+` do not survive text extraction on
the bundled fonts — do not assert on strings that contain them.

If either check fails, treat it exactly like a render failure: surface it, keep the
`.data.json`, do not compress, do not claim success — fix the data and re-render.

## Page count

The integer in the `OK: … (N page[s])` line. The résumé's soft ceiling is **2**. If
it renders longer: WARN the user and list candidate trims (drop the lowest-ranked
bullet per role, shorten the intro, drop a de-emphasized skill group). Never
silently trim content to fit.
