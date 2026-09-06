# Workflow Rules (Generic)

Stable, candidate-agnostic rules for the job-application workflow. Skills link here
instead of copying the rules inline. Anything specific to one person's history
belongs in that user's `factual-bounds.md`, not here.

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

## 4. `factual-bounds.md` is a hard constraint

`<sourceDir>/factual-bounds.md` is the user's own "never claim" list (technologies
never used, per-employer stack scoping, metrics not to invent, whether the
university may be named in a cover letter, …). Load it verbatim. On any conflict
between what the JD pushes for and a bound: **stop and ask the user.** Do not
silently comply and do not silently omit.

## 5. Claims are pressure-tested in the interview, not gated at generation

`generate` does not require a per-bullet citation trail. Instead,
`interview mock technical` grills every number and every claim on the résumé — how
it was measured, its boundaries, what breaks at 10×, the candidate's personal
contribution vs the team's. That is where a weak claim surfaces.

## 6. Output language

All generated application content (résumé PDF, cover letter, plain-text and
form-answer variants) is English by default, regardless of conversation language.
`apply --lang zh` is the one sanctioned exception: a Chinese résumé and cover letter
produced by faithfully translating the English source-of-truth content — never
inventing detail to smooth a sentence. A skill's own report / prep text stays
English even under `--lang zh`.

## 7. Save the job description

Whenever a résumé or cover letter is generated for a role, the verbatim JD is saved
in the same output directory as `jd.md`. Later interview-prep steps read it there.

## 8. Experienced-hire default (configurable)

By default treat the candidate as an experienced hire: omit GPA, grades, class rank,
and academic distinctions; lead with professional work experience; reduce education
to institution, credential, and dates. A user targeting new-grad / academic roles
can override this in `profile.yml`.

## 9. Cover letter core content

Every cover letter establishes, in prose: (1) total professional
software-engineering experience duration; (2) the specific companies worked at by
name; (3) the specific business domains / sectors; (4) the specific technologies,
each tied to the company where it was used, consistent with the source-of-truth
records. Keep it to one page. Per-user constraints (e.g. whether the university may
be named) live in `factual-bounds.md`.

## 10. Redundancy control

Avoid duplicate or near-duplicate bullets within a document and across the résumé
and cover letter. When merging new material into the source of truth, collapse
bullets that state the same accomplishment in different words into one canonical
bullet.

## 11. Mock interviews stay grounded and balanced

Base mock-interview questions strictly on the candidate's actual résumé and source
of truth. Feedback must name what went well **and** concrete weaknesses — never
purely positive.
