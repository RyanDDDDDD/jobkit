# Workflow Rules (Generic)

Stable, candidate-agnostic rules for the job-application workflow. The skills link
here instead of copying these rules inline. Anything specific to one person's history
(technologies they have never used, per-employer stack scoping, cloud-provider
sub-service scopes) does **not** belong here — it belongs in that user's
`resume_sections/factual-bounds.md`.

---

## 1. Source of truth is authoritative

- The de-duplicated markdown/YAML files under the source-of-truth directory
  (default `resume_sections/`) are the single source of truth for achievements,
  skills, employment history, education, and contact details.
- When tailoring a resume or cover letter to a job description (JD), **retrieve
  first**: pull the relevant existing history points, company facts, and
  achievements that match the JD before drafting. Do not draft from memory of the
  conversation.
- Only highlight and reword material that already exists in the source of truth.
  Do not add skills, employers, projects, tools, or experiences that are not
  recorded there.

## 2. No hallucinated skills or metrics

- Never introduce a skill, framework, or tool that is not present in the source of
  truth just because the JD asks for it.
- Never invent numeric data, metrics, or performance figures (uptime percentages,
  latency reductions, cost savings, team sizes, etc.). Use only numbers explicitly
  recorded in the source of truth or supplied by the user for this application.
- If a quantified claim would strengthen a bullet but no real number exists, use a
  qualitative description ("significantly improved throughput") or leave it out and
  ask the user for the real figure.
- Keep every technology stack tied to the company or project it actually belongs
  to. Do not shift or blend tools between employers to improve JD match.

## 3. Redundancy control

- Avoid duplicate or near-duplicate bullet points within a document and across the
  resume and cover letter.
- When merging new material into the source of truth, collapse bullets that state
  the same accomplishment in different words into one canonical bullet.

## 4. English-only output

All generated application content (resume PDF/LaTeX, cover letter, plain-text
versions, Word text) must be in English, regardless of the conversation language.

## 5. Save the job description

Whenever a resume or cover letter is generated for a role, save a copy of the JD in
the same output directory (e.g. `jd.md`). Later interview-preparation steps read it
from there.

## 6. Experienced-hire default (configurable)

By default, treat the candidate as an experienced hire: omit GPA, academic grades,
class rank, and academic distinctions from the resume and cover letter; lead with
professional work experience and engineering achievements. Education is reduced to
institution, credential, and dates.

This is a **default, not a hard rule**. A user targeting new-graduate or
academic roles can override it via a profile setting so that grades and coursework
are included.

## 7. Cover letter core content

Every cover letter should establish, in prose:

1. **Experience duration** — state the total professional software-engineering
   experience (e.g. "over three years").
2. **Named companies** — name the specific companies the candidate has worked at.
3. **Business domains** — name the specific sectors and problem domains worked in
   (e.g. supply chain, warehousing, logistics, payments, healthcare).
4. **Company-tied tech stacks** — name the specific technologies used, each tied to
   the company where it was used, consistent with the source-of-truth records.

Keep the letter to one page. Additional per-user constraints (for example, whether
the university may be named) live in that user's `factual-bounds.md`.

## 8. Mock interviews stay grounded and balanced

- Base mock-interview questions strictly on the candidate's actual resume and
  source of truth.
- Feedback must be balanced: name what went well **and** concrete weaknesses. Do
  not give purely positive or flattering responses.
