#!/usr/bin/env python3
"""Retain constructed reader controls or one deletion from an actual trial."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def run_reader(record, destination, label):
    command = [sys.executable, "-I", str(HERE / "read.py"), str(record.resolve())]
    result = subprocess.run(command, capture_output=True, timeout=30, close_fds=False)
    (destination / (label + ".stdout")).write_bytes(result.stdout)
    (destination / (label + ".stderr")).write_bytes(result.stderr)
    save(destination / (label + ".command.json"),
         {"argv": command, "returncode": result.returncode})
    try:
        value = json.loads(result.stdout)
    except (UnicodeError, json.JSONDecodeError):
        value = {"complete_evidence": False, "complete_delegation_sequence": False,
                 "errors": [{"code": "reader_output_invalid"}]}
    return value, result.returncode


def derived_control(source, out):
    source_bytes = source.read_bytes()
    original = json.loads(source_bytes)
    accepted, accepted_rc = run_reader(source, out, "original-reader")
    if accepted_rc or not accepted.get("complete_delegation_sequence"):
        save(out / "summary.json", {"kind": "actual_trial_derived_control", "ok": False,
             "reason": "original_not_accepted_as_complete_delegation", "source": str(source)})
        return False
    indexes = [i for i, event in enumerate(original["events"])
               if event.get("role") == "issuer" and event.get("stage") == "issue_result"]
    if len(indexes) != 1:
        save(out / "summary.json", {"kind": "actual_trial_derived_control", "ok": False,
             "reason": "issuance_publication_not_unique", "source": str(source)})
        return False
    index = indexes[0]
    changed = copy.deepcopy(original)
    del changed["events"][index]
    source_id = original["trial"]["id"]
    # Keep original trial metadata verbatim: control identity belongs to this
    # enclosing manifest and filename, not a second modification to the record.
    control_path = out / ("derived-from-" + source_id + "-missing-issuance.json")
    save(control_path, changed)
    readback, returncode = run_reader(control_path, out, "mutated-reader")
    unchanged = source.read_bytes() == source_bytes
    ok = unchanged and not readback.get("complete_delegation_sequence", True)
    save(out / "mutation.json", {
        "kind": "actual_trial_derived_control", "source_trial_id": source_id,
        "source": str(source.resolve()), "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "original_unchanged": unchanged, "control_record": control_path.name,
        "changes": [{"op": "remove", "path": "/events/" + str(index),
                     "role": "issuer", "stage": "issue_result", "original_seq": original["events"][index]["seq"]}],
        "change_count": 1,
        "preserved": ["all_other_events", "all_metadata", "all_driver_observations"],
        "reader_returncode": returncode,
        "complete_sequence_rejected": not readback.get("complete_delegation_sequence", True)})
    save(out / "summary.json", {"kind": "actual_trial_derived_control", "ok": ok,
         "source_trial_id": source_id, "input": control_path.name})
    return ok


def constructed_controls(out):
    reference = constructed_record()
    cases = [("complete_delegation", reference, True, True, None)]

    def add(name, mutate, complete=False, delegation=False, diagnostic=None):
        value = copy.deepcopy(reference)
        mutate(value)
        cases.append((name, value, complete, delegation, diagnostic))

    def event(value, role, stage):
        return next(e for e in value["events"] if e["role"] == role and e["stage"] == stage)

    def remove(value, role, stage):
        value["events"].remove(event(value, role, stage))

    def move_pair(value, role, stage, before_role, before_stage):
        events = value["events"]
        chosen = event(value, role, stage)
        pair = [chosen]
        if role != "supervisor":
            pair.append(next(e for e in events if e["stage"] == "publication_ack"
                             and e["details"]["child_role"] == role
                             and e["details"]["producer_seq"] == chosen["producer_seq"]))
        for selected in pair:
            events.remove(selected)
        insertion = events.index(event(value, before_role, before_stage))
        events[insertion:insertion] = pair
        normalize_publications(value)

    add("missing_application", lambda r: remove(r, "issuer", "apply"), diagnostic="stage_count")
    add("application_after_issuance", lambda r: move_pair(r, "issuer", "apply", "issuer", "token_publication"), diagnostic="stage_order")
    add("missing_issue_result", lambda r: remove(r, "issuer", "issue_result"), diagnostic="stage_count")
    add("missing_transfer_acceptance", lambda r: remove(r, "recipient", "transfer_acceptance"), diagnostic="stage_count")
    add("acceptance_before_transfer_ready", lambda r: move_pair(r, "recipient", "transfer_acceptance", "supervisor", "transfer_ready"), diagnostic="stage_order")
    add("missing_publication_ack", lambda r: remove(r, "supervisor", "publication_ack"), diagnostic="acknowledgement_count")
    add("different_issuer_pid", lambda r: event(r, "issuer", "issue_result").update(pid=9011), diagnostic="role_process_changed")
    add("wrong_query_target", lambda r: event(r, "supervisor", "query")["details"].update(target_pid=9002), diagnostic="query_arguments")
    add("malformed_status", lambda r: event(r, "issuer", "issue_result").update(status="success"), diagnostic="stage_status")

    def inherited(value):
        snapshot = event(value, "recipient", "fd_snapshot")
        target = event(value, "supervisor", "targets_prepared")["details"]["a"]
        snapshot["details"]["descriptors"].append({"fd": 19, "type": "regular", "stat_rc": 0,
            "stat_errno": 0, "identity": target["identity"], "matches_a": True, "matches_b": False})
    add("inherited_target_descriptor", inherited, diagnostic="target_descriptor_at_boundary")

    def retained(value):
        before = event(value, "recipient", "read_before")["details"]
        target = event(value, "supervisor", "targets_prepared")["details"]["a"]
        before.update(fresh_read(target, fd=6, success=True))
        before["close"] = {"status": "unavailable", "reason": "held_for_later_read"}
        snapshot = next(e for e in value["events"] if e["role"] == "recipient"
                        and e["stage"] == "fd_snapshot" and e["details"]["boundary"] == "before_read_after")
        snapshot["details"]["descriptors"].append({"fd": 6, "type": "regular", "stat_rc": 0,
            "stat_errno": 0, "identity": target["identity"], "matches_a": True, "matches_b": False})
    add("target_descriptor_held_across_reads", retained, diagnostic="target_descriptor_at_boundary")

    def reused(value):
        target = event(value, "supervisor", "targets_prepared")["details"]["a"]
        event(value, "recipient", "read_before")["details"] = fresh_read(target, fd=6, success=True)
        event(value, "recipient", "read_after")["details"] = fresh_read(target, fd=6, success=True)
    add("closed_descriptor_number_reused", reused, True, False)
    add("claimed_read_wrong_identity", lambda r: event(r, "recipient", "read_after")["details"]["identity"].update(inode=99999), diagnostic="unsupported_known_bytes_claim")
    add("claimed_read_wrong_bytes", lambda r: event(r, "recipient", "read_after")["details"].update(content_hex="58595a0a"), diagnostic="unsupported_known_bytes_claim")

    def honest_mismatch(value):
        detail = event(value, "recipient", "read_after")["details"]
        detail.pop("claimed_known_bytes")
        detail["content_hex"] = "58595a0a"
    add("honest_unexpected_read_bytes", honest_mismatch, True, False)

    def negative_queries(value):
        queries = [e for e in value["events"] if e["stage"] == "query"]
        queries[0]["details"].update(rc=-1, errno=22)
        queries[1]["details"].update(rc=1, errno=22)
    add("negative_and_unexpected_queries", negative_queries, True, True, "no_query_denials")

    def unavailable_queries(value):
        cap = event(value, "supervisor", "query_capability")["details"]
        cap.update(api={"available": False, "image": None}, flag={"available": False, "image": None}, no_report_flag=None)
        for query in [e for e in value["events"] if e["stage"] == "query"]:
            query["status"] = "unavailable"
            query["details"].update(reason="query_symbols_unavailable", rc=None, errno=None,
                                    no_report_flag=None, type_argument=None)
    add("unavailable_queries", unavailable_queries, True, True)

    def failed_consume(value):
        event(value, "recipient", "consume_result")["details"].update(rc=-1, errno=22)
        target = event(value, "supervisor", "targets_prepared")["details"]["a"]
        event(value, "recipient", "read_after")["details"] = fresh_read(target, success=False)
    add("honest_failed_consumption", failed_consume, True, False)

    def refused(value):
        event(value, "issuer", "issue_result")["details"].update(nonnull=False, errno=1)
        for role, stage in (("issuer", "raw_token_erasure"), ("issuer", "token_publication"),
                            ("supervisor", "transfer_ready"), ("recipient", "transfer_acceptance"),
                            ("supervisor", "transfer_equality"), ("recipient", "consume_begin"),
                            ("recipient", "consume_result")):
            item = event(value, role, stage)
            item["status"] = "unavailable"
            item["details"] = {"reason": "issuance_returned_null"}
        event(value, "supervisor", "consume_release")["details"].update(accepted=False, equality_confirmed=False)
        target = event(value, "supervisor", "targets_prepared")["details"]["a"]
        event(value, "recipient", "read_after")["details"] = fresh_read(target, success=False)
    add("honest_issuance_refusal_and_dependent_unavailability", refused, True, False)

    def omitted(value):
        value["trial"]["arrangement"] = "C6"
        event(value, "supervisor", "supervisor_start")["details"]["arrangement"] = "C6"
        for stage in ("consume_begin", "consume_result"):
            item = event(value, "recipient", stage)
            item["status"] = "omitted"
            item["details"] = {"reason": "C6_omits_consumption"}
        target = event(value, "supervisor", "targets_prepared")["details"]["a"]
        event(value, "recipient", "read_after")["details"] = fresh_read(target, success=False)
    add("omitted_consumption_with_second_read", omitted, True, False)

    def zero_consume(value):
        event(value, "recipient", "consume_result")["details"].update(rc=0, errno=0)
    add("zero_consume_candidate_handle", zero_consume, True, True)
    add("missing_second_read_after_failed_consume", lambda r: (failed_consume(r), remove(r, "recipient", "read_after")), diagnostic="stage_count")
    add("fabricated_unknown_cleanup", lambda r: r["driver"]["cleanup"].update(process_group_absent=False, pending=True), diagnostic="driver_cleanup_incomplete")

    def nonunique_shm_metadata(value):
        channels = event(value, "supervisor", "channel_setup")["details"]
        for key in ("evidence", "issued_token", "delivered_token"):
            channels[key]["identity"].update(device=0, inode=0)
        for item in value["events"]:
            if item["stage"] == "fd_snapshot" and item["details"].get("boundary") == "entry":
                for descriptor in item["details"]["descriptors"]:
                    if descriptor["fd"] in (3, 4):
                        descriptor["identity"].update(device=0, inode=0)
    add("distinct_shm_with_nonunique_stat_metadata", nonunique_shm_metadata, True, True)

    def repeated_channel_creation(value):
        creations = [e for e in value["events"] if e["stage"] == "channel_resource"]
        creations[1]["details"]["name"] = creations[0]["details"]["name"]
    add("repeated_channel_creation_identity", repeated_channel_creation, diagnostic="separate_channel_creations")

    results = []
    for name, value, complete, delegation, diagnostic in cases:
        path = out / ("constructed-" + name + ".json")
        save(path, value)
        result, returncode = run_reader(path, out, name)
        codes = {error.get("code") for error in result.get("errors", [])}
        observed = result.get("complete_evidence") is complete and result.get("complete_delegation_sequence") is delegation
        observed = observed and returncode == (0 if complete else 1)
        if diagnostic == "no_query_denials":
            observed = observed and result.get("query_counts", {}).get("deny") == 0
            observed = observed and result.get("query_counts", {}).get("error") == 1
            observed = observed and result.get("query_counts", {}).get("unclassified") == 1
        elif diagnostic:
            observed = observed and diagnostic in codes
        results.append({"name": name, "kind": "constructed_control", "input": path.name,
                        "expected_complete_evidence": complete, "expected_complete_delegation_sequence": delegation,
                        "expected_diagnostic": diagnostic, "ok": observed,
                        "observed_complete_evidence": result.get("complete_evidence"),
                        "observed_complete_delegation_sequence": result.get("complete_delegation_sequence"),
                        "reader_returncode": returncode})
    ok = all(result["ok"] for result in results)
    save(out / "summary.json", {"kind": "constructed_reader_controls", "ok": ok,
         "native_trials": 0, "controls": results,
         "limit": "Author-constructed records test interpretation; they do not establish native semantics or connection to actual trial publications."})
    return ok


def fresh_read(target, fd=6, success=True):
    def call(rc):
        return {"status": "attempted", "rc": rc, "errno": 0}
    if not success:
        return {"path": target["path"], "descriptor": None,
                "open": {"status": "attempted", "rc": -1, "errno": 1},
                "identity_check": {"status": "unavailable", "reason": "open_failed"},
                "read": {"status": "unavailable", "reason": "open_failed"},
                "close": {"status": "unavailable", "reason": "open_failed"},
                "identity": None, "content_hex": "", "claimed_known_bytes": False}
    return {"path": target["path"], "descriptor": fd, "open": call(fd), "identity_check": call(0),
            "read": call(len(bytes.fromhex(target["known_content_hex"]))), "close": call(0),
            "identity": copy.deepcopy(target["identity"]), "content_hex": target["known_content_hex"],
            "claimed_known_bytes": True}


def normalize_publications(value):
    counters = {"issuer": 0, "recipient": 0}
    associations = {}
    for seq, item in enumerate(value["events"], 1):
        item["seq"] = seq
        item["monotonic_ns"] = seq * 1000
        if item["role"] != "supervisor":
            old = item["producer_seq"]
            counters[item["role"]] += 1
            item["producer_seq"] = counters[item["role"]]
            associations[(item["role"], old)] = item["producer_seq"]
        elif item["stage"] == "publication_ack":
            d = item["details"]
            d["producer_seq"] = associations[(d["child_role"], d["producer_seq"])]
    publication = next(e for e in value["events"] if e["stage"] == "token_publication")
    ready = next(e for e in value["events"] if e["stage"] == "transfer_ready")
    ready["details"]["issuer_publication_producer_seq"] = publication["producer_seq"]


def constructed_record():
    """Hand-built evidence, separate from the native event producer."""
    identity = lambda inode, size=4: {"device": 7, "inode": inode, "mode": 33152,
                                    "uid": 501, "gid": 20, "size": size}
    target_a = {"path": "/private/tmp/pw-reader-constructed/A", "identity": identity(1001), "known_content_hex": "4142430a"}
    target_b = {"path": "/private/tmp/pw-reader-constructed/B", "identity": identity(1002), "known_content_hex": "4445460a"}
    for target in (target_a, target_b):
        target["baseline"] = fresh_read(target)
    pids = {"supervisor": 9000, "issuer": 9001, "recipient": 9002}
    processes = {}
    for role, pid in pids.items():
        processes[role] = {"pid": pid, "ppid": 8999 if role == "supervisor" else 9000,
                           "pgid": 9000, "uid": 501, "euid": 501, "gid": 20, "egid": 20,
                           "start_identity": {"seconds": 1700000000, "microseconds": pid},
                           "executable_path": "/constructed/pilot", "executable_identity": identity(777, 100),
                           "identity_rc": 136, "identity_errno": 0, "executable_rc": 18, "executable_errno": 0,
                           "executable_stat_rc": 0, "executable_stat_errno": 0}
    environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
    issuer_policy = '(version 1) (allow default) (deny file-write*) (deny file-issue-extension) (allow file-issue-extension (require-all (extension-class "com.apple.app-sandbox.read") (literal "/private/tmp/pw-reader-constructed/A")))'
    recipient_policy = '(version 1) (allow default) (deny file-read-data) (allow file-read-data (extension "com.apple.app-sandbox.read"))'
    result = {"schema_version": 1, "trial": {"id": "constructed-reference", "arrangement": "C2",
              "block": 1, "position": 3, "planned_position": 3, "chronological_position": 3, "revision": "constructed-only",
              "equipment_ref": "constructed-equipment-not-native", "schedule_ref": "constructed-schedule-not-native",
              "diagnostic": False}, "events": [], "driver": {
                  "ownership": {"supervisor": {"pid": 9000, "pgid": 9000,
                      "start_identity": processes["supervisor"]["start_identity"], "executable": "/constructed/pilot"},
                      "temporary_directory": {"path": "/private/tmp/pw-reader-constructed", "device": 7,
                          "inode": 1000, "uid": 501, "mode": 16832}},
                  "execution": {"command": ["/constructed/pilot", "supervise", "C2"], "environment": environment,
                      "start_utc": "constructed", "elapsed_seconds": 0.1, "returncode": 0,
                      "deadline_reached": False, "cancel_signal": None, "stream_errors": []},
                  "cleanup": {"signals": [], "supervisor_reaped": True, "process_group_absent": True,
                      "group_observations": [{"pgid": 9000, "kill_zero_rc": -1, "kill_zero_errno": 3,
                                              "absent": True, "list_complete": True, "members": []}],
                      "resources_removed": True, "pending": False, "observations": [{"removed": True}]}}}
    producer = {"issuer": 0, "recipient": 0}

    def emit(role, stage, details, status="attempted"):
        seq = len(result["events"]) + 1
        item = {"schema_version": 1, "seq": seq, "role": role, "pid": pids[role],
                "stage": stage, "status": status, "monotonic_ns": seq * 1000, "details": details}
        if role != "supervisor":
            producer[role] += 1
            item["producer_seq"] = producer[role]
        result["events"].append(item)
        if role != "supervisor":
            emit("supervisor", "publication_ack", {"child_role": role, "child_pid": pids[role],
                 "producer_seq": producer[role], "acknowledged_stage": stage})
        return item

    def snapshot(role, boundary):
        descriptors = [{"fd": fd, "type": "character", "stat_rc": 0, "stat_errno": 0,
                        "identity": {**identity(8000), "mode": 8576}, "matches_a": False, "matches_b": False}
                       for fd in (0, 1, 2)]
        if boundary == "entry":
            descriptors += [{"fd": fd, "type": "regular", "stat_rc": 0, "stat_errno": 0,
                             "identity": identity(inode, size), "matches_a": False, "matches_b": False}
                            for fd, inode, size in ((3, 3000, 65536), (4, 3001 if role == "issuer" else 3002, 16384))]
        emit(role, "fd_snapshot", {"boundary": boundary, "inspection_complete": True,
                                  "scan_limit": 1024, "descriptors": descriptors})

    emit("supervisor", "supervisor_start", {"trial_id": "constructed-reference", "arrangement": "C2",
         "process": processes["supervisor"], "environment": environment, "core_limit": {"rc": 0, "errno": 0}})
    emit("supervisor", "targets_prepared", {"a": target_a, "b": target_b, "issuer_policy": issuer_policy,
         "recipient_policy": recipient_policy, "extension_class": "com.apple.app-sandbox.read", "flags": 0})
    for channel in ("evidence", "issued_token", "delivered_token"):
        emit("supervisor", "channel_resource", {"channel": channel,
             "name": "/constructed-" + channel, "owner_pid": pids["supervisor"],
             "created_exclusively": True, "descriptor": 9, "unlink_rc": 0,
             "unlink_errno": 0, "cleanup_pending": False})
    emit("supervisor", "channel_setup", {"evidence": {"descriptor": 3, "size": 65536, "identity": identity(3000, 65536)},
         "issued_token": {"descriptor": 4, "size": 16384, "identity": identity(3001, 16384)},
         "delivered_token": {"descriptor": 5, "size": 16384, "identity": identity(3002, 16384)},
         "issued_initial_zero": True, "delivered_initial_zero": True})
    for role, policy in (("issuer", issuer_policy), ("recipient", recipient_policy)):
        emit("supervisor", "child_launch", {"child_role": role, "rc": 0, "errno": 0,
             "child_pid": pids[role], "process": processes[role]})
        emit(role, "process_entry", {"process": processes[role], "environment": environment,
                                    "core_limit": {"rc": 0, "errno": 0}})
        snapshot(role, "entry")
        emit(role, "channel_mapped", {"evidence": {"descriptor": 3, "map_succeeded": True,
             "close": {"rc": 0, "errno": 0}}, "token": {"descriptor": 4, "map_succeeded": True,
             "close": {"rc": 0, "errno": 0}}})
        emit(role, "symbols", {name: {"available": True, "image": "/usr/lib/libsandbox.1.dylib", "dladdr_rc": 1}
                              for name in ("issue", "consume", "compile", "apply")})
        emit(role, "images", {"loaded_images": ["/usr/lib/libSystem.B.dylib", "/usr/lib/libsandbox.1.dylib"], "count": 2})
        emit(role, "policy_compile", {"policy": policy, "nonnull": True, "errno": 0})
        snapshot(role, "before_apply")
        emit(role, "apply", {"rc": 0, "errno": 0, "application_count": 1})
    snapshot("recipient", "before_read_before")
    emit("recipient", "read_before", fresh_read(target_a, success=False))
    emit("supervisor", "query_capability", {"api": {"available": True, "image": "/usr/lib/libsandbox.1.dylib"},
         "flag": {"available": True, "image": "/usr/lib/libsandbox.1.dylib"}, "no_report_flag": 16})
    emit("supervisor", "images", {"loaded_images": ["/usr/lib/libSystem.B.dylib", "/usr/lib/libsandbox.1.dylib"], "count": 2})
    for filter_id in (0, 1):
        emit("supervisor", "query", {"filter_id": filter_id, "filter_value": target_a["path"] if filter_id else None,
             "operation": "file-issue-extension", "caller_pid": 9000, "target_pid": 9001,
             "no_report_flag": 16, "type_argument": 16 | filter_id, "rc": 0, "errno": 0})
    emit("supervisor", "issue_release", {"issuer_pid": 9001, "recipient_pid": 9002, "queries_collected": 2})
    snapshot("issuer", "before_issue")
    emit("issuer", "issue_begin", {"extension_class": "com.apple.app-sandbox.read", "flags": 0, "path": target_a["path"]})
    emit("issuer", "issue_result", {"nonnull": True, "errno": 0})
    emit("issuer", "raw_token_erasure", {"inspected_bytes": 120, "erased_bytes": 121,
                                         "zero_confirmed": True, "allocation_extent_observed": True})
    published = emit("issuer", "token_publication", {"published": True, "length": 120,
                     "length_valid": True, "terminator_valid": True, "embedded_nul_absent": True})
    framing = {"length": 120, "header_valid": True, "length_valid": True,
               "terminator_valid": True, "embedded_nul_absent": True}
    emit("supervisor", "transfer_ready", {**framing, "ready": True,
                                          "issuer_publication_producer_seq": published["producer_seq"]})
    emit("recipient", "transfer_acceptance", {**framing, "accepted": True})
    emit("supervisor", "transfer_equality", {"equal": True, "length": 120})
    emit("supervisor", "consume_release", {"recipient_pid": 9002, "accepted": True, "equality_confirmed": True})
    emit("recipient", "consume_begin", {"length": 120})
    emit("recipient", "consume_result", {"rc": 1, "errno": 0})
    snapshot("recipient", "before_read_after")
    emit("recipient", "read_after", fresh_read(target_a))
    for role, buffer in (("recipient", "delivered"), ("issuer", "issued")):
        emit(role, "token_erasure", {"buffer": buffer, "capacity": 16384, "zero_confirmed": True})
        emit(role, "child_exit", {"exit_code": 0})
        emit("supervisor", "child_reap", {"child_role": role, "child_pid": pids[role], "rc": pids[role],
             "errno": 0, "wait_status": 0, "exit_code": 0, "term_signal": None, "reaped": True})
    emit("supervisor", "targets_after", {name: {"path": target["path"], "read": fresh_read(target)}
                                          for name, target in (("a", target_a), ("b", target_b))})
    emit("supervisor", "supervisor_token_erasure", {"issued": {"capacity": 16384, "zero_confirmed": True},
         "delivered": {"capacity": 16384, "zero_confirmed": True}, "children_absent": True})
    emit("supervisor", "supervisor_complete", {"elapsed_seconds": 0.1, "deadline_reached": False,
         "equipment_failure": False, "reason": "completed", "issuer_reaped": True, "recipient_reaped": True,
         "issuer_wait_status": 0, "recipient_wait_status": 0, "all_children_reaped": True, "output_failed": False})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--derive-from", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    source_hashes = {}
    for name in ("read.py", "reader_controls.py"):
        data = (HERE / name).read_bytes()
        (args.out / (name + ".source.txt")).write_bytes(data)
        source_hashes[name] = hashlib.sha256(data).hexdigest()
    save(args.out / "invocation.json", {"argv": [sys.executable, *sys.argv],
         "native_trials": 0, "kind": "reader_control_execution", "source_sha256": source_hashes})
    ok = (derived_control(args.derive_from, args.out) if args.derive_from
          else constructed_controls(args.out))
    print(json.dumps({"ok": ok, "output": str(args.out)}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
