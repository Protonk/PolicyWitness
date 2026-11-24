"""Keep a read-only local copy of one terminal, owned run and the tested build."""
from pathlib import Path
import hashlib,json,subprocess as sp,sys
base=Path(__file__).resolve().parents[1]
label=sys.argv[1];assert label in ('original','mutant','clean-mutant')
name='four-findings-'+label+'-equipped'
src=Path('/private/tmp/pw-findings-b7113f57-'+label)/'tests/out/runs'/name
run=(src/'run.json').read_bytes()
owner=json.loads((src/'owner.json').read_bytes())
assert json.loads(run)['terminal'] and json.loads(run)['run_id']==owner['run_id']
archives=base/'mutation/local-archives'
archive=archives/(name+'.tar.gz')
partial=archive.with_suffix('.partial')
with (archives/(name+'.stderr')).open('wb') as se:
    sp.run(['/usr/bin/tar','-czf',partial,'-C',src.parent,name],stderr=se,check=True)
    assert sp.check_output(['/usr/bin/tar','-xOzf',partial,name+'/run.json'],stderr=se)==run
partial.replace(archive)
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
bundle=archives/(label+'.zip')
live_build=json.loads((base/'provenance'/label/'current-bytes.json').read_bytes())
assert sha(bundle)==live_build['zip_sha256']
receipt=dict(run_id=owner['run_id'],source=str(src),run_summary_sha256=hashlib.sha256(run).hexdigest(),
             archive=archive.name,size=archive.stat().st_size,sha256=sha(archive),
             build_zip=bundle.name,build_zip_sha256=sha(bundle))
(archives/(label+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
