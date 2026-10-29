"""D2 read-only ownership/scope extraction; writes only this records directory."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SOURCE='7562d24ac2334122499ea349010fd67211058ac3'
sys.path[:0]=[str(ROOT/'docs'),str(ROOT/'tests/lib')]
import fixture_inputs
import generator_common
import markdown_reader
import repository_tree


def historical(path):
    return subprocess.check_output(['git','show',f'{SOURCE}:{path}'],cwd=ROOT)


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    changed=subprocess.check_output(['git','diff','--name-only',SOURCE],cwd=ROOT,text=True).splitlines()
    assert all(p.startswith('records/checks-before-check/') or p=='docs/CHECKS-BEFORE-CHECK-PLAN.md' for p in changed),changed
    machinery=module('d2_generators','tests/suites/source_drift/generators.py')
    tree=repository_tree.Tree(ROOT)
    commands=tree.inventory(repository_tree.COMMAND_DOCUMENTS)
    prose=[p.relative_to(ROOT).as_posix() for p in machinery.scanned_documents(ROOT)]
    owners={};gens=[]
    for name in fixture_inputs.GENERATORS:
        gen=fixture_inputs.generator_module(name,ROOT)
        regions,whole=machinery.region_ownership(ROOT,name)
        gens.append(dict(name=name,inputs=fixture_inputs.generator_inputs(ROOT,name),
                         regions=regions,whole=sorted(whole),span_documents=list(getattr(gen,'SPAN_DOCUMENTS',()))))
        for path,markers in regions.items():
            owners.setdefault(path,[]).append(dict(generator=name,kind='regions',markers=markers))
        for path in whole:
            owners.setdefault(path,[]).append(dict(generator=name,kind='whole-file'))
        for path in getattr(gen,'SPAN_DOCUMENTS',()):
            matches=generator_common.authored_spans(historical(path).decode(),path)
            names=[m[1] for m in matches if m[1].startswith(name+'.')]
            if names: owners.setdefault(path,[]).append(dict(generator=name,kind='spans',names=names))
    # Use historical bytes for the mutable associated plan's link scope; all
    # other source documents are unchanged by this investigation.
    link_inputs=set(prose)
    for path in prose:
        for link in markdown_reader.parse(historical(path).decode(),path).links:
            target=link.target.split('#')[0]
            if target and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):
                link_inputs.add((ROOT/path).parent.joinpath(target).resolve().relative_to(ROOT.resolve()).as_posix())
    documents=[]
    for path in sorted(set(commands)|set(prose)|{p for p in owners if p.endswith('.md')}):
        raw=historical(path)
        alias=(ROOT/path).is_symlink()
        documents.append(dict(path=path,source_sha256=hashlib.sha256(raw).hexdigest(),
                              alias=raw.decode().strip() if alias else None,
                              command_scan=path in commands,prose_scan=path in prose,
                              owned=owners.get(path,[]),role='transient plan' if path.endswith('-PLAN.md') else 'guidance alias' if alias else 'account or guidance'))
    result=dict(source=SOURCE,working_plan_delta='D2 plan edits excluded from historical link input extraction',
                command_documents=commands,prose_documents=prose,prose_link_inputs=sorted(link_inputs),
                generators=gens,outputs=owners,documents=documents,
                generated_guide=dict(source='docs/PolicyWitness.md',destination='${DIST_DIR}/PolicyWitness.md',
                                     operation='generate_limits.py --stage-guide; validate current then copy checked bytes'),
                architecture_graphs=[dict(id=g['id'],document=g.get('document',m['document'])) for m in [json.loads(historical('docs/architecture.json'))] for g in m['graphs']])
    (OUT/'ownership-facts.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(command_documents=len(commands),prose_documents=len(prose),owned_paths=len(owners),
                          graph_count=len(result['architecture_graphs']))))


if __name__=='__main__':main()
