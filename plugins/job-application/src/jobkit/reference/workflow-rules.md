# Workflow Rules (Generic)

Stable, candidate-agnostic rules for the job-application workflow. Skills link here
instead of copying the rules inline. Anything specific to one person's history
belongs in that user's own `CLAUDE.md` / `AGENTS.md`, not here.

---

## 1. The source of truth is user-authored fact

The markdown/YAML files under the source-of-truth directory (default
`resume_sections/`) and `profile.yml` are the candidate's own record of what they
have done. The tool does not second-guess whether an entry is accurate — that is the
user's call and the user's risk. When tailoring an application, use any of it
freely.

**Retrieve first.** Pull the relevant recorded history, company facts, and
achievements that match the job description before drafting. Do not draft from
memory of the conversation.

## 2. Reframing is the job, not a violation

Selecting, re-weighting, re-languaging, and combining recorded material to fit a JD
is expected: mapping a bullet onto JD keywords, leading with a transferable angle,
describing a recorded pipeline in more JD-aligned wording than the source file uses,
combining two real bullets into one. The source of truth not phrasing something the
JD's way is never a reason to exclude it or to mark a criterion a gap.

## 3. The one prohibition: zero-basis additions

Never put a technology, tool, domain, employer, or number on the résumé or cover
letter that appears **nowhere** in the source of truth. That is the tool inventing,
not the user asserting. A genuine gap, stated honestly, is the expected outcome for
some criteria.

## 4. The user's own CLAUDE.md / AGENTS.md is a hard constraint

jobkit does not manage a separate "never claim" rules file. A user's own "never
claim" list (technologies never used, per-employer stack scoping, metrics not to
invent, whether the university may be named in a cover letter, …) lives in their
workspace `CLAUDE.md` or `AGENTS.md`, which every skill run already loads
automatically — there is nothing extra to read. On any conflict between what the
JD pushes for and a constraint stated there: **stop and ask the user.** Do not
silently comply and do not silently omit.

## 5. Claims are pressure-tested in the interview, not gated at generation

`apply` does not require a per-bullet citation trail. Instead,
`interview mock technical` grills every number and every claim on the résumé — how
it was measured, its boundaries, what breaks at 10×, the candidate's personal
contribution vs the team's. That is where a weak claim surfaces.

## 6. Output language

Workspace `jobapp.config.yml` `lang` (`en` | `zh`) is set at setup and is the
default for every generated application document (résumé PDF, cover letter,
plain-text and form-answer variants) and for interview prep. `apply --lang` /
`interview --lang` override that default for a single run. `zh` means a Chinese
résumé and cover letter produced by faithfully translating the English
source-of-truth content — never inventing detail to smooth a sentence. This
includes structural fields, not just prose: job titles, institution/credential
names, and locations are translated to Chinese, and dates are reformatted to
Chinese numerals (e.g. `"Jan. 2024"` → `"2024年1月"`); company names and any
stock ticker stay verbatim (proper nouns). A skill's own report / prep text
follows the resolved `--lang` (except the initial English interview-playbook seed).

## 7. Save the job description

Whenever a résumé or cover letter is generated for a role, the verbatim JD is saved
in the same output directory as `jd.md`. Later interview-prep steps read it there.

## 8. Experienced-hire default (configurable)

By default treat the candidate as an experienced hire: omit GPA, grades, class rank,
and academic distinctions; lead with professional work experience; reduce education
to institution, credential, and dates. A user targeting new-grad / academic roles
can override this via `profile.yml` `conventions.include_gpa: true` (asked at
`setup`) plus a `gpa` value on the relevant `conventions.education` entry. A school
ranking (QS / U.S. News / THE) may still be shown via `conventions.education[].rank`
regardless of `include_gpa` — it is not part of the experienced-hire GPA
suppression.

## 9. Cover letter core content

Every cover letter establishes, in prose: (1) total professional
software-engineering experience duration; (2) the specific companies worked at by
name; (3) the specific business domains / sectors; (4) the specific technologies,
each tied to the company where it was used, consistent with the source-of-truth
records. Keep it to one page. Per-user constraints (e.g. whether the university may
be named) live in the user's own `CLAUDE.md` / `AGENTS.md` (§4).

## 10. Redundancy control

Avoid duplicate or near-duplicate bullets within a document and across the résumé
and cover letter. When merging new material into the source of truth, collapse
bullets that state the same accomplishment in different words into one canonical
bullet.

## 11. Mock interviews stay grounded and balanced

Base mock-interview questions strictly on the candidate's actual résumé and source
of truth. Feedback must name what went well **and** concrete weaknesses — never
purely positive.
