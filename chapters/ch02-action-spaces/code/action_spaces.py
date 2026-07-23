"""Express the same 3-step task as free text, JSON tool calls, and a single code action.

The task: files a.txt, b.txt, c.txt each hold one integer; sum them and write the
result to total.txt. It's deliberately small — the point isn't the task, it's
counting *turns* and *tokens* each action space needs to do it, using a real
tokenizer (tiktoken) instead of asserted numbers.

A real filesystem/workspace doesn't exist yet in this guide (that's Chapter 11);
`FAKE_WORKSPACE` below is an in-memory stand-in just so `read_file`/`write_file`
have something to act on for this comparison.
"""

from dataclasses import dataclass, field

import tiktoken

# ---------------------------------------------------------------------------
# The task and its "environment" (in-memory stand-in; see module docstring)
# ---------------------------------------------------------------------------

FAKE_WORKSPACE: dict[str, str] = {"a.txt": "42", "b.txt": "17", "c.txt": "8"}
TASK_PROMPT = (
    "Files a.txt, b.txt, and c.txt each contain one integer. "
    "Compute their sum and write it to total.txt."
)


def read_file(path: str) -> str:
    return FAKE_WORKSPACE[path]


def write_file(path: str, content: str) -> str:
    FAKE_WORKSPACE[path] = content
    return f"ok: wrote {len(content)} bytes to {path}"


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------

_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Approximate token count via tiktoken's cl100k_base encoding.

    This is a proxy, not the exact tokenizer of whatever model the backbone
    agent ends up calling (that's chosen per-run via litellm from Chapter 5
    onward) — it's used here only so the comparisons below are a real,
    reproducible measurement instead of an invented number.
    """
    return len(_ENCODING.encode(text))


# ---------------------------------------------------------------------------
# 1. Free-text actions — early prompting style, shown for its fragility
# ---------------------------------------------------------------------------
# The model describes what it wants done in a sentence; a hand-written parser
# has to guess the intent. There's no schema, so "call read_file with a.txt"
# and "please read a.txt for me" and "I'll need the contents of a.txt" are all
# valid-looking free text that a regex/keyword parser must all handle — and it
# will inevitably miss phrasings the model tries later. We show one turn, not
# a full trace: free text doesn't scale to multi-step composition without
# reinventing structure (which is exactly what JSON tool calling adds).

FREE_TEXT_EXAMPLE = (
    "I should start by reading the contents of a.txt so I know the first number."
)
FREE_TEXT_AMBIGUOUS_VARIANTS = [
    "I should start by reading the contents of a.txt so I know the first number.",
    "Let's open a.txt and see what's inside.",
    "First, can you get me a.txt?",
    "Read: a.txt",
]


# ---------------------------------------------------------------------------
# 2. Structured tool calling (JSON / function calling)
# ---------------------------------------------------------------------------

JSON_SYSTEM_PROMPT = (
    "You are an assistant with access to tools. On each turn, call exactly one "
    "tool by responding with a single JSON object of the form "
    '{"tool": "<name>", "arguments": {...}}. When the task is fully complete, '
    "respond with plain text instead of a tool call."
)

TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read the entire contents of a text file in the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file, relative to the workspace root."},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write text content to a file in the workspace, overwriting it if it exists.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file, relative to the workspace root."},
                "content": {"type": "string", "description": "The text content to write."},
            },
            "required": ["path", "content"],
        },
    },
]


@dataclass
class Turn:
    """One model call: what it saw (input) and what it emitted (output)."""

    label: str
    input_text: str
    output_text: str
    input_tokens: int = field(init=False)
    output_tokens: int = field(init=False)

    def __post_init__(self) -> None:
        self.input_tokens = count_tokens(self.input_text)
        self.output_tokens = count_tokens(self.output_text)


def build_json_tool_call_trace() -> list[Turn]:
    """Reconstruct the 3-step task as JSON tool calls, one tool per model turn.

    Each turn's *input* is the full context the model would need: system
    prompt + tool schemas + task + every prior action/observation. That's the
    realistic cost — a stateless chat-completions call resends history every
    turn — not just the marginal new text.
    """
    tool_schema_text = str(TOOL_SCHEMAS)
    history = ""
    turns: list[Turn] = []

    def context() -> str:
        return f"{JSON_SYSTEM_PROMPT}\n\nTOOLS:\n{tool_schema_text}\n\nTASK:\n{TASK_PROMPT}\n\n{history}"

    # Turn 1: read a.txt
    call = '{"tool": "read_file", "arguments": {"path": "a.txt"}}'
    turns.append(Turn("read a.txt", context(), call))
    obs = read_file("a.txt")
    history += f"ASSISTANT: {call}\nTOOL RESULT: {obs}\n"

    # Turn 2: read b.txt
    call = '{"tool": "read_file", "arguments": {"path": "b.txt"}}'
    turns.append(Turn("read b.txt", context(), call))
    obs = read_file("b.txt")
    history += f"ASSISTANT: {call}\nTOOL RESULT: {obs}\n"

    # Turn 3: read c.txt
    call = '{"tool": "read_file", "arguments": {"path": "c.txt"}}'
    turns.append(Turn("read c.txt", context(), call))
    obs = read_file("c.txt")
    history += f"ASSISTANT: {call}\nTOOL RESULT: {obs}\n"

    # Turn 4: write total.txt (the model must have summed 42+17+8=67 itself)
    total = 42 + 17 + 8
    call = f'{{"tool": "write_file", "arguments": {{"path": "total.txt", "content": "{total}"}}}}'
    turns.append(Turn("write total.txt", context(), call))
    obs = write_file("total.txt", str(total))
    history += f"ASSISTANT: {call}\nTOOL RESULT: {obs}\n"

    # Turn 5: final answer, no more tool calls
    final = f"The sum of the three files is {total}, written to total.txt."
    turns.append(Turn("final answer", context(), final))

    return turns


# ---------------------------------------------------------------------------
# 3. Code actions
# ---------------------------------------------------------------------------

CODE_SYSTEM_PROMPT = (
    "You are an assistant that solves tasks by writing and running Python code. "
    "Respond with a single ```python code block; it will be executed in a "
    "workspace where `read_file(path)` and `write_file(path, content)` are "
    "already available. You will see stdout after execution. When the task is "
    "fully complete, respond with plain text instead of a code block."
)


def build_code_action_trace() -> list[Turn]:
    """Reconstruct the same task as a single code action plus a final answer."""
    history = ""
    turns: list[Turn] = []

    def context() -> str:
        return f"{CODE_SYSTEM_PROMPT}\n\nTASK:\n{TASK_PROMPT}\n\n{history}"

    code = (
        "```python\n"
        'total = sum(int(read_file(f).strip()) for f in ["a.txt", "b.txt", "c.txt"])\n'
        'write_file("total.txt", str(total))\n'
        "print(total)\n"
        "```"
    )
    turns.append(Turn("compute + write (one action)", context(), code))

    total = sum(int(read_file(f).strip()) for f in ["a.txt", "b.txt", "c.txt"])
    write_file("total.txt", str(total))
    stdout = str(total)
    history += f"ASSISTANT:\n{code}\nSTDOUT: {stdout}\n"

    final = f"The sum of the three files is {total}, written to total.txt."
    turns.append(Turn("final answer", context(), final))

    return turns


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def summarize(trace: list[Turn]) -> dict:
    return {
        "turns": len(trace),
        "input_tokens": sum(t.input_tokens for t in trace),
        "output_tokens": sum(t.output_tokens for t in trace),
        "total_tokens": sum(t.input_tokens + t.output_tokens for t in trace),
    }


def render_comparison() -> str:
    json_trace = build_json_tool_call_trace()
    code_trace = build_code_action_trace()
    json_summary = summarize(json_trace)
    code_summary = summarize(code_trace)

    lines = [
        f"{'Action space':<20} | {'Turns':>6} | {'Input tok':>10} | {'Output tok':>11} | {'Total tok':>10}",
        "-" * 20 + "-+-" + "-" * 6 + "-+-" + "-" * 10 + "-+-" + "-" * 11 + "-+-" + "-" * 10,
        f"{'JSON tool calls':<20} | {json_summary['turns']:>6} | {json_summary['input_tokens']:>10} | "
        f"{json_summary['output_tokens']:>11} | {json_summary['total_tokens']:>10}",
        f"{'Single code action':<20} | {code_summary['turns']:>6} | {code_summary['input_tokens']:>10} | "
        f"{code_summary['output_tokens']:>11} | {code_summary['total_tokens']:>10}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_comparison())
    print()
    json_trace = build_json_tool_call_trace()
    code_trace = build_code_action_trace()
    print(f"JSON mode: {len(json_trace)} model turns")
    for t in json_trace:
        print(f"  - {t.label}: input={t.input_tokens} tok, output={t.output_tokens} tok")
    print(f"\nCode mode: {len(code_trace)} model turns")
    for t in code_trace:
        print(f"  - {t.label}: input={t.input_tokens} tok, output={t.output_tokens} tok")
