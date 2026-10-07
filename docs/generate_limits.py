#!/usr/bin/env python3
"""Render the generated documentation blocks and copy the shared ones into the guide.

One run renders the limits inventory into LIMITS.md, renders the comparison
scenario matrix (tests/fixtures/comparison/matrix.json) into the failure
contract's table, and copies the shared sections into the user guide: the
limits tables from LIMITS.md, the questions from QUESTIONS.md and the
comparison reading rules from the failure contract. References identify
owners, not proof of values. Compiled C, Swift and Rust tests compare
implementation values with the limits manifest independently.
--check verifies every document without writing. --stage-guide copies the
checked guide for distribution without regenerating stale documentation.

Generator invariants: this generator holds G1 to G6 and G8 to G10 directly and G11 through the shared prose-link rule, as stated under Generator
contracts in tests/suites/source_drift/README.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # --check must not create import caches.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generator_common import citation, require_test, format_value, render_spans, span_problems, heading_anchors

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- BEGIN GENERATED LIMITS -->"
END = "<!-- END GENERATED LIMITS -->"
COVERAGE_START = "<!-- BEGIN GENERATED LIMIT COVERAGE -->"
COVERAGE_END = "<!-- END GENERATED LIMIT COVERAGE -->"
SHARED_START = "<!-- BEGIN SHARED LIMITS -->"
SHARED_END = "<!-- END SHARED LIMITS -->"
GUIDE_START = "<!-- BEGIN COPIED LIMITS -->"
GUIDE_END = "<!-- END COPIED LIMITS -->"
QUESTIONS_START = "<!-- BEGIN SHARED QUESTIONS -->"
QUESTIONS_END = "<!-- END SHARED QUESTIONS -->"
GUIDE_QUESTIONS_START = "<!-- BEGIN COPIED QUESTIONS -->"
GUIDE_QUESTIONS_END = "<!-- END COPIED QUESTIONS -->"
MATRIX_START = "<!-- BEGIN GENERATED SCENARIO MATRIX -->"
MATRIX_END = "<!-- END GENERATED SCENARIO MATRIX -->"
RULES_START = "<!-- BEGIN SHARED READING RULES -->"
RULES_END = "<!-- END SHARED READING RULES -->"
GUIDE_RULES_START = "<!-- BEGIN COPIED READING RULES -->"
GUIDE_RULES_END = "<!-- END COPIED READING RULES -->"
SPAN_DOCUMENTS = ("docs/LIMITS.md", "docs/ARCHITECTURE.md")
GUIDE_NAME = "PolicyWitness.md"
CONTRACT_NAME = "tests/FAILURE-PROPAGATION-CONTRACT.md"
MATRIX_NAME = "tests/fixtures/comparison/matrix.json"
COMPARISON_KEYS = ("observation", "observation_basis", "operation_relation", "target_relation", "order", "limitations")
CONTROL_WORDS = ("Fixed", "Flag `--", "Derived", "Not enforced")
SECTIONS = {
    "admission": "Specimen admission",
    "execution": "Execution budgets",
    "transport": "Queries and transport",
    "evidence": "Evidence capture",
    "helper": "Diagnostic helpers",
}


VALUE_OWNERS = {
    'tests/suites/runner_abi_layout/limits.py',
    'runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift',
    'controller/src/run_flow.rs', 'controller/src/log_capture.rs',
    'controller/src/bin/sbpl-check.rs', 'controller/src/bin/sandbox-log-observer.rs',
    'controller/src/runner_manager.rs', 'controller/src/runner_commands.rs',
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_limits(path: Path, root: Path = ROOT):
    data = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if set(data) != {"schema_version", "limits"} or data["schema_version"] != 2:
        raise ValueError("expected limits manifest schema_version 2")
    if not isinstance(data["limits"], list) or not data["limits"]:
        raise ValueError("limits must be a nonempty list")
    seen = set()
    fields = {"id", "section", "title", "value", "unit", "counting", "effect",
              "control", "sources", "checks", "behavior"}
    for item in data["limits"]:
        # Admission rows also name the field a refusal reports, so a reader can
        # go from `admission_failure.field` to the row. Other sections have no
        # specimen-admission lookup, so they must not carry one.
        expected_fields = fields | {"refusal_field"} if item.get("section") == "admission" else fields
        if set(item) != expected_fields:
            raise ValueError(f"unexpected/missing fields: {item.get('id')}")
        ident = item["id"]
        if not re.fullmatch(r"[a-z][a-z0-9_]*", ident) or ident in seen:
            raise ValueError(f"invalid/duplicate limit id: {ident}")
        seen.add(ident)
        if type(item["value"]) is not int or item["value"] <= 0:
            raise ValueError(f"{ident}: value must be a positive integer")
        if item["section"] not in SECTIONS:
            raise ValueError(f"{ident}: unknown section")
        if item["unit"] not in {"UTF-8 bytes", "bytes", "items", "milliseconds", "seconds", "levels", "records"}:
            raise ValueError(f"{ident}: unknown unit")
        for key in ("title", "counting", "effect", "control", "behavior") + (("refusal_field",) if "refusal_field" in item else ()):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"{ident}: empty {key}")
        # The Control column uses four words the guide defines; dev-only
        # remarks belong in `behavior`, which only LIMITS.md renders.
        if not item["control"].startswith(CONTROL_WORDS):
            raise ValueError(f"{ident}: control must start with one of {CONTROL_WORDS}")
        for key in ("sources", "checks"):
            if not isinstance(item[key], list) or not item[key]:
                raise ValueError(f"{ident}: missing {key}")
            for ref in item[key]:
                expected = {"path", "symbol", "kind", "form"} if key == "checks" else {"path", "symbol"}
                if set(ref) != expected:
                    raise ValueError(f"{ident}: malformed {key} reference")
                citation(ref, root, check=key == "checks", forbidden={
                    "docs/limits.json", "docs/LIMITS.md", "docs/PolicyWitness.md", CONTRACT_NAME})
                if key == "checks" and ref["kind"] == "value" and (
                        ref["form"] != "test" or ref["path"] not in VALUE_OWNERS):
                    raise ValueError(f"{ident}: value owner must be a test in VALUE_OWNERS")
                if key == "checks" and ref["kind"] not in {"value", "boundary", "path"}:
                    raise ValueError(f"{ident}: unknown check kind")
        require_test(ident, item["checks"])
        if not any(ref["kind"] == "value" for ref in item["checks"]):
            raise ValueError(f"{ident}: no implementation-value check owner")
    if {item["section"] for item in data["limits"]} != set(SECTIONS):
        raise ValueError("each documented section needs entries")
    return data["limits"]


def cell(text):
    return text.replace("|", "\\|").replace("\n", " ")


def load_matrix(path: Path):
    """The comparison matrix rows this table renders; every field the table shows must be present."""
    data = json.loads(path.read_text(), object_pairs_hook=unique_object)
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("matrix rows must be a nonempty list")
    seen = set()
    for row in rows:
        for key in ("id", "specimen", "scenario", "query", "control"):
            if not isinstance(row.get(key), str) or not row[key]:
                raise ValueError(f"matrix row {row.get('id')}: missing {key}")
        if row["id"] in seen:
            raise ValueError(f"duplicate matrix row id: {row['id']}")
        seen.add(row["id"])
        comparison = row.get("comparison")
        if not isinstance(comparison, dict) or set(comparison) != set(COMPARISON_KEYS):
            raise ValueError(f"matrix row {row['id']}: comparison must carry exactly {COMPARISON_KEYS}")
        if not isinstance(comparison["limitations"], list) or any(not isinstance(x, str) for x in comparison["limitations"]):
            raise ValueError(f"matrix row {row['id']}: limitations must be a list of strings")
    return rows


def render_matrix(rows):
    lines = [MATRIX_START, "",
             "| Row | Specimen | Scenario | Query | Observation | Basis | Operation | Target | Order | Limitations | Independent control |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        comparison = row["comparison"]
        limitations = ", ".join(f"`{x}`" for x in comparison["limitations"]) or "—"
        lines.append("| " + " | ".join(map(cell, [
            row["id"], row["specimen"], row["scenario"], f"`{row['query']}`",
            f"`{comparison['observation']}`", f"`{comparison['observation_basis']}`",
            f"`{comparison['operation_relation']}`", f"`{comparison['target_relation']}`",
            f"`{comparison['order']}`", limitations, row["control"]])) + " |")
    return "\n".join(lines) + "\n\n" + MATRIX_END


def update_contract(text, rows):
    return replace_block(text, MATRIX_START, MATRIX_END, render_matrix(rows))


def shared_rules(contract_document):
    """The reading rules the failure contract owns, verbatim, for the guide's copy."""
    begin, finish = block_bounds(contract_document, RULES_START, RULES_END)
    shared = contract_document[begin + len(RULES_START):finish - len(RULES_END)].strip()
    if not re.search(r"^1\. ", shared, re.MULTILINE) or re.search(r"^#", shared, re.MULTILINE):
        raise ValueError("shared reading rules must be one numbered list without headings")
    return shared


def update_guide_rules(text, contract_document):
    return replace_block(text, GUIDE_RULES_START, GUIDE_RULES_END,
                         GUIDE_RULES_START + "\n\n" + shared_rules(contract_document) + "\n\n" + GUIDE_RULES_END)


def reference(ref):
    # Repository-relative paths in JSON become document-relative links here.
    return f"[`{ref['symbol']}`](../{ref['path']})"


def render(limits):
    lines = [START]
    for section, title in SECTIONS.items():
        refuses = section == "admission"
        columns = ["Limit", "Value"] + (["Refusal names"] if refuses else []) + ["Counting and consequence", "Control"]
        lines += ["", f"## {title}", "", "| " + " | ".join(columns) + " |",
                  "| " + " | ".join("---" for _ in columns) + " |"]
        for item in limits:
            if item["section"] != section:
                continue
            cells = [f"{item['title']} (`{item['id']}`)", format_value(item["value"], item["unit"])]
            if refuses:
                cells.append(item["refusal_field"])
            cells += [item['counting'] + " " + item['effect'], item['control']]
            lines.append("| " + " | ".join(map(cell, cells)) + " |")
    return "\n".join(lines) + "\n\n" + END


def render_coverage(limits):
    lines = [COVERAGE_START, "", "## Grounding and coverage", "",
              "Value checks compare the inventory with compiled constants, constructed defaults or actual returned bytes. Boundary checks exercise a limit and its consequence; path checks cover related behavior without proving the exact boundary. A source reference alone is not a value check. Coverage notes below identify where behavior remains source-inspected.", "",
              "| Limit ID | Implementation | Permanent checks | Behavioral coverage |",
              "| --- | --- | --- | --- |"]
    for item in limits:
        lines.append("| " + " | ".join(map(cell, [f"`{item['id']}`",
            "; ".join(reference(ref) for ref in item['sources']),
            "; ".join(f"{ref['kind']} ({ref['form']}): {reference(ref)}" for ref in item['checks']),
            item['behavior']])) + " |")
    return "\n".join(lines) + "\n\n" + COVERAGE_END


def block_bounds(text, start, end):
    if text.count(start) != 1 or text.count(end) != 1 or text.index(end) < text.index(start):
        raise ValueError(f"expected exactly one ordered block: {start} ... {end}")
    return text.index(start), text.index(end) + len(end)


def replace_block(text, start, end, replacement):
    begin, finish = block_bounds(text, start, end)
    return text[:begin] + replacement + text[finish:]


def span_values(limits):
    return {row["id"] + suffix: format_value(row["value"], unit)
            for row in limits for suffix, unit in ((".value", None), (".value_unit", row["unit"]))}


def update_document(text, limits):
    text = render_spans(text, "limits", span_values(limits))
    text = replace_block(text, START, END, render(limits))
    return replace_block(text, COVERAGE_START, COVERAGE_END, render_coverage(limits))


def update_guide(text, limits_document):
    begin, finish = block_bounds(limits_document, SHARED_START, SHARED_END)
    shared = limits_document[begin + len(SHARED_START):finish - len(SHARED_END)].strip()
    # The source uses level-two headings; nest them under the guide's Limits
    # heading. All explanatory prose and table contents are copied verbatim.
    shared = re.sub(r"^## ", "### ", shared, flags=re.MULTILINE)
    return replace_block(text, GUIDE_START, GUIDE_END,
                         GUIDE_START + "\n\n" + shared + "\n\n" + GUIDE_END)


def shared_questions(questions_document):
    begin, finish = block_bounds(questions_document, QUESTIONS_START, QUESTIONS_END)
    shared = questions_document[begin + len(QUESTIONS_START):finish - len(QUESTIONS_END)].strip()
    headings = re.findall(r"^#+ ", "\n".join(prose_lines(shared)), re.MULTILINE)
    if not headings or any(heading != "## " for heading in headings):
        raise ValueError("shared questions must use level-two headings only")
    # Questions nest under the guide's Questions heading, and links into the
    # guide become internal links in the copy. Everything else is verbatim.
    shared = re.sub(r"^## ", "### ", shared, flags=re.MULTILINE)
    return shared.replace(f"]({GUIDE_NAME}#", "](#")


def update_guide_questions(text, questions_document):
    return replace_block(text, GUIDE_QUESTIONS_START, GUIDE_QUESTIONS_END,
                         GUIDE_QUESTIONS_START + "\n\n" + shared_questions(questions_document)
                         + "\n\n" + GUIDE_QUESTIONS_END)


def require_standalone(prose, what):
    # The copied sections use inline links only, and must need no companion
    # files or web pages. Reject reference links/definitions rather than
    # assuming they can be resolved in a standalone release asset.
    if re.search(r"\]\s*\[|^\s*\[[^]\n]+\]:|<https?://", prose, re.MULTILINE):
        raise ValueError(f"{what} must use inline internal links only")
    for target in re.findall(r"\]\(([^)]+)\)", prose):
        if not target.startswith("#"):
            raise ValueError(f"{what} depend on another document: {target}")


def prose_lines(text):
    """Ignore fenced examples when inspecting this guide's Markdown links."""
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            delimiter = match.group(1)
            if fence is None:
                fence = delimiter
            elif delimiter[0] == fence[0] and len(delimiter) >= len(fence):
                fence = None
        elif fence is None:
            yield line


def validate_guide(text, limits):
    """Check the standalone text; never resolve links against repository files."""
    begin, finish = block_bounds(text, GUIDE_START, GUIDE_END)
    copied = text[begin + len(GUIDE_START):finish - len(GUIDE_END)]
    for item in limits:
        if copied.count(f"(`{item['id']}`)") != 1:
            raise ValueError(f"guide must contain exactly one limits row: {item['id']}")
    require_standalone("\n".join(prose_lines(copied)), "copied limits")
    begin, finish = block_bounds(text, GUIDE_QUESTIONS_START, GUIDE_QUESTIONS_END)
    questions = "\n".join(prose_lines(text[begin + len(GUIDE_QUESTIONS_START):finish - len(GUIDE_QUESTIONS_END)]))
    if not re.search(r"^### ", questions, re.MULTILINE):
        raise ValueError("guide must contain at least one copied question")
    require_standalone(questions, "copied questions")
    begin, finish = block_bounds(text, GUIDE_RULES_START, GUIDE_RULES_END)
    rules = "\n".join(prose_lines(text[begin + len(GUIDE_RULES_START):finish - len(GUIDE_RULES_END)]))
    if not re.search(r"^1\. ", rules, re.MULTILINE):
        raise ValueError("guide must contain the copied reading rules")
    require_standalone(rules, "copied reading rules")

    # Headings in this guide use ATX syntax. Match the punctuation-stripped
    # anchors used by its Markdown links, including duplicate-heading suffixes.
    prose = "\n".join(prose_lines(text))
    anchors = heading_anchors(prose)
    if "limits" not in anchors:
        raise ValueError("guide is missing its Limits heading")
    for target in re.findall(r"\]\((#[^)]+)\)", prose):
        if target[1:] not in anchors:
            raise ValueError(f"guide has an unresolved internal link: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check the documents; do not write")
    mode.add_argument("--stage-guide", type=Path, metavar="PATH",
                      help="check the documents, then copy the guide to PATH")
    args = parser.parse_args()
    path = ROOT / "docs/LIMITS.md"
    guide_path = ROOT / "docs/PolicyWitness.md"
    questions_path = ROOT / "docs/QUESTIONS.md"
    contract_path = ROOT / CONTRACT_NAME
    try:
        limits = load_limits(ROOT / "docs/limits.json")
        rows = load_matrix(ROOT / MATRIX_NAME)
        before = path.read_text()
        after = update_document(before, limits)
        contract_before = contract_path.read_text()
        contract_after = update_contract(render_spans(contract_before, "limits", span_values(limits)), rows)
        # Documents the limits generator touches only through authored spans.
        span_only = {}
        for name in SPAN_DOCUMENTS:
            if name in ("docs/LIMITS.md", "docs/PolicyWitness.md", CONTRACT_NAME):
                continue
            text = (ROOT / name).read_text()
            span_only[name] = (text, render_spans(text, "limits", span_values(limits)))
        # Derive the copies from the freshly rendered sources and the FAQ, even
        # when the on-disk tables were stale. Validate every input before any
        # writes. QUESTIONS.md is an input only; it is never rewritten.
        questions = questions_path.read_text()
        guide_bytes = guide_path.read_bytes()
        guide_before = guide_bytes.decode("utf-8")
        guide_after = update_guide_rules(update_guide_questions(
            update_guide(render_spans(guide_before, "limits", span_values(limits)), after), questions), contract_after)
        validate_guide(guide_after, limits)
        question_count = len(re.findall(r"^### ", shared_questions(questions), re.MULTILINE))
        if args.check or args.stage_guide is not None:
            stale = [name for name, old, new in [
                ("LIMITS.md", before, after), (CONTRACT_NAME, contract_before, contract_after),
                ("PolicyWitness.md", guide_before, guide_after)]
                + [(name, old, new) for name, (old, new) in span_only.items()]
                if old != new]
            if stale:
                detail = "; ".join(problem for text in [before, contract_before, guide_before, *(old for old, _ in span_only.values())]
                                   for problem in span_problems(text, "limits", span_values(limits)))
                raise ValueError(f"stale {', '.join(stale)}; " + (f"{detail}; " if detail else "")
                                 + "run python3 docs/generate_limits.py")
            if args.stage_guide is not None:
                if not args.stage_guide.is_file() or args.stage_guide.read_bytes() != guide_bytes:
                    args.stage_guide.write_bytes(guide_bytes)
        else:
            if before != after:
                path.write_text(after)
            if contract_before != contract_after:
                contract_path.write_text(contract_after)
            if guide_before != guide_after:
                guide_path.write_text(guide_after)
            for name, (old, new) in span_only.items():
                if old != new:
                    (ROOT / name).write_text(new)
        print(f"ok: {len(limits)} limits, {question_count} questions, {len(rows)} matrix rows; " +
              (f"guide staged at {args.stage_guide}" if args.stage_guide is not None else
               "documents current" if args.check else "LIMITS.md and the matrix table generated; guide copies updated"))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(f"limits: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
