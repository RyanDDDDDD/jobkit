# ATS & Resume Quality Checklist

Run through this before producing any resume PDF. It keeps the document parseable by
applicant-tracking systems (ATS) and readable by a human screener.

---

## Layout

- [ ] **Single-column layout.** No sidebars. Multi-column resumes are frequently
      reordered or scrambled by ATS text extraction. The bundled
      `templates/resume.html` is single-column with standard headings by
      construction — a repo-level `templates/` override must keep that.
- [ ] **The generated PDF is text-extractable.** `render_pdf.py` produces PDFs
      whose text `pdftotext -enc UTF-8` round-trips, CJK included. Never bake résumé
      text into an image, and avoid multi-column layouts or content trapped in
      floats — both defeat ATS extraction.
- [ ] **No content locked inside tables, text boxes, headers/footers, or images.**
      All text — including contact details, dates, and skills — sits in the normal
      document body. A screen reader or copy-paste must recover every word in order.
- [ ] **Standard, recognisable fonts** at a readable size (roughly 10–12pt body).
- [ ] **Length: within the soft ceiling of 2 pages.** Never let content overflow
      onto a near-empty extra page — trim to fit the last full page. (The page
      budget is a fixed soft 2; résumé density is the `conventions.density` key.)

## Section headings

- [ ] Use conventional headings an ATS maps to known fields: `Summary` /
      `Profile`, `Experience` / `Work Experience`, `Skills`, `Education`,
      `Projects`. Avoid creative renames ("Where I've Made an Impact").
- [ ] Headings appear in a consistent order and visual style throughout.

## Experience entries

- [ ] Each role shows **company, job title, location, and real start/end dates**
      (month + year, or year). Use `Present` for a current role. No vague
      "2 years" in place of dates; no fabricated dates.
- [ ] Date formatting is identical across every entry.
- [ ] Roles are in reverse-chronological order (most recent first), unless a
      documented relevance-ordering decision overrides it.

## Bullet points

- [ ] Every bullet is **verb-first** and starts with a strong past-tense action
      verb for past roles ("Built", "Migrated", "Diagnosed").
- [ ] **Tense is consistent**: past tense for finished work, present tense only for
      an ongoing responsibility in a current role — and applied the same way in
      every entry.
- [ ] Bullets are **quantified where a real number exists** (throughput, request
      volume, dataset size, team size). Where no real metric exists, describe the
      outcome qualitatively rather than inventing a figure.
- [ ] Each bullet states an outcome or impact, not just a task performed.
- [ ] No duplicate or near-duplicate bullets within or across sections.

## Keyword alignment

- [ ] The concrete skills, tools, and domain terms from the JD's essential
      criteria appear **verbatim** in the resume **when they are genuinely part of
      the candidate's background** (e.g. write "REST APIs" if the JD says "REST
      APIs" and the candidate has built them).
- [ ] Do **not** keyword-stuff. Every term must be backed by real experience in the
      source of truth. Missing a genuine gap is expected; papering over it is not.
- [ ] Spell out an acronym once, then use whichever form the JD uses.

## File naming & output

- [ ] Output file name is professional and identifies the candidate and document
      type (e.g. `Jane_Doe_Resume.pdf`, `Jane_Doe_Cover_Letter.pdf`). No
      `resume_final_v3(2).pdf`.
- [ ] The resume, cover letter, and a copy of the JD land in the same
      per-application output directory.
- [ ] The PDF is text-based (selectable text), not a flattened scan or image.
