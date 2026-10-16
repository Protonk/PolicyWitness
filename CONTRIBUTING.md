# Contributing to PolicyWitness

PolicyWitness is a research/teaching tool. Contributions are welcome, but 
“the product” here is not just code — it’s **inspectable behavior** plus 
the written contracts that explain what that behavior means. Meaning: 
documentation and tests are part of the product.

## How to help

PolicyWitness has two subjects: the macOS sandbox, and how to conduct an
experiment that supports an honest claim about it. Contributions can help
people investigate either subject.

The experimental apparatus can interfere with the experiment. For example,
opening a file before applying a sandbox does not test whether the sandbox
permits opening it afterward. The order of operations, the process doing the
work, and its existing permissions can all matter. When changing an experiment
or the code that runs it, consider whether the change also changes what the
result can tell us.

Working here means reproducing reasoning about the sandbox through
experimentation. Start with a small question: can this process read this file
under this policy? Find an existing specimen close to that question, state
what you expect and why, then run it and inspect the effect. Change one
condition and try again. Keep the inputs and observations so another person
can follow your reasoning.

## Planning a change

The welcome above stands: an issue can be an open question, and a pull request
can take shape in discussion. This section is for the other case, when you
prepare a plan that someone else will execute. That reader knows the
repository's code and documentation but not your conversation or earlier
changes. Give them a first draft that is already your best executable proposal:
enough to act on alone, and disposable once the work is done. Nothing below
prescribes a shape or headings; the shape follows the change.

A plan is a recommendation, not a menu. Choose one course and justify the
decisions that matter; mention a rejected alternative only where an executor
might otherwise take it, and leave routine implementation choices to the
executor. Do the inspection or reproduction the recommendation needs before you
hand off; what the implementation itself must find out stays in the plan as
work. A plan to make the worker refuse a truncated policy could have started
from design. Closing the policy pipe after 28 bytes of a 43-byte submission
first showed the shipped worker compiling the prefix with no published failure,
indistinguishable from a complete 28-byte policy. That observation chose the
repair: the host states the expected length, the worker publishes the count it
read before judging it, and a control distinguishes a truncated prefix from a
short complete submission. Hand on conclusions and where to verify them, not
reading notes; an inspection belongs in the plan where it chose a decision or
the executor relies on it.

A successor needs the problem, the intended behavior, the decisions already made
and their reasons, the scope and its edges, the actions in order, what each
depends on, and the evidence that shows completion. Acceptance evidence is an
observation, not a return code: name the check and what it must show, and prefer
a check that would fail against the unrepaired code. Put anything lasting where
it belongs as you go: contracts in their owning documents, operating rules in
the relevant AGENTS file, assertions beside their suites. The plan is
scaffolding; when the work is complete, deleting it should lose nothing.

Some questions cannot be settled before handoff. State each as the missing fact,
why you cannot settle it now, the step that will settle it, and what changes
with each answer. If a design depends on whether a platform tool reports a
field, name the command that samples it. Design up to the point where the
answer decides and say what each answer selects; detailing a branch not yet
chosen is work for after the answer, not deferral. A question left for review
or an answer invented to keep moving is deferral, and not executable.

Before handing off, ask where the proposal could be wrong: where it rests on a
premise that could fail, name it and say how you tested it, or that you did
not. Then scale the document to the change. A settled repair with one check is
a paragraph, even when preparation turns up a complication: add the
complication and its consequence, not a report. A change that crosses a process
boundary needs the reproduction, the boundary and the readers it affects; a
capability behind an unsettled premise needs the experiment and its gate.

Present a proposal ready to act on within your authorization. When a decision
belongs to someone else, say so, say why, and bring a recommendation rather than
a list. Anticipated review is not a reason to leave ordinary design decisions
open; a reviewer can correct a written decision far more easily than make a
missing one.

## Development environment

Building PolicyWitness requires macOS 26 and a **Developer ID Application**
signing identity installed in your login keychain.

Install the Rust toolchain with Cargo and rustfmt, Xcode Command Line Tools
(or full Xcode), Meson, Ninja, and Python. The selected Xcode developer
directory supplies Clang, Swift, and the macOS SDK. Graphviz is also needed
when regenerating documentation figures.

The build configuration and its checks are authoritative for tool version
requirements. See the [build guide](docs/BUILD.md) for setup, signing
requirements, and troubleshooting, including restrictions imposed by
sandboxed automation environments.

## Read AGENTS.md, even if you're a human

Guidance in this repository is aimed at human and non-human agents. Don't assume 
that the contents of layered agent guidance are for others to worry about; 
we put useful direction in there.

READMEs describe what is here; AGENTS files explain how to work here. Keep
implementation inventories and directory descriptions in the READMEs, and use
agent guidance for decisions, working rules and links to the relevant details.

`CLAUDE.md` at the repo root and under `controller/`, `runner/` and `tests/` are
symlinks to the `AGENTS.md` beside them, so Claude Code loads the same guidance
without a branded copy.
Edit the `AGENTS.md` files; they are the source of truth.
