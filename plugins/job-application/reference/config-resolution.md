# Path resolution (generic)

Every skill that reads the source of truth or writes into a per-application
directory resolves paths the same way. Do it once, at the top of the skill run.

1. Run `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/lib/config.py`.
   It prints a JSON object with these keys:
   - `root` — the directory where `jobapp.config.yml` was found by walking up from
     the current working directory, or the current directory if none was found.
   - `source_of_truth_dir` — default `resume_sections` (a user's `jobapp.config.yml`
     often sets `private/resume_sections`).
   - `output_dir` — default `applications/{Company}` (the literal token `{Company}`
     is substituted with the application name).
   - `interview_playbook` — default `interview_playbook.md`.
   - `browser_path` — a machine hint for `render_pdf.py`, may be `null`.

2. `{sourceDir}` = `<root>/<source_of_truth_dir>`.
   If it does not exist, tell the user to run `/job-application:setup` first and stop.

3. `{dir}` (the per-application directory) = `<root>/<output_dir>` with the literal
   `{Company}` token replaced by the company name — e.g. `<root>/applications/Testco`.
   `profile.yml` has no `output_dir` key; the output directory is machine/repo config.
   Create `{dir}` (and `{dir}/tmp` where needed) with `mkdir -p` semantics.

4. **Template override:** before using a bundled template, check for a repo-level
   override under `<root>`. If `<root>/templates/<name>.html` exists, use it instead
   of `${CLAUDE_PLUGIN_ROOT}/templates/<name>.html`. `<name>` is `resume` or
   `cover_letter`.

The per-application directory layout inside `{dir}` is fixed and documented in
`${CLAUDE_PLUGIN_ROOT}/reference/output-layout.md`.
