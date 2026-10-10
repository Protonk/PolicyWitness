# Makefile verbs plan

The Makefile audit measured the six verbs under a conditions matrix; its
report is local under `.tmp/audits/`. Its findings are fixed: `make test`
follows `DIST_DIR`, the ordering test reads the app the dispatcher names, the
worker harness names the argv bound instead of exiting silently, the build
script says when the keychain listed nothing at all, and the header no longer
claims that nothing but notarization leaves the machine or that every
notarize step shares one bound. Two of the audit's design proposals were
adopted and this plan carries them out. Like the build document plan, this
file is working material and is deleted when the work lands.

## Decisions

1. **Bare `make` prints the card and does nothing else.** A `help` target
   becomes the default goal and prints the header comment, which stays the
   one hand-maintained description of the verbs; `make build` builds. The
   card is the header's own bytes printed by the recipe, so there is nothing
   to generate and nothing that can drift from it. The system's GNU Make
   honors `.DEFAULT_GOAL`, checked on this machine.
2. **`prune` replaces `clean`, with no alias.** `make prune` previews what the
   pruner would remove, through `tests/run.sh --prune`; `make prune APPLY=1`
   removes it, through `--prune --apply`. The name is the dispatcher's own
   word for what the verb does, and the default shows eligibility before
   anything changes. No verb touches `builddir/`, `controller/target/` or
   the distribution directory; discarding those is a command, not a verb,
   and no document gives it today.

## Steps

- Makefile: add `help` as the default goal; rename `clean` to `prune` with
  the `APPLY` knob and a refusal for any value other than `1`; list `help`
  and `prune` in the header's Targets and in `.PHONY`; say under Conventions
  that bare `make` prints this card.
- Documents that name `make clean` or assume bare `make` builds:
  [AGENTS.md](../AGENTS.md) (the Testing bullet), the
  [tests README](../tests/README.md), the
  [dispatcher suite README](../tests/suites/dispatcher/README.md). The build
  document's Makefile row describes `make build` and is unchanged.
- Controls: the retention control in
  [check_retention.py](../tests/suites/dispatcher/check_retention.py) invokes
  `make clean` and asserts delegation; it moves to `make prune APPLY=1` and
  gains a preview assertion that `make prune` removes nothing and prints the
  pruner's report. A sibling of the make-guard control in
  [contract.py](../tests/suites/source_drift/contract.py) asserts that bare
  `make` prints the card, runs nothing and exits zero.
- [BUILD.md](BUILD.md), in the section on directories: one sentence naming
  the two cache directories a person removes to start over, since no verb
  does it and no document says it.
- Generator and manifest: the Makefile rule compares only the `build`
  recipe, so nothing is regenerated; the Makefile is outside the identity
  closure.
- Gates, in order: the drift suite, the dispatcher suite, one default
  battery; by hand, bare `make` in a fresh shell, `make prune` as a preview,
  and `make prune APPLY=1` against a disposable run directory.

## Not in scope

The audit's other three proposals stay deferred: a selector interface on
`test`, retiring `notarize` as a verb, and a `check-build` verb for the
pre-compile refusals. Each relocates an established boundary for a benefit
no one has yet asked for.
