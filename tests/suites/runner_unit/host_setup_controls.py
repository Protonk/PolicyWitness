"""Characterize setup faults, not a claim that the host refuses every fault.

Copies production sources, renames selected native boundaries and compiles them
with test-only adapters. The adapters leave control flow intact. Real spawns
run an independent fd observer; invalid handles are contained by the adapter.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tests/fixtures/host_setup"


def identity(value):
    return tuple(value.get(k) for k in ("device", "inode", "mode"))


def check(receipt, owner, fault):
    assert receipt["owner"] == owner and receipt["fault"] == fault, "case identity"
    events = receipt["events"]
    calls = [e["call"] for e in events]
    injected = [e["point"] for e in events if e["call"] == "injected"]
    assert injected == ([] if fault in ("baseline", "collision") else [fault]), "injection not observed exactly once"
    assert receipt["fds_closed"] and receipt["maps_remaining"] == 0, "descriptor/mapping cleanup"
    assert receipt["strings_remaining"] == 0 and receipt["handles_remaining"] == 0, "allocation cleanup"
    names = receipt["names_present_before_fixture_cleanup"]
    assert bool(names) == (fault == "unlink"), "unlink observation"
    assert receipt["fixture_names_removed"], "fixture cleanup"
    guarded = fault == "nosigpipe" or (owner == "issuer" and fault in ("actions_init", "attrs_init", "dup2.3", "open.1", "flags"))
    if guarded:
        assert "spawn_reached" not in calls and receipt["spawn_pid"] == 0, "unexpected spawn dispatch"
        assert receipt["child"] is None, "unexpected child receipt"
        if fault == "actions_init":
            assert "nil_actions_use" in calls and "nil_actions_destroy" in calls, "missing invalid-handle use"
        if fault == "attrs_init":
            assert "nil_attrs_use" in calls and "nil_attrs_destroy" in calls, "missing invalid-handle use"
        return "no spawn; invalid-handle containment is fixture-owned" if fault.endswith("init") else "checked refusal, cleanup observed"
    assert calls.count("spawn_reached") == 1, "missing dispatch observation"
    if fault == "actions_init":
        assert "fixture_refused_invalid_handle" in calls and "nil_actions_use" in calls, "missing fixture containment"
        assert "native_spawn" not in calls and receipt["child"] is None and receipt["spawn_pid"] == 0, "invalid handle reached libc"
        return "host continued after failed init; fixture contained invalid handle"
    native = [e for e in events if e["call"] == "native_spawn"]
    assert len(native) == 1, "native spawn missing"
    if native[0]["rc"] != 0:
        assert fault == "strdup.0" and receipt["child"] is None and receipt["spawn_pid"] == 0, "unexpected native refusal"
        assert next(e for e in events if e["call"] == "spawn_reached")["argc"] == 0, "argv truncation missing"
        return "host dispatched empty argv; native spawn refused"
    child = receipt["child"]
    assert child and child["pid"] == receipt["spawn_pid"] == native[0]["pid"] and child["pid"] > 0, "child identity missing"
    assert receipt["host_reaped"], "host reap missing"
    expected_argc = (0 if fault == "strdup.0" else 2 if fault == "strdup.2" else 9 if owner == "worker_token" else 7 if owner == "worker" else 1)
    assert child["argc"] == expected_argc, "child argument count"
    actions = [e for e in events if e["call"] == "dup2"]
    observed = {e["fd"]: e for e in child["fds"]}
    mismatches = [a["destination"] for a in actions if observed[a["destination"]]["rc"] != 0 or identity(a["identity"]) != identity(observed[a["destination"]])]
    if fault == "collision":
        collisions = [(a["destination"], b["source"]) for i, a in enumerate(actions) for b in actions[i+1:]
                      if a["destination"] == b["source"] and a["source"] != b["source"]]
        if owner == "worker":
            assert collisions and 3 in mismatches, "actual overwrite collision and wrong child evidence fd required"
            return "source/destination collision observed; child evidence fd is wrong"
        assert not collisions and not mismatches, "issuer high duplicate did not protect channel"
        return "low descriptors exercised; issuer channel identity preserved"
    if fault.startswith("dup2."):
        assert int(fault.split(".")[1]) in mismatches, "failed action did not change child endpoint"
        return "child spawned despite failed action; endpoint mismatch observed"
    assert not mismatches, "unexpected endpoint mismatch"
    return "child observed; setup failure did not prevent spawn" if fault != "baseline" else "baseline endpoints observed"


def run(out):
    out.mkdir(parents=True)
    package = out / "runner"
    shutil.copytree(ROOT / "runner/Sources", package / "Sources")
    shutil.copyfile(ROOT / "runner/Package.swift", package / "Package.swift")
    shutil.copyfile(FIXTURE / "shim.c", package / "Sources/PWCWorkerShim/setup.c")
    shutil.copyfile(FIXTURE / "SetupControls.swift", package / "Sources/PWRunnerCore/SetupControls.swift")
    names = {"posix_spawn_file_actions_init": "setup_actions_init", "posix_spawn_file_actions_destroy": "setup_actions_destroy",
             "posix_spawn_file_actions_adddup2": "setup_dup2", "posix_spawn_file_actions_addopen": "setup_open",
             "posix_spawnattr_init": "setup_attrs_init", "posix_spawnattr_destroy": "setup_attrs_destroy",
             "posix_spawnattr_setflags": "setup_flags", "posix_spawn": "setup_spawn", "strdup": "setup_strdup",
             "free": "setup_free", "fcntl": "setup_fcntl", "pipe": "setup_pipe", "mmap": "setup_mmap",
             "munmap": "setup_munmap", "shm_unlink": "setup_unlink", "pw_cworker_shm_open_create": "setup_shm"}
    manifest = []
    expected = {
        "CWorker.swift": {"posix_spawn_file_actions_init": 1, "posix_spawn_file_actions_destroy": 1,
            "posix_spawn_file_actions_adddup2": 4, "posix_spawn": 1, "strdup": 1, "free": 1,
            "fcntl": 8, "pipe": 2, "mmap": 1, "munmap": 1, "shm_unlink": 1, "pw_cworker_shm_open_create": 1},
        "ExtensionIssuer.swift": {"posix_spawn_file_actions_init": 1, "posix_spawn_file_actions_destroy": 1,
            "posix_spawn_file_actions_adddup2": 1, "posix_spawn_file_actions_addopen": 1,
            "posix_spawnattr_init": 1, "posix_spawnattr_destroy": 1, "posix_spawnattr_setflags": 1,
            "posix_spawn": 1, "fcntl": 2, "mmap": 1, "munmap": 1, "shm_unlink": 1, "pw_cworker_shm_open_create": 1}}
    for filename, counts in expected.items():
        path = package / "Sources/PWRunnerCore" / filename
        original = path.read_text()
        # Only non-comment call lines; do not rename the @_silgen_name binding.
        lines = original.splitlines(keepends=True)
        for name, count in counts.items():
            found = 0
            for i, line in enumerate(lines):
                if line.lstrip().startswith(("//", "*", "/*", "func ")):
                    continue
                line, n = re.subn(r"(?<![\w])(?:Darwin\.)?" + name + r"\(", names[name] + "(", line)
                lines[i] = line; found += n
            assert found == count, (filename, name, found, count, "boundary changed; review instrumentation")
        path.write_text("".join(lines))
        manifest.append({"path": str(path.relative_to(out)), "source_sha256": hashlib.sha256(original.encode()).hexdigest(),
                         "instrumented_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "substitutions": counts})
    (out / "instrumentation.json").write_text(json.dumps(manifest, indent=2) + "\n")
    main = package / "Tests/PWRunnerCoreTests/main.swift"; main.parent.mkdir(parents=True)
    main.write_text('import Foundation\n@testable import PWRunnerCore\ntry runSetupControl(CommandLine.arguments[1], CommandLine.arguments[2], CommandLine.arguments[3], CommandLine.arguments[4])\n')
    observer = out / "observer"; child_path = out / "child.json"
    with (out / "build.log").open("w") as log:
        subprocess.run(["clang", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter", f'-DRECEIPT_PATH="{child_path}"', str(FIXTURE / "observer.c"), "-o", str(observer)], check=True, stdout=log, stderr=log)
        subprocess.run(["swift", "build", "--package-path", str(package), "--product", "PWRunnerCoreTests"], check=True, stdout=log, stderr=log, timeout=180)
    binary_dir = subprocess.check_output(["swift", "build", "--package-path", str(package), "--show-bin-path"], text=True).strip()
    executable = Path(binary_dir) / "PWRunnerCoreTests"
    cases = [("worker", f) for f in ("baseline", "collision", "actions_init", "dup2.0", "dup2.3", "dup2.4", "strdup.0", "strdup.2", "unlink", "clear_cloexec", "nosigpipe")]
    cases += [("worker_token", "baseline"), ("worker_token", "dup2.5")]
    cases += [("issuer", f) for f in ("baseline", "collision", "actions_init", "attrs_init", "dup2.3", "open.1", "flags", "strdup.0", "unlink")]
    results = []; receipts = {}
    for owner, fault in cases:
        name = f"{owner}-{fault}"; output = out / (name + ".json")
        child_path.unlink(missing_ok=True)
        with (out / (name + ".log")).open("w") as log:
            subprocess.run([str(executable), owner, fault, str(observer), str(output)], check=True, stdout=log, stderr=log, timeout=15)
        receipt = json.loads(output.read_text())
        receipt["child"] = json.loads(child_path.read_text()) if child_path.exists() else None
        output.write_text(json.dumps(receipt, indent=2) + "\n")
        verdict = check(receipt, owner, fault)
        results.append({"case": name, "observation": verdict}); receipts[name] = receipt
    # Checker rejection controls independently remove or contradict required
    # observations. These do not stand in for the native fault experiments.
    mutations = [
        ("worker-dup2.3", "missing injection", lambda r: r.update(events=[e for e in r["events"] if e["call"] != "injected"])),
        ("worker-baseline", "wrong child", lambda r: r["child"].update(pid=-1)),
        ("worker-baseline", "no reap", lambda r: r.update(host_reaped=False)),
        ("worker-nosigpipe", "unintended spawn", lambda r: r["events"].append({"call": "spawn_reached"})),
        ("worker-nosigpipe", "leaked descriptor", lambda r: r.update(fds_closed=False)),
        ("worker-baseline", "leaked mapping", lambda r: r.update(maps_remaining=1)),
        ("worker-baseline", "leaked strings", lambda r: r.update(strings_remaining=1)),
        ("worker-unlink", "name not cleaned", lambda r: r.update(fixture_names_removed=False)),
        ("worker-collision", "unestablished collision", lambda r: [e.update(source=100 + i) for i, e in enumerate(r["events"]) if e["call"] == "dup2"]),
        ("worker-collision", "missing child effect", lambda r: r.update(child=None)),
    ]
    for name, label, mutate in mutations:
        receipt = copy.deepcopy(receipts[name]); mutate(receipt)
        try:
            check(receipt, receipt["owner"], receipt["fault"])
        except AssertionError as error:
            results.append({"rejected_control": label, "reason": str(error)})
        else:
            raise AssertionError((label, "checker accepted counterexample"))
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"{len(cases)} setup observations; {len(mutations)} rejected checker controls")


if __name__ == "__main__":
    run(Path(sys.argv[1]).resolve())
