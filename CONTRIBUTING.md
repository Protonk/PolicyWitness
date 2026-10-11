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

You can help by bringing a concrete question, even if you do not know the
answer. Open an issue describing what you want to understand, anything you
have tried, and what remains unclear. If your investigation leads to a change,
send a pull request—we welcome discussion while the work is still taking shape.

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

`CLAUDE.md` at the repo root and under `runner/` are symlinks to the `AGENTS.md` 
beside them, so Claude Code loads the same guidance without a branded copy. 
Edit the `AGENTS.md` files; they are the source of truth.
