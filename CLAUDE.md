# CLAUDE.md — Project Guidance

This repository builds a **complete technical study guide**: *Code Execution as an Agent's Action Space*. The specification is the file **`agent_code_execution_study_guide.md`** at the repo root. That file is the index; this file is the operating manual for how to fill it in.

Read `agent_code_execution_study_guide.md` (the whole thing, at least the part index and Appendix G) before doing any work. Treat **Appendix G — Chapter Template** as the required structure for every chapter.

---

## The Golden Rules (non-negotiable)

1. **One chapter at a time. Finish it completely, then STOP and wait for human review.** Never start the next chapter in the same run. Completing a chapter is a stopping point, not a checkpoint you blow through.
2. **Every chapter must be *complete* before we move on.** "Complete" means every section of the Definition of Done below exists and the code and notebooks actually run.
3. **Run everything you write.** No code, snippet, or notebook ships unless you have executed it in this repo's environment and seen it succeed. If it can't run, it isn't done.
4. **Never fabricate.** No invented APIs, function signatures, library behavior, benchmark numbers, citations, or paper claims. If you're unsure whether an API exists or behaves as written, *run it* or look it up. If you cannot verify, say so in the text rather than guessing.
5. **Follow the pedagogical arc** (see below): basic → why/what → detail → advanced, in that order, every chapter.
6. **Extend the backbone; don't restart.** From Chapter 5 onward there is one evolving agent. Each chapter builds on the previous chapters' code. Do not re-scaffold a fresh agent each chapter.
7. **Defer containment to the sibling guide.** This project is about agent *behavior* (the loop, tools, context). Runtime isolation/sandboxing belongs to the sibling guide *Code Execution Sandboxing for AI Agents*. When a chapter touches safety/isolation, teach the agent-side concern and explicitly hand off to the sandbox guide rather than reimplementing it.

---

## Repository Structure

```
.
├── CLAUDE.md                              # this file
├── agent_code_execution_study_guide.md    # the spec / chapter index
├── PROGRESS.md                            # chapter status tracker (source of truth for "what's next")
├── README.md                              # how to run the repo
├── requirements.txt / pyproject.toml      # pinned dependencies
├── src/
│   └── backbone_agent/                    # the single evolving agent (grows across chapters)
└── chapters/
    ├── ch01-what-is-an-agent/
    │   ├── README.md                      # the chapter (all Appendix G sections)
    │   ├── code/                          # runnable modules for this chapter
    │   └── notebooks/                     # runnable .ipynb labs
    ├── ch05-minimal-code-executing-agent/
    │   ├── README.md
    │   ├── code/
    │   └── notebooks/
    └── ...
```

- One folder per chapter, zero-padded (`ch01`, `ch05`, `ch23`).
- The chapter's prose lives in its `README.md` and follows Appendix G exactly.
- Shared, evolving agent code lives in `src/backbone_agent/`. Chapter code that extends the backbone imports from there; the chapter's `code/` holds chapter-specific demos, labs, and the deliverable.

---

## Definition of Done (a chapter is not finished until ALL of these are true)

The chapter's `README.md` contains every Appendix G section, in order:

1. Concept
2. Why This Matters for Code-Executing Agents
3. Mental Model
4. Architecture (place in the loop / context)
5. Detailed Explanation
6. Minimal Implementation
7. Hands-on Lab
8. Failure Lab
9. Instrumentation (what to log / trace / measure)
10. Design Considerations
11. Common Mistakes
12. Comparisons / Alternatives
13. Review Questions
14. Chapter Summary
15. Chapter Deliverable
16. Further Reading

Plus:

- [ ] All code in `code/` runs successfully (you executed it and pasted/observed real output).
- [ ] The notebook in `notebooks/` executes top-to-bottom without errors (run it; commit it executed).
- [ ] The **Chapter Deliverable** named in the spec actually exists as a runnable artifact.
- [ ] Any claim about a library, API, or benchmark was verified, not assumed.
- [ ] `PROGRESS.md` is updated and the work is committed with a clear message.
- [ ] The chapter builds on prior chapters where the spec says it should (backbone continuity).

---

## The Pedagogical Arc (every chapter, in this order)

Write each chapter so a smart reader who is new to the specific topic can follow it start to finish:

1. **Basic + example first.** Open with the simplest possible concrete example the reader can run or picture. Show, then tell.
2. **Why + what.** Explain *why this exists* (what problem it solves, what breaks without it) and *what it actually is*. Plain language before jargon; define terms on first use.
3. **Detail.** Build up the real mechanics, the architecture, and how it sits in the agent loop or context pipeline.
4. **Advanced.** Edge cases, failure modes, production trade-offs, and the "what experts get wrong" material.

Prose is the connective tissue; runnable code and the notebook are the proof. Prefer showing a behavior by running it over asserting it.

---

## Per-Chapter Workflow

When implementing a chapter (triggered by the human, or by `/next-chapter`):

1. **Locate the chapter** in `agent_code_execution_study_guide.md` and read its Main goal, Subtopics, Fill-in pointers, Hands-on direction, and Chapter deliverable.
2. **Check `PROGRESS.md`** to confirm this is the right next chapter and to see what prior chapters produced (especially the backbone's current state).
3. **Plan briefly**: list what the chapter's code, notebook, and deliverable will be. If the plan is non-obvious or large, surface it before writing.
4. **Write the code first, run it, iterate until it works.** Build the minimal implementation, the lab, and the deliverable. Execute each. Capture real output for the prose.
5. **Build and execute the notebook.** It must run top to bottom cleanly. Commit it in executed form.
6. **Write `README.md`** following the arc and the 16 Appendix G sections, using real output from steps 4–5. No placeholder text, no "TODO", no invented results.
7. **Self-check against the Definition of Done.** Fix anything missing.
8. **Update `PROGRESS.md`** (mark the chapter done, note what changed in the backbone, note anything the human should review).
9. **Commit** with message `ch<NN>: <chapter title>`.
10. **STOP.** Summarize what you built, flag anything uncertain or worth a human decision, and wait. Do not start the next chapter.

---

## Backbone Agent Continuity

- `src/backbone_agent/` is the one agent that grows from a ~40-line loop (Ch 5) into the capstone.
- Each chapter that advances the agent edits the backbone in place and keeps it working. Never fork a parallel copy.
- Keep the backbone runnable at the end of every chapter: there should always be a `python -m backbone_agent ...` (or equivalent) entry point that works.
- When a chapter adds a capability, add a short regression check so later chapters don't silently break it.

---

## Code Standards

- Python is the default. Use a virtual environment; pin versions in `requirements.txt`.
- Prefer standard library and widely-used, current packages. Verify any package/API you're unsure about by running it.
- Keep example code readable and teaching-oriented: clear names, short functions, comments that explain *why*, not *what*.
- Every runnable file should be executable on its own (a `__main__` or a clear "how to run" line at the top).
- Handle the model/API layer behind a thin interface so examples don't hard-depend on one provider; read API keys from environment variables, never hard-code secrets.
- If an example needs a model call, make it cheap and deterministic where possible, and keep it runnable with a clearly documented setup.

## Notebook Standards

- One primary notebook per chapter in `notebooks/`, named for the chapter.
- Structure the notebook to mirror the arc: a runnable basic example near the top, then progressively deeper cells.
- Every cell must execute without error. Commit the notebook with outputs present.
- Notebooks illustrate and let the reader experiment; they are not a dumping ground for untested code.

---

## Environment & Setup

- On first run, create the environment and `requirements.txt`, write `README.md` with exact setup/run instructions, and verify a trivial example runs before building chapter content.
- Record every dependency you add, with a pinned version, at the time you add it.
- If a chapter needs a new dependency, add it to `requirements.txt` and note it in that chapter's README.

---

## Progress Tracking

- `PROGRESS.md` is the source of truth for what's done and what's next. Keep it current every chapter.
- Suggested format: a table of `Chapter | Title | Status (todo/in-progress/done) | Notes`, plus a short "Backbone state" section describing the agent's current capabilities.
- Git history is the second tracker: one commit per completed chapter, message `ch<NN>: <title>`.
- Because context resets between sessions, `PROGRESS.md` + the guide + this file must be enough to resume cold with no other memory.

---

## Accuracy & Sourcing

- For the Further Reading and Comparisons sections, name real papers, frameworks, and tools (see the spec's Appendices B and F). Do not invent titles, authors, or results.
- When you reference a framework's behavior (e.g., how a library exposes tools), verify it — read its docs or run it — before describing it as fact.
- If something can't be verified in-session, write it as "worth verifying" rather than stating it as settled.
- Benchmark or performance numbers must come from a run you did or a source you can name. Never fabricate figures.

---

## What "good" looks like

A finished chapter reads like a great textbook section: it opens with something concrete you can run, explains why it matters in plain terms, builds to real depth, ends with the advanced/edge material, and every piece of code in it actually works because you ran it. A reader could follow only that chapter's README and notebook and come away able to build the thing.
