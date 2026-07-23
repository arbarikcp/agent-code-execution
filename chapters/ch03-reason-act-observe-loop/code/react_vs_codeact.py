"""Hand-write a ReAct trace for a task, then rewrite it as a CodeAct trace, and run
both through a real loop against a real (in-memory) environment.

There is no live model call yet — that starts in Chapter 5. What's scripted here
is only the *model's* output (`ScriptedReActModel`, `CODEACT_THOUGHT`/`CODEACT_CODE`
below play back fixed text instead of calling an LLM). The loop, the environment,
and the code execution are all real: `run_react_loop` actually calls `read_file`
three times and threads real observations back into context; `run_codeact_loop`
actually `exec()`s the CodeAct code block and captures its real stdout.

Task: which of a.txt, b.txt, c.txt holds the largest number, and what is that
number plus 10? (a.txt=42, b.txt=17, c.txt=8, so the answer is a.txt / 52.)
"""

import contextlib
import io
from dataclasses import dataclass

FAKE_WORKSPACE: dict[str, str] = {"a.txt": "42", "b.txt": "17", "c.txt": "8"}
TASK_PROMPT = (
    "Which of a.txt, b.txt, c.txt contains the largest number, "
    "and what is that number plus 10?"
)


def read_file(path: str) -> str:
    return FAKE_WORKSPACE[path]


# ---------------------------------------------------------------------------
# ReAct: interleaved Thought / Action / Observation, one tool call per step
# ---------------------------------------------------------------------------


@dataclass
class ReActStep:
    """One turn of a ReAct trace. `action is None` marks the final (Finish) step."""

    thought: str
    action: str | None
    action_input: str | None
    finish_answer: str | None = None


REACT_SCRIPT: list[ReActStep] = [
    ReActStep(
        thought="I need each file's value before I can compare them. Start with a.txt.",
        action="read_file",
        action_input="a.txt",
    ),
    ReActStep(
        thought="a.txt is 42. Now check b.txt.",
        action="read_file",
        action_input="b.txt",
    ),
    ReActStep(
        thought="b.txt is 17, smaller than 42 so far. Now check c.txt.",
        action="read_file",
        action_input="c.txt",
    ),
    ReActStep(
        thought="c.txt is 8. The largest value seen is 42, from a.txt. 42 + 10 = 52.",
        action=None,
        action_input=None,
        finish_answer="a.txt has the largest number (42); 42 + 10 = 52.",
    ),
]

TOOLS = {"read_file": read_file}


class ScriptedReActModel:
    """Plays back REACT_SCRIPT one step per call, standing in for a live model.

    Only this class is scripted. `run_react_loop` below calls it exactly the way
    it would call a real model: pass the accumulated context, get back the next
    step, execute the step's action for real, and feed the real result back in.
    """

    def __init__(self, script: list[ReActStep]) -> None:
        self._script = list(script)
        self._i = 0

    def __call__(self, context: str) -> ReActStep:
        step = self._script[self._i]
        self._i += 1
        return step


def run_react_loop(model: ScriptedReActModel, max_steps: int = 10) -> list[tuple[str, str]]:
    """The actual ReAct loop: call model -> Thought+Action -> execute -> Observation -> repeat.

    This is "loop pseudocode" made real: every Observation below comes from an
    actual `read_file` call against `FAKE_WORKSPACE`, not a scripted string.
    """
    transcript: list[tuple[str, str]] = []
    context = TASK_PROMPT
    for _ in range(max_steps):
        step = model(context)
        transcript.append(("Thought", step.thought))
        context += f"\nThought: {step.thought}"
        if step.action is None:
            transcript.append(("Finish", step.finish_answer or ""))
            return transcript
        observation = TOOLS[step.action](step.action_input)  # real call, real result
        transcript.append(("Action", f"{step.action}({step.action_input!r})"))
        transcript.append(("Observation", observation))
        context += f"\nAction: {step.action}({step.action_input!r})\nObservation: {observation}"
    raise RuntimeError("max_steps exceeded without a Finish step")


# ---------------------------------------------------------------------------
# CodeAct: one Thought, one executable code action, real execution
# ---------------------------------------------------------------------------

CODEACT_THOUGHT = "I'll read all three files, compare them, and compute the answer in one action."

CODEACT_CODE = '''\
values = {f: int(read_file(f)) for f in ["a.txt", "b.txt", "c.txt"]}
largest_file = max(values, key=values.get)
result = values[largest_file] + 10
print(f"{largest_file} has the largest number ({values[largest_file]}); "
      f"{values[largest_file]} + 10 = {result}")
'''


def run_codeact_loop(thought: str, code: str, env_globals: dict) -> list[tuple[str, str]]:
    """The actual CodeAct loop: one Thought, one code action, real `exec()`, real stdout.

    `env_globals` is the namespace the code runs in — here just `{"read_file": read_file}`,
    standing in for the tool-registry-as-namespace idea Chapter 28 develops fully.
    """
    transcript: list[tuple[str, str]] = [("Thought", thought)]
    transcript.append(("Action (code)", code.strip()))

    buf = io.StringIO()
    exec_globals = dict(env_globals)
    with contextlib.redirect_stdout(buf):
        exec(code, exec_globals)  # real execution, real side effects
    observation = buf.getvalue().strip()

    transcript.append(("Observation", observation))
    transcript.append(("Finish", observation))
    return transcript


# ---------------------------------------------------------------------------
# A real failure class: correct Observations, wrong Thought-level arithmetic
# ---------------------------------------------------------------------------
#
# PAL's own abstract (Gao et al., verified quote in the chapter README) names
# this exact failure mode: "LLMs often make logical and arithmetic mistakes
# in the solution part, even when the problem is decomposed correctly." ReAct
# is vulnerable to precisely this, in a way CodeAct structurally is not: a
# ReAct trace's running comparison ("is X bigger than the max so far?") lives
# entirely in free-form Thought text, re-derived by the model at every step,
# with NOTHING in the loop verifying a Thought's claim against the actual
# numbers. Two scripts below share IDENTICAL, correct Observations (every
# read_file call returns the true value) but differ at exactly one Thought's
# arithmetic — showing the loop has no mechanism to catch a wrong claim about
# data it already observed correctly.

LONG_WORKSPACE: dict[str, str] = {
    "a.txt": "42", "b.txt": "17", "c.txt": "8", "d.txt": "55", "e.txt": "31", "f.txt": "9",
}
LONG_TASK_PROMPT = (
    "Which of a.txt..f.txt contains the largest number, and what is that number plus 10?"
)


def read_long_file(path: str) -> str:
    return LONG_WORKSPACE[path]


LONG_TOOLS = {"read_file": read_long_file}

# Ground truth, computed independently of either script below.
_EXPECTED_MAX_FILE = max(LONG_WORKSPACE, key=lambda f: int(LONG_WORKSPACE[f]))
_EXPECTED_MAX_VALUE = int(LONG_WORKSPACE[_EXPECTED_MAX_FILE])
_EXPECTED_ANSWER = f"{_EXPECTED_MAX_FILE} has the largest number ({_EXPECTED_MAX_VALUE}); {_EXPECTED_MAX_VALUE} + 10 = {_EXPECTED_MAX_VALUE + 10}."

CORRECT_LONG_REACT_SCRIPT: list[ReActStep] = [
    ReActStep("Check a.txt first.", "read_file", "a.txt"),
    ReActStep("a.txt is 42. Current max is 42 (a.txt). Check b.txt.", "read_file", "b.txt"),
    ReActStep("b.txt is 17. 17 < 42, so max stays 42 (a.txt). Check c.txt.", "read_file", "c.txt"),
    ReActStep("c.txt is 8. 8 < 42, so max stays 42 (a.txt). Check d.txt.", "read_file", "d.txt"),
    ReActStep("d.txt is 55. 55 > 42, so the new max is 55 (d.txt). Check e.txt.", "read_file", "e.txt"),
    ReActStep("e.txt is 31. 31 < 55, so max stays 55 (d.txt). Check f.txt.", "read_file", "f.txt"),
    ReActStep(
        "f.txt is 9. 9 < 55, so max stays 55 (d.txt). That was the last file.",
        action=None, action_input=None,
        finish_answer=_EXPECTED_ANSWER,
    ),
]

# Identical Observations to the script above (every read_file call is real and
# correct) — the ONLY difference is the Thought at step 5, which misreads the
# comparison (claims 55 is NOT bigger than 42) exactly the way PAL's abstract
# describes: correct decomposition (it did check the right file), wrong
# arithmetic in the solution part.
FLAWED_LONG_REACT_SCRIPT: list[ReActStep] = [
    ReActStep("Check a.txt first.", "read_file", "a.txt"),
    ReActStep("a.txt is 42. Current max is 42 (a.txt). Check b.txt.", "read_file", "b.txt"),
    ReActStep("b.txt is 17. 17 < 42, so max stays 42 (a.txt). Check c.txt.", "read_file", "c.txt"),
    ReActStep("c.txt is 8. 8 < 42, so max stays 42 (a.txt). Check d.txt.", "read_file", "d.txt"),
    ReActStep(  # <-- the injected flaw: the Observation is 55, but the Thought below misjudges it
        "d.txt is 55. That's less than 42, so max stays 42 (a.txt). Check e.txt.",
        "read_file", "e.txt",
    ),
    ReActStep("e.txt is 31. 31 < 42, so max stays 42 (a.txt). Check f.txt.", "read_file", "f.txt"),
    ReActStep(
        "f.txt is 9. 9 < 42, so max stays 42 (a.txt). That was the last file.",
        action=None, action_input=None,
        finish_answer="a.txt has the largest number (42); 42 + 10 = 52.",  # wrong: real max is 55
    ),
]


def run_long_react_loop(script: list[ReActStep], max_steps: int = 10) -> list[tuple[str, str]]:
    """Same loop mechanics as run_react_loop, against the 6-file workspace/tools."""
    transcript: list[tuple[str, str]] = []
    context = LONG_TASK_PROMPT
    model = ScriptedReActModel(script)
    for _ in range(max_steps):
        step = model(context)
        transcript.append(("Thought", step.thought))
        context += f"\nThought: {step.thought}"
        if step.action is None:
            transcript.append(("Finish", step.finish_answer or ""))
            return transcript
        observation = LONG_TOOLS[step.action](step.action_input)  # real call, real (correct) result
        transcript.append(("Action", f"{step.action}({step.action_input!r})"))
        transcript.append(("Observation", observation))
        context += f"\nAction: {step.action}({step.action_input!r})\nObservation: {observation}"
    raise RuntimeError("max_steps exceeded without a Finish step")


def run_long_codeact_loop() -> tuple[list[tuple[str, str]], str]:
    """The same 6-file task as one CodeAct action — correctness delegated to max()."""
    thought = "I'll read all six files and let Python's max() find the largest — no manual tracking."
    code = (
        'values = {f: int(read_file(f)) for f in ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt", "f.txt"]}\n'
        "largest_file = max(values, key=values.get)\n"
        "result = values[largest_file] + 10\n"
        'print(f"{largest_file} has the largest number ({values[largest_file]}); '
        '{values[largest_file]} + 10 = {result}.")\n'
    )
    transcript = run_codeact_loop(thought, code, {"read_file": read_long_file})
    final_answer = transcript[-1][1]
    return transcript, final_answer


# ---------------------------------------------------------------------------
# Historical lineage — verified titles/authors/dates (see chapter README)
# ---------------------------------------------------------------------------

HISTORICAL_TIMELINE = [
    (
        "2022-10-06", "ReAct",
        "Yao, Zhao, Yu, Du, Shafran, Narasimhan, Cao — arXiv:2210.03629",
        "Interleaves free-text Thought/Action/Observation steps; the action is a "
        "call into a small, fixed tool set, expressed and parsed as text.",
    ),
    (
        "2022-11-18", "PAL",
        "Gao, Madaan, Zhou, Alon, Liu, Yang, Callan, Neubig — arXiv:2211.10435",
        "Verified abstract quote: 'LLMs often make logical and arithmetic mistakes "
        "in the solution part, even when the problem is decomposed correctly.' "
        "PAL delegates the solution/computation step to a real Python interpreter "
        "while leaving decomposition to the LLM — 'PAL using Codex achieves "
        "state-of-the-art few-shot accuracy on GSM8K, surpassing PaLM-540B which "
        "uses chain-of-thought by absolute 15% top-1' (verified abstract claim). "
        "This is the exact failure class the FLAWED_LONG_REACT_SCRIPT demo below "
        "reproduces on purpose.",
    ),
    (
        "2023-02-09", "Toolformer",
        "Schick, Dwivedi-Yu, Dessi, Raileanu, Lomeli, Zettlemoyer, Cancedda, Scialom — arXiv:2302.04761",
        "Verified abstract quote: the model learns, self-supervised, 'which APIs "
        "to call, when to call them, what arguments to pass, and how to best "
        "incorporate the results into future token prediction,' from as few as "
        "'a handful of demonstrations for each API.' Different axis from PAL/"
        "CodeAct: not code-as-computation, but training the tool-use DECISION "
        "into the model itself rather than eliciting it via prompting.",
    ),
    (
        "2024-02-01", "CodeAct",
        "Wang, Chen, Yuan, Zhang, Li, Peng, Ji — arXiv:2402.01030",
        "Proposes executable code as a unified action space for a ReAct-style "
        "loop, replacing one-tool-per-turn text/JSON actions with a single "
        "Python action that can call any available tool/library and compose "
        "them with real control flow.",
    ),
]


def render_timeline() -> str:
    lines = []
    for date, name, citation, description in HISTORICAL_TIMELINE:
        lines.append(f"{date}  {name}")
        lines.append(f"           {citation}")
        lines.append(f"           {description}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== ReAct trace ===")
    react_transcript = run_react_loop(ScriptedReActModel(REACT_SCRIPT))
    for kind, text in react_transcript:
        print(f"{kind}: {text}")

    print(f"\nReAct: {sum(1 for k, _ in react_transcript if k == 'Action')} actions, "
          f"{len(react_transcript)} trace entries")

    print("\n=== CodeAct trace ===")
    codeact_transcript = run_codeact_loop(CODEACT_THOUGHT, CODEACT_CODE, {"read_file": read_file})
    for kind, text in codeact_transcript:
        print(f"{kind}: {text}")

    print(f"\nCodeAct: {sum(1 for k, _ in codeact_transcript if k.startswith('Action'))} actions, "
          f"{len(codeact_transcript)} trace entries")

    print("\n=== A real failure class: correct Observations, wrong Thought-level arithmetic ===")
    print(f"Ground truth (computed independently): {_EXPECTED_ANSWER}")

    correct_transcript = run_long_react_loop(CORRECT_LONG_REACT_SCRIPT)
    correct_answer = correct_transcript[-1][1]
    print(f"\nCORRECT ReAct script finish:  {correct_answer!r}")
    print(f"  matches ground truth: {correct_answer == _EXPECTED_ANSWER}")

    flawed_transcript = run_long_react_loop(FLAWED_LONG_REACT_SCRIPT)
    flawed_answer = flawed_transcript[-1][1]
    print(f"\nFLAWED ReAct script finish:  {flawed_answer!r}")
    print(f"  matches ground truth: {flawed_answer == _EXPECTED_ANSWER}  <- wrong, despite every Observation being correct")

    all_observations_correct = all(
        obs == LONG_WORKSPACE[action.split("(")[1].strip("')")]
        for (kind, action), (kind2, obs) in zip(flawed_transcript, flawed_transcript[1:])
        if kind == "Action"
    )
    print(f"  every Observation in the flawed trace was still correct: {all_observations_correct}")

    codeact_long_transcript, codeact_long_answer = run_long_codeact_loop()
    print(f"\nCodeAct (max() delegated to the interpreter): {codeact_long_answer!r}")
    print(f"  matches ground truth: {codeact_long_answer == _EXPECTED_ANSWER}")

    print("\n=== Historical timeline ===")
    print(render_timeline())
