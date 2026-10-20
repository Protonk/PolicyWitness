"""TestKit's sleep record against substituted clock readings in a disposable package."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "tests/lib"))
from build_receipt import record_build

SWIFT = ['swift']
scratch = Path(sys.argv[2]).resolve()
out = Path(sys.argv[1]); out.mkdir(parents=True)
package = out/'package'
sources = package/'Sources/SleepRecordControls'; sources.mkdir(parents=True)
shutil.copyfile(root/'runner/Tests/PWRunnerCoreTests/TestKit.swift', sources/'TestKit.swift')
(package/'Package.swift').write_text(
    '// swift-tools-version: 5.10\nimport PackageDescription\n'
    'let package = Package(name: "SleepRecordControls", platforms: [.macOS(.v13)],\n'
    '    targets: [.executableTarget(name: "SleepRecordControls")])\n')
# Each case consumes a start and an end reading: (continuous, uptime) in ns.
# The last case reads the real clocks.
(sources/'main.swift').write_text('''import Foundation
let tk = TestKit()
let real = tk.sleepClocks
var readings: [(continuous: UInt64, uptime: UInt64)] = [
    (0, 0), (5_000_000, 5_000_000),                // awake pass
    (0, 0), (2_000_005_000, 5_000),                // slept pass
    (0, 0), (2_000_005_000, 5_000),                // slept fail
    (0, 0), (5_000, 5_000),                        // awake fail
    (0, 0), (1_000_999_999, 1_000_000_000),        // sub-millisecond gap
    (10, 1_000), (10, 1_000_000),                  // uptime ahead: read skew, no line
]
tk.sleepClocks = { readings.removeFirst() }
tk.run("awake pass") {}
tk.run("slept pass") {}
tk.run("slept fail") { throw TestFailure(message: "constructed") }
tk.run("awake fail") { throw TestFailure(message: "constructed") }
tk.run("sub-millisecond gap") {}
tk.run("uptime ahead") {}
tk.sleepClocks = real
tk.run("real clocks") { usleep(20_000) }
if let slept = tk.sleepSummary() {
    FileHandle.standardOutput.write(Data("\\n\\(slept)\\n".utf8))
}
FileHandle.standardOutput.write(Data("\\n\\(tk.summary())\\n".utf8))
exit(tk.exitCode())
''')
with (out/'run.log').open('w') as log:
    run = subprocess.run([*SWIFT, 'run', '--package-path', str(package), '--scratch-path', str(scratch), 'SleepRecordControls'],
                         stdout=subprocess.PIPE, stderr=log, timeout=300)
stdout = run.stdout.decode()
(out/'stdout.txt').write_text(stdout)
lines = [line for line in stdout.splitlines() if line.strip()]
expected = [
    '  ok   awake pass',
    '  ok   slept pass',
    '       system slept 2000 ms during this case',
    '  FAIL slept fail: constructed',
    '       system slept 2000 ms during this case',
    '  FAIL awake fail: constructed',
    '  ok   sub-millisecond gap',
    '  ok   uptime ahead',
    '  ok   real clocks',
    '1 of 2 failures overlapped system sleep',
    '5/7 tests passed',
]
assert run.returncode == 1, (run.returncode, stdout)
assert lines == expected, stdout
# The readers of the core log keep their meaning: the wrapper's internal
# failure pattern, its sleep-count and summary patterns, and the mutation
# controls' exact ok lines and SKIP refusal.
failure_lines = [line for line in lines if re.match(r'^\s*(SKIP|FAIL)\s', line)]
assert failure_lines == ['  FAIL slept fail: constructed', '  FAIL awake fail: constructed'], failure_lines
assert [line for line in lines if re.fullmatch(r'[0-9]+ of [0-9]+ failures overlapped system sleep', line)] == [expected[-2]]
assert [line for line in lines if re.fullmatch(r'[0-9]+/[0-9]+ tests passed', line)] == [expected[-1]]
assert [line.strip() for line in lines if line.strip().startswith('ok ')] == [
    'ok   awake pass', 'ok   slept pass', 'ok   sub-millisecond gap', 'ok   uptime ahead', 'ok   real clocks']
assert 'SKIP' not in stdout
(out/'results.json').write_text(json.dumps({'exit_code': run.returncode, 'lines': lines}, indent=2) + '\n')
record_build(package, out, scratch, "SleepRecordControls", swift_command=SWIFT)
