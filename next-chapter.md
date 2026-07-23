---
description: Implement the next incomplete chapter of the study guide, fully, then stop for review.
---

You are advancing the study guide project defined in `agent_code_execution_study_guide.md` and governed by `CLAUDE.md`. Read both if they are not already in context.

Target chapter: **$ARGUMENTS**
- If a chapter number was given above, implement that chapter.
- If it is empty, open `PROGRESS.md` and implement the **next chapter whose status is not `done`**.

Then do exactly this, and only this:

1. Read the target chapter's entry in `agent_code_execution_study_guide.md` (Main goal, Subtopics, Fill-in pointers, Hands-on direction, Chapter deliverable).
2. Check `PROGRESS.md` and `src/backbone_agent/` for the current state so you build *on top of* prior chapters (backbone continuity).
3. State a short plan for this chapter's code, notebook, and deliverable.
4. Write the code, **run it**, and iterate until it works. Capture real output.
5. Build and **execute** the chapter notebook top-to-bottom; commit it executed.
6. Write the chapter `README.md` following the pedagogical arc (basic + example → why/what → detail → advanced) and all 16 Appendix G sections, using the real output you captured. No placeholders, no invented results, no unverified API claims.
7. Verify the chapter against the Definition of Done in `CLAUDE.md`. Fix any gaps.
8. Update `PROGRESS.md` (mark done, note backbone changes, flag anything for human review).
9. Commit with message `ch<NN>: <chapter title>`.
10. **STOP.** Summarize what you built, list anything uncertain or needing a decision, and wait for review. Do **not** begin the next chapter.

Hard rules: one chapter only; run everything you write; never fabricate APIs, numbers, or citations; defer runtime containment/sandboxing to the sibling guide.
