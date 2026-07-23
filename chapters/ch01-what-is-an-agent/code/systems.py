"""Classify real systems on the autonomy spectrum FROM STRUCTURE, not from a label.

The first version of this module hand-assigned each system an `Autonomy` level
directly — which makes the taxonomy unfalsifiable: nothing stops you from
mislabeling a system except your own judgment. This version derives the level
from four yes/no structural predicates instead, so "is this an agent?" becomes
a question with a checkable answer, not a vibe. `classify_autonomy()` is the
actual definition; the `Autonomy` enum is just its output space.

Two systems here (`AGENTIC_RAG`, `THERMOSTAT`) are deliberately chosen to
stress-test the predicates rather than illustrate an easy case — see their
docstring-style comments below and the chapter README's discussion of what
each one exposes about the definition's boundaries.
"""

from dataclasses import dataclass, field
from enum import Enum


class Autonomy(Enum):
    """Where a system sits on the fixed-orchestration -> model-driven-loop spectrum.

    NON_MODEL_CONTROL_LOOP is not part of the spectrum proper — it's the
    classification for a system with a real closed feedback loop but no
    model as its policy (see THERMOSTAT below). It exists so
    `classify_autonomy` has somewhere honest to put a system like that,
    instead of forcing it into SINGLE_CALL just because the spectrum has no
    other slot for "loop-shaped but not a model."
    """

    NON_MODEL_CONTROL_LOOP = 0
    SINGLE_CALL = 1
    FIXED_PIPELINE = 2
    SINGLE_TOOL_CALL = 3
    AUTONOMOUS_LOOP = 4


@dataclass(frozen=True)
class LoopPredicates:
    """Four structural yes/no questions that together determine autonomy level.

    These are deliberately about STRUCTURE — what the system's control flow
    actually does — not about what the system is called, what model powers
    it, or how impressive its output is. A system named "agentic X" that
    answers these predicates like a fixed pipeline IS a fixed pipeline; see
    `AGENTIC_RAG` below for a case that resolves the opposite way.
    """

    policy_is_a_language_model: bool
    # Is the thing choosing actions a language model (of any capability),
    # as opposed to a hardcoded rule (an `if` statement, a fixed threshold)?
    # This is checked FIRST and short-circuits everything else: Chapter 1's
    # definition of "agent" specifically requires a model as the policy.
    # A perfectly loop-shaped system with a hardcoded policy (THERMOSTAT)
    # fails here, not on any of the next three predicates.

    has_hardcoded_pipeline_steps: bool
    # Are there steps in the system (retrieval, embedding, formatting) whose
    # occurrence and order are fixed by an engineer, independent of anything
    # the model decides? (Only meaningful to check when policy_is_a_language_model
    # is True — a hardcoded-everywhere system like THERMOSTAT is already
    # classified by the first predicate.)

    model_chooses_the_action: bool
    # Does the model select WHICH action/tool/operation happens next, as
    # opposed to the action being predetermined by the pipeline and the
    # model only filling in content within it?

    loop_repeats_based_on_model_output: bool
    # Is there more than one model decision point, where WHETHER and HOW
    # the system continues is itself something the model's own prior output
    # determines (not a fixed number of pipeline stages)?

    observation_reenters_model_context: bool
    # Does the result of one action get fed back into context for the SAME
    # model to condition its NEXT decision on? (Not "does information reach
    # a human," not "does information get logged" — specifically: does it
    # come back to the model that produced the action, before its next call?)


def classify_autonomy(p: LoopPredicates) -> Autonomy:
    """The taxonomy, as a decision procedure over the four predicates.

    Every branch below corresponds to exactly one cell in the truth table a
    reader could construct from `LoopPredicates`' four fields — there is no
    hidden judgment call once the predicates are answered honestly.
    """
    if not p.policy_is_a_language_model:
        return Autonomy.NON_MODEL_CONTROL_LOOP

    if not p.model_chooses_the_action and not p.loop_repeats_based_on_model_output:
        # The model never picks the action AND nothing repeats based on its
        # output. Only the presence of other hardcoded steps distinguishes
        # "the model is the whole system" from "the model is one stage in a
        # bigger fixed system."
        return Autonomy.FIXED_PIPELINE if p.has_hardcoded_pipeline_steps else Autonomy.SINGLE_CALL

    if p.model_chooses_the_action and not (
        p.loop_repeats_based_on_model_output and p.observation_reenters_model_context
    ):
        # The model picks the action, but nothing feeds the result back for
        # another model-driven decision — one shot, however smart the shot.
        return Autonomy.SINGLE_TOOL_CALL

    if (
        p.model_chooses_the_action
        and p.loop_repeats_based_on_model_output
        and p.observation_reenters_model_context
    ):
        return Autonomy.AUTONOMOUS_LOOP

    # p.model_chooses_the_action is False but the loop-repeats/observation
    # predicates are True: a system that loops and feeds itself observations
    # without the model ever choosing what happens — this combination
    # doesn't correspond to any of the four labeled classes, and deliberately
    # has no home in the spectrum below; see the chapter README.
    raise ValueError(
        "predicates describe a repeating, observation-fed loop where the "
        "model never chooses the action — this is not one of the four "
        "classes this taxonomy covers (see LoopPredicates docstring)"
    )


@dataclass
class AgentSystem:
    """The four parts CLAUDE.md and Chapter 1 insist on separating, plus the
    predicates that DERIVE this system's place on the autonomy spectrum.

    `autonomy` is computed in `__post_init__`, not passed in — there is no
    way to construct an `AgentSystem` with a label that disagrees with its
    own predicates.
    """

    name: str
    predicates: LoopPredicates
    model_role: str            # what the model is asked to produce each call
    loop_description: str      # what actually drives the next step, structurally
    tools: list[str] = field(default_factory=list)
    environment: str = ""      # what the action acts on / the observation comes from
    action_unit: str = ""      # the thing the model emits as "an action"
    observation_unit: str = ""  # the thing that comes back and re-enters context
    autonomy: Autonomy = field(init=False)

    def __post_init__(self) -> None:
        self.autonomy = classify_autonomy(self.predicates)

    @property
    def has_model_driven_loop(self) -> bool:
        return self.autonomy == Autonomy.AUTONOMOUS_LOOP


CHATBOT = AgentSystem(
    name="Customer-support chatbot",
    predicates=LoopPredicates(
        policy_is_a_language_model=True,
        has_hardcoded_pipeline_steps=False,
        model_chooses_the_action=False,   # there's no "action" to choose — it only ever replies
        loop_repeats_based_on_model_output=False,
        observation_reenters_model_context=False,
    ),
    model_role="Generate the next reply in a conversation",
    loop_description=(
        "A human types, the model replies, the human types again. The 'loop' is a "
        "human-in-the-loop UI turn-taker: each model call is independent given its "
        "input context, and what happens next is decided by the human, not by "
        "anything the model's own prior output determined about the environment."
    ),
    tools=[],
    environment="A chat transcript the human reads and appends to",
    action_unit="A chat message",
    observation_unit="The human's next message (not a consequence of the agent's own action)",
)

RAG_PIPELINE = AgentSystem(
    name="RAG question-answering pipeline",
    predicates=LoopPredicates(
        policy_is_a_language_model=True,
        has_hardcoded_pipeline_steps=True,   # embed -> vector search -> stuff -> generate, fixed order
        model_chooses_the_action=False,      # the model doesn't decide to retrieve; the pipeline does
        loop_repeats_based_on_model_output=False,
        observation_reenters_model_context=False,
    ),
    model_role="Generate an answer conditioned on retrieved passages",
    loop_description=(
        "embed query -> vector search -> stuff top-k into prompt -> generate, always in "
        "that order. The model is called exactly once, in the last slot; it cannot decide "
        "to retrieve again, retrieve differently, or do anything but produce the answer text."
    ),
    tools=["vector_search (called by the pipeline, not by the model)"],
    environment="A document/vector store, queried once per pipeline run on a fixed schedule",
    action_unit="N/A — the model does not choose actions, only generates text",
    observation_unit="N/A — retrieved passages are pipeline input, not a returned observation",
)

AGENTIC_RAG = AgentSystem(
    name="Agentic RAG (model decides whether to retrieve again)",
    predicates=LoopPredicates(
        policy_is_a_language_model=True,
        has_hardcoded_pipeline_steps=False,   # no fixed retrieve-then-generate order is imposed
        model_chooses_the_action=True,        # the model decides: retrieve more, or answer now
        loop_repeats_based_on_model_output=True,   # keeps going as long as the model keeps retrieving
        observation_reenters_model_context=True,   # each retrieved batch feeds the next decision
    ),
    model_role=(
        "Decide, given the question and everything retrieved so far, whether to issue "
        "another retrieval query or to answer now — and if answering, produce the answer"
    ),
    loop_description=(
        "The model is called repeatedly; each call sees prior retrieved passages and "
        "either emits a new retrieval query (the action) or a final answer. Retrieval "
        "results re-enter context for the model's own next decision. Structurally "
        "identical in shape to the coding agent below — only the action TYPE differs "
        "(a search query instead of code)."
    ),
    tools=["vector_search (invoked by the model's own choice, not a fixed schedule)"],
    environment="A document/vector store the model can query zero, one, or many times",
    action_unit="A retrieval query, or a final answer",
    observation_unit="The retrieved passages for that query",
)

SINGLE_TOOL_CALL_EXAMPLE = AgentSystem(
    name="Email auto-tagger (one tool call, no loop)",
    predicates=LoopPredicates(
        policy_is_a_language_model=True,
        has_hardcoded_pipeline_steps=False,
        model_chooses_the_action=True,             # the model picks which label to apply
        loop_repeats_based_on_model_output=False,  # exactly one call, then the run ends
        observation_reenters_model_context=False,  # the applied label doesn't come back to the model
    ),
    model_role="Given an email, choose exactly one label from a fixed set and apply it",
    loop_description=(
        "One model call. The model picks a tool call (apply_label(label=...)) from several "
        "options — unlike the RAG pipeline, the model IS choosing the action — but the "
        "system runs that one call, applies the label, and stops. Nothing about the "
        "label's effect ever reaches the model again within this task."
    ),
    tools=["apply_label"],
    environment="An email inbox / ticketing system the label is written to",
    action_unit="One tool call: apply_label(label=...)",
    observation_unit="N/A — the run ends before any observation could reach the model again",
)

CODING_AGENT = AgentSystem(
    name="Coding agent (writes and runs code to complete a task)",
    predicates=LoopPredicates(
        policy_is_a_language_model=True,
        has_hardcoded_pipeline_steps=False,
        model_chooses_the_action=True,
        loop_repeats_based_on_model_output=True,
        observation_reenters_model_context=True,
    ),
    model_role="Decide the next action: emit code (or a final answer) given everything observed so far",
    loop_description=(
        "Reason-act-observe: the model emits code, the environment executes it, the result is "
        "appended to context as an observation, and the model is called again with that new "
        "context. The model's own prior output is what determines its next input — this is "
        "the defining property of the loop, and it repeats until the model itself signals done "
        "or a budget/guardrail stops it."
    ),
    tools=["code interpreter/shell", "filesystem read/write"],
    environment="A workspace: filesystem + process/interpreter the code actually runs in",
    action_unit="A block of executable code",
    observation_unit="stdout/stderr/return value/traceback from running that code",
)

THERMOSTAT = AgentSystem(
    name="Home thermostat (closed loop, no model)",
    predicates=LoopPredicates(
        policy_is_a_language_model=False,   # a fixed rule: if temp < setpoint, heat on, else off
        has_hardcoded_pipeline_steps=True,
        model_chooses_the_action=True,      # the RULE chooses, structurally the same slot a model would fill
        loop_repeats_based_on_model_output=True,   # runs forever, each cycle conditioned on the last
        observation_reenters_model_context=True,   # the room's new temperature feeds the next decision
    ),
    model_role="N/A — there is no model; a fixed threshold rule plays the policy's structural role",
    loop_description=(
        "Measure temperature -> compare to setpoint -> turn heat on/off -> wait -> measure again, "
        "forever. This is a REAL closed feedback loop: the thermostat's own prior action (heat "
        "on) changes the environment (room warms), which changes the next observation (new "
        "temperature reading), which determines the next action. Every loop-shape predicate "
        "in this module is satisfied. It is excluded from the spectrum entirely — not placed "
        "at SINGLE_CALL or anywhere else — because the policy is a fixed rule, not a model; "
        "see the chapter README for why this is the point of including it."
    ),
    tools=["heater relay"],
    environment="A room; the thermostat's own sensor and actuator",
    action_unit="heat_on() or heat_off()",
    observation_unit="The next temperature reading",
)

ALL_SYSTEMS = [
    CHATBOT, RAG_PIPELINE, AGENTIC_RAG, SINGLE_TOOL_CALL_EXAMPLE, CODING_AGENT, THERMOSTAT,
]


def render_comparison_table(systems: list[AgentSystem]) -> str:
    """Render the model/loop/tools/environment breakdown as a plain-text table."""
    headers = ["System", "Autonomy", "Model-driven loop?", "Action unit", "Observation unit"]
    rows = [
        [
            s.name,
            s.autonomy.name,
            "YES" if s.has_model_driven_loop else "no",
            s.action_unit,
            s.observation_unit,
        ]
        for s in systems
    ]
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]

    def fmt_row(cells: list[str]) -> str:
        return " | ".join(c.ljust(w) for c, w in zip(cells, widths))

    sep = "-+-".join("-" * w for w in widths)
    lines = [fmt_row(headers), sep] + [fmt_row(r) for r in rows]
    return "\n".join(lines)


# Expected classification for each system, independent of how `classify_autonomy`
# is implemented — a hand-reasoned answer key. Used as a real correctness check
# (see __main__), not just documentation: if a future edit to `classify_autonomy`
# or to any system's predicates silently changes an outcome, this catches it.
EXPECTED_CLASSIFICATION = {
    "Customer-support chatbot": Autonomy.SINGLE_CALL,
    "RAG question-answering pipeline": Autonomy.FIXED_PIPELINE,
    "Agentic RAG (model decides whether to retrieve again)": Autonomy.AUTONOMOUS_LOOP,
    "Email auto-tagger (one tool call, no loop)": Autonomy.SINGLE_TOOL_CALL,
    "Coding agent (writes and runs code to complete a task)": Autonomy.AUTONOMOUS_LOOP,
    "Home thermostat (closed loop, no model)": Autonomy.NON_MODEL_CONTROL_LOOP,
}


if __name__ == "__main__":
    print(render_comparison_table(ALL_SYSTEMS))
    print()

    print("=== Classification check: derived autonomy vs. hand-reasoned expectation ===")
    all_match = True
    for system in ALL_SYSTEMS:
        expected = EXPECTED_CLASSIFICATION[system.name]
        match = system.autonomy == expected
        all_match &= match
        print(f"  {system.name:<55} derived={system.autonomy.name:<22} "
              f"expected={expected.name:<22} {'OK' if match else 'MISMATCH'}")
    assert all_match, "a system's derived autonomy disagreed with the hand-reasoned expectation"
    print("\nAll 6 systems: derived classification matches hand-reasoned expectation.")

    print("\n=== Full per-system breakdown ===")
    for system in ALL_SYSTEMS:
        print(f"--- {system.name} ({system.autonomy.name}) ---")
        print(f"  predicates:  {system.predicates}")
        print(f"  model_role:  {system.model_role}")
        print(f"  loop:        {system.loop_description}")
        print(f"  tools:       {system.tools}")
        print(f"  environment: {system.environment}")
        print()
