from pathlib import Path
import hashlib,shutil,subprocess as sp,json,datetime,sys
base=Path(__file__).resolve().parents[1]
root=base.parents[1]; out=base/'provenance'
def cap(cmd):
    p=sp.run(cmd,capture_output=True,text=True,timeout=30)
    return dict(argv=list(map(str,cmd)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
def save(p,v): p.write_text(json.dumps(v,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
facts=[cap(x) for x in [['sw_vers'],['uname','-m'],['git','rev-parse','HEAD'],['git','log','-1','--format=%H %aI %s'],['git','worktree','list'],['xcrun','--show-sdk-version']]]
if not sys.argv[1:]: save(out/'host.json',dict(at_utc=datetime.datetime.now(datetime.UTC).isoformat(),commands=facts,
                          installed_search={str(p):p.exists() for p in [Path('/Applications/PolicyWitness.app'),Path.home()/'Applications/PolicyWitness.app']},
                          path_lookup=shutil.which('policy-witness')))
for name,src in [('shipped',root),('original',Path('/private/tmp/pw-findings-b7113f57-original')),('mutant',Path('/private/tmp/pw-findings-b7113f57-mutant')),('clean-mutant',Path('/private/tmp/pw-findings-b7113f57-clean-mutant'))]:
    if sys.argv[1:] and name not in sys.argv[1:]:continue
    d=out/name;d.mkdir(exist_ok=True);app=src/'dist/PolicyWitness.app'
    service=app/'Contents/XPCServices/PWRunner.xpc'; tools=service/'Contents/MacOS'
    controller=app/'Contents/MacOS/policy-witness'
    for p in (app/'Contents/Resources/Evidence').glob('*.json'):shutil.copyfile(p,d/p.name)
    shutil.copyfile(service/'Contents/Resources/worker-equipment.json',d/'worker-equipment.json')
    bins=[controller,app/'Contents/MacOS/pw-runner-client',tools/'PWRunner',tools/'pw-probe-runner',tools/'pw-probe-runner-unentitled',tools/'sb_api_validator']
    save(d/'current-bytes.json',dict(app=str(app),executable_sha256={str(b.relative_to(app)):digest(b) for b in bins},zip_sha256=digest(src/'dist/PolicyWitness.zip'),guide_sha256=digest(src/'dist/PolicyWitness.md'),
                                     worker=cap([tools/'pw-probe-runner','--version']),controller=cap([controller,'--version']),
                                     codesign_display=cap(['codesign','-dvvv',app]),verify=cap(['codesign','--verify','--deep','--strict','--verbose=2',app])))
h=root/'tests/suites/witness_contract/harness'
save(out/'calibration-tools.json',{str(p.relative_to(root)) if p.is_relative_to(root) else str(p):digest(p) for p in [h/'verify_filter_id.sh',h/'enforcement_probe.c',h/'enforcement_probe',Path('/opt/homebrew/opt/python@3.14/bin/python3.14')]})
archive=root/'dist/archive/v0.3.8/PolicyWitness-0.3.8.zip'
save(out/'archive.json',dict(path=str(archive),sha256=digest(archive),recorded=(archive.parent/'SHA256SUMS').read_text()))
