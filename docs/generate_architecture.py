#!/usr/bin/env python3
"""Generate the architecture figures and tables from docs/architecture.json.

The manifest owns every node and edge of the graphs in docs/ARCHITECTURE.md,
each with the source symbol and the check that pin it. This script renders
each graph to Graphviz dot text, renders that dot to SVG with the installed
`dot`, stamps the SVG with the hash of its dot text, and writes the figure
embed plus the node and edge tables into the marked regions of the document.

  generate_architecture.py             write dot files, SVGs and document regions
  generate_architecture.py --skip-svg  write dot files and document regions only
  generate_architecture.py --check     verify every copy without writing

`--check` needs no Graphviz: an SVG is checked by its stamp, which names the
hash of the dot text it was rendered from. Rendering needs `dot` on PATH.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "docs/architecture.json"
GENERATOR_NAME = "docs/generate_architecture.py"
REGION_START = "<!-- BEGIN GENERATED ARCHITECTURE GRAPH {graph} -->"
REGION_END = "<!-- END GENERATED ARCHITECTURE GRAPH {graph} -->"
STAMP_RE = re.compile(r"<!-- architecture\.json graph (\S+); dot sha256 ([0-9a-f]{64}) -->")
ID_RE = re.compile(r"[a-z][a-z0-9_]*")
EDGE_ID_RE = re.compile(r"[A-Z][0-9]+")
FILE_RE = re.compile(r"[a-z][a-z0-9-]*")


def unique_object(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"duplicate key {key!r}")
        seen.add(key)
    return dict(pairs)


def _citation(owner, key, ref, root):
    if not isinstance(ref, dict) or set(ref) != {"path", "symbol"}:
        raise ValueError(f"{owner}: malformed {key} reference")
    path = Path(ref["path"])
    if path.is_absolute() or ".." in path.parts or not (root / path).is_file():
        raise ValueError(f"{owner}: missing/invalid reference {path}")
    text = (root / path).read_text(errors="replace")
    if not ref["symbol"] or ref["symbol"] not in text:
        raise ValueError(f"{owner}: missing symbol {ref['symbol']!r} in {path}")


def _facts(owner, facts):
    if not isinstance(facts, dict):
        raise ValueError(f"{owner}: facts must be an object")
    for key, value in facts.items():
        if not key.strip() or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{owner}: empty fact {key!r}")


def _attrs(owner, attrs):
    if not isinstance(attrs, dict):
        raise ValueError(f"{owner}: style attributes must be an object")
    for key, value in attrs.items():
        if not re.fullmatch(r"[a-z]+", key) or not isinstance(value, str):
            raise ValueError(f"{owner}: bad style attribute {key!r}")


def load_manifest(path: Path, root: Path = ROOT):
    data = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if set(data) != {"schema_version", "document", "styles", "graphs"} or data["schema_version"] != 1:
        raise ValueError("expected architecture manifest schema_version 1")
    document = Path(data["document"])
    if document.is_absolute() or ".." in document.parts or document.suffix != ".md":
        raise ValueError("document must be a repository-relative Markdown path")
    styles = data["styles"]
    if set(styles) != {"node_kinds", "edge_kinds"}:
        raise ValueError("styles must define node_kinds and edge_kinds")
    for group in ("node_kinds", "edge_kinds"):
        for kind, attrs in styles[group].items():
            if not ID_RE.fullmatch(kind):
                raise ValueError(f"invalid style kind {kind!r}")
            _attrs(f"styles.{group}.{kind}", attrs)
    if not isinstance(data["graphs"], list) or not data["graphs"]:
        raise ValueError("graphs must be a nonempty list")
    graph_ids, files, edge_ids = set(), set(), set()
    for graph in data["graphs"]:
        expected = {"id", "title", "file", "rankdir", "clusters", "nodes", "edges"}
        if set(graph) != expected:
            raise ValueError(f"graph {graph.get('id')}: unexpected/missing fields")
        gid = graph["id"]
        if not ID_RE.fullmatch(gid) or gid in graph_ids:
            raise ValueError(f"invalid/duplicate graph id {gid!r}")
        graph_ids.add(gid)
        if not FILE_RE.fullmatch(graph["file"]) or graph["file"] in files:
            raise ValueError(f"{gid}: invalid/duplicate file {graph['file']!r}")
        files.add(graph["file"])
        if not isinstance(graph["title"], str) or not graph["title"].strip():
            raise ValueError(f"{gid}: empty title")
        if graph["rankdir"] not in {"LR", "TB"}:
            raise ValueError(f"{gid}: rankdir must be LR or TB")
        if not isinstance(graph["nodes"], list) or not graph["nodes"]:
            raise ValueError(f"{gid}: nodes must be a nonempty list")
        node_ids = set()
        for node in graph["nodes"]:
            fields = {"id", "label", "kind", "facts", "sources", "checks"}
            if not fields <= set(node) or not set(node) <= fields | {"note"}:
                raise ValueError(f"{gid}: node {node.get('id')}: unexpected/missing fields")
            nid = node["id"]
            if not ID_RE.fullmatch(nid) or nid in node_ids:
                raise ValueError(f"{gid}: invalid/duplicate node id {nid!r}")
            node_ids.add(nid)
            owner = f"{gid}.{nid}"
            if not isinstance(node["label"], str) or not node["label"].strip():
                raise ValueError(f"{owner}: empty label")
            if node["kind"] not in styles["node_kinds"]:
                raise ValueError(f"{owner}: unknown node kind {node['kind']!r}")
            _facts(owner, node["facts"])
            _citations(owner, node, root)
        if not isinstance(graph["edges"], list):
            raise ValueError(f"{gid}: edges must be a list")
        for edge in graph["edges"]:
            fields = {"id", "from", "to", "kind", "label", "sources", "checks"}
            if not fields <= set(edge) or not set(edge) <= fields | {"facts", "note", "short"}:
                raise ValueError(f"{gid}: edge {edge.get('id')}: unexpected/missing fields")
            eid = edge["id"]
            if not EDGE_ID_RE.fullmatch(eid) or eid in edge_ids:
                raise ValueError(f"{gid}: invalid/duplicate edge id {eid!r}")
            edge_ids.add(eid)
            owner = f"{gid}.{eid}"
            for end in ("from", "to"):
                if edge[end] not in node_ids:
                    raise ValueError(f"{owner}: unknown node {edge[end]!r}")
            if edge["kind"] not in styles["edge_kinds"]:
                raise ValueError(f"{owner}: unknown edge kind {edge['kind']!r}")
            if not isinstance(edge["label"], str) or not edge["label"].strip():
                raise ValueError(f"{owner}: empty label")
            _facts(owner, edge.get("facts", {}))
            if "short" in edge and (not isinstance(edge["short"], str) or not edge["short"].strip()):
                raise ValueError(f"{owner}: empty short label")
            _citations(owner, edge, root)
        if not isinstance(graph["clusters"], list):
            raise ValueError(f"{gid}: clusters must be a list")
        clustered = set()
        for cluster in graph["clusters"]:
            if set(cluster) != {"id", "label", "nodes"} or not ID_RE.fullmatch(cluster["id"]):
                raise ValueError(f"{gid}: malformed cluster")
            if not isinstance(cluster["nodes"], list) or not cluster["nodes"]:
                raise ValueError(f"{gid}: cluster {cluster['id']} lists no nodes")
            for nid in cluster["nodes"]:
                if nid not in node_ids or nid in clustered:
                    raise ValueError(f"{gid}: cluster {cluster['id']}: unknown or repeated node {nid!r}")
                clustered.add(nid)
    return data


def _citations(owner, item, root):
    for key in ("sources", "checks"):
        if not isinstance(item[key], list):
            raise ValueError(f"{owner}: {key} must be a list")
        for ref in item[key]:
            _citation(owner, key, ref, root)
    if not item["sources"]:
        raise ValueError(f"{owner}: at least one source citation is required")
    if "note" in item and (not isinstance(item["note"], str) or not item["note"].strip()):
        raise ValueError(f"{owner}: empty note")


# ---- rendering ---------------------------------------------------------------

def esc(text):
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def anchor(text):
    return re.sub(r"[^a-z0-9 -]", "", text.lower()).strip().replace(" ", "-")


def nodes_heading(graph):
    return f"{graph['title']} nodes"


def edges_heading(graph):
    return f"{graph['title']} edges"


def _attr_text(attrs):
    return ", ".join(f'{k}="{esc(v)}"' for k, v in attrs.items())


def render_dot(graph, styles, document_name):
    lines = [f"digraph {graph['id']} {{"]
    lines.append(
        f'    graph [rankdir={graph["rankdir"]}, bgcolor="white", fontname="Helvetica", fontsize=11, '
        f'label="{esc(graph["title"])}", labelloc=t, pad=0.3, nodesep=0.35, ranksep=0.6];'
    )
    lines.append('    node [fontname="Helvetica", fontsize=10];')
    lines.append('    edge [fontname="Helvetica", fontsize=9];')
    node_url = f"{document_name}#{anchor(nodes_heading(graph))}"
    edge_url = f"{document_name}#{anchor(edges_heading(graph))}"
    for cluster in graph["clusters"]:
        lines.append(f"    subgraph cluster_{cluster['id']} {{")
        lines.append(f'        label="{esc(cluster["label"])}"; style=dashed; color="#888888"; fontsize=10;')
        for nid in cluster["nodes"]:
            lines.append(f"        {nid};")
        lines.append("    }")
    for node in graph["nodes"]:
        attrs = dict(styles["node_kinds"][node["kind"]])
        attrs["label"] = f"{node['label']}\n{node['id']}"
        attrs["URL"] = node_url
        attrs["tooltip"] = f"{node['id']}: {node['label']}"
        lines.append(f"    {node['id']} [{_attr_text(attrs)}];")
    for edge in graph["edges"]:
        attrs = dict(styles["edge_kinds"][edge["kind"]])
        # The figure shows the id and a short label; the table beside it holds the full edge text.
        attrs["label"] = f"{edge['id']} {edge['short']}" if "short" in edge else edge["id"]
        attrs["URL"] = edge_url
        attrs["tooltip"] = f"{edge['id']}: {edge['label']}"
        lines.append(f"    {edge['from']} -> {edge['to']} [{_attr_text(attrs)}];")
    lines.append("}")
    return "\n".join(lines) + "\n"


def dot_hash(dot_text):
    return hashlib.sha256(dot_text.encode("utf-8")).hexdigest()


def stamp(graph_id, dot_text):
    return f"<!-- architecture.json graph {graph_id}; dot sha256 {dot_hash(dot_text)} -->"


def stamp_svg(svg_text, graph_id, dot_text):
    first, _, rest = svg_text.partition("\n")
    return f"{first}\n{stamp(graph_id, dot_text)}\n{rest}"


def svg_stamp_matches(svg_text, graph_id, dot_text):
    match = STAMP_RE.search(svg_text)
    return bool(match) and match.group(1) == graph_id and match.group(2) == dot_hash(dot_text)


def cell(text):
    return text.replace("|", "\\|").replace("\n", " ")


def reference(ref):
    # Repository-relative paths in JSON become document-relative links here.
    return f"[`{ref['symbol']}`](../{ref['path']})"


def _citation_cell(refs):
    return "; ".join(reference(ref) for ref in refs) if refs else "none"


def _table(header, rows):
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for row in rows:
        out.append("| " + " | ".join(cell(c) for c in row) + " |")
    return "\n".join(out)


def _fact_columns(items):
    columns = []
    for item in items:
        for key in item.get("facts", {}):
            if key not in columns:
                columns.append(key)
    return columns


def render_region(graph, document_name):
    svg = f"{graph['file']}.svg"
    dot = f"{graph['file']}.dot"
    manifest = Path(MANIFEST_NAME).name
    generator = Path(GENERATOR_NAME).name
    parts = [
        f"![{graph['title']}]({svg})",
        "",
        f"*Figure: {graph['title'].lower()}. Generated from [{manifest}]({manifest}) by "
        f"[{generator}]({generator}); dot source in [{dot}]({dot}). The ids in the figure are the "
        f"ids in the tables below, and each row names the source and the check that pin it.*",
        "",
        f"#### {nodes_heading(graph)}",
        "",
    ]
    columns = _fact_columns(graph["nodes"])
    rows = []
    for node in graph["nodes"]:
        row = [node["id"], node["label"], node["kind"]]
        row += [node["facts"].get(c, "") for c in columns]
        row += [_citation_cell(node["sources"]), _citation_cell(node["checks"])]
        rows.append(row)
    parts.append(_table(["Id", "Node", "Kind", *columns, "Sources", "Checks"], rows))
    parts += ["", f"#### {edges_heading(graph)}", ""]
    columns = _fact_columns(graph["edges"])
    rows = []
    for edge in graph["edges"]:
        row = [edge["id"], edge["from"], edge["to"], edge["kind"], edge["label"]]
        row += [edge.get("facts", {}).get(c, "") for c in columns]
        row += [_citation_cell(edge["sources"]), _citation_cell(edge["checks"])]
        rows.append(row)
    parts.append(_table(["Id", "From", "To", "Kind", "Edge", *columns, "Sources", "Checks"], rows))
    notes = [(n["id"], n["note"]) for n in graph["nodes"] if "note" in n]
    notes += [(e["id"], e["note"]) for e in graph["edges"] if "note" in e]
    if notes:
        parts += ["", "Notes:", ""]
        parts += [f"- `{ident}`: {note}" for ident, note in notes]
    unpinned = [n["id"] for n in graph["nodes"] if not n["checks"]]
    unpinned += [e["id"] for e in graph["edges"] if not e["checks"]]
    parts.append("")
    if unpinned:
        parts.append("Claims without a pinning check: " + ", ".join(f"`{i}`" for i in unpinned) + ".")
    else:
        parts.append("Every node and edge above names at least one check.")
    return "\n".join(parts)


def block_bounds(text, start, end):
    if text.count(start) != 1 or text.count(end) != 1 or text.index(end) < text.index(start):
        raise ValueError(f"expected exactly one ordered block: {start} ... {end}")
    return text.index(start), text.index(end) + len(end)


def replace_block(text, start, end, body):
    begin, finish = block_bounds(text, start, end)
    return text[:begin] + start + "\n" + body + "\n" + end + text[finish:]


def render_document(text, manifest):
    document_name = Path(manifest["document"]).name
    for graph in manifest["graphs"]:
        start = REGION_START.format(graph=graph["id"])
        end = REGION_END.format(graph=graph["id"])
        text = replace_block(text, start, end, render_region(graph, document_name))
    return text


def render_svg(dot_text):
    tool = shutil.which("dot")
    if tool is None:
        raise RuntimeError("Graphviz `dot` is not on PATH; install Graphviz or pass --skip-svg")
    result = subprocess.run([tool, "-Tsvg"], input=dot_text, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"dot failed: {result.stderr.strip()}")
    return result.stdout


# ---- commands -----------------------------------------------------------------

def expected_outputs(root: Path, manifest):
    """Every file this generator owns, with the text it should hold (SVGs by stamp)."""
    document_path = root / manifest["document"]
    document_name = document_path.name
    outputs = {}
    for graph in manifest["graphs"]:
        dot_text = render_dot(graph, manifest["styles"], document_name)
        outputs[document_path.parent / f"{graph['file']}.dot"] = dot_text
    return outputs


def check(root: Path):
    manifest = load_manifest(root / MANIFEST_NAME, root)
    problems = []
    document_path = root / manifest["document"]
    document_name = document_path.name
    for graph in manifest["graphs"]:
        dot_text = render_dot(graph, manifest["styles"], document_name)
        dot_path = document_path.parent / f"{graph['file']}.dot"
        svg_path = document_path.parent / f"{graph['file']}.svg"
        if not dot_path.is_file() or dot_path.read_text() != dot_text:
            problems.append(f"{dot_path.relative_to(root)}: stale or missing; regenerate")
        if not svg_path.is_file():
            problems.append(f"{svg_path.relative_to(root)}: missing; regenerate with dot")
        elif not svg_stamp_matches(svg_path.read_text(errors="replace"), graph["id"], dot_text):
            problems.append(f"{svg_path.relative_to(root)}: stamp does not name the current dot text; re-render")
    if not document_path.is_file():
        problems.append(f"{manifest['document']}: missing")
    else:
        text = document_path.read_text()
        try:
            if render_document(text, manifest) != text:
                problems.append(f"{manifest['document']}: generated regions are stale; regenerate")
        except ValueError as error:
            problems.append(f"{manifest['document']}: {error}")
    nodes = sum(len(g["nodes"]) for g in manifest["graphs"])
    edges = sum(len(g["edges"]) for g in manifest["graphs"])
    summary = (f"architecture manifest: {len(manifest['graphs'])} graphs, {nodes} nodes, {edges} edges; "
               f"dot files, svg stamps and document regions current")
    return problems, summary


def write(root: Path, skip_svg: bool):
    manifest = load_manifest(root / MANIFEST_NAME, root)
    document_path = root / manifest["document"]
    document_name = document_path.name
    text = document_path.read_text()
    rendered = render_document(text, manifest)  # validate markers before writing anything
    written = []
    for graph in manifest["graphs"]:
        dot_text = render_dot(graph, manifest["styles"], document_name)
        dot_path = document_path.parent / f"{graph['file']}.dot"
        if not dot_path.is_file() or dot_path.read_text() != dot_text:
            dot_path.write_text(dot_text)
            written.append(dot_path)
        if not skip_svg:
            svg_path = document_path.parent / f"{graph['file']}.svg"
            if not svg_path.is_file() or not svg_stamp_matches(svg_path.read_text(errors="replace"), graph["id"], dot_text):
                svg_path.write_text(stamp_svg(render_svg(dot_text), graph["id"], dot_text))
                written.append(svg_path)
    if rendered != text:
        document_path.write_text(rendered)
        written.append(document_path)
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify every generated copy; write nothing")
    mode.add_argument("--skip-svg", action="store_true", help="write dot files and document regions; leave SVGs")
    args = parser.parse_args()
    try:
        if args.check:
            problems, summary = check(ROOT)
            if problems:
                print("architecture documentation is stale:", file=sys.stderr)
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
