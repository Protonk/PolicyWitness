"""Deterministic confirmed-reap controls against disposable Swift host sources.

The fixture publishes no acknowledgement until the host is inside its native
wait, after the last publication samples. It then exits cleanly or by SIGTERM.
Removing final reconciliation must fail both positive ownership assertions,
while an acknowledgement after a poll ownership fault must remain unqualified.
This compiles an ABI fixture and a test host, never the inspected signed app.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests/lib"))
from build_receipt import record_build

SWIFT = ['/usr/bin/xcrun', 'swift']
scratch = Path(sys.argv[2]).resolve()
OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(parents=True)
commands = []


def run(label, argv, *, env=None, timeout=180):
    args = [str(value) for value in argv]
    commands.append(dict(label=label, argv=args))
    (OUT / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    with (OUT / (label + ".log")).open("w") as log:
        result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                env=env, timeout=timeout)
    return result.returncode, (OUT / (label + ".log")).read_text()


package = OUT / "runner"
shutil.copytree(ROOT / "runner/Sources", package / "Sources")
shutil.copy2(ROOT / "runner/Package.swift", package / "Package.swift")
tests = package / "Tests/PWRunnerCoreTests"
tests.mkdir(parents=True)
for name in ("CWorkerLifecycleTests.swift", "TestKit.swift"):
    shutil.copy2(ROOT / "runner/Tests/PWRunnerCoreTests" / name, tests / name)
(tests / "main.swift").write_text(
    "import Foundation\nlet tk = TestKit()\nrunCWorkerReapedAcknowledgementControls(tk)\n"
    "print(tk.summary())\nexit(tk.exitCode())\n")

# Retain exactly the fixture and headers used by this compile. The relative
# diagnostic include keeps the same layout as the owning fixture directory.
native = OUT / "native"
native.mkdir()
for header in (ROOT / "controller/tools/pw_probe_runner").glob("*.h"):
    shutil.copy2(header, native / header.name)
fixture_source = OUT / "fixtures/worker_lifecycle/worker.c"
fixture_source.parent.mkdir(parents=True)
shutil.copy2(ROOT / "tests/fixtures/worker_lifecycle/worker.c", fixture_source)
diagnostic = OUT / "fixtures/diagnostic_transport"
diagnostic.mkdir()
shutil.copy2(ROOT / "tests/fixtures/diagnostic_transport/worker.h", diagnostic / "worker.h")
snapshot = {str(path.relative_to(OUT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(OUT.rglob("*")) if path.is_file()}
(OUT / "source-sha256.json").write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
fixture = OUT / "lifecycle-fixture"
rc, log = run("fixture-build", ["/usr/bin/xcrun", "--sdk", "macosx", "clang", "-std=c11",
                              "-Wall", "-Wextra", "-Werror", "-O2", "-I", native,
                              fixture_source, "-lsandbox", "-o", fixture])
assert rc == 0, log
# First-exec evaluation is equipment setup, outside the bounded race control.
rc, log = run("fixture-warm", [fixture], timeout=30)
assert rc == 90, ("fixture must refuse absent shared descriptor", rc, log)

source = package / "Sources/PWRunnerCore/CWorker.swift"
fixed = source.read_text()
anchor = "    if process.status != nil { observeAcknowledgement() }\n"
assert fixed.count(anchor) == 1, "reconciliation anchor changed; review mutation"
environment = dict(os.environ, PW_LIFECYCLE_WORKER_FIXTURE=str(fixture))
results = []
try:
    for variant in ("fixed", "missing_final_reconciliation"):
        mutated = variant != "fixed"
        body = fixed.replace(anchor, "", 1) if mutated else fixed
        source.write_text(body)
        (OUT / (variant + ".swift")).write_text(body)
        rc, log = run(variant, [*SWIFT, "run", "--package-path", package, "--scratch-path", scratch,
                               "PWRunnerCoreTests"], env=environment)
        failures = [line.strip() for line in log.splitlines() if line.strip().startswith("FAIL ")]
        successes = [line.strip() for line in log.splitlines() if line.strip().startswith("ok ")]
        prefix = "unseen acknowledgement at confirmed reap: "
        if mutated:
            assert rc == 1 and "1/3 tests passed" in log, log
            assert len(failures) == 2, log
            for scenario in ("clean", "signal"):
                assert any(prefix + scenario + ": expected true, got false" in line
                           and "confirmed reap must recover unseen acknowledgement" in line
                           for line in failures), log
            assert successes == ["ok   " + prefix + "ownership_lost"], log
        else:
            assert rc == 0 and "3/3 tests passed" in log and not failures, log
        results.append(dict(variant=variant, exit_code=rc, expected_rejections=failures,
                            passed=successes, source_sha256=hashlib.sha256(body.encode()).hexdigest()))
        (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
finally:
    source.write_text(fixed)
print(json.dumps(results, indent=2))
record_build(package, OUT, scratch, "PWRunnerCoreTests", swift_command=SWIFT)
