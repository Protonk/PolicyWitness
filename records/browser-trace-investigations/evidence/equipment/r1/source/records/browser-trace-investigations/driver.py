#!/usr/bin/env python3
"""Locked, durable driver for the bounded browser-trace native pilot.

All commands run through tests/lib/checkout_lock.sh -- /bin/sh .../run.sh.
The driver does not interpret extension outcomes. Checkpoints record an explicit
review of retained evidence; native success is never a continuation condition.
"""
from __future__ import annotations

import argparse
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import resource
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EVIDENCE = HERE / "evidence"
STATE = EVIDENCE / "state.json"
NATIVE_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
ARRANGEMENTS = tuple(f"C{i}" for i in range(8))
sys.path.insert(0, str(ROOT / "tests/lib"))
import checkout_lock  # noqa: E402; the repository owns this lock implementation.


class Refusal(RuntimeError):
    pass


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def relative(path):
    return str(Path(path).relative_to(HERE))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)
    fsync_dir(path.parent)


def read(path):
    return json.loads(Path(path).read_text())


def load_state():
    if STATE.exists():
        return read(STATE)
    return {"schema_version": 1, "created_utc": utc(), "trials": [],
            "checkpoints": {}, "corrections": [], "troubleshooting_seconds": 0,
            "active_revision": None, "halted": None, "closed": False}


def valid_name(value):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}", value):
        raise Refusal(f"invalid record name: {value!r}")
    return value


def run_capture(argv, directory, name, pass_fds, *, env=None, timeout=180):
    """Record equipment/checker commands, never native token-bearing storage."""
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    record = {"command": [str(x) for x in argv], "cwd": str(ROOT),
              "started_utc": utc(), "timeout_seconds": timeout}
    save(directory / f"{name}.command.json", record)
    try:
        result = subprocess.run(argv, cwd=ROOT, env=env, pass_fds=pass_fds,
                                capture_output=True, timeout=timeout, check=False)
        stdout, stderr = result.stdout, result.stderr
        record.update(returncode=result.returncode, timed_out=False)
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        record.update(returncode=None, timed_out=True)
    record["elapsed_seconds"] = time.monotonic() - started
    for stream, data in (("stdout", stdout), ("stderr", stderr)):
        path = directory / f"{name}.{stream}.txt"
        with path.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        record[stream] = relative(path)
    save(directory / f"{name}.command.json", record)
    return record, stdout, stderr


def require_command(argv, directory, name, fds, **kwargs):
    record, stdout, stderr = run_capture(argv, directory, name, fds, **kwargs)
    if record["returncode"] != 0:
        raise Refusal(f"{name} failed; see {relative(directory / (name + '.command.json'))}")
    return record, stdout, stderr


def source_paths():
    local = [p for p in HERE.iterdir() if p.is_file() and
             (p.suffix in (".c", ".h", ".py", ".sh") or p.name == "NATIVE-PROTOCOL.md")]
    helpers = [ROOT / "BROWSER-TRACE-INVESTIGATIONS-PLAN.md"]
    helpers += [ROOT / "tests/lib" / name for name in
                ("checkout_lock.py", "checkout_lock.sh", "python.sh", "python_start.sh", "sdk_guard.sh")]
    return sorted(set(local + helpers))


def build(args, fds):
    revision = valid_name(args.revision)
    state = load_state()
    if state["closed"]:
        raise Refusal("pilot is closed")
    if pending_records(state):
        raise Refusal("unresolved trial cleanup prevents further apparatus builds")
    active_cycle = next((item for item in state["corrections"] if item.get("ended_utc") is None), None)
    troubleshooting = state["troubleshooting_seconds"] + (max(0, time.time() - active_cycle["started_unix"]) if active_cycle else 0)
    if troubleshooting >= 3600:
        raise Refusal("troubleshooting allowance is exhausted")
    if state["halted"] and not active_cycle:
        raise Refusal("start a documented correction cycle before rebuilding failed equipment")
    identity = os.environ.get("PW_BYOXPC_IDENTITY") or os.environ.get("IDENTITY")
    if not identity or not identity.startswith("Developer ID Application: "):
        raise Refusal("set PW_BYOXPC_IDENTITY or IDENTITY to an explicit Developer ID Application identity")
    old_identity = state.get("selected_identity")
    if old_identity and old_identity != identity:
        raise Refusal("changing the pilot signing context requires review")
    state["selected_identity"] = identity
    destination = EVIDENCE / "equipment" / revision
    product_dir = HERE / "local" / revision
    if destination.exists() or product_dir.exists():
        raise Refusal("apparatus revision already exists; preserve it and use a new revision")
    destination.mkdir(parents=True)
    product_dir.mkdir(parents=True)
    (product_dir / "tmp").mkdir()
    equipment = {"schema_version": 1, "revision": revision, "started_utc": utc(),
                 "status": "building", "selected_identity": identity,
                 "binary": str(product_dir / "pilot"), "binary_is_gitignored": True,
                 "source": {}, "commands": []}
    save(destination / "equipment.json", equipment)
    save(STATE, state)
    try:
        _, commit, _ = require_command(["/usr/bin/git", "rev-parse", "HEAD"], destination, "source-commit", fds)
        _, status, _ = require_command(["/usr/bin/git", "status", "--porcelain=v1", "--untracked-files=all"], destination, "source-status", fds)
        hashes = {}
        for source in source_paths():
            name = str(source.relative_to(ROOT))
            snapshot = destination / "source" / name
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, snapshot)
            hashes[name] = digest(snapshot)
        equipment["source"] = {"commit": commit.decode().strip(), "status": status.decode(), "hashes": hashes,
                               "snapshot_root": relative(destination / "source")}
        environment_names = ("PATH", "SDKROOT", "DEVELOPER_DIR", "CPATH", "LIBRARY_PATH", "MACOSX_DEPLOYMENT_TARGET")
        equipment["build_environment"] = {key: os.environ.get(key) for key in environment_names}
        build_env = dict(os.environ, TMPDIR=str(product_dir / "tmp"), CLANG_MODULE_CACHE_PATH=str(product_dir / "module-cache"))
        equipment["build_environment"].update(TMPDIR=build_env["TMPDIR"], CLANG_MODULE_CACHE_PATH=build_env["CLANG_MODULE_CACHE_PATH"])
        facts = (("os", ["/usr/bin/sw_vers"]), ("darwin", ["/usr/bin/uname", "-smr"]),
                 ("sdk", ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"]),
                 ("sdk-version", ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-version"]),
                 ("compiler", ["/usr/bin/xcrun", "--sdk", "macosx", "clang", "--version"]))
        for name, command in facts:
            result, _, _ = require_command(command, destination, name, fds, env=build_env)
            equipment["commands"].append(result)
        binary = Path(equipment["binary"])
        command = ["/usr/bin/xcrun", "--sdk", "macosx", "clang", "-Wall", "-Wextra", "-Werror", "-O2", "-g", "-std=c11",
                   "-fno-builtin-malloc", "-fno-builtin-free", "-mmacosx-version-min=26.0", str(HERE / "pilot.c"), "-lsandbox", "-o", str(binary)]
        result, _, _ = require_command(command, destination, "build", fds, env=build_env)
        equipment["commands"].append(result)
        commands = (("sign", ["/usr/bin/codesign", "--force", "--options", "runtime", "--timestamp", "-s", identity, str(binary)]),
                    ("verify", ["/usr/bin/codesign", "--verify", "--strict", "--verbose=4", str(binary)]),
                    ("signature", ["/usr/bin/codesign", "-dvvv", str(binary)]),
                    ("entitlements", ["/usr/bin/codesign", "-d", "--entitlements", ":-", str(binary)]),
                    ("linked-images", ["/usr/bin/otool", "-L", str(binary)]),
                    ("load-commands", ["/usr/bin/otool", "-l", str(binary)]))
        outputs = {}
        for name, command in commands:
            result, stdout, stderr = require_command(command, destination, name, fds)
            equipment["commands"].append(result)
            outputs[name] = (stdout, stderr)
        signature = b"\n".join(outputs["signature"]).decode("utf-8", "replace")
        if f"Authority={identity}" not in signature or not re.search(r"flags=.*\bruntime\b", signature):
            raise Refusal("signature read-back does not establish selected authority and runtime flag")
        entitlements_data = outputs["entitlements"][0].strip()
        if entitlements_data:
            try:
                entitlements = plistlib.loads(entitlements_data)
            except (ValueError, plistlib.InvalidFileException) as exc:
                raise Refusal("entitlement read-back is not an empty plist") from exc
            if entitlements != {}:
                raise Refusal("pilot binary has nonempty entitlements")
            equipment["entitlements"] = {"status": "empty", "value": {}}
        else:
            equipment["entitlements"] = {"status": "absent", "value": None}
        changed = [name for name, expected in hashes.items() if digest(ROOT / name) != expected]
        if changed:
            raise Refusal("sources changed during build: " + ", ".join(changed))
        equipment.update(status="ready", completed_utc=utc(), binary_sha256=digest(binary))
        state["active_revision"] = revision
        print(f"equipment ready: {revision}; {relative(destination / 'equipment.json')}")
    except (OSError, Refusal) as exc:
        equipment.update(status="failed", completed_utc=utc(), failure=str(exc))
        state["halted"] = {"reason": "equipment build failed", "equipment_ref": relative(destination / "equipment.json")}
        raise
    finally:
        save(destination / "equipment.json", equipment)
        save(STATE, state)


class BSDInfo(ctypes.Structure):
    # SDK sys/proc_info.h proc_bsdinfo, verified against the selected SDK source.
    _fields_ = [(name, ctypes.c_uint32) for name in
                ("flags", "status", "xstatus", "pid", "ppid", "uid", "gid", "ruid", "rgid", "svuid", "svgid", "rfu")]
    _fields_ += [("comm", ctypes.c_char * 16), ("name", ctypes.c_char * 32)]
    _fields_ += [(name, ctypes.c_uint32) for name in ("nfiles", "pgid", "pjobc", "tdev", "tpgid")]
    _fields_ += [("nice", ctypes.c_int32), ("start_sec", ctypes.c_uint64), ("start_usec", ctypes.c_uint64)]


def libproc():
    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    library.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    library.proc_pidinfo.restype = ctypes.c_int
    library.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    library.proc_pidpath.restype = ctypes.c_int
    library.proc_listpids.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int]
    library.proc_listpids.restype = ctypes.c_int
    return library


def process_identity(pid):
    info = BSDInfo()
    library = libproc()
    ctypes.set_errno(0)
    rc = library.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
    error = ctypes.get_errno()
    observation = {"pid": pid, "api": "proc_pidinfo/PROC_PIDTBSDINFO", "rc": rc, "errno": error}
    if rc != ctypes.sizeof(info) or info.pid != pid:
        return dict(observation, available=False, reason="process identity unavailable")
    buffer = ctypes.create_string_buffer(4096)
    ctypes.set_errno(0)
    path_rc = library.proc_pidpath(pid, buffer, len(buffer))
    path_errno = ctypes.get_errno()
    observation.update(available=True, ppid=info.ppid, pgid=info.pgid,
                       start_identity={"seconds": info.start_sec, "microseconds": info.start_usec},
                       uid=info.uid, gid=info.gid, ruid=info.ruid, rgid=info.rgid,
                       executable=buffer.value.decode("utf-8", "replace") if path_rc > 0 else None,
                       executable_rc=path_rc, executable_errno=path_errno)
    return observation


def group_observation(pgid):
    result = {"pgid": pgid, "observed_utc": utc(), "monotonic_ns": time.monotonic_ns()}
    try:
        os.killpg(pgid, 0)
        result.update(kill_zero_rc=0, kill_zero_errno=0, absent=False)
    except ProcessLookupError as exc:
        result.update(kill_zero_rc=-1, kill_zero_errno=exc.errno, absent=True)
    except OSError as exc:
        result.update(kill_zero_rc=-1, kill_zero_errno=exc.errno, absent=None, reason="group inspection failed")
    library = libproc()
    members = (ctypes.c_int * 4096)()
    ctypes.set_errno(0)
    rc = library.proc_listpids(2, pgid, members, ctypes.sizeof(members))
    result.update(list_rc=rc, list_errno=ctypes.get_errno(), list_complete=0 <= rc < ctypes.sizeof(members) and rc % 4 == 0)
    result["members"] = [int(members[i]) for i in range(max(0, min(rc // 4, 4096))) if members[i] > 0]
    if result["absent"] is True and (not result["list_complete"] or result["members"]):
        result.update(absent=None, reason="group inspection observations are inconsistent or incomplete")
    return result


def signal_owned_group(record, record_path, pgid):
    """Revalidate live start identities before signaling, including after exit.

    A PID or group number from a former launch is insufficient. Unknown or
    changed membership leaves cleanup pending; it never licenses termination.
    """
    cleanup = record["driver"]["cleanup"]
    observation = {"pgid": pgid, "signal": int(signal.SIGKILL), "utc": utc(),
                   "ownership_verified": False, "process_observations": []}
    group = group_observation(pgid)
    observation["group_before"] = group
    known = {}
    supervisor = record["driver"]["ownership"].get("supervisor")
    if supervisor and supervisor.get("start_identity"):
        known[supervisor["pid"]] = supervisor
    for event in record["events"]:
        details = event.get("details", {})
        if event.get("role") == "supervisor" and event.get("stage") in ("supervisor_start", "child_launch"):
            process = details.get("process", {})
            if process.get("pid") and process.get("start_identity"):
                known[process["pid"]] = process
    reason = None
    if group["absent"] is True:
        reason = "owned group already absent"
    elif not group["list_complete"] or not group["members"]:
        reason = "group membership could not be enumerated completely"
    else:
        for pid in group["members"]:
            actual = process_identity(pid)
            expected = known.get(pid)
            expected_path = (expected.get("executable") or expected.get("executable_path") or expected.get("launched_executable")) if expected else None
            matches = bool(expected and actual.get("available") and actual.get("pgid") == pgid
                           and actual.get("start_identity") == expected.get("start_identity")
                           and actual.get("executable") == expected_path
                           and actual.get("uid") == expected.get("euid", expected.get("uid")))
            observation["process_observations"].append({"actual": actual, "matches_retained_identity": matches})
            if not matches:
                reason = "live group member lacks matching retained start, executable or credential identity"
    observation["ownership_verified"] = reason is None
    observation["reason"] = reason
    cleanup["signals"].append(observation)
    save(record_path, record)  # Persist the ownership observations before action.
    if reason is not None:
        observation.update(status="omitted", rc=None, errno=None)
        save(record_path, record)
        return
    try:
        os.killpg(pgid, signal.SIGKILL)
        observation.update(status="attempted", rc=0, errno=0)
    except OSError as exc:
        observation.update(status="attempted", rc=-1, errno=exc.errno)
    save(record_path, record)


def path_identity(info):
    return {"device": info.st_dev, "inode": info.st_ino, "uid": info.st_uid,
            "gid": info.st_gid, "mode": info.st_mode, "size": info.st_size}


def same_object(actual, expected):
    return all(actual.get(key) == expected.get(key) for key in ("device", "inode", "uid", "mode"))


def retain_native_cleanup(record):
    """Keep named native resources when their owner could not remove them.

    The driver owns A/B and the temporary directory, not arbitrary shared-memory
    names. A native pending publication therefore prevents path cleanup and
    subsequent launches, while preserving the exact ownership observation.
    """
    pending = []
    for event in record["events"]:
        details = event.get("details")
        if isinstance(details, dict) and details.get("cleanup_pending") is True:
            pending.append({"seq": event.get("seq"), "role": event.get("role"),
                            "pid": event.get("pid"), "stage": event.get("stage"), "details": details})
    cleanup = record["driver"]["cleanup"]
    cleanup["native_cleanup_pending"] = bool(pending)
    cleanup["native_pending_resources"] = pending
    if pending:
        cleanup.update(pending=True, resource_reason="native resource cleanup is pending; owned paths retained for review")
    return bool(pending)


def remove_owned_resources(record):
    """No recursive cleanup: only the recorded directory, receipt and A/B."""
    if retain_native_cleanup(record):
        return
    cleanup = record["driver"]["cleanup"]
    ownership = record["driver"]["ownership"]
    directory = ownership["temporary_directory"]
    observations = cleanup.setdefault("resource_observations", [])
    fd = None
    try:
        fd = os.open(directory["path"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        actual = path_identity(os.fstat(fd))
        if not same_object(actual, directory):
            raise Refusal("trial directory identity changed")
        receipt_fd = os.open(".owner.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        with os.fdopen(receipt_fd, "r") as receipt_file:
            receipt = json.load(receipt_file)
        if receipt.get("nonce") != ownership["nonce"] or receipt.get("trial_id") != record["trial"]["id"]:
            raise Refusal("trial directory ownership receipt changed")
        expected = {}
        for event in record["events"]:
            if event.get("role") == "supervisor" and event.get("stage") == "targets_prepared":
                for key, name in (("a", "A"), ("b", "B")):
                    target = event.get("details", {}).get(key, {})
                    if target.get("identity"):
                        expected[name] = target["identity"]
        entries = os.listdir(fd)
        if set(entries) - {"A", "B", ".owner.json"}:
            raise Refusal("unexpected entry in owned trial directory; retained for inspection")
        for name in ("A", "B"):
            if name not in entries:
                observations.append({"name": name, "absent": True})
                continue
            actual = path_identity(os.stat(name, dir_fd=fd, follow_symlinks=False))
            observations.append({"name": name, "identity": actual})
            if not stat.S_ISREG(actual["mode"]) or name not in expected or not same_object(actual, expected[name]):
                raise Refusal(f"{name} lacks matching retained target identity; retained for inspection")
        for name in ("A", "B", ".owner.json"):
            if name in entries:
                os.unlink(name, dir_fd=fd)
                observations.append({"name": name, "unlink_rc": 0})
        os.close(fd)
        fd = None
        # Revalidate immediately before removing the empty, owned directory.
        if not same_object(path_identity(os.lstat(directory["path"])), directory):
            raise Refusal("trial directory identity changed before rmdir")
        os.rmdir(directory["path"])
        observations.append({"path": directory["path"], "rmdir_rc": 0})
        cleanup.update(resources_removed=True, pending=False, resource_reason=None)
    except (OSError, ValueError, Refusal) as exc:
        cleanup.update(resources_removed=False, pending=True, resource_reason=str(exc))
    finally:
        if fd is not None:
            os.close(fd)


def equipment_for(revision):
    equipment_path = EVIDENCE / "equipment" / valid_name(revision) / "equipment.json"
    equipment = read(equipment_path)
    if equipment.get("status") != "ready":
        raise Refusal("selected apparatus equipment is not ready")
    binary = Path(equipment["binary"])
    if digest(binary) != equipment["binary_sha256"]:
        raise Refusal("signed pilot binary differs from its equipment record")
    for name, expected in equipment["source"]["hashes"].items():
        if digest(ROOT / name) != expected:
            raise Refusal(f"source differs from apparatus revision: {name}; build a new revision")
    return equipment_path, equipment, binary


def one_trial(metadata, binary, fds):
    trial_dir = EVIDENCE / "trials" / metadata["id"]
    trial_dir.mkdir(parents=True, exist_ok=False)
    temporary = tempfile.mkdtemp(prefix="pw-browser-trace-", dir="/private/tmp")
    owner = {"nonce": uuid.uuid4().hex, "created_utc": utc(), "trial_id": metadata["id"],
             "temporary_directory": dict(path=temporary, **path_identity(os.lstat(temporary))),
             "driver": process_identity(os.getpid()), "supervisor": None}
    save(Path(temporary) / ".owner.json", {"nonce": owner["nonce"], "trial_id": metadata["id"]})
    save(trial_dir / "ownership.json", owner)
    command = [str(binary), "supervise", metadata["arrangement"], metadata["id"], temporary,
               ",".join(str(fd) for fd in fds)]
    record = {"schema_version": 1, "trial": metadata, "events": [], "driver": {
        "ownership": owner,
        "execution": {"command": command, "environment": NATIVE_ENV, "started_utc": utc(),
                      "outer_deadline_seconds": 30, "kill_grace_seconds": 5,
                      "returncode": None, "deadline_reached": False, "cancel_signal": None, "stream_errors": []},
        "cleanup": {"signals": [], "supervisor_reaped": False, "process_group_absent": None,
                    "group_observations": [], "resources_removed": False, "pending": True,
                    "native_cleanup_pending": False, "native_pending_resources": []}}}
    record_path = trial_dir / "trial.json"
    save(record_path, record)
    execution = record["driver"]["execution"]
    cleanup = record["driver"]["cleanup"]
    signals_received = []
    handlers = {}
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        handlers[signum] = signal.signal(signum, lambda number, frame: signals_received.append(number))
    process = None
    started = time.monotonic()
    pending = b""
    try:
        with (trial_dir / "native-events.jsonl").open("xb") as event_output, (trial_dir / "native-stderr.txt").open("xb") as diagnostic_output:
            started = time.monotonic()  # The outer allowance begins at launch.
            process = subprocess.Popen(command, cwd=ROOT, env=NATIVE_ENV, pass_fds=fds,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True)
            owner["supervisor"] = process_identity(process.pid)
            owner["supervisor"].update(owned_child_pid=process.pid, created_process_group=process.pid,
                                       launched_executable=str(binary))
            if not owner["supervisor"].get("available") or not owner["supervisor"].get("start_identity"):
                execution["stream_errors"].append("supervisor start identity was unavailable after launch")
            elif (owner["supervisor"].get("executable") != str(binary) or
                  owner["supervisor"].get("ppid") != os.getpid() or
                  owner["supervisor"].get("pgid") != process.pid):
                execution["stream_errors"].append("supervisor executable, parent or process group did not match its launch")
            save(trial_dir / "ownership.json", owner)
            save(record_path, record)
            selector = selectors.DefaultSelector()
            for stream, label in ((process.stdout, "events"), (process.stderr, "diagnostics")):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, label)
            total_bytes = 0
            kill_started = None
            final_exit_time = None
            while True:
                now = time.monotonic()
                if signals_received:
                    execution["cancel_signal"] = signals_received[0]
                if now - started >= 30:
                    execution["deadline_reached"] = True
                if (execution["deadline_reached"] or execution["cancel_signal"] or execution["stream_errors"]) and kill_started is None:
                    kill_started = now
                    signal_owned_group(record, record_path, process.pid)
                for key, _ in selector.select(0.025):
                    try:
                        data = os.read(key.fileobj.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    total_bytes += len(data)
                    if total_bytes > 16 * 1024 * 1024:
                        if "native output exceeded 16 MiB equipment bound" not in execution["stream_errors"]:
                            execution["stream_errors"].append("native output exceeded 16 MiB equipment bound")
                        continue
                    if key.data == "diagnostics":
                        diagnostic_output.write(data)
                        diagnostic_output.flush()
                        os.fsync(diagnostic_output.fileno())
                    else:
                        pending += data
                        while b"\n" in pending:
                            line, pending = pending.split(b"\n", 1)
                            event_output.write(line + b"\n")
                            event_output.flush()
                            os.fsync(event_output.fileno())
                            try:
                                event = json.loads(line)
                                if not isinstance(event, dict):
                                    raise ValueError("event is not an object")
                                record["events"].append(event)
                            except (ValueError, UnicodeError) as exc:
                                execution["stream_errors"].append(f"invalid NDJSON event: {exc}")
                        if len(pending) > 1024 * 1024:
                            execution["stream_errors"].append("native event exceeded 1 MiB equipment bound")
                            pending = b""
                        save(record_path, record)
                returncode = process.poll()
                if returncode is not None:
                    cleanup["supervisor_reaped"] = True
                    execution["returncode"] = returncode
                    if final_exit_time is None:
                        final_exit_time = time.monotonic()
                    observed = group_observation(process.pid)
                    if not cleanup["group_observations"] or cleanup["group_observations"][-1]["absent"] != observed["absent"]:
                        cleanup["group_observations"].append(observed)
                    cleanup["process_group_absent"] = observed["absent"]
                    if observed["absent"] is True and not selector.get_map():
                        break
                if kill_started is not None and time.monotonic() - kill_started >= 5:
                    break
                # A normal supervisor exit without group absence is an equipment
                # failure; apply the same bounded group cleanup, preserving facts.
                if final_exit_time is not None and time.monotonic() - final_exit_time >= 0.25 and kill_started is None:
                    execution["stream_errors"].append("supervisor exit did not establish process-group absence and closed streams")
            selector.close()
            process.stdout.close()
            process.stderr.close()
            if pending:
                event_output.write(pending)
                event_output.flush()
                os.fsync(event_output.fileno())
                execution["stream_errors"].append("unterminated native event at stream end")
            execution["elapsed_seconds"] = time.monotonic() - started
            execution["finished_utc"] = utc()
            observed = group_observation(process.pid)
            cleanup["group_observations"].append(observed)
            cleanup["process_group_absent"] = observed["absent"]
            save(record_path, record)  # Final native observations precede removal.
            if cleanup["supervisor_reaped"] and cleanup["process_group_absent"] is True:
                remove_owned_resources(record)
            else:
                cleanup.update(pending=True, resource_reason="process absence is unconfirmed; owned paths retained")
    except (OSError, ValueError, Refusal) as exc:
        execution["stream_errors"].append(f"driver operation failed: {exc}")
        execution["elapsed_seconds"] = time.monotonic() - started
        if process is None:
            cleanup.update(supervisor_reaped=True, process_group_absent=True)
            save(record_path, record)
            remove_owned_resources(record)
        else:
            # An unexpected driver failure obeys the same outer cleanup bound.
            # Keep any already-published stream tail before closing the pipes.
            cleanup_deadline = time.monotonic() + 5
            try:
                signal_owned_group(record, record_path, process.pid)
            except (OSError, ValueError) as signal_error:
                execution["stream_errors"].append(f"owned group termination unavailable: {signal_error}")
            try:
                stdout, stderr = process.communicate(timeout=max(0, cleanup_deadline - time.monotonic()))
                execution["returncode"] = process.returncode
                cleanup["supervisor_reaped"] = True
                tail = pending + (stdout or b"")
                if tail:
                    with (trial_dir / "native-events.jsonl").open("ab") as output:
                        output.write(tail)
                        output.flush()
                        os.fsync(output.fileno())
                    for line in tail.splitlines():
                        try:
                            event = json.loads(line)
                            if isinstance(event, dict):
                                record["events"].append(event)
                        except (ValueError, UnicodeError):
                            pass  # The earlier equipment fault and raw tail remain.
                if stderr:
                    with (trial_dir / "native-stderr.txt").open("ab") as output:
                        output.write(stderr)
                        output.flush()
                        os.fsync(output.fileno())
            except (OSError, ValueError, subprocess.TimeoutExpired) as drain_error:
                execution["stream_errors"].append(f"bounded cleanup collection failed: {drain_error}")
            while time.monotonic() < cleanup_deadline:
                try:
                    observed = group_observation(process.pid)
                    cleanup["group_observations"].append(observed)
                    cleanup["process_group_absent"] = observed["absent"]
                    if observed["absent"] is True:
                        break
                except OSError as inspection_error:
                    cleanup["resource_reason"] = f"group inspection unavailable: {inspection_error}"
                    break
                time.sleep(0.025)
            save(record_path, record)
            if cleanup["supervisor_reaped"] and cleanup["process_group_absent"] is True:
                remove_owned_resources(record)
            else:
                cleanup.update(pending=True, resource_reason="driver failed and process absence remains unconfirmed")
    finally:
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
        retain_native_cleanup(record)
        save(record_path, record)
        save(trial_dir / "ownership.json", owner)
    return record_path, record


def pending_records(state):
    return [entry["record"] for entry in state["trials"]
            if not (HERE / entry["record"]).exists() or read(HERE / entry["record"]).get("driver", {}).get("cleanup", {}).get("pending", True)]


def assert_can_launch(state, *, diagnostic=False):
    if state["closed"]:
        raise Refusal("pilot is closed")
    pending = pending_records(state)
    if pending:
        raise Refusal("unresolved cleanup or interrupted trial: " + ", ".join(pending))
    active = next((cycle for cycle in state["corrections"] if cycle.get("ended_utc") is None), None)
    elapsed = state["troubleshooting_seconds"]
    if active:
        elapsed += max(0, time.time() - active["started_unix"])
    if elapsed >= 3600:
        raise Refusal("60-minute cumulative troubleshooting allowance exhausted")
    if active and not diagnostic:
        raise Refusal("finish the documented correction cycle before planned execution")
    if state["halted"] and not (diagnostic and active):
        raise Refusal("equipment is halted: " + str(state["halted"]))


def schedule(args, fds):
    del fds
    sequence = args.sequence.split(",")
    if len(sequence) != 8 or set(sequence) != set(ARRANGEMENTS):
        raise Refusal("a block sequence must contain C0 through C7 exactly once")
    path = EVIDENCE / "schedules" / f"block-{args.block}.json"
    if path.exists():
        raise Refusal("block sequence was already chosen; it is immutable")
    for other in (EVIDENCE / "schedules").glob("block-*.json") if (EVIDENCE / "schedules").exists() else ():
        if read(other)["sequence"] == sequence:
            raise Refusal("block sequence must vary positions")
    save(path, {"schema_version": 1, "block": args.block, "chosen_utc": utc(), "sequence": sequence,
                "rationale": args.rationale, "chosen_before_execution": True})
    print(relative(path))


def required_checkpoint(state, block):
    if block > 1:
        name = f"block-{block - 1}-complete"
        if not state["checkpoints"].get(name, {}).get("functional"):
            return name
    rows = {entry["arrangement"] for entry in state["trials"] if entry.get("block") == 1 and not entry.get("diagnostic")}
    if {"C0", "C1"} <= rows and not state["checkpoints"].get("block-1-initial", {}).get("functional"):
        return "block-1-initial"
    return None


def run_block(args, fds):
    state = load_state()
    assert_can_launch(state)
    schedule_path = EVIDENCE / "schedules" / f"block-{args.block}.json"
    chosen = read(schedule_path)
    equipment_path, _, binary = equipment_for(args.revision)
    for position, arrangement in enumerate(chosen["sequence"], 1):
        if any(entry.get("block") == args.block and entry.get("position") == position and not entry.get("diagnostic") for entry in state["trials"]):
            continue
        checkpoint_name = required_checkpoint(state, args.block)
        if checkpoint_name:
            print(f"checkpoint required: {checkpoint_name}")
            return
        if args.block > 1 and sum(entry.get("block") == args.block - 1 and not entry.get("diagnostic") for entry in state["trials"]) != 8:
            raise Refusal("preceding block has unrun positions")
        metadata = {"id": f"b{args.block}-p{position}-{arrangement}-{args.revision}", "arrangement": arrangement,
                    "block": args.block, "position": position, "chronological_position": len(state["trials"]) + 1,
                    "planned_position": (args.block - 1) * 8 + position,
                    "revision": args.revision, "equipment_ref": relative(equipment_path), "schedule_ref": relative(schedule_path),
                    "diagnostic": False, "original_trial_id": None, "correction_cycle": None}
        reservation = dict(metadata, record=f"evidence/trials/{metadata['id']}/trial.json", reserved_utc=utc(), execution_state="reserved")
        state["trials"].append(reservation)
        save(STATE, state)
        path, record = one_trial(metadata, binary, fds)
        reservation["execution_state"] = "executed" if record["driver"]["ownership"]["supervisor"] is not None else "unrun"
        failure = trial_equipment_failure(record)
        if failure:
            state["halted"] = {"reason": failure, "trial": metadata["id"]}
        save(STATE, state)
        print(f"retained {relative(path)}", flush=True)
        if failure:
            raise Refusal(failure)
    print(f"block {args.block} complete; checkpoint required: block-{args.block}-complete")


def trial_equipment_failure(record):
    execution, cleanup = record["driver"]["execution"], record["driver"]["cleanup"]
    if cleanup["pending"]:
        return "cleanup is pending"
    if execution["returncode"] != 0 or execution["stream_errors"] or execution["deadline_reached"] or execution["cancel_signal"]:
        return "native process or evidence collection failed"
    return None


def checkpoint(args, fds):
    del fds
    state = load_state()
    name = valid_name(args.name)
    expected_names = {"block-1-initial", "block-1-complete", "block-2-complete", "block-3-complete"}
    if name not in expected_names:
        raise Refusal("unknown checkpoint")
    relevant = [entry for entry in state["trials"] if not entry.get("diagnostic") and
                ((name == "block-1-initial" and entry.get("block") == 1 and entry["arrangement"] in ("C0", "C1")) or
                 (name != "block-1-initial" and entry.get("block") == int(name.split("-")[1])))]
    if len(relevant) != (2 if name == "block-1-initial" else 8):
        raise Refusal("checkpoint's planned positions have not all run")
    refs = []
    for supplied in args.evidence:
        path = Path(supplied).resolve()
        if not path.is_file() or not path.is_relative_to(HERE):
            raise Refusal("checkpoint evidence must be a retained investigation file")
        refs.append(relative(path))
    if args.functional == "yes" and pending_records(state):
        raise Refusal("cannot declare functional cleanup while ownership remains pending")
    checkpoint_dir = EVIDENCE / "checkpoints"
    count = len(list(checkpoint_dir.glob("*.json"))) if checkpoint_dir.exists() else 0
    path = checkpoint_dir / f"{count + 1:02d}-{name}.json"
    item = {"schema_version": 1, "name": name, "reviewed_utc": utc(), "functional": args.functional == "yes",
            "planned_trial_ids": [entry["id"] for entry in relevant], "evidence_refs": refs,
            "notes": args.notes, "previous_review": state["checkpoints"].get(name),
            "success_of_native_calls_required": False}
    save(path, item)
    state["checkpoints"][name] = {"functional": item["functional"], "record": relative(path)}
    if not item["functional"]:
        state["halted"] = {"reason": "checkpoint diagnosed equipment fault", "checkpoint": relative(path)}
    save(STATE, state)
    print(relative(path))


def correction_start(args, fds):
    del fds
    state = load_state()
    if any(item.get("ended_utc") is None for item in state["corrections"]):
        raise Refusal("a correction cycle is already active")
    if len(state["corrections"]) >= 2 or state["troubleshooting_seconds"] >= 3600:
        raise Refusal("troubleshooting allowance exhausted")
    if args.trial and not any(item["id"] == args.trial for item in state["trials"]):
        raise Refusal("original trial identity is unknown")
    cycle = {"number": len(state["corrections"]) + 1, "reason": args.reason,
             "original_trial_id": args.trial, "started_utc": utc(), "started_unix": time.time(),
             "started_monotonic_ns": time.monotonic_ns(), "ended_utc": None, "diagnostic_rerun": None}
    state["corrections"].append(cycle)
    state["halted"] = {"reason": "correction cycle active", "cycle": cycle["number"]}
    save(STATE, state)
    save(EVIDENCE / "corrections" / f"cycle-{cycle['number']}.json", cycle)
    print(f"correction cycle {cycle['number']} started")


def correction_end(args, fds):
    del fds
    state = load_state()
    active = [item for item in state["corrections"] if item.get("ended_utc") is None]
    if len(active) != 1:
        raise Refusal("no active correction cycle")
    cycle = active[0]
    elapsed = max(0, time.time() - cycle["started_unix"])
    cycle.update(ended_utc=utc(), elapsed_seconds=elapsed, result=args.result, notes=args.notes)
    state["troubleshooting_seconds"] += elapsed
    if args.result == "functional" and state["troubleshooting_seconds"] < 3600 and not pending_records(state):
        state["halted"] = None
    else:
        state["halted"] = {"reason": "correction did not restore equipment within allowance", "cycle": cycle["number"]}
    save(EVIDENCE / "corrections" / f"cycle-{cycle['number']}.json", cycle)
    save(STATE, state)
    print(f"correction cycle {cycle['number']} retained; cumulative seconds {state['troubleshooting_seconds']:.3f}")


def retry(args, fds):
    state = load_state()
    assert_can_launch(state, diagnostic=True)
    active = [item for item in state["corrections"] if item.get("ended_utc") is None]
    if len(active) != 1 or active[0].get("diagnostic_rerun"):
        raise Refusal("an active correction permits at most one diagnostic rerun")
    cycle = active[0]
    original = next((entry for entry in state["trials"] if entry["id"] == cycle["original_trial_id"]), None)
    if not original or original.get("diagnostic"):
        raise Refusal("diagnostic rerun requires the correction's original planned trial")
    equipment_path, _, binary = equipment_for(args.revision)
    metadata = {key: original[key] for key in ("arrangement", "schedule_ref")}
    metadata.update(id=f"diagnostic-{cycle['number']}-{original['id']}-{args.revision}", block=None, position=None,
                    chronological_position=len(state["trials"]) + 1, planned_position=None,
                    revision=args.revision, equipment_ref=relative(equipment_path),
                    diagnostic=True, original_trial_id=original["id"], correction_cycle=cycle["number"])
    cycle["diagnostic_rerun"] = metadata["id"]
    reservation = dict(metadata, record=f"evidence/trials/{metadata['id']}/trial.json", reserved_utc=utc(), execution_state="reserved")
    state["trials"].append(reservation)
    save(STATE, state)
    save(EVIDENCE / "corrections" / f"cycle-{cycle['number']}.json", cycle)
    path, record = one_trial(metadata, binary, fds)
    reservation["execution_state"] = "executed" if record["driver"]["ownership"]["supervisor"] is not None else "unrun"
    save(STATE, state)
    print(f"diagnostic retained: {relative(path)}")
    if trial_equipment_failure(record):
        raise Refusal("diagnostic rerun retained an equipment failure")


def check(args, fds):
    script = HERE / args.script
    if not script.is_file() or script.parent != HERE or script.suffix != ".py" or script.name == "driver.py":
        raise Refusal("checker must be an investigation-local Python script")
    name = valid_name(args.name)
    destination = EVIDENCE / "checks" / name
    if destination.exists():
        raise Refusal("checker command record already exists")
    command = [sys.executable, "-B", "-S", str(script)] + (args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments)
    result, stdout, _ = run_capture(command, destination, "check", fds)
    print(stdout.decode("utf-8", "replace"), end="")
    if result["returncode"] != 0:
        raise Refusal(f"checker returned {result['returncode']}; retained under {relative(destination)}")


def close(args, fds):
    del fds
    state = load_state()
    planned = [entry for entry in state["trials"] if not entry.get("diagnostic") and entry.get("execution_state") == "executed"]
    unrun = []
    for block in (1, 2, 3):
        chosen_path = EVIDENCE / "schedules" / f"block-{block}.json"
        chosen = read(chosen_path)["sequence"] if chosen_path.exists() else [None] * 8
        for position, arrangement in enumerate(chosen, 1):
            if not any(item["block"] == block and item["position"] == position for item in planned):
                unrun.append({"block": block, "position": position, "arrangement": arrangement})
    if args.status == "complete" and (unrun or pending_records(state)):
        raise Refusal("complete closeout requires all planned positions and resolved cleanup")
    state.update(closed=True, closed_utc=utc(), closeout_status=args.status, closeout_reason=args.reason, unrun_positions=unrun)
    save(STATE, state)
    print(f"{args.status}: {len(planned)} planned positions recorded; {len(unrun)} unrun")


def parser():
    result = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = result.add_subparsers(dest="command", required=True)
    command = commands.add_parser("build")
    command.add_argument("--revision", required=True)
    command.set_defaults(action=build)
    command = commands.add_parser("schedule")
    command.add_argument("--block", type=int, choices=(1, 2, 3), required=True)
    command.add_argument("--sequence", required=True)
    command.add_argument("--rationale", required=True)
    command.set_defaults(action=schedule)
    command = commands.add_parser("block")
    command.add_argument("--block", type=int, choices=(1, 2, 3), required=True)
    command.add_argument("--revision", required=True)
    command.set_defaults(action=run_block)
    command = commands.add_parser("checkpoint")
    command.add_argument("--name", required=True)
    command.add_argument("--functional", choices=("yes", "no"), required=True)
    command.add_argument("--evidence", action="append", required=True)
    command.add_argument("--notes", required=True)
    command.set_defaults(action=checkpoint)
    command = commands.add_parser("correction-start")
    command.add_argument("--trial")
    command.add_argument("--reason", required=True)
    command.set_defaults(action=correction_start)
    command = commands.add_parser("correction-end")
    command.add_argument("--result", choices=("functional", "failed"), required=True)
    command.add_argument("--notes", required=True)
    command.set_defaults(action=correction_end)
    command = commands.add_parser("retry")
    command.add_argument("--revision", required=True)
    command.set_defaults(action=retry)
    command = commands.add_parser("check")
    command.add_argument("--name", required=True)
    command.add_argument("--script", required=True)
    command.add_argument("arguments", nargs=argparse.REMAINDER)
    command.set_defaults(action=check)
    command = commands.add_parser("close")
    command.add_argument("--status", choices=("complete", "incomplete"), required=True)
    command.add_argument("--reason", required=True)
    command.set_defaults(action=close)
    return result


def main():
    args = parser().parse_args()
    if sys.flags.optimize:
        raise Refusal("Python assertions must remain enabled")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    admission = checkout_lock.admit(ROOT)
    try:
        fds = tuple(sorted(set(checkout_lock.inherited_fds()) | {admission.fd}))
        args.action(args, fds)
    finally:
        admission.close()


if __name__ == "__main__":
    try:
        main()
    except (Refusal, checkout_lock.Refusal, OSError, ValueError) as error:
        print(f"pilot driver: {error}", file=sys.stderr)
        sys.exit(2)
