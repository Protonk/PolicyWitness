"""Rule tables, result records and the dispatcher the drift checkers share.

A rule is a callable over a `repository_tree.Tree` that returns problem
records. It does not exit, print or mutate files; it obtains its own parsed
inputs through the tree. The dispatcher attempts every selected rule once, in
table order, stamps each record with its rule ID, converts an expected-input
failure into one precondition record for that rule alone, and leaves the exit
status to the caller: `status` is 2 when any rule was blocked by its input, 1
when any rule reported a problem, otherwise 0. Rows declare no prerequisites.
`run_gated` is the one documented exception, for the build rules: the gate
row runs first and, when it is not clean, every other row is reported as
blocked by it and never called.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import sys

if str(Path(__file__).resolve().parents[2] / 'docs') not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'docs'))
import repository_tree  # noqa: E402

OUTCOMES = ('evaluated', 'input_blocked', 'gate_blocked')


@dataclass(frozen=True)
class Problem:
    """One diagnostic: a stable key, a readable message, and the location when known."""
    key: str
    message: str
    path: str | None = None
    line: int | None = None
    severity: str = 'drift'  # drift | refused | precondition
    rule_id: str | None = None


class InputFailure(Exception):
    """An expected input is missing, malformed or unreadable, so the rule cannot make its comparison."""

    def __init__(self, key, message, path=None, line=None):
        super().__init__(message)
        self.key, self.message, self.path, self.line = key, message, path, line


@dataclass(frozen=True)
class Rule:
    """A table row: ID, callable, inputs and helper modules. Inputs are a declaration tuple or a function
    from an explicit root to that tuple, for dependencies selected by a manifest."""
    id: str
    call: object
    inputs: object = ()
    helpers: tuple = ()


@dataclass
class Result:
    rule_id: str
    outcome: str
    problems: list = field(default_factory=list)
    blocked_by: str | None = None


def select(rules, selected=None):
    if selected is None:
        return list(rules)
    unknown = sorted(set(selected) - {rule.id for rule in rules})
    if unknown:
        raise ValueError(f'unknown rule IDs: {unknown}')
    return [rule for rule in rules if rule.id in selected]


def attempt(tree, rule, refused=()):
    """One rule over one tree: its records, or the one precondition record that blocked it."""
    try:
        found = rule.call(tree)
    except InputFailure as failure:
        return Result(rule.id, 'input_blocked',
                      [Problem(failure.key, failure.message, failure.path, failure.line, 'precondition', rule.id)])
    except repository_tree.InputError as error:
        key = 'input.missing' if isinstance(error, repository_tree.MissingInput) else 'input.unreadable'
        return Result(rule.id, 'input_blocked', [Problem(key, str(error), error.relative, None, 'precondition', rule.id)])
    except refused as error:
        return Result(rule.id, 'evaluated', [Problem('reader.refused', f'  markdown: {error}', None, None, 'refused', rule.id)])
    return Result(rule.id, 'evaluated', [replace(problem, rule_id=rule.id) for problem in found])


def run_rules(tree, rules, selected=None, refused=()):
    """Every selected rule once, in table order; no row depends on another's result."""
    return [attempt(tree, rule, refused) for rule in select(rules, selected)]


def run_gated(tree, rules, gate, selected=None, refused=()):
    """The gate row first; the other selected rows run only when it evaluated cleanly, else they are gate-blocked."""
    gate_rule = next((rule for rule in rules if rule.id == gate), None)
    if gate_rule is None:
        raise ValueError(f'no gate rule {gate!r}')
    first = attempt(tree, gate_rule, refused)
    results = [first]
    clean = first.outcome == 'evaluated' and not first.problems
    for rule in select(rules, selected):
        if rule.id == gate:
            continue
        results.append(attempt(tree, rule, refused) if clean else Result(rule.id, 'gate_blocked', blocked_by=gate))
    return results


def status(results):
    if any(result.outcome == 'input_blocked' for result in results):
        return 2
    return 1 if any(result.problems for result in results) else 0


def summary_lines(results):
    """Deterministic counts and names by outcome, in table order; each rule appears in exactly one category."""
    names = {outcome: [result.rule_id for result in results if result.outcome == outcome] for outcome in OUTCOMES}
    lines = ['rules: ' + ', '.join(f'{len(names[outcome])} {outcome}' for outcome in OUTCOMES)]
    lines += [f'{outcome}: ' + ', '.join(names[outcome]) for outcome in OUTCOMES if names[outcome]]
    return lines


def to_json(results):
    return {'schema_version': 1, 'status': status(results), 'results': [
        dict(rule_id=result.rule_id, outcome=result.outcome, blocked_by=result.blocked_by,
             problems=[dict(key=p.key, message=p.message, path=p.path, line=p.line, severity=p.severity)
                       for p in result.problems])
        for result in results]}
