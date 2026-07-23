# Code Execution as an Agent's Action Space

## Structured Study Guide and Book Index

**Purpose:** Build a deep, practical understanding of how an AI agent uses code generation and execution as its primary way of acting on the world — starting from the smallest possible reason–act–observe loop and progressing to advanced loop engineering, tool creation, and context engineering for a production-grade code-executing agent.

**Target audience:** Software engineers, ML/AI application engineers, platform and MLOps/AgentOps engineers, and architects who want to understand and build agents that write and run code.

**Primary outcome:** Design and implement an agent that, given a task, can write code, run it in a workspace with a filesystem and CLI, observe the results, create and reuse its own tools, recover from its own errors, and manage its context and budget across many steps — reliably, observably, and cheaply.

**Relationship to the sandbox guide:** This guide is the *agent-behavior* half. Its sibling — *Code Execution Sandboxing for AI Agents* — is the *containment* half. This guide answers "how and why does the agent run code, and how do I engineer the loop and context around it?" The sibling answers "how do I run that untrusted code without it escaping?" Parts XI and the capstone here deliberately hand off to the sibling rather than duplicate it. Study both to build something real; study this one first to understand the thing you are later containing.

---

# How to Use This Guide

Each chapter will eventually contain:

1. **Concept** — the idea and why it matters for code-executing agents.
2. **Mental model** — the right way to reason about it.
3. **Architecture** — how it sits in the loop, harness, or context.
4. **Minimal implementation** — the smallest code that demonstrates it.
5. **Hands-on lab** — runnable code, notebooks, and experiments to extend.
6. **Failure lab** — how it breaks, and what the failure looks like.
7. **Instrumentation** — what to log, trace, and measure.
8. **Design considerations** — production trade-offs.
9. **Review questions** — questions to confirm understanding.
10. **Chapter deliverable** — a reusable component of the capstone agent.

**Backbone project:** From Chapter 5 onward, every chapter extends one evolving agent — a single "backbone" you grow from a 40-line REPL loop into a full code-executing agent. Resist the urge to start fresh each chapter; the point is to feel each concept land on a system you already understand.

---

# Part I — Foundations: The Agent as a Code-Executing System

## Chapter 1 — What Is an Agent?

### Main goal

Establish a precise mental model of an agent as a loop that couples a language model to an environment through actions and observations.

### Subtopics and goals

- **Model, loop, tools, environment**
  - Separate the four parts and see that "agent" is the loop, not the model.
- **Autonomy spectrum**
  - Place chatbots, workflows, single-tool calls, and autonomous agents on one axis.
- **Action and observation**
  - Define the fundamental unit: the agent emits an action, the environment returns an observation.
- **The controller view**
  - Understand the model as a policy that maps context to the next action.
- **Agent versus pipeline**
  - Distinguish a fixed orchestration graph from a model-driven loop.

### Chapter fill-in pointers

- Definition of an agent.
- Loop versus workflow.
- Levels of autonomy.
- Policy and environment framing.
- Where code execution fits.
- Common misconceptions ("an agent is just a prompt").

### Hands-on direction

- Diagram three real systems (a chatbot, a RAG pipeline, a coding agent) and label model, loop, tools, and environment in each.

### Chapter deliverable

A one-page reference defining the agent loop and its vocabulary.

---

## Chapter 2 — Action Spaces: Text, JSON, and Code

### Main goal

Understand the three dominant ways an agent expresses actions and why the choice of action space shapes everything downstream.

### Subtopics and goals

- **Free-text actions**
  - Understand early prompting styles and their fragility.
- **Structured tool calling (JSON / function calling)**
  - Understand predefined tools, schemas, and their limits.
- **Code actions**
  - Understand executable code as a unified, composable action space.
- **Expressiveness comparison**
  - Compare control flow, data flow, and tool composition across the three.
- **Cost and step-count implications**
  - See why richer actions can mean fewer turns.

### Chapter fill-in pointers

- Action-space taxonomy.
- Function-calling schema example.
- Code-action example.
- Composition (one action, many operations).
- Tokens and round-trips per action.
- When JSON tool calling is still the right choice.

### Hands-on direction

- Express the same three-step task as (a) JSON tool calls and (b) a single code action; compare turns and tokens.

### Chapter deliverable

A comparison matrix of action spaces with worked examples.

---

## Chapter 3 — The Reason–Act–Observe Loop

### Main goal

Understand the reasoning-and-acting loop lineage that underpins all modern agents.

### Subtopics and goals

- **ReAct**
  - Understand interleaved reasoning traces and actions.
- **Observation feedback**
  - Understand how the result of an action re-enters the model's context.
- **Multi-turn iteration**
  - Understand how the loop accumulates state across steps.
- **From ReAct to CodeAct**
  - Trace the shift from text/JSON actions to executable code actions.
- **Related lineage**
  - Situate PAL/Program-aided reasoning, Toolformer, and code interpreters.

### Chapter fill-in pointers

- ReAct trace anatomy.
- Thought / action / observation format.
- Loop pseudocode.
- Historical timeline.
- Why code became the action of choice.

### Hands-on direction

- Hand-write a ReAct trace for a small task, then rewrite it as a CodeAct trace.

### Chapter deliverable

An annotated loop diagram with the ReAct→CodeAct lineage.

---

## Chapter 4 — Why Code Execution

### Main goal

Internalize the argument for executable code as an agent's action space, and its trade-offs.

### Subtopics and goals

- **Composability**
  - Loops, conditionals, and variables let one action do the work of many.
- **Tool reuse**
  - Code can call existing libraries and previously defined functions.
- **Alignment with pretraining**
  - Models are heavily trained on code, so code actions can be more reliable.
- **Dynamic revision**
  - The interpreter's output lets the agent correct itself mid-task.
- **Costs and risks**
  - Understand the containment burden, non-determinism, and debugging cost.

### Chapter fill-in pointers

- The CodeAct thesis (executable code as a unified action space).
- Empirical claims (fewer steps, higher success versus JSON).
- Failure surface introduced by code.
- When *not* to use code actions.
- Security handoff to the sandbox guide.

### Hands-on direction

- Reproduce a small CodeAct-style example and measure success and step count against a JSON-tool baseline.

### Chapter deliverable

A written rationale for code-as-action with your own benchmark notes.

---

## Chapter 5 — A Minimal Code-Executing Agent

### Main goal

Build the smallest possible working agent: prompt a model, extract code, run it, feed back the result, repeat.

### Subtopics and goals

- **The core loop**
  - Implement generate → extract → execute → observe → repeat.
- **Code extraction**
  - Parse the model's output for the executable action.
- **Execution**
  - Run the code and capture its output.
- **Observation formatting**
  - Return output to the model as the next message.
- **Termination**
  - Detect a final answer and stop.

### Chapter fill-in pointers

- End-to-end loop code (under ~100 lines).
- System prompt for a code agent.
- Regex/parse strategy for code blocks.
- `exec`/subprocess execution.
- Stop signal.
- The first thing that will go wrong.

### Hands-on direction

- Build the backbone agent in a notebook and solve three small tasks (a math problem, a file transform, an API-free data task).

### Chapter deliverable

**The backbone agent v0** — a minimal, working code-executing loop.

---

# Part II — The Execution Substrate

## Chapter 6 — Interpreters, REPLs, and Kernels

### Main goal

Understand the machinery that actually runs the agent's code and the difference between a one-shot interpreter and a persistent kernel.

### Subtopics and goals

- **REPL model**
  - Understand read–eval–print as the agent's natural execution surface.
- **One-shot execution**
  - Run a fresh process per action; understand its simplicity and limits.
- **Persistent kernels**
  - Keep a live interpreter (e.g., IPython/Jupyter) across actions.
- **Execution protocol**
  - Understand how code goes in and results come out.
- **Language runtimes**
  - Relate the concept to Python, Node, and shell.

### Chapter fill-in pointers

- REPL versus script execution.
- Jupyter/IPython kernel model.
- Execute request/reply.
- Process-per-call versus kernel-per-session.
- Startup cost and warm kernels.

### Hands-on direction

- Run the same sequence of actions against (a) a fresh subprocess each time and (b) a persistent IPython kernel; observe the difference.

### Chapter deliverable

An execution-backend interface with two implementations.

---

## Chapter 7 — Stateful vs Stateless Execution

### Main goal

Understand how execution state (variables, imports, loaded data) persisting across steps changes the agent loop.

### Subtopics and goals

- **Statelessness**
  - Understand the "each action stands alone" model and its re-work cost.
- **Statefulness**
  - Understand carrying variables and objects between actions.
- **State as memory**
  - See in-kernel state as a form of working memory.
- **State hazards**
  - Understand stale state, hidden dependencies, and non-reproducibility.
- **Reset and checkpoint**
  - Understand clearing, restarting, and snapshotting a kernel.

### Chapter fill-in pointers

- Variable persistence across turns.
- Import and data reuse.
- Hidden-state bugs.
- Kernel reset semantics.
- Reproducing a run from scratch.

### Hands-on direction

- Give the backbone agent a persistent kernel; have it load a dataset once and reference it across several later actions.

### Chapter deliverable

Backbone agent upgraded to stateful execution, with a reset control.

---

## Chapter 8 — Capturing Output: stdout, stderr, Values, and Rich Media

### Main goal

Capture everything an execution produces and turn it into a useful observation.

### Subtopics and goals

- **Standard streams**
  - Capture stdout and stderr separately.
- **Return values and expressions**
  - Capture the value of the last expression, not just printed text.
- **Exceptions and tracebacks**
  - Capture errors as first-class, actionable observations.
- **Rich outputs**
  - Capture dataframes, plots/images, and files the agent produces.
- **Large outputs**
  - Deal with output that is too big to return whole.

### Chapter fill-in pointers

- Stream redirection.
- Last-expression capture (IPython display hooks).
- Traceback formatting.
- Image/plot capture and encoding.
- Artifact files versus inline output.
- Output size limits (preview of context engineering).

### Hands-on direction

- Make the agent produce a plot and a large table; return a useful, bounded observation for each.

### Chapter deliverable

An observation-capture module (streams, values, errors, media, artifacts).

---

## Chapter 9 — Execution Backends

### Main goal

Compare the concrete ways to run agent code and choose per use case.

### Subtopics and goals

- **In-process `exec`**
  - Understand the simplest, least safe option.
- **Subprocess**
  - Isolate execution in a child process.
- **Local kernel service**
  - Run a managed local interpreter service.
- **Remote / sandboxed execution**
  - Send code to a remote or containerized executor.
- **Managed platforms**
  - Use hosted code-execution services (usage view only).

### Chapter fill-in pointers

- Backend trade-off table (speed, isolation, statefulness, cost).
- Local versus remote latency.
- The abstraction boundary (one interface, many backends).
- Where the sandbox guide takes over.

### Hands-on direction

- Implement one `Executor` interface with in-process, subprocess, and remote backends behind it.

### Chapter deliverable

A pluggable executor interface with three backends.

---

## Chapter 10 — Languages and Polyglot Execution

### Main goal

Decide which languages the agent can act in and how to support more than one.

### Subtopics and goals

- **Python-first**
  - Understand why Python dominates code-agent action spaces.
- **Shell/bash actions**
  - Understand when a shell command is the better action than code.
- **JavaScript/TypeScript**
  - Understand JS execution and its ecosystem fit.
- **Language routing**
  - Let the agent choose the right language per action.
- **Cross-language state**
  - Understand why state rarely crosses language boundaries.

### Chapter fill-in pointers

- Language suitability by task.
- Shell versus code decision rule.
- Multi-runtime harness.
- Per-language observation formatting.

### Hands-on direction

- Add a bash action type alongside Python and let the agent pick.

### Chapter deliverable

A polyglot action router.

---

# Part III — Workspace, Filesystem, and CLI

## Chapter 11 — Giving the Agent a Workspace

### Main goal

Provide the agent with a working directory it can inspect, modify, and treat as persistent scratch space.

### Subtopics and goals

- **Working directory model**
  - Establish a per-task workspace root.
- **Persistence scope**
  - Decide what survives across actions, tasks, and sessions.
- **Artifacts**
  - Treat files the agent creates as outputs.
- **Workspace as shared state**
  - Understand the filesystem as memory shared between actions.
- **Cleanup and disposability**
  - Understand tearing down and recreating a workspace.

### Chapter fill-in pointers

- Workspace layout.
- Ephemeral versus persistent files.
- Artifact directory.
- Working-directory injection into execution.
- Cleanup policy (handoff to sandbox guide for isolation).

### Hands-on direction

- Give the backbone agent a workspace it writes intermediate files into and reads back later.

### Chapter deliverable

A workspace manager for the agent.

---

## Chapter 12 — Files as Tools

### Main goal

Give the agent reliable file operations: read, write, edit, list, and search.

### Subtopics and goals

- **Read and write**
  - Provide bounded, encoding-aware file access.
- **Listing and globbing**
  - Let the agent discover files.
- **Search**
  - Provide grep/content search over the workspace.
- **Large files**
  - Read by range, line, or chunk instead of whole.
- **File tools versus code**
  - Decide when to expose a file tool versus let the agent write code.

### Chapter fill-in pointers

- File-tool API.
- Bounded reads.
- Search tool design.
- Binary versus text handling.
- Path handling (isolation handoff to sandbox guide).

### Hands-on direction

- Implement read/write/list/search file tools and have the agent locate and summarize a file.

### Chapter deliverable

A file-operations toolset.

---

## Chapter 13 — The Shell/CLI as an Action Surface

### Main goal

Let the agent run command-line programs and treat the shell as a first-class action space.

### Subtopics and goals

- **Command execution**
  - Run a command and capture output, errors, and exit code.
- **Working directory and environment**
  - Control where and how commands run.
- **Interactive versus non-interactive**
  - Understand programs that expect input or a TTY.
- **Streaming output**
  - Handle long-running command output incrementally.
- **Shell versus code decision**
  - Codify when the agent should shell out.

### Chapter fill-in pointers

- Command runner design.
- Exit-code semantics.
- Env and cwd control.
- Timeouts and streaming.
- Dangerous-command awareness (handoff to sandbox guide).

### Hands-on direction

- Give the agent a shell tool and have it install a package, run a linter, and run tests.

### Chapter deliverable

A CLI/shell action tool with streaming and timeouts.

---

## Chapter 14 — Editing Code

### Main goal

Let the agent modify existing code reliably, not just write new files.

### Subtopics and goals

- **Whole-file rewrite**
  - Understand the simplest edit strategy and its costs.
- **Diff/patch edits**
  - Apply unified diffs or search-replace edits.
- **Structured edits**
  - Edit via anchors, line ranges, or AST-aware operations.
- **Edit verification**
  - Confirm the edit applied as intended.
- **Failure recovery**
  - Handle failed or ambiguous edits.

### Chapter fill-in pointers

- Rewrite versus diff versus search-replace.
- Patch application and conflicts.
- Anchor/uniqueness requirements.
- Post-edit validation.
- Editing large files economically.

### Hands-on direction

- Implement a search-replace edit tool and have the agent fix a bug across two files.

### Chapter deliverable

A robust code-edit tool.

---

## Chapter 15 — Environments, Packages, and Dependencies

### Main goal

Let the agent manage runtime environments and install what a task needs.

### Subtopics and goals

- **Package installation**
  - Let the agent add dependencies safely.
- **Virtual environments**
  - Isolate per-task dependencies.
- **Toolchain management**
  - Handle language versions and build tools.
- **Reproducibility**
  - Pin versions and record what was installed.
- **Registry access**
  - Understand where packages come from (handoff to sandbox guide for egress).

### Chapter fill-in pointers

- Install-as-action pattern.
- Environment lifecycle.
- Lockfiles and pinning.
- Recording installed state.

### Hands-on direction

- Have the agent create an environment, install dependencies, and record them for reproducibility.

### Chapter deliverable

An environment-and-dependency helper for the agent.

---

## Chapter 16 — Long-Running Processes and Services

### Main goal

Let the agent start, use, and stop servers, jobs, and background processes.

### Subtopics and goals

- **Backgrounding**
  - Start a process without blocking the loop.
- **Readiness**
  - Detect when a service is usable.
- **Interaction**
  - Let subsequent actions talk to the running service.
- **Supervision and cleanup**
  - Track and terminate descendants reliably.
- **Log collection**
  - Capture service logs as observations.

### Chapter fill-in pointers

- Background process handle.
- Health/readiness checks.
- Port and endpoint handling.
- Guaranteed teardown.
- Log capture.

### Hands-on direction

- Have the agent start a local web service, make requests to it, then shut it down cleanly.

### Chapter deliverable

A process-supervision helper.

---

## Chapter 17 — Navigating Large Codebases

### Main goal

Give the agent strategies to understand a repository too large to fit in context.

### Subtopics and goals

- **Repo mapping**
  - Build a compact overview of structure.
- **Search-driven navigation**
  - Find relevant code by symbol and content.
- **AST and symbol tools**
  - Locate definitions, references, and call sites.
- **Progressive reading**
  - Read only what's needed, when needed.
- **Context assembly**
  - Turn navigation results into focused context (preview of Part VI).

### Chapter fill-in pointers

- Repo map / skeleton.
- Grep and symbol search.
- Definition/reference lookup.
- Read-on-demand strategy.
- Relevance ranking.

### Hands-on direction

- Point the agent at an unfamiliar medium-sized repo and have it answer "where is X implemented?" without reading everything.

### Chapter deliverable

A codebase-navigation toolset.

---

# Part IV — The Agent Loop (Loop Engineering)

## Chapter 18 — Anatomy of the Harness

### Main goal

Understand the harness — the code around the model that runs the loop — as an engineered system.

### Subtopics and goals

- **Harness responsibilities**
  - Enumerate what the harness owns versus what the model owns.
- **Turn structure**
  - Understand a single iteration: build context, call model, act, observe.
- **Message accumulation**
  - Manage the growing conversation across turns.
- **Orchestration state**
  - Track step count, budgets, and status outside the model.
- **Harness versus framework**
  - Decide when to hand-roll versus adopt a framework.

### Chapter fill-in pointers

- Harness component diagram.
- Single-turn sequence.
- State the harness holds.
- Separation of concerns (model, harness, tools, executor).
- Minimal harness pseudocode.

### Hands-on direction

- Refactor the backbone agent into an explicit harness with clear responsibilities.

### Chapter deliverable

A clean harness abstraction.

---

## Chapter 19 — Parsing and Extracting Actions

### Main goal

Reliably turn model output into executable actions.

### Subtopics and goals

- **Code-block extraction**
  - Parse fenced code and language hints.
- **Structured action wrapping**
  - Use tool-call/JSON wrappers around code when appropriate.
- **Mixed reasoning and action**
  - Separate the "thinking" from the "action" in one response.
- **Malformed output**
  - Handle missing, partial, or multiple code blocks.
- **Action validation**
  - Sanity-check an action before executing it.

### Chapter fill-in pointers

- Parsing strategy.
- Multiple/interleaved blocks.
- Reasoning/action separation.
- Robustness to formatting drift.
- Re-prompting on parse failure.

### Hands-on direction

- Feed the parser deliberately messy outputs and make it degrade gracefully.

### Chapter deliverable

A robust action parser with failure handling.

---

## Chapter 20 — Formatting Observations

### Main goal

Turn raw execution results into observations the model can actually use.

### Subtopics and goals

- **Result rendering**
  - Format output, values, and errors clearly.
- **Truncation and summarization**
  - Bound large observations without losing the signal.
- **Referencing**
  - Point to files/artifacts instead of inlining everything.
- **Error emphasis**
  - Surface the actionable part of a traceback.
- **Signal-to-noise**
  - Strip noise that wastes context and distracts the model.

### Chapter fill-in pointers

- Observation schema.
- Truncation strategy (head/tail, middle-out).
- Summarized observations.
- Error highlighting.
- Artifact references.

### Hands-on direction

- Compare agent success with raw versus well-formatted observations on the same tasks.

### Chapter deliverable

An observation formatter with truncation and summarization.

---

## Chapter 21 — Termination and Stop Conditions

### Main goal

Decide, robustly, when the loop should stop.

### Subtopics and goals

- **Task-complete signals**
  - Let the model declare a final answer.
- **Budget stops**
  - Stop on max steps, time, tokens, or cost.
- **No-progress detection**
  - Detect thrashing and repeated actions.
- **Success verification**
  - Confirm the task is actually done, not just claimed done.
- **Graceful termination**
  - Clean up and summarize on stop.

### Chapter fill-in pointers

- Final-answer protocol.
- Budget ceilings.
- Loop-detection heuristics.
- Verified versus claimed completion.
- Termination cleanup.

### Hands-on direction

- Add multiple stop conditions and test each fires correctly (including a task designed to never finish).

### Chapter deliverable

A termination controller.

---

## Chapter 22 — Error Handling and Self-Debugging

### Main goal

Turn execution errors into a productive self-correction loop.

### Subtopics and goals

- **Errors as observations**
  - Feed tracebacks back as actionable input.
- **Self-debugging**
  - Let the agent diagnose and fix its own failures.
- **Retry policy**
  - Bound retries and avoid repeating the same mistake.
- **Distinguishing error types**
  - Separate syntax, runtime, environment, and logic errors.
- **Escalation**
  - Decide when to stop retrying and ask or abort.

### Chapter fill-in pointers

- Traceback feedback.
- Retry counting and backoff.
- Repeated-failure detection.
- Error taxonomy.
- Escalation rules.

### Hands-on direction

- Inject failing tasks and confirm the agent recovers, and that it gives up sensibly when it can't.

### Chapter deliverable

A self-debugging retry mechanism.

---

## Chapter 23 — Planning and Control Flow

### Main goal

Add explicit planning and task decomposition to the loop.

### Subtopics and goals

- **Plan-and-execute**
  - Generate a plan, then execute steps against it.
- **Decomposition**
  - Break a task into subtasks.
- **Replanning**
  - Revise the plan as observations arrive.
- **Sequential versus branching**
  - Handle conditional and parallel work.
- **Plan tracking**
  - Keep the plan visible and updated in context.

### Chapter fill-in pointers

- Planner design.
- Plan representation.
- Replanning triggers.
- Subtask state.
- Plan-in-context management.

### Hands-on direction

- Add a planning step and compare performance with and without it on a multi-step task.

### Chapter deliverable

A plan-and-execute loop variant.

---

## Chapter 24 — Reflection and Self-Correction

### Main goal

Let the agent critique and improve its own work beyond just fixing errors.

### Subtopics and goals

- **Reflexion pattern**
  - Add a reflection step that learns from failed attempts.
- **Self-critique**
  - Have the agent evaluate its own output before finishing.
- **Verification actions**
  - Let the agent write tests or checks for its own results.
- **Reflection memory**
  - Carry lessons forward within a task.
- **Diminishing returns**
  - Know when reflection stops helping.

### Chapter fill-in pointers

- Reflection loop.
- Self-critique prompt.
- Agent-written verification.
- Reflection notes in context.
- Cost of reflection.

### Hands-on direction

- Add a reflect-and-retry stage and measure quality gain versus token cost.

### Chapter deliverable

A reflection stage for the loop.

---

## Chapter 25 — Interruption, Cancellation, and Human-in-the-Loop

### Main goal

Make the loop controllable by a human in real time.

### Subtopics and goals

- **Cancellation**
  - Stop the loop and in-flight execution safely.
- **Pause and resume**
  - Suspend the loop while preserving state.
- **Approval gates**
  - Require human confirmation before risky actions.
- **Steering**
  - Let a human inject guidance mid-run.
- **Feedback incorporation**
  - Fold human input back into context correctly.

### Chapter fill-in pointers

- Cancellation semantics.
- Pause/resume state.
- Approval prompt design.
- Mid-run steering.
- Handoff points.

### Hands-on direction

- Add an approval gate before any shell command and a mid-run steering message.

### Chapter deliverable

A human-in-the-loop control layer.

---

## Chapter 26 — Loop Failure Modes and Guardrails

### Main goal

Catalog the ways agent loops fail and the guardrails that prevent them.

### Subtopics and goals

- **Infinite and near-infinite loops**
  - Detect and break non-terminating runs.
- **Thrashing and oscillation**
  - Detect repeated or contradictory actions.
- **Hallucinated APIs**
  - Handle calls to things that don't exist.
- **Getting stuck**
  - Recognize and escape dead ends.
- **Runaway cost**
  - Prevent quiet budget blowups.

### Chapter fill-in pointers

- Failure-mode taxonomy.
- Loop/oscillation detection.
- Hallucination handling.
- Dead-end escape.
- Hard guardrails.

### Hands-on direction

- Reproduce each failure mode deliberately, then add a guardrail that catches it.

### Chapter deliverable

A loop-guardrail suite.

---

## Chapter 27 — Budgets: Steps, Time, Tokens, and Cost

### Main goal

Treat every agent run as a bounded, accounted-for resource consumer.

### Subtopics and goals

- **Step budgets**
  - Cap iterations per task.
- **Time budgets**
  - Cap wall-clock per task.
- **Token budgets**
  - Cap input/output tokens across the run.
- **Cost accounting**
  - Track spend per task and per tool.
- **Budget-aware behavior**
  - Let the agent adapt as budget runs low.

### Chapter fill-in pointers

- Budget model.
- Per-run accounting.
- Cost attribution (model calls, tools, execution).
- Graceful degradation near limits.
- Reporting.

### Hands-on direction

- Instrument the backbone agent to report tokens, steps, and cost per task, and enforce a ceiling.

### Chapter deliverable

A budget-and-accounting layer.

---

# Part V — Tools and Tool Creation

## Chapter 28 — Tools as Code: Definition and Exposure

### Main goal

Understand how tools are defined as code and made available to the agent.

### Subtopics and goals

- **Tools as functions**
  - Represent tools as callable functions the agent invokes from code.
- **Exposure to the model**
  - Present signatures, docstrings, and types so the model knows how to call them.
- **Tool calling from code**
  - Let a code action call one or many tools with real control flow.
- **Tool namespaces**
  - Organize tools the agent can reach.
- **Function-calling versus code-calling**
  - Compare direct tool calls with calling tools from within code.

### Chapter fill-in pointers

- Tool-as-function pattern.
- Signature/docstring exposure.
- Calling tools inside a code action.
- Tool registry.
- Function-calling versus code-mode trade-offs.

### Hands-on direction

- Expose two tools as callable functions and have the agent compose them inside one code action.

### Chapter deliverable

A tool registry with code-callable tools.

---

## Chapter 29 — Designing the Tool Interface

### Main goal

Design tool interfaces that models use correctly and reliably.

### Subtopics and goals

- **Naming and semantics**
  - Choose names and behaviors the model predicts correctly.
- **Signatures and types**
  - Make inputs and outputs unambiguous.
- **Docstrings as prompts**
  - Treat documentation as instructions to the model.
- **Return-value design**
  - Return results that are easy to observe and chain.
- **Error surfaces**
  - Make tool errors actionable.

### Chapter fill-in pointers

- Tool-naming guidance.
- Type and schema design.
- Docstring conventions.
- Result shape.
- Error messages for models.

### Hands-on direction

- Take a poorly designed tool and iterate its interface until the agent uses it reliably.

### Chapter deliverable

A tool-design style guide.

---

## Chapter 30 — Dynamic Tool Synthesis

### Main goal

Let the agent write its own new tools during a task and reuse them.

### Subtopics and goals

- **On-the-fly functions**
  - Let the agent define a function once and call it again.
- **Promotion to tools**
  - Turn an ad-hoc function into a registered, reusable tool.
- **Parameterization**
  - Generalize a one-off into a reusable utility.
- **Naming and storage**
  - Track agent-authored tools.
- **Trust and review**
  - Decide how much to trust self-authored tools.

### Chapter fill-in pointers

- Define-once/reuse pattern.
- Function-to-tool promotion.
- Generalization prompts.
- Self-authored tool registry.
- Review/verification hooks.

### Hands-on direction

- Give the agent a repetitive task and let it write a helper tool it then reuses across items.

### Chapter deliverable

A mechanism for agent-authored tools.

---

## Chapter 31 — Skill Libraries and Persistent Toolboxes

### Main goal

Let the agent accumulate reusable skills across steps, tasks, and sessions.

### Subtopics and goals

- **Skill library concept**
  - Persist learned functions as a growing library (the Voyager idea).
- **Retrieval of skills**
  - Fetch relevant skills into context when needed.
- **Versioning and dedup**
  - Manage overlapping and evolving skills.
- **Cross-session persistence**
  - Store skills on the filesystem or a store.
- **Skill quality**
  - Keep only skills that proved useful.

### Chapter fill-in pointers

- Library structure.
- Skill indexing and retrieval.
- Dedup and versioning.
- Persistence backend.
- Pruning strategy.

### Hands-on direction

- Persist agent-written tools to disk and have a later session discover and reuse them.

### Chapter deliverable

A persistent skill library with retrieval.

---

## Chapter 32 — Tool Discovery and Progressive Disclosure

### Main goal

Expose large tool sets without flooding the context window.

### Subtopics and goals

- **The tool-bloat problem**
  - Understand how upfront tool definitions consume context.
- **On-demand discovery**
  - Load tool definitions only when relevant.
- **Tools as a searchable catalog**
  - Let the agent find tools like files.
- **Just-in-time definitions**
  - Pull a tool's full spec only when it's about to be used.
- **Namespacing at scale**
  - Organize hundreds of tools.

### Chapter fill-in pointers

- Tool-definition token cost.
- Discovery mechanism.
- Catalog/search design.
- Lazy definition loading.
- Scaling to many tools.

### Hands-on direction

- Give the agent 50 tools via a searchable catalog instead of upfront definitions; measure context savings.

### Chapter deliverable

A progressive tool-discovery system.

---

## Chapter 33 — Code Execution with MCP

### Main goal

Combine code execution with the Model Context Protocol so the agent calls tools as code APIs.

### Subtopics and goals

- **MCP basics**
  - Understand MCP as a standard interface to external tools and data.
- **Tools as code APIs**
  - Present MCP servers as code the agent imports and calls.
- **Filesystem-of-tools**
  - Let the agent discover tools by browsing, not by loading all definitions.
- **Keeping data out of context**
  - Process intermediate results in code instead of routing them through the model.
- **Efficiency and its cost**
  - Understand the large token savings and the added execution complexity.

### Chapter fill-in pointers

- MCP overview.
- Code-mode tool invocation.
- On-demand tool loading.
- Intermediate-data handling.
- Trade-offs and when it's worth it.

### Hands-on direction

- Expose a couple of tools via MCP and call them from agent-written code; compare token usage with direct tool calling.

### Chapter deliverable

A code-execution-with-MCP proof of concept and token comparison.

---

## Chapter 34 — Verifying and Testing Agent-Authored Tools

### Main goal

Trust agent-created tools only after checking them.

### Subtopics and goals

- **Test generation**
  - Have the agent write tests for its own tools.
- **Contract checks**
  - Verify inputs, outputs, and side effects.
- **Regression protection**
  - Prevent a "fixed" tool from breaking later.
- **Isolation of risky tools**
  - Separate high-impact tools (handoff to sandbox guide).
- **Promotion gates**
  - Require checks before a tool joins the library.

### Chapter fill-in pointers

- Auto-generated tests.
- Contract validation.
- Regression suite.
- Promotion criteria.
- Review workflow.

### Hands-on direction

- Add a gate that a self-authored tool must pass tests before entering the skill library.

### Chapter deliverable

A verification gate for agent-authored tools.

---

# Part VI — Context Engineering

## Chapter 35 — What Lives in the Context Window

### Main goal

Understand context engineering as the discipline of deciding exactly what the model sees at each step.

### Subtopics and goals

- **Context components**
  - Enumerate system prompt, task, tool defs, history, observations, memory, retrieved data.
- **Context as a managed resource**
  - Treat the window as a scarce, actively curated budget, not a dumping ground.
- **Context engineering versus prompt engineering**
  - Distinguish curating dynamic context from writing a static prompt.
- **Attention and placement**
  - Understand that position and salience affect what the model uses.
- **The context assembly step**
  - See context construction as an explicit stage of each turn.

### Chapter fill-in pointers

- Context inventory.
- Static versus dynamic context.
- The curation mindset.
- Placement effects.
- Assembly pipeline.

### Hands-on direction

- Log the exact context sent on each turn of the backbone agent and audit what it contains.

### Chapter deliverable

A context-assembly module with full logging.

---

## Chapter 36 — Context Budgeting and Token Economics

### Main goal

Manage the context window as a finite budget with real cost and latency implications.

### Subtopics and goals

- **Window limits**
  - Work within model context limits.
- **Token accounting**
  - Measure what each component costs.
- **Budget allocation**
  - Decide how much window each component gets.
- **Cost and latency**
  - Understand how context size drives spend and speed.
- **Caching**
  - Exploit prompt/prefix caching to cut cost.

### Chapter fill-in pointers

- Window sizing.
- Per-component token measurement.
- Budget allocation policy.
- Cost/latency curves.
- Prefix/prompt caching.

### Hands-on direction

- Instrument per-component token usage and set a budget for each part of the context.

### Chapter deliverable

A context-budget policy with measurement.

---

## Chapter 37 — Managing Observations

### Main goal

Keep observations from overwhelming the context while preserving their signal.

### Subtopics and goals

- **Truncation strategies**
  - Bound observations by head/tail or middle-out.
- **Summarization**
  - Compress verbose output into usable form.
- **Offloading to files**
  - Write big results to disk and reference them.
- **Selective retention**
  - Keep recent/relevant observations, drop stale ones.
- **Structured observations**
  - Return compact, structured results over raw dumps.

### Chapter fill-in pointers

- Truncation policy.
- Summarize-on-overflow.
- File offload and read-back.
- Observation aging.
- Structured result formats.

### Hands-on direction

- Give the agent a tool that produces huge output; keep the run under budget without losing the answer.

### Chapter deliverable

An observation-management policy.

---

## Chapter 38 — Memory: Scratchpads, Files, and External Stores

### Main goal

Give the agent memory beyond the raw conversation history.

### Subtopics and goals

- **Short-term scratchpad**
  - Maintain a working-notes area.
- **Filesystem memory**
  - Use files as durable, addressable memory.
- **External stores**
  - Use key-value or vector stores for larger memory.
- **Memory read/write policy**
  - Decide when the agent records and recalls.
- **Memory hygiene**
  - Prevent stale or contradictory memory.

### Chapter fill-in pointers

- Scratchpad design.
- Files as memory.
- Vector/KV memory.
- Write/recall triggers.
- Memory conflicts.

### Hands-on direction

- Add a notes file the agent maintains and consults across many steps.

### Chapter deliverable

A memory subsystem with at least two tiers.

---

## Chapter 39 — State Externalization

### Main goal

Move state out of the context window and into the environment, then pull it back on demand.

### Subtopics and goals

- **Filesystem as state**
  - Keep intermediate results as files rather than context.
- **Variables as state**
  - Keep data in the kernel rather than re-sending it.
- **Handles and references**
  - Refer to state by name/path instead of value.
- **Just-in-time loading**
  - Bring state into context only when needed.
- **Consistency**
  - Keep externalized state and the model's view in sync.

### Chapter fill-in pointers

- File-backed state.
- Kernel-variable state.
- Reference/handle pattern.
- On-demand hydration.
- Sync hazards.

### Hands-on direction

- Refactor a data-heavy task so large data stays in files/variables and only references enter context.

### Chapter deliverable

A state-externalization pattern applied to the backbone agent.

---

## Chapter 40 — History Compaction and Summarization

### Main goal

Keep long-running loops within budget by compacting conversation history.

### Subtopics and goals

- **When to compact**
  - Trigger compaction on size or step thresholds.
- **What to preserve**
  - Keep goals, decisions, and open threads; drop noise.
- **Summarization quality**
  - Compact without losing task-critical detail.
- **Rolling windows**
  - Combine recent-verbatim with older-summarized history.
- **Compaction risks**
  - Avoid dropping something the agent still needs.

### Chapter fill-in pointers

- Compaction triggers.
- Preserve/drop policy.
- Summarization method.
- Verbatim-plus-summary window.
- Information-loss checks.

### Hands-on direction

- Run a long task and add compaction; verify the agent still succeeds after history is summarized.

### Chapter deliverable

A history-compaction mechanism.

---

## Chapter 41 — Retrieval into Context

### Main goal

Pull the right external knowledge (docs, code, examples, tools) into context at the right time.

### Subtopics and goals

- **Retrieval targets**
  - Retrieve API docs, code, prior runs, and skills.
- **Just-in-time retrieval**
  - Fetch only what the current step needs.
- **Ranking and relevance**
  - Get the most useful chunks, not the most chunks.
- **Grounding actions**
  - Use retrieved signatures/schemas to reduce hallucination.
- **Retrieval cost**
  - Balance recall against context budget.

### Chapter fill-in pointers

- Retrieval sources.
- JIT retrieval triggers.
- Relevance ranking.
- Grounding with retrieved specs.
- Budget-aware retrieval.

### Hands-on direction

- Retrieve the exact API signature the agent needs before it writes a call, and measure the drop in errors.

### Chapter deliverable

A retrieval layer feeding the context assembler.

---

## Chapter 42 — Prompt Architecture for Code Agents

### Main goal

Design the instructions and structure that make a code agent behave reliably.

### Subtopics and goals

- **System-prompt design**
  - Specify role, action format, constraints, and stop protocol.
- **Output-format control**
  - Enforce how the agent emits code and final answers.
- **Few-shot examples**
  - Ground behavior with worked examples.
- **Instruction placement**
  - Position rules where they'll be followed.
- **Structured delimiters**
  - Separate instructions, data, observations, and memory clearly.

### Chapter fill-in pointers

- System-prompt template.
- Action/answer format rules.
- Example selection.
- Placement and salience.
- Section delimiters.

### Hands-on direction

- A/B two system prompts for the backbone agent and measure reliability differences.

### Chapter deliverable

A production-quality system prompt and format spec.

---

## Chapter 43 — Context Failure Modes

### Main goal

Recognize and mitigate the ways context degrades agent performance.

### Subtopics and goals

- **Context rot / degradation**
  - Understand how quality drops as context grows.
- **Lost-in-the-middle**
  - Understand weak recall of mid-context information.
- **Distraction and clutter**
  - Understand how irrelevant context hurts.
- **Contradiction and staleness**
  - Handle conflicting or outdated context.
- **Poisoning via observations**
  - Treat tool/observation content as potentially adversarial (preview of Part XI).

### Chapter fill-in pointers

- Degradation-with-length effects.
- Positional recall.
- Clutter effects.
- Stale/contradictory context.
- Untrusted observation content.

### Hands-on direction

- Deliberately bloat context and measure the accuracy drop; then apply Part VI techniques to recover it.

### Chapter deliverable

A context-health checklist and mitigations.

---

# Part VII — Code Generation Quality

## Chapter 44 — Prompting for Reliable Code

### Main goal

Get the model to produce correct, runnable code consistently.

### Subtopics and goals

- **Specification clarity**
  - Give the model enough to write correct code.
- **Output discipline**
  - Enforce clean, single-block, runnable output.
- **Constraints and conventions**
  - Steer toward safe, idiomatic code.
- **Determinism controls**
  - Reduce variance where it matters.
- **Common generation failures**
  - Anticipate the usual mistakes.

### Chapter fill-in pointers

- Spec completeness.
- Output constraints.
- Style/convention steering.
- Temperature and sampling.
- Failure catalog.

### Hands-on direction

- Iterate prompts on a task until first-run success rate is high; record what moved the needle.

### Chapter deliverable

A code-generation prompting playbook.

---

## Chapter 45 — Grounding Generation in Real APIs and Schemas

### Main goal

Anchor generated code to real interfaces so it actually runs.

### Subtopics and goals

- **Providing signatures**
  - Give real function/class signatures.
- **Providing schemas**
  - Give data and API schemas.
- **Type stubs and docs**
  - Supply typed interfaces and documentation.
- **Example-driven grounding**
  - Provide correct usage examples.
- **Verification against the real API**
  - Check calls against reality before trusting them.

### Chapter fill-in pointers

- Signature injection.
- Schema injection.
- Stubs and docs.
- Usage examples.
- Call validation.

### Hands-on direction

- Give the agent the real signatures for a library it tends to misuse and measure the error drop.

### Chapter deliverable

A grounding pipeline for generated code.

---

## Chapter 46 — Reducing Hallucinated APIs and Imports

### Main goal

Detect and prevent calls to functions, packages, and parameters that don't exist.

### Subtopics and goals

- **Hallucination patterns**
  - Recognize invented APIs, args, and imports.
- **Static checks**
  - Catch undefined names and bad imports before running.
- **Availability checks**
  - Verify packages and symbols exist.
- **Feedback correction**
  - Turn "not found" errors into fast fixes.
- **Prevention via grounding**
  - Reduce hallucination at the source (link to Ch 45).

### Chapter fill-in pointers

- Hallucination taxonomy.
- Lint/static analysis pass.
- Import/symbol resolution.
- Error-driven correction.
- Grounding prevention.

### Hands-on direction

- Add a pre-execution static check that catches hallucinated names and feeds them back.

### Chapter deliverable

A pre-execution validation pass.

---

## Chapter 47 — Test-Driven and Iterative Agent Coding

### Main goal

Have the agent use tests and iteration to reach correct results.

### Subtopics and goals

- **Write-test-then-code**
  - Let the agent define success as tests first.
- **Run-and-refine**
  - Iterate against test results.
- **Assertion-driven checks**
  - Use assertions as cheap verification.
- **Coverage of edge cases**
  - Push the agent to test boundaries.
- **Stopping on green**
  - Terminate when tests pass (link to Ch 21).

### Chapter fill-in pointers

- TDD-for-agents flow.
- Iteration loop.
- Assertion checks.
- Edge-case prompting.
- Pass-based termination.

### Hands-on direction

- Give the agent a spec and require it to write and pass tests before declaring done.

### Chapter deliverable

A test-driven coding loop variant.

---

## Chapter 48 — Multi-File Generation and Editing

### Main goal

Scale generation from single snippets to coherent changes across many files.

### Subtopics and goals

- **Project-level context**
  - Assemble enough of the project to edit coherently.
- **Coordinated edits**
  - Change multiple files consistently.
- **Consistency and imports**
  - Keep cross-file references valid.
- **Incremental application**
  - Apply and validate changes in safe increments.
- **Rollback**
  - Revert a bad multi-file change.

### Chapter fill-in pointers

- Project context assembly.
- Multi-file edit strategy.
- Cross-file consistency.
- Incremental apply/verify.
- Rollback mechanism.

### Hands-on direction

- Have the agent implement a feature that touches three files with consistent imports and passing tests.

### Chapter deliverable

A multi-file edit workflow.

---

# Part VIII — Patterns and Architectures

## Chapter 49 — Agent Patterns Compared

### Main goal

Map the major agent patterns and know when to use each.

### Subtopics and goals

- **ReAct**
  - Reason and act in interleaved steps.
- **CodeAct**
  - Use code as the unified action.
- **Plan-and-execute**
  - Separate planning from execution.
- **Reflexion**
  - Learn from failed attempts within a task.
- **Tree/graph search**
  - Explore multiple action paths where warranted.

### Chapter fill-in pointers

- Pattern catalog.
- Strengths/weaknesses.
- Selection criteria.
- Combining patterns.
- Cost implications.

### Hands-on direction

- Implement the same task under two patterns and compare cost, reliability, and latency.

### Chapter deliverable

A pattern-selection decision guide.

---

## Chapter 50 — Data-Analysis / Code-Interpreter Agents

### Main goal

Study the most common real-world code-executing agent: the data-analysis assistant.

### Subtopics and goals

- **The pattern**
  - Load data, compute, visualize, iterate.
- **Stateful analysis**
  - Rely on a persistent kernel across steps.
- **Rich outputs**
  - Return tables and plots as observations.
- **File I/O**
  - Ingest and emit data files.
- **Reproducibility**
  - Make an analysis re-runnable.

### Chapter fill-in pointers

- Interpreter-agent architecture.
- Stateful data flow.
- Plot/table observations.
- Data ingestion.
- Reproducible notebooks.

### Hands-on direction

- Build a data-analysis agent that answers questions over a CSV with computation and charts.

### Chapter deliverable

A working code-interpreter-style agent.

---

## Chapter 51 — Software-Engineering (SWE) Agents

### Main goal

Study agents that operate on real repositories: understand, edit, test, and propose changes.

### Subtopics and goals

- **Repo comprehension**
  - Navigate and understand a codebase (link to Ch 17).
- **Edit-test loop**
  - Change code and verify with tests.
- **Localization**
  - Find where a change belongs.
- **Change proposal**
  - Produce reviewable diffs/patches.
- **Verification**
  - Confirm correctness before finishing.

### Chapter fill-in pointers

- SWE-agent architecture.
- Localization strategy.
- Edit-test cycle.
- Patch output.
- Verification step.

### Hands-on direction

- Point the agent at a repo with a failing test and have it produce a passing patch.

### Chapter deliverable

A minimal SWE-agent.

---

## Chapter 52 — Notebook and Computational Agents

### Main goal

Study agents that operate in a notebook paradigm of persistent, cell-based computation.

### Subtopics and goals

- **Cell execution model**
  - Map actions to notebook cells.
- **Persistent computation**
  - Carry rich state across cells.
- **Human-notebook collaboration**
  - Let humans and agents share a notebook.
- **Exploration workflows**
  - Support open-ended, iterative computation.
- **Export and reuse**
  - Turn a session into a reusable artifact.

### Chapter fill-in pointers

- Notebook-as-loop mapping.
- State across cells.
- Shared notebooks.
- Exploration UX.
- Export.

### Hands-on direction

- Drive a Jupyter kernel from the agent and produce a runnable notebook as output.

### Chapter deliverable

A notebook-driving agent.

---

## Chapter 53 — Multi-Agent and Delegated Execution

### Main goal

Understand when to split work across multiple agents and how they share an execution environment.

### Subtopics and goals

- **Orchestrator and workers**
  - Delegate subtasks to specialized agents.
- **Context isolation**
  - Give sub-agents their own clean context.
- **Shared workspace**
  - Coordinate through files and state.
- **Result aggregation**
  - Combine sub-agent outputs.
- **Coordination hazards**
  - Avoid conflicts and duplicated work.

### Chapter fill-in pointers

- Multi-agent topology.
- Sub-agent context boundaries.
- Shared-state coordination.
- Aggregation.
- Conflict avoidance.

### Hands-on direction

- Split a task into a planner and two workers sharing one workspace.

### Chapter deliverable

A minimal multi-agent execution setup.

---

## Chapter 54 — Computer-Use and Desktop Agents

### Main goal

Understand agents that act through a screen/keyboard/mouse or browser rather than pure code (and how code execution complements them).

### Subtopics and goals

- **GUI action space**
  - Understand screen-based actions.
- **Browser automation**
  - Drive a browser as an environment.
- **Code plus GUI**
  - Combine code execution with UI actions.
- **Observation from pixels/DOM**
  - Turn screens and DOM into observations.
- **Reliability challenges**
  - Understand why GUI actions are harder than code.

### Chapter fill-in pointers

- GUI/browser action spaces.
- Screen/DOM observations.
- Hybrid code+GUI loops.
- Grounding UI actions.
- Failure characteristics.

### Hands-on direction

- Add a simple browser action to the agent alongside code execution for one task.

### Chapter deliverable

A note on when code beats GUI actions and vice versa.

---

# Part IX — Frameworks and Real Systems

## Chapter 55 — Framework Landscape

### Main goal

Survey the frameworks for building code-executing agents and their design philosophies.

### Subtopics and goals

- **Code-action frameworks**
  - Study frameworks built around code as the action space.
- **Graph/orchestration frameworks**
  - Study explicit loop/graph orchestration.
- **SDKs and toolkits**
  - Study provider and community agent SDKs.
- **Design-philosophy differences**
  - Compare control, abstraction, and lock-in.
- **Build-versus-adopt**
  - Decide when to use a framework versus hand-roll.

### Chapter fill-in pointers

- Framework comparison table.
- Code-first versus graph-first.
- Abstraction levels.
- Extensibility.
- Selection criteria.

### Hands-on direction

- Rebuild one backbone-agent task in a framework and compare with the hand-rolled version.

### Chapter deliverable

A framework comparison matrix.

---

## Chapter 56 — Reading Real Loops

### Main goal

Learn by reading the source of real code-executing agents.

### Subtopics and goals

- **Code-action agents**
  - Read a framework whose agent emits Python actions.
- **Interpreter agents**
  - Read an open code-interpreter implementation.
- **SWE agents**
  - Read a repository-editing agent.
- **CLI coding agents**
  - Read a terminal-based coding agent.
- **What to extract**
  - Identify the loop, action parsing, observation handling, and context management in each.

### Chapter fill-in pointers

- Reading checklist (loop, parse, observe, context, tools).
- Notable design choices.
- Differences across systems.
- Ideas to adopt.
- Pitfalls to avoid.

### Hands-on direction

- Annotate the core loop of one real open-source agent and diagram it.

### Chapter deliverable

Annotated source walkthroughs of at least two real agents.

---

## Chapter 57 — Managed Execution Platforms

### Main goal

Evaluate hosted code-execution services from the agent-builder's perspective.

### Subtopics and goals

- **Hosted interpreters**
  - Use managed code-execution/sandbox services via SDK.
- **State and sessions**
  - Understand persistence models across calls.
- **Files and artifacts**
  - Move data in and results out.
- **Networking and tools**
  - Understand what the executor can reach.
- **Cost and limits**
  - Model spend, quotas, and latency (isolation details in the sandbox guide).

### Chapter fill-in pointers

- Platform comparison (usage view).
- Session/state model.
- File transfer.
- Limits and cost.
- When managed beats self-hosted.

### Hands-on direction

- Run one backbone-agent task against a managed execution platform.

### Chapter deliverable

A managed-platform evaluation from the agent perspective.

---

# Part X — Evaluation, Observability, and Reliability

## Chapter 58 — Evaluating Code-Executing Agents

### Main goal

Measure whether the agent actually accomplishes tasks, not just whether it runs.

### Subtopics and goals

- **Task-success metrics**
  - Define correct completion for your tasks.
- **Standard benchmarks**
  - Understand coding and agentic benchmarks and what they measure.
- **pass@k and reliability**
  - Measure consistency across repeated runs.
- **Custom eval sets**
  - Build task suites representative of your use case.
- **Regression evaluation**
  - Catch quality drops as you change the agent.

### Chapter fill-in pointers

- Success definitions.
- Benchmark overview.
- pass@k / variance.
- Eval-set construction.
- Regression harness.

### Hands-on direction

- Build a small eval suite for the backbone agent and track success across versions.

### Chapter deliverable

A reproducible agent evaluation harness.

---

## Chapter 59 — Tracing and Observability of the Loop

### Main goal

Make every agent run inspectable, replayable, and debuggable.

### Subtopics and goals

- **Step tracing**
  - Record each thought, action, and observation.
- **Structured traces**
  - Use spans/traces linking model calls, tool calls, and executions.
- **Token and cost telemetry**
  - Attribute tokens and cost per step and tool.
- **Replay**
  - Reconstruct a run from its trace.
- **Debugging workflows**
  - Investigate failures efficiently.

### Chapter fill-in pointers

- Trace schema.
- OpenTelemetry-style spans.
- Cost/token attribution.
- Run replay.
- Failure investigation.

### Hands-on direction

- Emit a full structured trace for one run and reconstruct the timeline from it.

### Chapter deliverable

A tracing and observability layer.

---

## Chapter 60 — Reliability Engineering and Guardrails

### Main goal

Make the agent dependable enough to run unattended.

### Subtopics and goals

- **Guardrails**
  - Enforce hard limits on actions and effects.
- **Determinism and idempotency**
  - Make retries safe.
- **Output validation**
  - Verify results before returning them.
- **Fallbacks**
  - Degrade gracefully when the agent can't succeed.
- **Monitoring and alerting**
  - Detect regressions and incidents in production.

### Chapter fill-in pointers

- Guardrail catalog.
- Idempotency design.
- Result validation.
- Fallback paths.
- Production monitoring.

### Hands-on direction

- Add guardrails and validation, then run the agent unattended over a batch of tasks.

### Chapter deliverable

A reliability and guardrail layer.

---

## Chapter 61 — Cost, Latency, and Performance

### Main goal

Understand and optimize the economics and speed of the loop.

### Subtopics and goals

- **Cost drivers**
  - Identify what makes runs expensive (context size, steps, tools).
- **Latency drivers**
  - Identify what makes runs slow (model calls, execution, cold starts).
- **Caching and warm state**
  - Reuse context caches and warm kernels.
- **Step reduction**
  - Do more per action to cut round-trips.
- **Optimization trade-offs**
  - Balance cost, latency, and reliability.

### Chapter fill-in pointers

- Cost model.
- Latency breakdown.
- Caching strategy.
- Fewer, richer actions.
- Optimization playbook.

### Hands-on direction

- Profile a run end to end, then cut cost and latency without hurting success rate.

### Chapter deliverable

A performance and cost optimization report.

---

# Part XI — Safety and Guardrails (Bridge to the Sandbox Guide)

## Chapter 62 — Threats Specific to Code-Executing Agents

### Main goal

Understand the agent-side attack surface that arises specifically from executing model-written code.

### Subtopics and goals

- **Prompt injection via observations**
  - Treat tool outputs, files, and repo content as untrusted instructions.
- **Malicious task and data**
  - Handle hostile inputs designed to hijack the agent.
- **Self-authored dangerous code**
  - Understand risk from tools the agent writes.
- **Data exfiltration paths**
  - Understand how execution can leak data.
- **Where containment belongs**
  - Draw the line to the sandbox guide.

### Chapter fill-in pointers

- Injection-via-observation examples.
- Untrusted-content handling.
- Self-authored code risk.
- Exfiltration awareness.
- Handoff boundary.

### Hands-on direction

- Plant an injection in a file the agent reads and observe (safely) how it responds.

### Chapter deliverable

An agent-side threat checklist that references the sandbox guide.

---

## Chapter 63 — Guardrails and Approval Gates

### Main goal

Add the minimum agent-side safety controls, then hand off runtime containment to the sandbox guide.

### Subtopics and goals

- **Action approval**
  - Gate risky actions behind confirmation.
- **Effect classification**
  - Separate read-only from mutating and irreversible actions.
- **Content sanitization**
  - Neutralize instructions embedded in observations.
- **Least authority**
  - Give the agent only the tools and access it needs.
- **Containment handoff**
  - Rely on the sandbox for real isolation.

### Chapter fill-in pointers

- Approval policy.
- Action risk tiers.
- Observation sanitization.
- Least-privilege tool exposure.
- Explicit handoff to the sandbox guide.

### Hands-on direction

- Add approval gates for mutating actions and sanitize untrusted observation content.

### Chapter deliverable

An agent-side guardrail policy with a documented handoff to the sandbox guide.

---

# Part XII — Capstone Project

## Chapter 64 — Capstone Requirements

### Main goal

Define exactly what the capstone code-executing agent must do.

### Required capabilities

- Accept a task and a workspace.
- Generate and execute code as its primary action.
- Maintain stateful execution across steps.
- Read, write, edit, and search files.
- Run shell commands and manage processes.
- Create, verify, and reuse its own tools.
- Manage context: budget, truncate, summarize, externalize, retrieve.
- Recover from its own errors and reflect.
- Enforce step/time/token/cost budgets and guardrails.
- Trace every run and evaluate task success.
- Hand off runtime containment to a sandbox (per the sibling guide).

### Non-functional requirements

- Reliable and reproducible runs.
- Bounded and accounted-for cost.
- Full observability.
- Pluggable execution backends.
- Clear model/harness/tool/executor separation.
- Documented safety boundary.

### Chapter fill-in pointers

- Functional requirements.
- Loop requirements.
- Context requirements.
- Tooling requirements.
- Evaluation targets.
- Safety boundary.

### Chapter deliverable

A complete requirements document for the capstone agent.

---

## Chapter 65 — Capstone: Building the Agent

### Main goal

Assemble the full agent from the components built throughout the guide.

### Suggested milestones

1. Minimal code-executing loop (Part I).
2. Stateful execution and rich observations (Part II).
3. Workspace, files, and CLI (Part III).
4. Loop engineering: parsing, termination, self-debug, planning, budgets (Part IV).
5. Tools and tool creation with a skill library (Part V).
6. Context engineering: budgeting, observation management, memory, compaction, retrieval (Part VI).
7. Generation quality: grounding and validation (Part VII).
8. Chosen pattern and architecture (Part VIII).
9. Evaluation, tracing, reliability, and cost (Part X).
10. Safety guardrails and sandbox handoff (Part XI + sibling guide).

### Chapter fill-in pointers

- Milestone scope and acceptance criteria.
- Integration order.
- Test plan per milestone.
- Backbone-to-capstone mapping.

### Chapter deliverable

A phase-by-phase build plan and the integrated agent.

---

## Chapter 66 — Capstone: Evaluation and Hardening

### Main goal

Prove the capstone agent is capable, reliable, economical, and safe.

### Validation areas

- Task success across an eval suite.
- Reliability across repeated runs (pass@k).
- Cost and latency within budget.
- Correct termination and guardrail behavior.
- Context stays within budget on long runs.
- Self-authored tools are verified before reuse.
- Full traces for every run.
- Safe behavior under injected/hostile inputs.
- Documented containment handoff to the sandbox.

### Chapter fill-in pointers

- Evaluation matrix.
- Reliability report.
- Cost/latency report.
- Guardrail test results.
- Trace completeness check.
- Residual-risk notes.

### Chapter deliverable

A capstone assessment report covering capability, reliability, cost, and safety.

---

# Appendices

## Appendix A — Glossary and Terminology

Terms to define: agent, harness, loop, action space, observation, tool, tool call, code action, CodeAct, ReAct, Reflexion, plan-and-execute, REPL, kernel, stateful/stateless execution, workspace, artifact, skill library, progressive disclosure, MCP, context engineering, context window, compaction, externalized state, budget, guardrail, trace/span, pass@k.

---

## Appendix B — Framework and Tool Reference

Categories to document (with what each is and when to reach for it):

- **Code-action / interpreter frameworks:** smolagents (CodeAgent), Open Interpreter, OpenHands / CodeActAgent.
- **Orchestration frameworks:** LangChain / LangGraph, LlamaIndex, AutoGen, CrewAI, Pydantic AI.
- **Provider agent SDKs:** OpenAI Agents SDK, Anthropic tooling / Claude Agent SDK.
- **Coding / CLI agents:** SWE-agent, Aider, Claude Code, and IDE-integrated agents.
- **Execution / sandbox platforms (usage view):** E2B, Modal, Daytona, Runloop, Riza, and hosted code interpreters.
- **Protocols:** Model Context Protocol (MCP) and code-execution-with-MCP.

For each: purpose, action model (code vs tool-call vs graph), state model, extensibility, and when to adopt versus hand-roll.

---

## Appendix C — Pattern Catalog

Patterns to document: ReAct, CodeAct, Plan-and-Execute, Reflexion, Tree/Graph-of-Thought search, Router/Dispatcher, Orchestrator-Workers, Evaluator-Optimizer, Test-Driven Agent, Retrieval-Augmented Action. For each: shape, when to use, cost profile, and failure modes.

---

## Appendix D — Loop and Prompt Templates

Reusable templates: minimal loop pseudocode, harness skeleton, code-agent system prompt, action/observation format spec, termination protocol, self-debug prompt, reflection prompt, planning prompt, context-assembly outline, and compaction prompt.

---

## Appendix E — Evaluation Reference

Benchmarks and eval concepts to document: SWE-bench / SWE-bench Verified, HumanEval-style coding evals, GAIA and agentic task benchmarks, task-specific eval suites, pass@k and variance, and how to build a representative custom eval set. Note what each does and does not measure.

---

## Appendix F — Reading List

Papers and sources to work through: the CodeAct paper (executable code actions), ReAct, Reflexion, Toolformer, PAL / program-aided reasoning, Voyager (skill libraries), the Anthropic "code execution with MCP" and advanced-tool-use writeups, and context-engineering writeups on managing the context window. Pair each with one real codebase to read.

---

## Appendix G — Chapter Template

Use the following structure when expanding each chapter:

```markdown
# Chapter N — Title

## 1. Concept

## 2. Why This Matters for Code-Executing Agents

## 3. Mental Model

## 4. Architecture (place in the loop / context)

## 5. Detailed Explanation

## 6. Minimal Implementation

## 7. Hands-on Lab

## 8. Failure Lab

## 9. Instrumentation (what to log / trace / measure)

## 10. Design Considerations

## 11. Common Mistakes

## 12. Comparisons / Alternatives

## 13. Review Questions

## 14. Chapter Summary

## 15. Chapter Deliverable

## 16. Further Reading
```

---

# Final Learning Path

```text
The agent loop (model + loop + tools + environment)
    ↓
Action spaces and why code (ReAct → CodeAct)
    ↓
A minimal code-executing agent
    ↓
Execution substrate (REPL, kernels, state, output capture)
    ↓
Workspace, filesystem, and CLI
    ↓
Loop engineering (parse, observe, terminate, self-debug, plan, budget)
    ↓
Tools and tool creation (dynamic synthesis, skill libraries, MCP)
    ↓
Context engineering (budget, observations, memory, compaction, retrieval)
    ↓
Generation quality (grounding, validation, test-driven)
    ↓
Patterns, frameworks, and real systems
    ↓
Evaluation, observability, reliability, and cost
    ↓
Safety and sandbox handoff
    ↓
Production-grade code-executing agent
```

---

# Primary Study Outcome

At the end of this guide, we should be able to answer and demonstrate:

1. Why an agent uses executable code as its action space, and when it should not.
2. How the reason–act–observe loop is engineered, end to end.
3. How execution state, output, and the workspace/CLI are given to and managed for the agent.
4. How the agent creates, verifies, reuses, and discovers its own tools.
5. How context is budgeted, curated, externalized, compacted, and retrieved across a run.
6. How the agent recovers from its own errors and improves through reflection.
7. How runs are bounded by step, time, token, and cost budgets.
8. How the agent is evaluated, traced, and made reliable.
9. Which pattern, framework, and execution backend to use for a given problem.
10. Where agent design ends and runtime containment (the sandbox guide) begins.
```
