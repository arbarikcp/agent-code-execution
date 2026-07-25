"""Deterministic trace accounting for three action-space examples:

1. A SCALING SWEEP: the "sum k files" task run across k=1..30, showing how
   JSON tool calling's cost grows with task size versus a code action's —
   not just one snapshot at k=3.
2. A small free-text parser run against 8 selected phrasings, demonstrating
   missed and silently wrong extractions. This is not an accuracy benchmark.
3. A boundary check: a HETEROGENEOUS task (three different
   operations, not one operation repeated k times) to see whether code's
   trace changes when the task cannot be expressed as a generic loop.

The module constructs messages and counts text. It does not call a model,
execute the represented operations, measure latency, or estimate billing.
"""

import re
from dataclasses import dataclass, field

import tiktoken

# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------

_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Approximate token count via tiktoken's cl100k_base encoding.

    A proxy, not the exact tokenizer of whatever model the backbone agent
    calls (chosen per-run via litellm from Chapter 5 onward) — used here so
    every comparison below is a real, reproducible measurement, not an
    invented number.
    """
    return len(_ENCODING.encode(text))


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


def summarize(trace: list[Turn]) -> dict:
    return {
        "turns": len(trace),
        "input_tokens": sum(t.input_tokens for t in trace),
        "output_tokens": sum(t.output_tokens for t in trace),
        "total_tokens": sum(t.input_tokens + t.output_tokens for t in trace),
    }


# ---------------------------------------------------------------------------
# 1. Free-text actions — fragility, MEASURED against a real naive parser
# ---------------------------------------------------------------------------
#
# A first-draft parser a developer might actually write: a short keyword
# list plus a filename regex. Deliberately narrow (not "the best parser
# possible") because the point is what a REASONABLE first attempt misses,
# not what's theoretically achievable with enough regex effort.

_READ_KEYWORDS = ["read", "open"]
_FILENAME_RE = re.compile(r"\b([\w\-]+\.\w+)\b")


def naive_parse_read_intent(text: str) -> str | None:
    """Return the filename the text seems to want read, or None if unrecognized."""
    text_lower = text.lower()
    if not any(kw in text_lower for kw in _READ_KEYWORDS):
        return None
    match = _FILENAME_RE.search(text)
    return match.group(1) if match else None


# (text, expected filename or None if the parser SHOULD fail to find one)
FREE_TEXT_VARIANTS: list[tuple[str, str | None]] = [
    ("I should start by reading the contents of a.txt so I know the first number.", "a.txt"),
    ("Let's open a.txt and see what's inside.", "a.txt"),
    ("First, can you get me a.txt?", "a.txt"),        # no "read"/"open" -> parser will miss this
    ("Read: a.txt", "a.txt"),
    ("I'll read the file called a.txt now.", "a.txt"),
    ("Could you check what's in a.txt for me?", "a.txt"),   # "check", not "read"/"open" -> miss
    ("Peek into a.txt quickly.", "a.txt"),                   # "peek" -> miss
    ("Could you read the file named 'lab notes.txt'?", "lab notes.txt"),  # keyword hits, but the
    # filename has a space, so \w+ stops at "notes.txt" — a WRONG (not missing) extraction,
    # which is a worse failure mode than returning None: it looks successful.
]


def evaluate_free_text_parser(variants: list[tuple[str, str | None]]) -> list[dict]:
    results = []
    for text, expected in variants:
        got = naive_parse_read_intent(text)
        if got == expected:
            outcome = "CORRECT"
        elif got is None:
            outcome = "MISSED"       # failed to detect intent at all
        else:
            outcome = "WRONG"        # detected intent, extracted the wrong filename
        results.append({"text": text, "expected": expected, "got": got, "outcome": outcome})
    return results


# ---------------------------------------------------------------------------
# 2. Structured tool calling (JSON / function calling) — now sized by k
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


def build_workspace(k: int) -> dict[str, str]:
    return {f"f{i}.txt": str((i * 7 + 3) % 50 + 1) for i in range(k)}


def build_json_tool_call_trace(k: int) -> list[Turn]:
    """Sum k files as k `read_file` calls + 1 `write_file` call + 1 final answer.

    Each turn's *input* is the full context that call would need: system
    prompt + tool schemas + task + every prior action/observation — the
    realistic cost, since a stateless chat-completions call resends history
    every turn, not just the marginal new text.
    """
    ws = build_workspace(k)
    task_prompt = f"Files {list(ws.keys())} each contain one integer. Compute their sum and write it to total.txt."
    tool_schema_text = str(TOOL_SCHEMAS)
    history = ""
    turns: list[Turn] = []

    def context() -> str:
        return f"{JSON_SYSTEM_PROMPT}\n\nTOOLS:\n{tool_schema_text}\n\nTASK:\n{task_prompt}\n\n{history}"

    total = 0
    for name, value in ws.items():
        call = f'{{"tool": "read_file", "arguments": {{"path": "{name}"}}}}'
        turns.append(Turn(f"read {name}", context(), call))
        total += int(value)
        history += f"ASSISTANT: {call}\nTOOL RESULT: {value}\n"

    call = f'{{"tool": "write_file", "arguments": {{"path": "total.txt", "content": "{total}"}}}}'
    turns.append(Turn("write total.txt", context(), call))
    history += f"ASSISTANT: {call}\nTOOL RESULT: ok: wrote {len(str(total))} bytes to total.txt\n"

    final = f"The sum of the {k} files is {total}, written to total.txt."
    turns.append(Turn("final answer", context(), final))
    return turns


# ---------------------------------------------------------------------------
# 3. Code actions — now sized by k, via a generic loop (not enumerated)
# ---------------------------------------------------------------------------

CODE_SYSTEM_PROMPT = (
    "You are an assistant that solves tasks by writing and running Python code. "
    "Respond with a single ```python code block; it will be executed in a "
    "workspace where `read_file(path)` and `write_file(path, content)` are "
    "already available. You will see stdout after execution. When the task is "
    "fully complete, respond with plain text instead of a code block."
)


def build_code_action_trace(k: int) -> list[Turn]:
    """Sum k files as a single generic code action + a final answer.

    The code doesn't enumerate k filenames — it loops over `range(k)` — so
    its own size stays close to constant as k grows. This is precisely the
    "composability" mechanism: one action's SIZE doesn't have to grow with
    the number of operations it performs, unlike JSON's TURN count.
    """
    ws = build_workspace(k)
    task_prompt = f"{k} files (f0.txt .. f{k-1}.txt) each contain one integer. Compute their sum and write it to total.txt."
    history = ""
    turns: list[Turn] = []

    def context() -> str:
        return f"{CODE_SYSTEM_PROMPT}\n\nTASK:\n{task_prompt}\n\n{history}"

    code = (
        "```python\n"
        f'total = sum(int(read_file(f"f{{i}}.txt")) for i in range({k}))\n'
        'write_file("total.txt", str(total))\n'
        "print(total)\n"
        "```"
    )
    turns.append(Turn("compute + write (one action)", context(), code))

    total = sum(int(v) for v in ws.values())
    history += f"ASSISTANT:\n{code}\nSTDOUT: {total}\n"

    final = f"The sum of the {k} files is {total}, written to total.txt."
    turns.append(Turn("final answer", context(), final))
    return turns


def sweep_k(ks: list[int]) -> list[dict]:
    """Measure both action spaces across a range of task sizes k."""
    rows = []
    for k in ks:
        json_summary = summarize(build_json_tool_call_trace(k))
        code_summary = summarize(build_code_action_trace(k))
        rows.append({
            "k": k,
            "json_turns": json_summary["turns"],
            "json_tokens": json_summary["total_tokens"],
            "code_turns": code_summary["turns"],
            "code_tokens": code_summary["total_tokens"],
        })
    return rows


def marginal_json_token_cost(rows: list[dict]) -> list[tuple[int, int, float]]:
    """Per-additional-file token cost between consecutive k values in the sweep.

    A flat (constant) series here would mean JSON's total cost grows LINEARLY
    with k. A rising series means each additional file costs MORE than the
    last — i.e. superlinear (roughly quadratic) growth, because every
    already-answered file's read/observation gets resent in every later
    turn's context, so adding file k+1 doesn't just add file k+1's own cost,
    it also lengthens every turn that comes after it.
    """
    deltas = []
    for prev, curr in zip(rows, rows[1:]):
        dk = curr["k"] - prev["k"]
        dtokens = curr["json_tokens"] - prev["json_tokens"]
        deltas.append((curr["k"], dk, dtokens / dk))  # per-additional-k marginal cost
    return deltas


def render_sweep(rows: list[dict]) -> str:
    lines = [f"{'k':>3} | {'json turns':>10} | {'json tokens':>11} | {'code turns':>10} | {'code tokens':>11} | {'token ratio':>11}"]
    lines.append("-" * len(lines[0]))
    for r in rows:
        ratio = r["json_tokens"] / r["code_tokens"]
        lines.append(
            f"{r['k']:>3} | {r['json_turns']:>10} | {r['json_tokens']:>11} | "
            f"{r['code_turns']:>10} | {r['code_tokens']:>11} | {ratio:>10.1f}x"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Boundary check: a HETEROGENEOUS task (no generic loop possible)
# ---------------------------------------------------------------------------

HETEROGENEOUS_WORKSPACE = {"a.txt": "hello world", "b.txt": "python rocks", "c.txt": "one two three four"}
HETEROGENEOUS_TASK = (
    "Uppercase the text in a.txt and write it to a.out; reverse the text in "
    "b.txt and write it to b.out; count the words in c.txt and write the "
    "count to c.out."
)


def build_heterogeneous_json_trace() -> list[Turn]:
    """3 reads + 3 (different) writes + 1 final — no operation repeats, so
    nothing about JSON's turn count changes versus the uniform case."""
    tool_schema_text = str(TOOL_SCHEMAS)
    history = ""
    turns: list[Turn] = []

    def context() -> str:
        return f"{JSON_SYSTEM_PROMPT}\n\nTOOLS:\n{tool_schema_text}\n\nTASK:\n{HETEROGENEOUS_TASK}\n\n{history}"

    ops = [
        ("a.txt", "a.out", HETEROGENEOUS_WORKSPACE["a.txt"].upper()),
        ("b.txt", "b.out", HETEROGENEOUS_WORKSPACE["b.txt"][::-1]),
        ("c.txt", "c.out", str(len(HETEROGENEOUS_WORKSPACE["c.txt"].split()))),
    ]
    for src, dst, _ in ops:
        call = f'{{"tool": "read_file", "arguments": {{"path": "{src}"}}}}'
        turns.append(Turn(f"read {src}", context(), call))
        history += f"ASSISTANT: {call}\nTOOL RESULT: {HETEROGENEOUS_WORKSPACE[src]}\n"

    for src, dst, result in ops:
        call = f'{{"tool": "write_file", "arguments": {{"path": "{dst}", "content": "{result}"}}}}'
        turns.append(Turn(f"write {dst}", context(), call))
        history += f"ASSISTANT: {call}\nTOOL RESULT: ok\n"

    turns.append(Turn("final answer", context(), "Done: a.out, b.out, c.out written."))
    return turns


def build_heterogeneous_code_trace() -> list[Turn]:
    """One action, but now it CAN'T be a generic loop — three bespoke lines."""
    history = ""
    turns: list[Turn] = []

    def context() -> str:
        return f"{CODE_SYSTEM_PROMPT}\n\nTASK:\n{HETEROGENEOUS_TASK}\n\n{history}"

    code = (
        "```python\n"
        'write_file("a.out", read_file("a.txt").upper())\n'
        'write_file("b.out", read_file("b.txt")[::-1])\n'
        'write_file("c.out", str(len(read_file("c.txt").split())))\n'
        'print("done")\n'
        "```"
    )
    turns.append(Turn("three bespoke ops (one action)", context(), code))
    history += f"ASSISTANT:\n{code}\nSTDOUT: done\n"
    turns.append(Turn("final answer", context(), "Done: a.out, b.out, c.out written."))
    return turns


if __name__ == "__main__":
    print("=== 1. Free-text parser: measured hit rate ===")
    results = evaluate_free_text_parser(FREE_TEXT_VARIANTS)
    for r in results:
        print(f"  [{r['outcome']:7}] {r['text']!r:65} -> got={r['got']!r}")
    n_correct = sum(1 for r in results if r["outcome"] == "CORRECT")
    print(f"\n  {n_correct}/{len(results)} correct ({n_correct/len(results):.0%})")

    print("\n=== 2. Scaling sweep: k = 1..30 ===")
    rows = sweep_k([1, 2, 3, 5, 8, 13, 21, 30])
    print(render_sweep(rows))
    first, last = rows[0], rows[-1]
    print(f"\n  From k={first['k']} to k={last['k']}: json_tokens grew "
          f"{last['json_tokens']/first['json_tokens']:.1f}x, code_tokens grew "
          f"{last['code_tokens']/first['code_tokens']:.1f}x")

    print("\n  Marginal JSON token cost per additional file (rising = superlinear growth):")
    deltas = marginal_json_token_cost(rows)
    for k, dk, per_file in deltas:
        print(f"    up to k={k:>2}: +{per_file:.0f} tokens per additional file (over the last {dk} added)")
    is_rising = all(b[2] > a[2] for a, b in zip(deltas, deltas[1:]))
    print(f"  Strictly increasing at every step measured: {is_rising}")

    print("\n=== 3. Boundary check: heterogeneous task (no generic loop possible) ===")
    het_json = summarize(build_heterogeneous_json_trace())
    het_code = summarize(build_heterogeneous_code_trace())
    print(f"  JSON: {het_json['turns']} turns, {het_json['total_tokens']} tokens")
    print(f"  Code: {het_code['turns']} turns, {het_code['total_tokens']} tokens")
    print(f"  Turn ratio: {het_json['turns']/het_code['turns']:.1f}x   "
          f"Token ratio: {het_json['total_tokens']/het_code['total_tokens']:.1f}x")
