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

Write the first draft as your best proposal for carrying out the change. It
should be usable by someone who knows this repository but has none of your
conversation history. Give that person enough to understand what needs to
change, why you chose this approach, how to proceed, and how to tell when the
work is complete. Choose the detail according to what they would otherwise
have to rediscover or decide.

Begin with the problem and the intended result. Inspect the relevant
implementation, contracts and tests; reproduce a failure or try a small
experiment when your recommendation depends on what actually happens. Settle
questions you can answer during preparation. Carry the conclusions into the
plan, with references to the evidence or code that supports them. Explain the
decisions well enough that the executor can recognize when a proposed shortcut
would undo something important.

Choose an approach and explain why it fits the problem. State what the change
covers and where it stops. Organize the work around dependencies: what must be
established first, which pieces have to change together, and where the result
can be checked. Include the documentation and test changes needed to complete
each part. Name affected interfaces and files where that helps locate the
work; leave room for routine implementation decisions that do not alter the
proposal.

If a necessary fact cannot be established during preparation, make obtaining
it an explicit part of the work. State the question, why it remains open, what
observation will resolve it, and how the answer affects what follows. When the
answer requires part of the implementation to exist, plan that part and the
check it enables. Define what would justify proceeding and what a contrary
result would require. Specify the work that can proceed independently and
which decisions depend on the result.

Specify verification in terms of the result it must establish. Name the checks
that exercise the changed behavior and say what their results should
demonstrate. For a repair, look for a check that exposes the original defect
and passes with the fix. Consider how the same check might pass despite an
incorrect implementation, and add a control or a different observation when
needed. Use existing coverage where it answers the question, and make any
required additions part of the planned work.

Read the draft as its executor before handing it over. Look for an unsupported
premise, an omitted dependency, or a step that leaves the reader to choose the
design. Check that the scope, steps and acceptance conditions describe the
same change. Resolve these gaps yourself wherever you can; do not leave
ordinary design decisions open in anticipation of review. Where a decision
requires someone else's authority, explain what they need to decide and bring
a recommendation with its consequences.

During execution, keep the plan's decisions and remaining work current. Put
lasting knowledge in the implementation, tests, contracts and working guidance
where future contributors will look for it. Once the work is complete,
deleting the plan should lose nothing needed to understand or operate the
system. Keep research notes and the history of drafting out of the plan unless
they supply something the executor needs to act on.

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
