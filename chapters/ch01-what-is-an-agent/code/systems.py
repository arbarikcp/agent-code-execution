"""Label three real systems by the four parts of an agent: model, loop, tools, environment.

The point of this module is not the code — it's the exercise. Chapter 1's claim is that
"agent" names a specific shape (a model-driven loop coupling actions to an environment),
not a vibe. Writing each system's parts down as data forces you to answer, concretely,
whether that shape is present.
"""

from dataclasses import dataclass, field
from enum import Enum


class Autonomy(Enum):
    """Where a system sits on the fixed-orchestration -> model-driven-loop spectrum.

    Ordered low to high. The name of the enum member is the vocabulary Chapter 1
    asks you to use when describing a system, so the values matter more than
    their numeric order.
    """

    SINGLE_CALL = 1        # one model call, no branching, no environment loop
    FIXED_PIPELINE = 2     # a hardcoded sequence of steps; the model fills in content, not control flow
    SINGLE_TOOL_CALL = 3   # the model picks zero or one tool per turn, no iteration on the result
    AUTONOMOUS_LOOP = 4    # the model's own output determines the next action, repeatedly, until it stops itself


@dataclass
class AgentSystem:
    """The four parts CLAUDE.md and Chapter 1 insist on separating.

    `has_model_driven_loop` is the field that actually answers "is this an agent?" —
    per the chapter's thesis, an agent is the loop, not the model. A system can have a
    powerful model and still not be an agent if nothing feeds the model's output back
    to it as a new observation.
    """

    name: str
    autonomy: Autonomy
    model_role: str            # what the model is asked to produce each call
    loop_description: str      # what drives the next step, if anything
    has_model_driven_loop: bool  # does the MODEL's own output pick the next action?
    tools: list[str] = field(default_factory=list)
    environment: str = ""      # what the action acts on / the observation comes from
    action_unit: str = ""      # the thing the model emits as "an action"
    observation_unit: str = ""  # the thing that comes back and re-enters context


CHATBOT = AgentSystem(
    name="Customer-support chatbot",
    autonomy=Autonomy.SINGLE_CALL,
    model_role="Generate the next reply in a conversation",
    loop_description=(
        "None in the agentic sense: a human types, the model replies, the human types again. "
        "The 'loop' is a human-in-the-loop UI turn-taker, not a model-driven control loop — "
        "the model never decides what happens next in the environment, only what to say."
    ),
    has_model_driven_loop=False,
    tools=[],
    environment="A chat transcript the human reads and appends to",
    action_unit="A chat message",
    observation_unit="The human's next message (not a consequence of the agent's own action)",
)

RAG_PIPELINE = AgentSystem(
    name="RAG question-answering pipeline",
    autonomy=Autonomy.FIXED_PIPELINE,
    model_role="Generate an answer conditioned on retrieved passages",
    loop_description=(
        "A fixed graph: embed query -> vector search -> stuff top-k into prompt -> generate. "
        "The sequence of steps is hardcoded by the engineer, every run, regardless of what "
        "the model says. The model cannot decide to retrieve again, retrieve differently, "
        "or take any action other than 'produce the final text'."
    ),
    has_model_driven_loop=False,
    tools=["vector_search (called by the pipeline, not by the model)"],
    environment="A document/vector store, queried once per pipeline run on a fixed schedule",
    action_unit="N/A — the model does not choose actions, only generates text",
    observation_unit="N/A — retrieved passages are pipeline input, not a returned observation",
)

CODING_AGENT = AgentSystem(
    name="Coding agent (writes and runs code to complete a task)",
    autonomy=Autonomy.AUTONOMOUS_LOOP,
    model_role="Decide the next action: emit code (or a final answer) given everything observed so far",
    loop_description=(
        "Reason-act-observe: the model emits code, the environment executes it, the result is "
        "appended to context as an observation, and the model is called again with that new "
        "context. The model's own prior output is what determines its next input — this is "
        "the defining property of the loop, and it repeats until the model itself signals done "
        "or a budget/guardrail stops it."
    ),
    has_model_driven_loop=True,
    tools=["code interpreter/shell", "filesystem read/write"],
    environment="A workspace: filesystem + process/interpreter the code actually runs in",
    action_unit="A block of executable code",
    observation_unit="stdout/stderr/return value/traceback from running that code",
)

ALL_SYSTEMS = [CHATBOT, RAG_PIPELINE, CODING_AGENT]


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


if __name__ == "__main__":
    print(render_comparison_table(ALL_SYSTEMS))
    print()
    for system in ALL_SYSTEMS:
        print(f"=== {system.name} ===")
        print(f"  model_role:  {system.model_role}")
        print(f"  loop:        {system.loop_description}")
        print(f"  tools:       {system.tools}")
        print(f"  environment: {system.environment}")
        print()
