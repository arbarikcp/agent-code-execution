# Code as an Action Space: Decision Memo

## Recommendation

Use code actions when tasks require open-ended composition, local data
processing, or reuse of runtime libraries. Use structured tools for small,
stable, consequential effects that benefit from narrow validation and
per-operation approval. Combine both when the task needs flexible computation
and governed external mutations.

## Why code can be the right choice

| Benefit | Mechanism | Qualification |
|---|---|---|
| Composition | Loops, branches, functions, and variables live inside one action | Batch tools or workflows can provide similar composition |
| Local data flow | Intermediate values stay in runtime memory | Requires suitable runtime state and observation design |
| Library reuse | Code imports APIs already available in the environment | Dependencies and import policy still need management |
| Runtime feedback | Exceptions and outputs become observations | Feedback enables repair but does not guarantee it |
| Flexible tool combinations | One program can call several exposed capabilities | Broader capability requires stronger governance |

## Evidence classification

The chapter contains three different kinds of evidence:

### Protocol simulation

For a uniform `k`-file task, the script assumes:

```text
one-call-per-turn structured protocol: k reads + 1 write + 1 finish = k + 2
one code-action protocol:            1 action + 1 finish            = 2
```

Under an eight-step budget:

| `k` | Structured steps | Fits? | Code steps | Fits? |
|---:|---:|:---:|---:|:---:|
| 1 | 3 | yes | 2 | yes |
| 3 | 5 | yes | 2 | yes |
| 5 | 7 | yes | 2 | yes |
| 6 | 8 | yes | 2 | yes |
| 7 | 9 | no | 2 | yes |
| 10 | 12 | no | 2 | yes |
| 20 | 22 | no | 2 | yes |

Four of seven sampled structured traces fit; all seven code traces fit. These
fractions describe this chosen task set and protocol. They are not measured
model success rates.

The budget sweep is equally mechanical:

| Budget | Sampled structured tasks that fit | Sampled code tasks that fit |
|---:|---:|---:|
| 3 | 14% | 100% |
| 4 | 14% | 100% |
| 6 | 29% | 100% |
| 8 | 57% | 100% |
| 10 | 71% | 100% |
| 12 | 86% | 100% |
| 16 | 86% | 100% |
| 24 | 100% | 100% |

The result follows from the assumed formulas. Parallel calls, a batch read
tool, a different finish protocol, or multiple code actions would change it.

### Scripted demonstrations

- `demo_tool_reuse()` executes `statistics.mean` from the standard library
  without a dedicated mean-tool schema.
- `demo_dynamic_revision()` captures a real `ZeroDivisionError` and then runs
  a prewritten corrected action.
- `demo_nondeterminism()` reads the clock twice and observes different values.

These runs demonstrate runtime mechanisms. They do not evaluate whether a live
model would choose the right library, repair the exception, or produce
reproducible code.

### Published evaluation

The CodeAct paper reports evaluation across 17 language models on API-Bank and
a newly curated benchmark, with improvements of up to 20 percentage points in
success rate over the alternatives studied. That is the paper's result, not a
result reproduced by this repository. See the
[paper](https://arxiv.org/abs/2402.01030) for tasks, baselines, and experimental
conditions.

## Costs and risks

| Cost | Practical consequence |
|---|---|
| Broader failure surface | Syntax, runtime, dependency, and generated-logic errors |
| Partial effects | Early statements may succeed before a later failure |
| Harder approval | Reviewers must understand compound behavior, not just arguments |
| Resource use | Programs need time, memory, output, and step limits |
| Reproducibility | Results may depend on files, packages, clocks, randomness, or services |
| Containment burden | The runtime must restrict access beyond intended capabilities |

Runtime isolation is delegated to the sibling guide, *Code Execution
Sandboxing for AI Agents*.

## Decision checklist

Choose code actions when most answers are “yes”:

- Does the task require loops, branches, or substantial intermediate data?
- Are useful libraries already available in a governed runtime?
- Would individual tool calls create costly model-mediated orchestration?
- Can results and side effects be verified?
- Can execution be budgeted and contained?

Choose structured tools when most answers are “yes”:

- Is the operation small, stable, and easy to describe with a schema?
- Does each effect require separate authorization or audit?
- Is arbitrary composition unnecessary or undesirable?
- Would one batch or domain-specific tool solve the problem cleanly?

## Bottom line

Code is valuable because it is a general composition language, not because it
always uses fewer tokens or produces correct answers. Its adoption should be a
deliberate exchange: greater flexibility and local computation in return for a
larger execution, validation, and governance surface.
