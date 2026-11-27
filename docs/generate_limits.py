#!/usr/bin/env python3
"""Render limit tables, the comparison matrix and scalar spans; validate and stage the standalone guide."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # --check must not create import caches.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generator_common import citation, cited_paths, require_test, format_value, render_spans, span_problems
from generator_common import admission_description, admission_key, unique_object, validate_admission_fields
import markdown_reader
import repository_tree
import publication

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- BEGIN GENERATED LIMITS -->"
END = "<!-- END GENERATED LIMITS -->"
COVERAGE_START = "<!-- BEGIN GENERATED LIMIT COVERAGE -->"
COVERAGE_END = "<!-- END GENERATED LIMIT COVERAGE -->"
MATRIX_START = "<!-- BEGIN GENERATED SCENARIO MATRIX -->"
MATRIX_END = "<!-- END GENERATED SCENARIO MATRIX -->"
EXTENSIONS_NAME = "docs/EXTENSIONS.md"
SPAN_DOCUMENTS = ("docs/LIMITS.md", "docs/ARCHITECTURE.md", "docs/PolicyWitness.md", "docs/REQUEST.md",
                  "tests/FAILURE-PROPAGATION-CONTRACT.md", "controller/README.md", "runner/README.md", EXTENSIONS_NAME)
GUIDE_NAME = "PolicyWitness.md"
# What a run reads besides the files the manifest cites: this generator and its helpers, the manifest, the
# documents it renders or copies, the coverage document and the matrix. The reader's files are
# added by input_paths.
INPUTS = ("docs/publication.py", "docs/generate_limits.py", "docs/generator_common.py", "tests/catalog.json", "docs/limits.json",
          "docs/repository_tree.py", "docs/LIMITS.md", "docs/PolicyWitness.md", *SPAN_DOCUMENTS)
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
    'tests/suites/runner_c_worker_harness/check_sysctl.py',
    'runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift',
    'runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift',
    'controller/src/run_flow.rs',
    'controller/src/request_patch.rs',
    'controller/src/runner_client.rs',
            'controller/src/porcelain.rs',
    'controller/src/bin/sbpl-check.rs',
    'controller/src/runner_manager.rs', 'controller/src/runner_commands.rs',
}


# The cell a route renders in **Where users find it**. Help routes come from the field entries.
ROUTES = {"help": None, "inventory": "Inventory only", "none": "—"}


def span_documents(root=ROOT):
    """Authored scalar destinations in the selected tree, including its surfaces."""
    return (*SPAN_DOCUMENTS,
            *repository_tree.Tree(root).inventory(repository_tree.CONTRACT_SURFACES))


def input_paths(root):
    """Every path a run reads under root; discovery only, so a malformed manifest still reaches load_limits."""
    root = Path(root)
    return sorted({*INPUTS, *span_documents(root), CONTRACT_NAME, MATRIX_NAME, *markdown_reader.source_files(root),
                   *cited_paths(root / "docs/limits.json")})


def load_limits(path: Path, root: Path = ROOT):
    data = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if set(data) != {"schema_version", "admission_fields", "limits"} or data["schema_version"] != 3:
        raise ValueError("expected limits manifest schema_version 3")
    if not isinstance(data["limits"], list) or not data["limits"]:
        raise ValueError("limits must be a nonempty list")
    validate_admission_fields(data)
    seen = set()
    fields = {"id", "section", "title", "value", "unit", "counting", "effect",
              "control", "route", "sources", "checks", "behavior"}
    for item in data["limits"]:
        # Admission rows also name the field a refusal reports, so a reader can
        # go from `admission_failure.field` to the row. Other sections have no
        # specimen-admission lookup, so they must not carry one.
        expected_fields = fields.copy()
        if item.get("section") == "admission":
            expected_fields.add("refusal_fields")
            if "refusal_context" in item:
                expected_fields.add("refusal_context")
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
        for key in ("title", "counting", "effect", "control", "behavior") + (("refusal_context",) if "refusal_context" in item else ()):
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
        declarations = data["admission_fields"]
        entries = [f for key in item.get("refusal_fields", []) if "statement" in (f := declarations[key])]
        if item["section"] == "admission":
            item["refusal_field"] = admission_description(item, declarations)
        # Every row states where its reader goes. A help route needs a registered entry.
        if not isinstance(item["route"], str) or item["route"] not in ROUTES or (item["route"] == "help") != bool(entries):
            raise ValueError(f"{ident}: route must be one of {sorted(ROUTES)} and agree with its help entries")
        item["user_route"] = ROUTES[item["route"]] or ", ".join(
            "`help run " + admission_key(f) + "`" for f in entries)
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


def matrix_table(rows, *, specimen):
    """The scenario table; the guide's selection omits the fixture's specimen column."""
    columns = ["Row", *(["Specimen"] if specimen else []), "Scenario", "Query", "Observation", "Basis",
               "Operation", "Target", "Order", "Limitations", "Independent control"]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        comparison = row["comparison"]
        limitations = ", ".join(f"`{x}`" for x in comparison["limitations"]) or "—"
        lines.append("| " + " | ".join(map(cell, [
            row["id"], *([row["specimen"]] if specimen else []), row["scenario"], f"`{row['query']}`",
            f"`{comparison['observation']}`", f"`{comparison['observation_basis']}`",
            f"`{comparison['operation_relation']}`", f"`{comparison['target_relation']}`",
            f"`{comparison['order']}`", limitations, row["control"]])) + " |")
    return "\n".join(lines)


def render_matrix(rows):
    return MATRIX_START + "\n\n" + matrix_table(rows, specimen=True) + "\n\n" + MATRIX_END



def update_contract(text, rows):
    return replace_block(text, MATRIX_START, MATRIX_END, render_matrix(rows))









def reference(ref):
    # Repository-relative paths in JSON become document-relative links here.
    return f"[`{ref['symbol']}`](../{ref['path']})"


def render(limits):
    lines = [START]
    for section, title in SECTIONS.items():
        refuses = section == "admission"
        columns = ["Limit", "Value"] + (["Refusal names"] if refuses else []) + ["Counting and consequence", "Control", "Where users find it"]
        lines += ["", f"## {title}", "", "| " + " | ".join(columns) + " |",
                  "| " + " | ".join("---" for _ in columns) + " |"]
        for item in limits:
            if item["section"] != section:
                continue
            cells = [f"{item['title']} (`{item['id']}`)", format_value(item["value"], item["unit"])]
            if refuses:
                cells.append(item["refusal_field"])
            cells += [item['counting'] + " " + item['effect'], item['control'], item['user_route']]
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


def binary_value(value, unit):
    """A byte limit that is a whole number of MiB or KiB, as prose states it."""
    if unit != "bytes":
        return None
    for size, name in ((1 << 20, "MiB"), (1 << 10, "KiB")):
        if value % size == 0:
            return f"{value // size:,} {name}"
    return None


def span_values(limits):
    values = {row["id"] + suffix: format_value(row["value"], unit)
              for row in limits for suffix, unit in ((".value", None), (".value_unit", row["unit"]))}
    values.update({row["id"] + ".binary": binary_value(row["value"], row["unit"])
                   for row in limits if binary_value(row["value"], row["unit"]) is not None})
    return values


def update_document(text, limits):
    text = render_spans(text, "limits", span_values(limits), "docs/LIMITS.md")
    text = replace_block(text, START, END, render(limits))
    return replace_block(text, COVERAGE_START, COVERAGE_END, render_coverage(limits))



def validate_guide(text):
    guide = markdown_reader.parse(text, GUIDE_NAME)
    if guide.references or any(link.autolink for link in guide.links):
        raise ValueError(f"{GUIDE_NAME} must use inline internal links only")
    for link in guide.links:
        if not link.target.startswith("#"):
            raise ValueError(f"{GUIDE_NAME} must not depend on another document: {link.target}")
        if link.target[1:] not in guide.anchors:
            raise ValueError(f"guide has an unresolved internal link: {link.target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check the documents; do not write")
    mode.add_argument("--stage-guide", type=Path, metavar="PATH",
                      help="check the documents, then copy the guide to PATH")
    mode.add_argument("--stage-development", type=Path, metavar="PATH",
                      help="stage the checked guide and its build-bound receipt")
    parser.add_argument("--publication", action="store_true",
                        help="require the standalone guide and its current scalar spans")
    parser.add_argument("--build-contract", help="derived identity for a development staging receipt")
    parser.add_argument("--signed-receipt", type=Path, help="verify staged bytes against this signed build receipt")
    args = parser.parse_args()
    path = ROOT / "docs/LIMITS.md"
    guide_path = ROOT / "docs/PolicyWitness.md"
    contract_path = ROOT / CONTRACT_NAME
    try:
        if publication.WITHHELD:
            publication.frozen_guide(ROOT)
        if args.stage_guide is not None and (publication.WITHHELD or not args.publication):
            raise ValueError('publication withheld: --stage-guide requires strict --publication checking')
        limits = load_limits(ROOT / "docs/limits.json")
        rows = load_matrix(ROOT / MATRIX_NAME)
        before = path.read_text()
        after = update_document(before, limits)
        contract_before = contract_path.read_text()
        contract_after = update_contract(render_spans(contract_before, "limits", span_values(limits), CONTRACT_NAME), rows)
        # Documents the limits generator touches only through authored spans.
        span_only = {}
        for name in span_documents(ROOT):
            if name in ("docs/LIMITS.md", "docs/PolicyWitness.md", CONTRACT_NAME):
                continue
            text = (ROOT / name).read_text()
            span_only[name] = (text, render_spans(text, "limits", span_values(limits), name))
        guide_bytes = guide_path.read_bytes()
        guide_before = guide_bytes.decode("utf-8")
        guide_after = render_spans(guide_before, "limits", span_values(limits), publication.GUIDE)
        validate_guide(guide_after)
        if args.check or args.stage_guide is not None or args.stage_development is not None:
            stale = [name for name, old, new in [
                ("LIMITS.md", before, after), (CONTRACT_NAME, contract_before, contract_after),
                ("PolicyWitness.md", guide_before, guide_after)]
                + [(name, old, new) for name, (old, new) in span_only.items()]
                if old != new]
            if stale:
                sources = [("docs/LIMITS.md", before), (CONTRACT_NAME, contract_before), ("docs/PolicyWitness.md", guide_before),
                           *((name, old) for name, (old, _) in span_only.items())]
                detail = "; ".join(problem for name, text in sources
                                   for problem in span_problems(text, "limits", span_values(limits), name))
                raise ValueError(f"stale {', '.join(stale)}; " + (f"{detail}; " if detail else "")
                                 + "run tests/lib/python.sh docs/generate_limits.py")
            if args.stage_development is not None:
                import build_contract
                actual = build_contract.identity(ROOT)
                if args.build_contract != actual:
                    raise ValueError('development publication boundary has the wrong build identity')
                distributed = args.stage_development.parent / 'PolicyWitness.md'
                receipt = publication.record(ROOT, actual)
                if args.signed_receipt is not None:
                    signed = json.loads(args.signed_receipt.read_bytes())
                    if signed != receipt or signed['guide']['sha256'] != hashlib.sha256(guide_bytes).hexdigest():
                        raise ValueError('staged guide differs from the signed publication receipt')
                if publication.WITHHELD:
                    if distributed.exists() and distributed.read_bytes() != guide_bytes:
                        raise ValueError('distributed frozen guide differs from ' + publication.REVISION)
                else:
                    distributed.write_bytes(guide_bytes)
                publication.write(args.stage_development, receipt)
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
        print(f"ok: {len(limits)} limits, {len(rows)} matrix rows; " +
              (f"guide staged at {args.stage_guide}" if args.stage_guide is not None else
               "documents current; publication withheld" if publication.WITHHELD else
               "documents current" if args.check else "LIMITS.md and the matrix table generated; guide spans updated"))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(f"limits: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
