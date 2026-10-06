"""Narrow reversions in a disposable source copy; never mutate the signed app."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1]); out.mkdir(parents=True)
package = out/'runner'
shutil.copytree(root/'runner/Sources', package/'Sources')
shutil.copyfile(root/'runner/Package.swift', package/'Package.swift')
tests = package/'Tests/PWRunnerCoreTests'; tests.mkdir(parents=True)
for name in ('ServiceAdmissionTests.swift','TestKit.swift'):
    shutil.copyfile(root/'runner/Tests/PWRunnerCoreTests'/name, tests/name)
(tests/'main.swift').write_text('import Foundation\nlet tk = TestKit()\nrunServiceAdmissionTests(tk)\nprint(tk.summary())\nexit(tk.exitCode())\n')
service=package/'Sources/PWRunnerCore/PWRunnerService.swift'
fixed=service.read_text()
mutations=[('fixed',None,None,None),
    ('per_connection','self.admission = admission','self.admission = PWRunnerAdmission()', 'expected 1, got 2'),
    ('refusal_exits','            reply(pwRunnerReplyData(resp))','            replyAndExit(resp)', 'refusal must not retire the active owner')]
results=[]
for name,anchor,replacement,reason in mutations:
    if anchor: assert fixed.count(anchor)==1, (name,'mutation anchor changed')
    text=fixed.replace(anchor,replacement) if anchor else fixed
    service.write_text(text); (out/(name+'.swift')).write_text(text)
    with (out/(name+'.log')).open('w') as log:
        run=subprocess.run(['swift','run','--package-path',str(package),'PWRunnerCoreTests'],stdout=log,stderr=log,timeout=120)
    log=(out/(name+'.log')).read_text()
    assert '[host single use admission]' in log and 'tests passed' in log, (name,'build/equipment failure')
    if reason:
        assert run.returncode!=0 and reason in log, (name,'original regression not detected',log)
    else: assert run.returncode==0 and '3/3 tests passed' in log, log
    results.append(dict(control=name,exit_code=run.returncode,expected_failure=reason))
service.write_text(fixed)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
