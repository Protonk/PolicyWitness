#!/usr/bin/env python3
"""Generate the build figure and tables from docs/build.json, grounded in build.sh.

The manifest owns the document's structured account of one build in time:
the steps in order with their banners, the refusals with the step each
protects and its status, the knobs, the signing list, the helpers the build
invokes and the trust placed in the build directories. Every item cites a
source symbol and a test or rule. This script verifies those citations,
parses build.sh and meson.build and compares what they say with the manifest
(banner order, refusal messages, statuses and steps, knob values, signing
calls, helper invocations and the signing inventory), renders the step figure
to dot and SVG, and writes the figure and the tables into the marked regions
of the document.

  generate_build.py             write the dot file, the SVG and the document regions
  generate_build.py --skip-svg  write the dot file and the document regions only
  generate_build.py --check     verify every copy and the script agreement; write nothing

What the comparison establishes is textual: the manifest and the script name
the same banners, messages, calls and values in the same places. It does not
establish that a refusal fires or that it precedes the operation it protects;
the behavioral controls the manifest cites, and the baseline of refusals that
have none, carry that distinction.

The parser accepts the forms build.sh uses and refuses any other: a banner is
`echo "==> ..."` outside a function; a refusal is `echo "ERROR: ..." 1>&2` or
a stderr heredoc whose first ERROR line is the message, followed within three
lines by `exit N`; a signature is a `sign_macho "..."` call and a seal a
`codesign --force` command; helpers run as `"${ROOT_DIR}/<path>"`; branches
are `if`/`else`/`fi`, loops `for`/`done`, and `case`/`esac` may hold refusals
but no banners. A refusal inside a function belongs to the steps that call
the function.

Generator invariants: this generator holds G1 to G10 directly and G11 through
the shared prose-link rule, as stated under Generator contracts in
tests/suites/source_drift/README.md.
"""
import argparse
import ast
import json
import plistlib
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # --check must not create import caches.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generator_common import citation, require_test, DURATION_SIZE_RE, strings, format_value, render_spans, span_problems
import generate_architecture as arch

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "docs/build.json"
GENERATOR_NAME = "docs/generate_build.py"
BASELINE_NAME = "tests/fixtures/docs/build_baseline.json"
SPAN_DOCUMENTS = ("docs/BUILD.md",)
REGIONS = ("FIGURE", "STEPS", "REFUSALS", "SIGNING", "KNOBS", "DIRECTORIES")
REGION_START = "<!-- BEGIN GENERATED BUILD {region} -->"
REGION_END = "<!-- END GENERATED BUILD {region} -->"
STAMP_RE = re.compile(r"<!-- build\.json figure (\S+); dot sha256 ([0-9a-f]{64}) -->")
ID_RE = re.compile(r"[a-z][a-z0-9_]*")
VARIANTS = ("full", "partial")
REFUSAL_KINDS = ("script", "meson", "propagated", "make")
COVERAGE = ("behavioral", "helper", "textual")
COVERED = {"behavioral", "helper"}


class ParseError(ValueError):
    """A form of the script the parser does not account for."""


# ---- the script --------------------------------------------------------------

def logical_lines(text):
    """Lines with backslash continuations joined, each with its first physical line number."""
    out, current, start = [], None, None
    for number, line in enumerate(text.splitlines(), start=1):
        if current is None:
            current, start = line, number
        else:
            current += " " + line.strip()
        if current.rstrip().endswith("\\"):
            current = current.rstrip()[:-1]
            continue
        out.append((start, current))
        current = None
    if current is not None:
        out.append((start, current))
    return out


def parse_script(text):
    """The banners, refusals, signing calls, helper invocations and knobs of build.sh, in order."""
    lines = logical_lines(text)
    model = dict(banners=[], refusals=[], signing=[], invocations=[], knobs=dict(names=[], defaults={}, accepted=[]),
                 arrays={}, functions={})
    stack = []          # frames: dict(kind=if|loop|case|func, cond, else_branch, name)
    step = None         # index into model['banners'] of the last top-level banner
    i = 0

    def function():
        return next((f["name"] for f in stack if f["kind"] == "func"), None)

    def variants():
        found = set(VARIANTS)
        for frame in stack:
            if frame["kind"] != "if":
                continue
            if '"${BUILD_XPC}" == "1"' in frame["cond"]:
                found &= {"partial"} if frame["else_branch"] else {"full"}
            elif '"${BUILD_XPC}" == "0"' in frame["cond"]:
                found &= {"full"} if frame["else_branch"] else {"partial"}
        return sorted(found)

    def loop():
        return next((f["name"] for f in reversed(stack) if f["kind"] == "loop"), None)

    def context(number):
        return dict(line=number, step=step, variants=variants(), function=function(), loop=loop())

    def exit_status(index, limit=3):
        for _, candidate in lines[index + 1:index + 1 + limit]:
            match = re.match(r"^\s*exit (\d+)\s*$", candidate)
            if match:
                return match.group(1)
        raise ParseError(f"line {lines[index][0]}: refusal without a constant exit status within {limit} lines")

    while i < len(lines):
        number, line = lines[i]
        stripped = line.strip()
        heredoc = re.search(r"<<-?'?(\w+)'?", line)
        if heredoc and not stripped.startswith("#"):
            terminator = heredoc.group(1)
            body, j = [], i + 1
            while j < len(lines) and lines[j][1].strip() != terminator:
                body.append(lines[j][1])
                j += 1
            if j >= len(lines):
                raise ParseError(f"line {number}: unterminated heredoc {terminator}")
            if re.match(r"^\s*cat <<'?\w+'? 1>&2\s*$", line):
                message = next((b for b in body if b.startswith("ERROR: ")), None)
                if message is None:
                    raise ParseError(f"line {number}: stderr heredoc without an ERROR line")
                model["refusals"].append(dict(message=message[len("ERROR: "):], status=exit_status(j), **context(number)))
            i = j + 1
            continue
        match = re.match(r"^(\w+)\(\) \{\s*$", line)
        if match:
            stack.append(dict(kind="func", name=match.group(1), cond="", else_branch=False))
            model["functions"][match.group(1)] = dict(refusals=[], calls=[])
            i += 1
            continue
        if stripped == "}" and stack and stack[-1]["kind"] == "func":
            stack.pop(); i += 1; continue
        if re.match(r"^\s*if .*; then\s*$", line):
            stack.append(dict(kind="if", name="", cond=line, else_branch=False)); i += 1; continue
        if re.match(r"^\s*elif ", line):
            raise ParseError(f"line {number}: elif is not a supported form")
        if stripped == "else":
            if not stack or stack[-1]["kind"] != "if":
                raise ParseError(f"line {number}: else outside an if")
            stack[-1]["else_branch"] = True; i += 1; continue
        if stripped == "fi":
            if not stack or stack[-1]["kind"] != "if":
                raise ParseError(f"line {number}: unbalanced fi")
            stack.pop(); i += 1; continue
        match = re.match(r"^\s*for (\w+) in (.+); do\s*$", line)
        if match or re.match(r"^\s*while .*; do\s*$", line):
            name = ""
            if match:
                arrays = re.findall(r'"\$\{(\w+)\[@\]\}"', match.group(2))
                name = arrays[0] if arrays else match.group(1)
                if match.group(1) == "knob":
                    model["knobs"]["names"] = match.group(2).split()
            stack.append(dict(kind="loop", name=name, cond=line, else_branch=False)); i += 1; continue
        if stripped == "done":
            if not stack or stack[-1]["kind"] != "loop":
                raise ParseError(f"line {number}: unbalanced done")
            stack.pop(); i += 1; continue
        if re.match(r"^\s*case .* in\s*$", line):
            stack.append(dict(kind="case", name="", cond=line, else_branch=False)); i += 1; continue
        if stripped == "esac":
            if not stack or stack[-1]["kind"] != "case":
                raise ParseError(f"line {number}: unbalanced esac")
            stack.pop(); i += 1; continue
        match = re.match(r'^(\w+)=\((.*)\)\s*$', line)
        if match:
            model["arrays"][match.group(1)] = re.findall(r'"([^"]*)"', match.group(2))
        match = re.match(r'^(\w+)="\$\{(\w+)-(\w+)\}"\s*$', line)
        if match and match.group(1) == match.group(2):
            model["knobs"]["defaults"][match.group(1)] = match.group(3)
        match = re.match(r"^\s*([0-9|]+)\) ;;\s*$", line)
        if match and any(f["kind"] == "case" for f in stack):
            model["knobs"]["accepted"] = match.group(1).split("|")
        match = re.match(r'^\s*echo "==> (.*)"\s*$', line)
        if match:
            if function() or any(f["kind"] == "case" for f in stack):
                raise ParseError(f"line {number}: a banner inside a function or case is not a supported form")
            model["banners"].append(dict(text=match.group(1), line=number, variants=variants()))
            step = len(model["banners"]) - 1
            i += 1
            continue
        match = re.match(r'^\s*echo "ERROR: (.*)" 1>&2\s*$', line)
        if match:
            model["refusals"].append(dict(message=match.group(1), status=exit_status(i), **context(number)))
            i += 1
            continue
        if re.match(r"""^\s*echo\s+['"]?ERROR""", line):
            raise ParseError(f"line {number}: an ERROR echo must be double-quoted and redirected to stderr")
        match = re.match(r'^\s*sign_macho "(.*)"\s*$', line)
        if match:
            model["signing"].append(dict(kind="signature", target=match.group(1), entitlements=None, **context(number)))
            i += 1
            continue
        if re.match(r"^\s*codesign\b", line):
            if function():
                if function() != "sign_macho" or not re.match(r"^\s*codesign --force", line):
                    raise ParseError(f"line {number}: a codesign command inside a function other than sign_macho")
                i += 1
                continue
            if re.match(r"^\s*codesign --force", line):
                tokens = re.findall(r'"[^"]*"|\S+', line)
                entitlements = None
                if "--entitlements" in tokens:
                    entitlements = tokens[tokens.index("--entitlements") + 1].strip('"')
                model["signing"].append(dict(kind="seal", target=tokens[-1].strip('"'), entitlements=entitlements, **context(number)))
            elif re.match(r"^\s*codesign --(verify|display)", line):
                model["invocations"].append(dict(command="codesign " + stripped.split()[1], **context(number)))
            else:
                raise ParseError(f"line {number}: a codesign command that is neither a seal nor a verification")
            i += 1
            continue
        match = re.search(r'"\$\{ROOT_DIR\}/([^"]+)"(.*)$', line)
        if match and re.match(r"^\s*/usr/bin/python3\b", line):
            flags = [a for a in match.group(2).split() if a.startswith("--")]
            model["invocations"].append(dict(command=" ".join([match.group(1), *flags[:1]]), **context(number)))
            i += 1
            continue
        match = re.match(r'^\s*(?:\w+="[^"]*"\s+)*(cargo build|meson setup|meson configure|meson compile|/usr/bin/ditto)\b', line)
        if match:
            model["invocations"].append(dict(command=match.group(1).replace("/usr/bin/", ""), **context(number)))
            i += 1
            continue
        match = re.match(r"^\s*(check_minimum_macos|embed_dsym|stamp_info_plist) ", line)
        if match:
            name = match.group(1)
            model["functions"].setdefault(name, dict(refusals=[], calls=[]))["calls"].append(context(number))
            model["invocations"].append(dict(command=name, **context(number)))
            i += 1
            continue
        if re.match(r"^\s*sign_macho ", line):
            raise ParseError(f"line {number}: a sign_macho call must name one double-quoted target")
        i += 1
    if stack:
        raise ParseError(f"unbalanced block at end of script: {stack[-1]['kind']}")
    # Calls of sign_macho are signing records; refusals inside functions belong to their callers' steps.
    for record in model["signing"]:
        if record["kind"] == "signature":
            model["functions"].setdefault("sign_macho", dict(refusals=[], calls=[]))["calls"].append(record)
    for refusal in model["refusals"]:
        if refusal["function"]:
            calls = model["functions"].get(refusal["function"], {}).get("calls", [])
            if not calls:
                raise ParseError(f"line {refusal['line']}: refusal in a function that is never called")
            refusal["steps"] = sorted({c["step"] for c in calls}, key=lambda s: -1 if s is None else s)
            refusal["variants"] = sorted({v for c in calls for v in c["variants"]})
        else:
            refusal["steps"] = [refusal["step"]]
    knobs = model["knobs"]
    if sorted(knobs["defaults"]) != sorted(knobs["names"]):
        raise ParseError(f"knob defaults {sorted(knobs['defaults'])} and the knob loop {knobs['names']} name different knobs")
    return model


# ---- the manifest ------------------------------------------------------------

def _ref(owner, key, ref, root):
    expected = {"path", "symbol", "form", "coverage"} if key == "checks" else {"path", "symbol"}
    if not isinstance(ref, dict) or set(ref) != expected:
        raise ValueError(f"{owner}: malformed {key} reference")
    if key == "checks" and ref["coverage"] not in COVERAGE:
        raise ValueError(f"{owner}: unknown coverage {ref['coverage']!r}")
    citation({k: v for k, v in ref.items() if k != "coverage"}, root, check=key == "checks")


def _citations(owner, item, root):
    for key in ("sources", "checks"):
        if not isinstance(item.get(key), list):
            raise ValueError(f"{owner}: {key} must be a list")
        for ref in item[key]:
            _ref(owner, key, ref, root)
    require_test(owner, [{k: v for k, v in r.items() if k != "coverage"} for r in item["checks"]])
    if not item["sources"]:
        raise ValueError(f"{owner}: at least one source citation is required")


def _text(owner, item, key, optional=False):
    value = item.get(key)
    if optional and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner}: empty {key}")


def _ids(owner, items, fields, optional=()):
    seen = set()
    for item in items:
        if not isinstance(item, dict) or not set(fields) <= set(item) or not set(item) <= set(fields) | set(optional):
            raise ValueError(f"{owner}: item {item.get('id') if isinstance(item, dict) else item!r}: unexpected/missing fields")
        if not ID_RE.fullmatch(item["id"]) or item["id"] in seen:
            raise ValueError(f"{owner}: invalid/duplicate id {item['id']!r}")
        seen.add(item["id"])
    return seen


def _variants(owner, value):
    if not isinstance(value, list) or not value or set(value) - set(VARIANTS) or len(set(value)) != len(value):
        raise ValueError(f"{owner}: variants must be a nonempty subset of {VARIANTS}")


def load_manifest(path: Path, root: Path = ROOT):
    data = json.loads(path.read_text(), object_pairs_hook=arch.unique_object)
    fields = {"schema_version", "document", "script", "makefile", "figure", "knobs", "steps", "refusals",
              "signing", "invocations", "directories"}
    if set(data) != fields or data["schema_version"] != 2:
        raise ValueError("expected build manifest schema_version 2")
    for text in strings(data):
        if DURATION_SIZE_RE.search(text):
            raise ValueError(f"literal duration or size: {text}")
    document = Path(data["document"])
    if document.is_absolute() or ".." in document.parts or document.suffix != ".md":
        raise ValueError("document must be a repository-relative Markdown path")
    if data["document"] not in SPAN_DOCUMENTS:
        raise ValueError("document is not registered for build spans")
    if not arch.FILE_RE.fullmatch(data["figure"]):
        raise ValueError("invalid figure file name")
    if data["script"] != "build.sh" or data["makefile"] != "Makefile":
        raise ValueError("the manifest describes build.sh and the Makefile")
    forbidden = {MANIFEST_NAME, data["document"],
                 str(document.parent / (data["figure"] + ".dot")), str(document.parent / (data["figure"] + ".svg"))}
    step_ids = _ids("steps", data["steps"], ("id", "banners", "variants", "reads", "writes", "refusals", "sources", "checks"), ("where",))
    make_steps = [s for s in data["steps"] if s.get("where") == "Makefile"]
    if len(make_steps) > 1 or (make_steps and data["steps"][0] is not make_steps[0]):
        raise ValueError("at most one step is in the Makefile, and it is the first")
    for step in data["steps"]:
        owner = f"step {step['id']}"
        if not isinstance(step["banners"], list) or any(not isinstance(b, str) or not b.strip() for b in step["banners"]):
            raise ValueError(f"{owner}: banners must be a list of nonempty strings")
        if "where" in step and step["where"] != "Makefile":
            raise ValueError(f"{owner}: where must be Makefile when present")
        _variants(owner, step["variants"])
        _text(owner, step, "reads"); _text(owner, step, "writes")
        if not isinstance(step["refusals"], list):
            raise ValueError(f"{owner}: refusals must be a list")
        _citations(owner, step, root)
    unbannered = [s for s in data["steps"] if not s["banners"] and s.get("where") != "Makefile"]
    if len(unbannered) > 1 or (unbannered and data["steps"].index(unbannered[0]) > 1):
        raise ValueError("only one step without a banner is allowed, before every bannered step of the script")
    refusal_ids = _ids("refusals", data["refusals"], ("id", "message", "kind", "steps", "status", "variants", "sources", "checks"))
    for refusal in data["refusals"]:
        owner = f"refusal {refusal['id']}"
        _text(owner, refusal, "message")
        if refusal["kind"] not in REFUSAL_KINDS:
            raise ValueError(f"{owner}: unknown kind {refusal['kind']!r}")
        if not isinstance(refusal["steps"], list) or not refusal["steps"] or set(refusal["steps"]) - step_ids:
            raise ValueError(f"{owner}: steps must name known steps")
        if not re.fullmatch(r"[0-9]+", str(refusal["status"])) or not isinstance(refusal["status"], str):
            raise ValueError(f"{owner}: status must be a decimal string")
        _variants(owner, refusal["variants"])
        _citations(owner, refusal, root)
    for step in data["steps"]:
        for rid in step["refusals"]:
            if rid not in refusal_ids:
                raise ValueError(f"step {step['id']}: unknown refusal {rid!r}")
    for refusal in data["refusals"]:
        for sid in refusal["steps"]:
            step = next(s for s in data["steps"] if s["id"] == sid)
            if refusal["id"] not in step["refusals"]:
                raise ValueError(f"refusal {refusal['id']}: step {sid} does not list it")
    for step in data["steps"]:
        for rid in step["refusals"]:
            refusal = next(r for r in data["refusals"] if r["id"] == rid)
            if step["id"] not in refusal["steps"]:
                raise ValueError(f"step {step['id']}: refusal {rid} does not name it")
    _ids("signing", data["signing"], ("id", "target", "kind", "entitlements", "loop", "step", "variants", "sources", "checks"))
    for entry in data["signing"]:
        owner = f"signing {entry['id']}"
        _text(owner, entry, "target")
        if entry["kind"] not in ("signature", "seal"):
            raise ValueError(f"{owner}: kind must be signature or seal")
        _text(owner, entry, "entitlements", optional=True); _text(owner, entry, "loop", optional=True)
        if entry["step"] not in step_ids:
            raise ValueError(f"{owner}: unknown step")
        _variants(owner, entry["variants"])
        _citations(owner, entry, root)
    _ids("invocations", data["invocations"], ("id", "command", "step", "variants", "sources", "checks"))
    for item in data["invocations"]:
        owner = f"invocation {item['id']}"
        _text(owner, item, "command")
        if item["step"] not in step_ids:
            raise ValueError(f"{owner}: unknown step")
        _variants(owner, item["variants"])
        _citations(owner, item, root)
    _ids("knobs", data["knobs"], ("id", "name", "default", "values", "governs", "sources", "checks"))
    for knob in data["knobs"]:
        owner = f"knob {knob['id']}"
        _text(owner, knob, "name"); _text(owner, knob, "default"); _text(owner, knob, "governs")
        if not isinstance(knob["values"], dict) or knob["default"] not in knob["values"] or not knob["values"]:
            raise ValueError(f"{owner}: values must be an object holding the default")
        for value, meaning in knob["values"].items():
            if not isinstance(meaning, str) or not meaning.strip():
                raise ValueError(f"{owner}: empty meaning for {value!r}")
        _citations(owner, knob, root)
    _ids("directories", data["directories"], ("id", "path", "facts", "sources", "checks"))
    for directory in data["directories"]:
        owner = f"directory {directory['id']}"
        _text(owner, directory, "path")
        arch._facts(owner, directory["facts"])
        if set(directory["facts"]) != {"Trusted as", "Refused when"}:
            raise ValueError(f"{owner}: facts must be 'Trusted as' and 'Refused when'")
        _citations(owner, directory, root)
    for group in ("steps", "refusals", "signing", "invocations", "knobs", "directories"):
        for item in data[group]:
            for key in ("sources", "checks"):
                for ref in item[key]:
                    if Path(ref["path"]).as_posix() in forbidden:
                        raise ValueError(f"self-citation: {ref['path']}")
    return data


def load_baseline(path: Path):
    data = json.loads(path.read_text(), object_pairs_hook=arch.unique_object)
    if set(data) != {"schema_version", "entries"} or data["schema_version"] != 1 or not isinstance(data["entries"], list):
        raise ValueError("expected build baseline schema_version 1")
    seen = set()
    for row in data["entries"]:
        keys = ("refusal", "variants", "claim", "control")
        if not isinstance(row, dict) or set(row) != set(keys):
            raise ValueError("malformed build baseline entry")
        if not ID_RE.fullmatch(row["refusal"]) or row["refusal"] in seen:
            raise ValueError(f"invalid/duplicate baseline refusal {row['refusal']!r}")
        seen.add(row["refusal"])
        _variants(f"baseline {row['refusal']}", row["variants"])
        for key in ("claim", "control"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError(f"baseline {row['refusal']}: empty {key}")
    return data


# ---- the comparisons: the manifest against the script, the Makefile, meson.build, the inventories, the baseline ----

def script_steps(manifest):
    return [s for s in manifest["steps"] if s.get("where") != "Makefile"]


def banner_problems(manifest, model):
    expected = [(b, s["id"]) for s in script_steps(manifest) for b in s["banners"]]
    actual = [b["text"] for b in model["banners"]]
    out = []
    for index, (want, have) in enumerate(zip([b for b, _ in expected], actual)):
        if want != have:
            out.append(f"banner order: position {index + 1}: manifest '{want}', script '{have}'")
            break
    else:
        if len(expected) != len(actual):
            out.append(f"banner order: manifest names {len(expected)} banners, script prints {len(actual)}")
    if out:
        return out
    for (text, sid), banner in zip(expected, model["banners"]):
        step = next(s for s in manifest["steps"] if s["id"] == sid)
        if sorted(step["variants"]) != banner["variants"]:
            out.append(f"step {sid}: manifest variants {step['variants']}, script {banner['variants']} for '{text}'")
    return out


def _step_of(manifest, model, banner_index):
    """The manifest step whose banner list holds the script's banner at this index."""
    if banner_index is None:
        unbannered = [s for s in script_steps(manifest) if not s["banners"]]
        return unbannered[0]["id"] if unbannered else None
    text = model["banners"][banner_index]["text"]
    for step in script_steps(manifest):
        if text in step["banners"]:
            return step["id"]
    return None


def refusal_problems(manifest, model):
    out = []
    expected = {r["message"]: r for r in manifest["refusals"] if r["kind"] == "script"}
    actual = {}
    for refusal in model["refusals"]:
        if refusal["message"] in actual:
            out.append(f"refusal '{refusal['message']}': the script prints it at two sites")
        actual[refusal["message"]] = refusal
    for message in sorted(set(expected) - set(actual)):
        out.append(f"refusal '{message}' (manifest {expected[message]['id']}): not printed by the script")
    for message in sorted(set(actual) - set(expected)):
        out.append(f"refusal '{message}' at line {actual[message]['line']}: not in the manifest")
    for message in sorted(set(expected) & set(actual)):
        want, have = expected[message], actual[message]
        steps = [_step_of(manifest, model, i) for i in have["steps"]]
        if sorted(want["steps"]) != sorted(s for s in steps if s):
            out.append(f"refusal {want['id']}: manifest steps {want['steps']}, script {steps}")
        if want["status"] != have["status"]:
            out.append(f"refusal {want['id']}: manifest status {want['status']}, script exit {have['status']}")
        if sorted(want["variants"]) != sorted(have["variants"]):
            out.append(f"refusal {want['id']}: manifest variants {want['variants']}, script {have['variants']}")
    return out


def meson_assertions(text):
    """The options meson.build asserts, with their expected values, in order."""
    block = re.search(r"fixed_options = \{(.*?)\n\}", text, re.S)
    if not block:
        raise ParseError("meson.build: no fixed_options block")
    found = re.findall(r"^\s*'([a-z_]+)':\s*(.+?),\s*$", block.group(1), re.M)
    swift = re.search(r"foreach name, expected : \{(.*?)\}", text, re.S)
    if swift:
        found += re.findall(r"'([a-z_]+)':\s*([^,}]+)", swift.group(1))
    return [(name, value.strip()) for name, value in found]


def meson_problems(manifest, meson_text):
    expected = {r["message"]: r for r in manifest["refusals"] if r["kind"] == "meson"}
    actual = {f"fixed native policy: {name} must be {value}": name for name, value in meson_assertions(meson_text)}
    out = [f"meson assertion '{m}' (manifest {expected[m]['id']}): not asserted by meson.build" for m in sorted(set(expected) - set(actual))]
    out += [f"meson assertion '{m}': not in the manifest" for m in sorted(set(actual) - set(expected))]
    return out


def propagated_problems(manifest, model):
    """A propagated refusal names a step whose invocations include the helper it cites."""
    out = []
    for refusal in manifest["refusals"]:
        if refusal["kind"] != "propagated":
            continue
        commands = {i["command"] for i in manifest["invocations"] if i["step"] in refusal["steps"]}
        commands |= {"codesign --force" for e in manifest["signing"] if e["step"] in refusal["steps"]}
        symbols = {s["symbol"] for s in refusal["sources"]}
        if not any(any(symbol in command for command in commands) for symbol in symbols):
            out.append(f"refusal {refusal['id']}: no invocation in steps {refusal['steps']} matches its sources {sorted(symbols)}")
    return out


def knob_problems(manifest, model):
    out = []
    expected = {k["name"]: k for k in manifest["knobs"]}
    knobs = model["knobs"]
    if sorted(expected) != sorted(knobs["names"]):
        return [f"knobs: manifest {sorted(expected)}, script {sorted(knobs['names'])}"]
    for name, knob in expected.items():
        if knob["default"] != knobs["defaults"].get(name):
            out.append(f"knob {name}: manifest default {knob['default']!r}, script {knobs['defaults'].get(name)!r}")
        if sorted(knob["values"]) != sorted(knobs["accepted"]):
            out.append(f"knob {name}: manifest values {sorted(knob['values'])}, script accepts {sorted(knobs['accepted'])}")
    return out


def signing_problems(manifest, model):
    expected = [(e["kind"], e["target"], e["entitlements"], e["loop"], e["step"], sorted(e["variants"])) for e in manifest["signing"]]
    actual = [(r["kind"], r["target"], r["entitlements"], r["loop"], _step_of(manifest, model, r["step"]), r["variants"]) for r in model["signing"]]
    for index, (want, have) in enumerate(zip(expected, actual)):
        if want != have:
            return [f"signing order: entry {index + 1}: manifest {want}, script {have}"]
    if len(expected) != len(actual):
        return [f"signing order: manifest lists {len(expected)} signing calls, script makes {len(actual)}"]
    return []


def invocation_problems(manifest, model):
    expected = {(i["command"], i["step"], tuple(sorted(i["variants"]))) for i in manifest["invocations"]}
    actual = {(r["command"], _step_of(manifest, model, r["step"]), tuple(r["variants"])) for r in model["invocations"]}
    out = [f"invocation {c!r} in step {s} ({', '.join(v)}): not in the manifest" for c, s, v in sorted(actual - expected, key=str)]
    out += [f"invocation {c!r} in step {s} ({', '.join(v)}): not made by the script" for c, s, v in sorted(expected - actual, key=str)]
    return out


def makefile_problems(manifest, makefile_text):
    step = next((s for s in manifest["steps"] if s.get("where") == "Makefile"), None)
    if step is None:
        return []
    recipe = re.search(r"^build:\n((?:\t.*\n)+)", makefile_text, re.M)
    if not recipe:
        return ["Makefile: no build recipe"]
    body = recipe.group(1)
    out = []
    for banner in step["banners"]:
        if f'@echo "==> {banner}"' not in body:
            out.append(f"Makefile build recipe: banner '{banner}' not printed")
    for rid in step["refusals"]:
        refusal = next(r for r in manifest["refusals"] if r["id"] == rid)
        if f'echo "ERROR: {refusal["message"]}"' not in body:
            out.append(f"Makefile build recipe: refusal '{refusal['message']}' not printed")
        if f"exit {refusal['status']};" not in body:
            out.append(f"Makefile build recipe: refusal {rid} does not exit {refusal['status']}")
    if "./build.sh" not in body:
        out.append("Makefile build recipe: does not run ./build.sh")
    return out


def bundle_paths(manifest, model, root):
    """Every executable the signing list signs or seals as a bundle's main executable, by bundle path."""
    services = model["arrays"].get("XPC_SERVICE_NAMES", [])
    mains = {}
    with (root / "Info.plist").open("rb") as stream:
        mains["app"] = "Contents/MacOS/" + plistlib.load(stream)["CFBundleExecutable"]
    for svc in services:
        with (root / "runner/Services" / svc / "Info.plist").open("rb") as stream:
            mains[svc] = f"Contents/XPCServices/{svc}.xpc/Contents/MacOS/" + plistlib.load(stream)["CFBundleExecutable"]
    paths, problems = {v: set() for v in VARIANTS}, []
    for entry in manifest["signing"]:
        target, kind = entry["target"], entry["kind"]
        found = []
        if target.startswith("${APP_BUNDLE}/"):
            found = [target[len("${APP_BUNDLE}/"):]]
        elif target == "${APP_BUNDLE}" and kind == "seal":
            found = [mains["app"]]
        elif target.startswith("${svc_bundle}/") and entry["loop"] == "XPC_SERVICE_NAMES":
            found = [f"Contents/XPCServices/{svc}.xpc/" + target[len("${svc_bundle}/"):] for svc in services]
        elif target == "${svc_bundle}" and kind == "seal" and entry["loop"] == "XPC_SERVICE_NAMES":
            found = [mains[svc] for svc in services]
        elif target == "${SANDBOX_LOG_OBSERVER_BIN}":
            continue  # outside the bundle
        else:
            problems.append(f"signing {entry['id']}: target {target!r} is not a bundle path the inventory rule can expand")
        for variant in entry["variants"]:
            paths[variant].update(found)
    return paths, problems


def readme_inventory(text):
    section = re.search(r"^## What ships\n(.*?)^## ", text, re.S | re.M)
    if not section:
        raise ParseError("README.md: no 'What ships' section")
    paths, services, service = [], [], None
    for line in section.group(1).splitlines():
        match = re.match(r"^(\s*)- `([^`]+)`", line)
        if not match:
            continue
        indent, item = len(match.group(1)), match.group(2)
        if indent == 2 and item.endswith(".xpc"):
            service = item
            services.append(item)
        elif indent == 2 and item.startswith("Contents/MacOS/"):
            paths.append(item)
        elif indent == 4 and item.startswith("Contents/MacOS/") and service:
            paths.append(f"{service}/{item}")
    return sorted(paths), services


def inventory_problems(manifest, model, root):
    paths, out = bundle_paths(manifest, model, root)
    text = (root / "tests/lib/artifact.py").read_text()
    namespace = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and node.targets[0].id in ("CONTROLLER", "SERVICE", "EXECUTABLES"):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "artifact", "exec"), namespace)
    executables = sorted(namespace["EXECUTABLES"])
    if sorted(paths["full"]) != executables:
        out.append(f"inventory: the full build signs {sorted(paths['full'])} but EXECUTABLES lists {executables}")
    if not paths["partial"] <= paths["full"]:
        out.append(f"inventory: the partial build signs {sorted(paths['partial'] - paths['full'])} that the full build does not")
    evidence = ast.parse((root / "tests/build-evidence.py").read_text())
    helpers = next((ast.literal_eval(node.value) for node in ast.walk(evidence)
                    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "helper_names"), None)
    top = sorted(p.split("/")[-1] for p in paths["full"] if p.startswith("Contents/MacOS/") and p != "Contents/MacOS/" + Path(namespace["CONTROLLER"]).name)
    if helpers is None or sorted(helpers) != top:
        out.append(f"inventory: build-evidence.py helper_names {helpers} differ from the signed top-level helpers {top}")
    readme, services = readme_inventory((root / "README.md").read_text())
    for bundle in services:  # a listed service bundle implies its main executable
        name = Path(bundle).name[:-len(".xpc")]
        with (root / "runner/Services" / name / "Info.plist").open("rb") as stream:
            readme.append(f"{bundle}/Contents/MacOS/" + plistlib.load(stream)["CFBundleExecutable"])
    readme.sort()
    if readme != executables:
        out.append(f"inventory: README 'What ships' lists {readme} but EXECUTABLES lists {executables}")
    return out


def coverage(refusal):
    kinds = {ref["coverage"] for ref in refusal["checks"]}
    return "behavioral" if "behavioral" in kinds else "helper" if "helper" in kinds else "textual"


def baseline_problems(manifest, baseline):
    uncovered = {r["id"]: r for r in manifest["refusals"] if coverage(r) == "textual"}
    listed = {row["refusal"]: row for row in baseline["entries"]}
    out = [f"baseline: refusal {rid} has no behavioral or helper control and is not listed" for rid in sorted(set(uncovered) - set(listed))]
    out += [f"baseline: listed refusal {rid} is unknown or now has a control; remove the entry" for rid in sorted(set(listed) - set(uncovered))]
    for rid in sorted(set(uncovered) & set(listed)):
        if sorted(listed[rid]["variants"]) != sorted(uncovered[rid]["variants"]):
            out.append(f"baseline: refusal {rid} variants {uncovered[rid]['variants']} differ from the entry's {listed[rid]['variants']}")
    return out


def script_problems(manifest, root):
    """Every comparison, over the real files; each problem names the differing item."""
    model = parse_script((root / manifest["script"]).read_text())
    problems = banner_problems(manifest, model)
    if problems:
        return problems  # later comparisons depend on the banner-to-step mapping
    problems += refusal_problems(manifest, model)
    problems += meson_problems(manifest, (root / "meson.build").read_text())
    problems += propagated_problems(manifest, model)
    problems += knob_problems(manifest, model)
    problems += signing_problems(manifest, model)
    problems += invocation_problems(manifest, model)
    problems += makefile_problems(manifest, (root / manifest["makefile"]).read_text())
    problems += inventory_problems(manifest, model, root)
    problems += baseline_problems(manifest, load_baseline(root / BASELINE_NAME))
    return problems


# ---- rendering ---------------------------------------------------------------

def render_dot(manifest):
    lines = ["digraph build_steps {",
             '    graph [rankdir=TB, bgcolor="white", fontname="Helvetica", fontsize=11, label="One build in time", labelloc=t, pad=0.3, nodesep=0.2, ranksep=0.25];',
             '    node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled", fillcolor="#f2f2f2", color="#444444"];',
             '    edge [fontname="Helvetica", fontsize=9, color="#444444"];']
    steps = manifest["steps"]
    document = Path(manifest["document"]).name
    for step in steps:
        label = step["banners"][0] if step["banners"] else "(before the first banner)"
        label = re.sub(r"\$\{[^}]+\}", "…", label)
        label = re.sub(r"\$\([^)]+\)", "…", label)
        refusals = len(step["refusals"])
        attrs = {"label": f"{step['id']}\\n{label}" + (f"\\n{refusals} refusal(s)" if refusals else ""),
                 "URL": f"{document}#{arch.anchor('build steps')}",
                 "tooltip": f"{step['id']}: reads {step['reads']}; writes {step['writes']}"}
        if step["variants"] == ["full"]:
            attrs["fillcolor"] = "#e8f0fe"
        elif step["variants"] == ["partial"]:
            attrs["style"] = "rounded,dashed"
            attrs["fillcolor"] = "white"
        if step.get("where") == "Makefile":
            attrs["fillcolor"] = "#fff4e0"
        lines.append(f"    {step['id']} [{arch._attr_text(attrs)}];")
    previous = None
    for step in steps:
        if previous is not None:
            lines.append(f"    {previous} -> {step['id']};")
        previous = step["id"]
    lines.append("}")
    return "\n".join(lines) + "\n"


def stamp(dot_text):
    return f"<!-- build.json figure steps; dot sha256 {arch.dot_hash(dot_text)} -->"


def stamp_svg(svg_text, dot_text):
    first, _, rest = svg_text.partition("\n")
    return f"{first}\n{stamp(dot_text)}\n{rest}"


def svg_stamp_matches(svg_text, dot_text):
    match = STAMP_RE.search(svg_text)
    return bool(match) and match.group(1) == "steps" and match.group(2) == arch.dot_hash(dot_text)


VERIFIED = ("Symbol presence and test definition are verified, and the banner order, refusal messages, "
            "statuses and steps, knob values, signing calls, helper invocations and the signing inventory are "
            "compared with the script by the build_documentation case; whether a test asserts the row, or a "
            "refusal fires before the operation it protects, is not verified.")


def _cites(item):
    return arch._citation_cell(item["sources"]), arch._citation_cell([{k: v for k, v in r.items() if k != "coverage"} for r in item["checks"]])


def _variant_cell(variants):
    return "both" if sorted(variants) == sorted(VARIANTS) else ", ".join(variants)


def render_figure(manifest):
    figure, manifest_name, generator = manifest["figure"], Path(MANIFEST_NAME).name, Path(GENERATOR_NAME).name
    return "\n".join([
        f"![One build in time]({figure}.svg)", "",
        f"*Figure: one build in time, step by step. Generated from [{manifest_name}]({manifest_name}) by "
        f"[{generator}]({generator}); dot source in [{figure}.dot]({figure}.dot). The ids in the figure are the "
        f"ids in the step table; a filled node runs only in a full build, a dashed one only in a partial build. {VERIFIED}*"])


def render_steps(manifest):
    rows = []
    for step in manifest["steps"]:
        banner = " / ".join(step["banners"]) if step["banners"] else "(none)"
        if step.get("where") == "Makefile":
            banner = f"Makefile: {banner}"
        rows.append([step["id"], banner, _variant_cell(step["variants"]), step["reads"], step["writes"],
                     ", ".join(step["refusals"]) or "none", *_cites(step)])
    summary = (f"<summary>{len(manifest['steps'])} steps in order, with symbol presence and test definition verified "
               f"and the banner order compared with the script; whether a test asserts the row is not verified</summary>")
    return "\n".join(["<details>", summary, "", arch._table(
        ["Id", "Banner", "Variants", "Reads", "Writes", "Refusals", "Sources", "Checks"], rows), "", "</details>"])


def render_refusals(manifest):
    rows = []
    for refusal in manifest["refusals"]:
        cover = coverage(refusal)
        cell = {"behavioral": "a control produces it", "helper": "a control produces it in the helper, not through the script",
                "textual": "none; listed in the baseline"}[cover]
        rows.append([refusal["id"], refusal["message"], ", ".join(refusal["steps"]), refusal["status"], refusal["kind"],
                     _variant_cell(refusal["variants"]), cell, *_cites(refusal)])
    counts = {kind: sum(r["kind"] == kind for r in manifest["refusals"]) for kind in REFUSAL_KINDS}
    uncovered = sum(coverage(r) == "textual" for r in manifest["refusals"])
    summary = (f"<summary>{len(manifest['refusals'])} refusals ({counts['script']} the script's own, {counts['meson']} Meson "
               f"assertions, {counts['propagated']} propagated from a check or a tool, {counts['make']} in the Makefile), "
               f"with symbol presence and test definition verified and the messages, statuses and steps compared with the "
               f"script; {uncovered} have no control that produces them and are listed in the baseline; whether a test "
               f"asserts the row is not verified</summary>")
    return "\n".join(["<details>", summary, "", arch._table(
        ["Id", "Message", "Steps", "Status", "Kind", "Variants", "Coverage", "Sources", "Checks"], rows), "", "</details>"])


def render_signing(manifest):
    rows = [[str(index), entry["target"], entry["kind"], entry["entitlements"] or "none",
             entry["loop"] or "no", entry["step"], _variant_cell(entry["variants"]), *_cites(entry)]
            for index, entry in enumerate(manifest["signing"], start=1)]
    summary = (f"<summary>{len(manifest['signing'])} signing calls in order, with symbol presence and test definition "
               f"verified and the calls, their targets and entitlements compared with the script and the signed inventory "
               f"with EXECUTABLES, the evidence generator and the README; whether a test asserts the row is not verified</summary>")
    return "\n".join(["<details>", summary, "", arch._table(
        ["#", "Target", "Kind", "Entitlements", "In the service loop", "Step", "Variants", "Sources", "Checks"], rows), "", "</details>"])


def render_knobs(manifest):
    rows = [[knob["name"], "; ".join(f"`{v}`: {m}" for v, m in knob["values"].items()), knob["default"], knob["governs"], *_cites(knob)]
            for knob in manifest["knobs"]]
    return arch._table(["Knob", "Values", "Unset means", "Governs", "Sources", "Checks"], rows)


def render_directories(manifest):
    rows = [[d["path"], d["facts"]["Trusted as"], d["facts"]["Refused when"], *_cites(d)] for d in manifest["directories"]]
    return arch._table(["Directory", "Trusted as", "Refused when", "Sources", "Checks"], rows)


RENDERERS = {"FIGURE": render_figure, "STEPS": render_steps, "REFUSALS": render_refusals,
             "SIGNING": render_signing, "KNOBS": render_knobs, "DIRECTORIES": render_directories}


def span_values(manifest):
    refusals = manifest["refusals"]
    values = {"steps": len(manifest["steps"]), "refusals": len(refusals), "signing": len(manifest["signing"]),
              "knobs": len(manifest["knobs"]), "invocations": len(manifest["invocations"]),
              "covered": sum(coverage(r) != "textual" for r in refusals),
              "uncovered": sum(coverage(r) == "textual" for r in refusals)}
    for kind in REFUSAL_KINDS:
        values[f"refusals.{kind}"] = sum(r["kind"] == kind for r in refusals)
    return {name: format_value(value) for name, value in values.items()}


def render_document(text, manifest):
    text = render_spans(text, "build", span_values(manifest))
    for region in REGIONS:
        text = arch.replace_block(text, REGION_START.format(region=region), REGION_END.format(region=region), RENDERERS[region](manifest))
    return text


# ---- commands -----------------------------------------------------------------

def check(root: Path):
    manifest = load_manifest(root / MANIFEST_NAME, root)
    problems = [f"manifest disagrees with the script: {p}" for p in script_problems(manifest, root)]
    document_path = root / manifest["document"]
    dot_text = render_dot(manifest)
    dot_path = document_path.parent / f"{manifest['figure']}.dot"
    svg_path = document_path.parent / f"{manifest['figure']}.svg"
    if not dot_path.is_file() or dot_path.read_text() != dot_text:
        problems.append(f"{dot_path.relative_to(root)}: stale or missing; regenerate")
    if not svg_path.is_file():
        problems.append(f"{svg_path.relative_to(root)}: missing; regenerate with dot")
    elif not svg_stamp_matches(svg_path.read_text(errors="replace"), dot_text):
        problems.append(f"{svg_path.relative_to(root)}: stamp does not name the current dot text; re-render")
    if not document_path.is_file():
        problems.append(f"{manifest['document']}: missing")
    else:
        text = document_path.read_text()
        try:
            problems.extend(span_problems(text, "build", span_values(manifest)))
            if render_document(text, manifest) != text:
                problems.append(f"{manifest['document']}: generated regions are stale; regenerate")
        except ValueError as error:
            problems.append(f"{manifest['document']}: {error}")
    values = span_values(manifest)
    summary = (f"build manifest: {values['steps']} steps, {values['refusals']} refusals ({values['uncovered']} in the baseline), "
               f"{values['signing']} signing calls, {values['knobs']} knobs; script agreement, dot file, svg stamp and document regions current")
    return problems, summary


def write(root: Path, skip_svg: bool):
    manifest = load_manifest(root / MANIFEST_NAME, root)
    problems = script_problems(manifest, root)
    if problems:
        raise ValueError("manifest disagrees with the script:\n  " + "\n  ".join(problems))
    document_path = root / manifest["document"]
    text = document_path.read_text()
    rendered = render_document(text, manifest)  # validate markers before writing anything
    dot_text = render_dot(manifest)
    dot_path = document_path.parent / f"{manifest['figure']}.dot"
    svg_path = document_path.parent / f"{manifest['figure']}.svg"
    pending = {}
    if not dot_path.is_file() or dot_path.read_text() != dot_text:
        pending[dot_path] = dot_text
    if not skip_svg and (not svg_path.is_file() or not svg_stamp_matches(svg_path.read_text(errors="replace"), dot_text)):
        pending[svg_path] = stamp_svg(arch.render_svg(dot_text), dot_text)
    if rendered != text:
        pending[document_path] = rendered
    for path, content in pending.items():
        path.write_text(content)
    return list(pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify every generated copy and the script agreement; write nothing")
    mode.add_argument("--skip-svg", action="store_true", help="write the dot file and the document regions; leave the SVG")
    args = parser.parse_args()
    try:
        if args.check:
            problems, summary = check(ROOT)
            if problems:
                print("build documentation is stale:", file=sys.stderr)
                for problem in problems:
                    print(f"  {problem}", file=sys.stderr)
                print(f"run: python3 {GENERATOR_NAME}", file=sys.stderr)
                return 1
            print(f"ok: {summary}")
            return 0
        written = write(ROOT, args.skip_svg)
        names = ", ".join(str(p.relative_to(ROOT)) for p in written) or "nothing"
        print(f"ok: wrote {names}")
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
