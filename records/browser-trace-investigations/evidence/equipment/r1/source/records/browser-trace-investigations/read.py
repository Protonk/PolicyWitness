#!/usr/bin/env python3
"""Independent reader for the bounded Q1/Q2 pilot; imports no PW classifier."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


STATES = {"attempted", "omitted", "unavailable", "interrupted"}
ROLES = {"supervisor", "issuer", "recipient"}
READ_CLASS = "com.apple.app-sandbox.read"
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}


def integer(value):
    return type(value) is int


def query_label(rc, err):
    """The plan's convention, not a calibrated file-issue-extension contract."""
    if not integer(rc) or not integer(err):
        return "unavailable"
    if rc == 0:
        return "allow"
    if rc == 1 and err == 0:
        return "deny"
    if rc < 0:
        return "error"
    return "unclassified"


def identity_equal(left, right):
    if not isinstance(left, dict) or not isinstance(right, dict):
        return False
    keys = ("device", "inode", "mode", "uid", "gid", "size")
    return all(integer(left.get(k)) and left[k] == right.get(k) for k in keys)


def object_equal(left, right):
    return (isinstance(left, dict) and isinstance(right, dict)
            and all(integer(left.get(k)) and left[k] == right.get(k)
                    for k in ("device", "inode")))


def exact_environment(value):
    return value == ENVIRONMENT or value == ["PATH=/usr/bin:/bin", "LC_ALL=C"]


class Reader:
    def __init__(self, document):
        self.document = document
        self.errors = []
        self.limits = []
        self.integrity_findings = []
        self.events = []
        self.index = {}
        self.pids = {}
        self.raw = {}
        self.query_counts = dict(allow=0, deny=0, error=0, unclassified=0, unavailable=0)
        self.access = {}

    def require(self, condition, code, context):
        if not condition:
            self.errors.append({"code": code, "context": context})
        return bool(condition)

    def event(self, role, stage, required=True):
        candidates = self.index.get((role, stage), [])
        if required:
            self.require(len(candidates) == 1, "stage_count", role + "." + stage)
        return candidates[0] if len(candidates) == 1 else None

    def selected(self, role, stage, key, value):
        candidates = [e for e in self.index.get((role, stage), [])
                      if e.get("details", {}).get(key) == value]
        self.require(len(candidates) == 1, "stage_count", role + "." + stage + "." + str(value))
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def details(event):
        return event.get("details", {}) if isinstance(event, dict) else {}

    @staticmethod
    def attempted(event):
        return isinstance(event, dict) and event.get("status") == "attempted"

    def before(self, first, second, context):
        if first is not None and second is not None:
            self.require(first["_position"] < second["_position"], "stage_order", context)

    def scan(self):
        document = self.document
        if not self.require(isinstance(document, dict), "object_required", "document"):
            return False
        self.require(document.get("schema_version") == 1, "schema_version", "document")
        trial = document.get("trial")
        if not self.require(isinstance(trial, dict), "object_required", "trial"):
            return False
        for key in ("id", "revision", "equipment_ref", "schedule_ref"):
            self.require(isinstance(trial.get(key), str) and bool(trial[key]), "trial_metadata", key)
        self.require(isinstance(trial.get("id"), str)
                     and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", trial["id"]) is not None,
                     "trial_id_spelling", "trial")
        self.require(trial.get("arrangement") in {"C" + str(i) for i in range(8)}, "arrangement", "trial")
        if trial.get("diagnostic"):
            self.require(isinstance(trial.get("original_trial_id"), str)
                         and trial.get("correction_cycle") in (1, 2)
                         and trial.get("planned_position") is None, "diagnostic_identity", "trial")
        else:
            for key, lower, upper in (("block", 1, 3), ("position", 1, 8),
                                      ("planned_position", 1, 24)):
                self.require(integer(trial.get(key)) and lower <= trial[key] <= upper,
                             "planned_position", key)
            if all(integer(trial.get(k)) for k in ("block", "position", "planned_position")):
                self.require(trial["planned_position"] == (trial["block"] - 1) * 8 + trial["position"],
                             "planned_position", "trial")
        self.require(integer(trial.get("chronological_position")) and 1 <= trial["chronological_position"] <= 26,
                     "chronological_position", "trial")
        raw_events = document.get("events")
        if not self.require(isinstance(raw_events, list) and bool(raw_events), "events_required", "events"):
            return False
        previous = {}
        global_sequence = -1
        for position, original in enumerate(raw_events):
            if not self.require(isinstance(original, dict), "event_object", str(position)):
                continue
            event = dict(original)
            event["_position"] = position
            role, stage, pid = event.get("role"), event.get("stage"), event.get("pid")
            valid = self.require(role in ROLES and isinstance(stage, str) and bool(stage)
                                 and integer(pid) and pid > 0, "event_identity", str(position))
            self.require(event.get("schema_version") == 1, "event_schema", str(position))
            self.require(event.get("status") in STATES, "stage_status", str(position))
            details = event.get("details")
            self.require(isinstance(details, dict), "stage_details", str(position))
            if not valid or not isinstance(details, dict):
                continue
            if event.get("status") != "attempted":
                self.require(isinstance(details.get("reason"), str) and bool(details["reason"]),
                             "stage_reason", role + "." + stage)
            seq = event.get("seq")
            self.require(integer(seq) and seq > previous.get(role, -1), "publication_sequence", role + "." + stage)
            self.require(integer(seq) and seq > global_sequence, "global_publication_sequence", role + "." + stage)
            if integer(seq):
                previous[role] = seq
                global_sequence = seq
            self.require(integer(event.get("monotonic_ns")) and event["monotonic_ns"] >= 0,
                         "publication_clock", role + "." + stage)
            if role in self.pids:
                self.require(self.pids[role] == pid, "role_process_changed", role + "." + stage)
            else:
                self.pids[role] = pid
            self.events.append(event)
            self.index.setdefault((role, stage), []).append(event)
        self.require(len(set(self.pids.values())) == len(self.pids), "shared_role_process", "events")
        return True

    def call(self, call, context):
        if not self.require(isinstance(call, dict), "call_observation", context):
            return False
        state = call.get("status")
        self.require(state in STATES, "call_status", context)
        if state == "attempted":
            return self.require(integer(call.get("rc")) and integer(call.get("errno")),
                                "call_raw_result", context)
        self.require(isinstance(call.get("reason"), str) and bool(call["reason"]), "call_reason", context)
        self.require(call.get("rc") is None and call.get("errno") is None, "invented_call_result", context)
        return False

    def access_observation(self, details, target, context, stage_status="attempted"):
        result = {"attempted": False, "known_bytes": False, "open_rc": None,
                  "read_rc": None, "descriptor_closed": False}
        if not isinstance(details, dict) or not isinstance(target, dict):
            self.require(False, "access_observation", context)
            return result
        if stage_status != "attempted":
            self.require(stage_status in ("unavailable", "interrupted"), "access_stage_status", context)
            return result
        self.require(details.get("path") == target.get("path"), "access_path", context)
        calls = {key: details.get(key) for key in ("open", "identity_check", "read", "close")}
        attempted = {key: self.call(value, context + "." + key) for key, value in calls.items()}
        if not attempted["open"]:
            self.require(False, "open_result_missing", context)
            return result
        result["attempted"] = True
        descriptor = calls["open"]["rc"]
        result["open_rc"] = descriptor
        result["open_errno"] = calls["open"]["errno"]
        if descriptor < 0:
            self.require(descriptor == -1, "open_return", context)
            self.require(details.get("descriptor") is None, "failed_open_descriptor", context)
            self.require(all(not attempted[key] for key in ("identity_check", "read", "close")),
                         "invented_access_after_open_failure", context)
            self.require(details.get("content_hex") in ("", None) and details.get("identity") is None,
                         "invented_access_content", context)
            self.require(details.get("claimed_known_bytes") is not True, "unsupported_known_bytes_claim", context)
            return result
        self.require(details.get("descriptor") == descriptor, "descriptor_association", context)
        self.require(all(attempted[key] for key in ("identity_check", "read", "close")),
                     "open_without_complete_calls", context)
        stat_ok = attempted["identity_check"] and calls["identity_check"]["rc"] == 0
        identity_ok = stat_ok and identity_equal(details.get("identity"), target.get("identity"))
        if stat_ok:
            if not identity_ok:
                self.integrity_findings.append({"code": "observed_identity_mismatch", "context": context})
        else:
            self.require(details.get("identity") is None, "invented_descriptor_identity", context)
        if attempted["read"]:
            rc = calls["read"]["rc"]
            result["read_rc"] = rc
            result["read_errno"] = calls["read"]["errno"]
            content = details.get("content_hex")
            try:
                data = bytes.fromhex(content) if isinstance(content, str) else None
            except ValueError:
                data = None
            self.require(data is not None, "invalid_read_bytes", context)
            if rc >= 0:
                self.require(data is not None and len(data) == rc, "read_byte_count", context)
                expected = bytes.fromhex(target.get("known_content_hex", ""))
                # A short read is a native observation. Bytes claimed at that
                # length must still be the controlled file's known prefix.
                if data != expected[:rc]:
                    self.integrity_findings.append({"code": "observed_bytes_mismatch", "context": context})
                result["known_bytes"] = identity_ok and data == expected and rc == len(expected)
            else:
                self.require(rc == -1 and data == b"", "failed_read_bytes", context)
        if attempted["close"]:
            result["close_rc"] = calls["close"]["rc"]
            result["close_errno"] = calls["close"]["errno"]
            result["descriptor_closed"] = calls["close"]["rc"] == 0
            self.require(result["descriptor_closed"], "target_descriptor_not_closed", context)
        if "claimed_known_bytes" in details:
            self.require(type(details["claimed_known_bytes"]) is bool
                         and details["claimed_known_bytes"] == result["known_bytes"],
                         "unsupported_known_bytes_claim", context)
        return result

    def snapshot(self, role, boundary, targets):
        event = self.selected(role, "fd_snapshot", "boundary", boundary)
        details = self.details(event)
        if not self.attempted(event):
            return event
        self.require(type(details.get("inspection_complete")) is bool, "snapshot_inspection_state", role + "." + boundary)
        self.require(integer(details.get("scan_limit")) and details["scan_limit"] > 0,
                     "snapshot_scan_limit", role + "." + boundary)
        descriptors = details.get("descriptors")
        if not self.require(isinstance(descriptors, list), "snapshot_descriptors", role + "." + boundary):
            return event
        fds = set()
        for descriptor in descriptors:
            if not self.require(isinstance(descriptor, dict), "descriptor_object", role + "." + boundary):
                continue
            fd = descriptor.get("fd")
            self.require(integer(fd) and fd >= 0 and fd not in fds,
                         "descriptor_number", role + "." + boundary)
            if integer(fd):
                fds.add(fd)
            self.require(isinstance(descriptor.get("type"), str)
                         and integer(descriptor.get("stat_rc")) and integer(descriptor.get("stat_errno")),
                         "descriptor_inspection", role + "." + boundary)
            if descriptor.get("stat_rc") != 0:
                self.limits.append({"code": "descriptor_identity_unavailable", "context": role + "." + boundary,
                                    "descriptor": fd})
            for name, target in targets.items():
                actual_match = object_equal(descriptor.get("identity"), target.get("identity"))
                declared_match = descriptor.get("matches_" + name)
                self.require(type(declared_match) is bool and declared_match == actual_match,
                             "descriptor_match_claim", role + "." + boundary)
                self.require(not actual_match, "target_descriptor_at_boundary", role + "." + boundary)
        if details.get("inspection_complete") is True:
            self.require({0, 1, 2}.issubset(fds), "standard_descriptors_missing_from_snapshot", role + "." + boundary)
        if details.get("inspection_complete") is not True:
            self.limits.append({"code": "descriptor_inspection_incomplete", "context": role + "." + boundary})
        return event

    def acknowledge(self):
        previous = {}
        child_events = [event for event in self.events if event["role"] != "supervisor"]
        acks = self.index.get(("supervisor", "publication_ack"), [])
        self.require(len(acks) == len(child_events), "acknowledgement_count", "children")
        for event in child_events:
            role = event["role"]
            producer = event.get("producer_seq")
            self.require(integer(producer) and producer > previous.get(role, -1),
                         "producer_sequence", role + "." + event["stage"])
            if integer(producer):
                previous[role] = producer
            matches = [ack for ack in acks if self.details(ack).get("child_role") == role
                       and self.details(ack).get("child_pid") == event["pid"]
                       and self.details(ack).get("producer_seq") == producer
                       and self.details(ack).get("acknowledged_stage") == event["stage"]]
            self.require(len(matches) == 1, "publication_acknowledgement", role + "." + event["stage"])
            if len(matches) == 1:
                self.before(event, matches[0], role + "." + event["stage"] + ".ack")
                subsequent = next((e for e in child_events if e["role"] == role
                                   and e["_position"] > event["_position"]), None)
                self.before(matches[0], subsequent, role + ".ack_before_next_publication")

    def process(self, value, role):
        if not self.require(isinstance(value, dict), "process_observation", role):
            return {}
        self.require(value.get("pid") == self.pids.get(role), "process_pid", role)
        for field in ("ppid", "pgid", "uid", "euid", "gid", "egid"):
            self.require(integer(value.get(field)) and value[field] >= 0, "process_field", role + "." + field)
        start = value.get("start_identity", {})
        self.require(isinstance(start, dict) and integer(start.get("seconds"))
                     and start["seconds"] > 0 and integer(start.get("microseconds"))
                     and 0 <= start["microseconds"] < 1000000, "process_start_identity", role)
        self.require(integer(value.get("identity_rc")) and value["identity_rc"] > 0 and integer(value.get("identity_errno")),
                     "process_identity_result", role)
        self.require(integer(value.get("executable_rc")) and value["executable_rc"] > 0
                     and integer(value.get("executable_errno"))
                     and value.get("executable_stat_rc") == 0 and integer(value.get("executable_stat_errno"))
                     and isinstance(value.get("executable_path"), str)
                     and value["executable_path"].startswith("/")
                     and isinstance(value.get("executable_identity"), dict), "executable_identity", role)
        return value

    def policy_tokens(self, value):
        return re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', value) if isinstance(value, str) else []

    def validate_chain(self):
        row = self.document["trial"]["arrangement"]
        start = self.event("supervisor", "supervisor_start")
        start_details = self.details(start)
        self.require(start_details.get("trial_id") == self.document["trial"]["id"]
                     and start_details.get("arrangement") == row, "native_trial_identity", "supervisor_start")
        processes = {"supervisor": self.process(start_details.get("process"), "supervisor")}
        self.require(exact_environment(start_details.get("environment")), "supervisor_environment", "supervisor_start")
        core = start_details.get("core_limit", {})
        self.require(core.get("rc") == 0 and integer(core.get("errno")), "core_dump_disabled", "supervisor")
        prepared = self.event("supervisor", "targets_prepared")
        targets = {name: self.details(prepared).get(name, {}) for name in ("a", "b")}
        for name, target in targets.items():
            self.require(isinstance(target, dict) and isinstance(target.get("path"), str)
                         and target["path"].startswith("/private/tmp/")
                         and isinstance(target.get("identity"), dict)
                         and isinstance(target.get("known_content_hex"), str), "target_preparation", name)
            self.access["baseline_" + name] = self.access_observation(target.get("baseline", {}), target, "baseline." + name)
            if not self.access["baseline_" + name]["known_bytes"]:
                self.integrity_findings.append({"code": "baseline_not_known_bytes", "context": name})
        self.require(not object_equal(targets["a"].get("identity"), targets["b"].get("identity")),
                     "targets_distinct", "targets_prepared")
        self.require(self.details(prepared).get("extension_class") == READ_CLASS
                     and self.details(prepared).get("flags") == 0, "native_issue_inputs", "targets_prepared")
        prefix = '(version 1) (allow default) (deny file-write*) (deny file-issue-extension)'
        clause = ''
        if row in ("C0", "C1"):
            clause = '(allow file-issue-extension)'
        elif row != "C3":
            path = targets["b" if row == "C5" else "a"].get("path", "")
            klass = "com.apple.app-sandbox.read-write" if row == "C4" else READ_CLASS
            clause = '(allow file-issue-extension (require-all (extension-class ' + json.dumps(klass) + ') (literal ' + json.dumps(path) + ')))'
        issuer_policy = self.details(prepared).get("issuer_policy")
        recipient_policy = self.details(prepared).get("recipient_policy")
        recipient_expected = '(version 1) (allow default) (deny file-read-data)'
        if row != "C7":
            recipient_expected += '(allow file-read-data (extension "com.apple.app-sandbox.read"))'
        self.require(self.policy_tokens(issuer_policy) == self.policy_tokens(prefix + clause),
                     "issuer_policy_matrix", row)
        self.require(self.policy_tokens(recipient_policy) == self.policy_tokens(recipient_expected),
                     "recipient_policy_matrix", row)
        channels = self.event("supervisor", "channel_setup")
        channel_details = self.details(channels)
        for key in ("evidence", "issued_token", "delivered_token"):
            channel = channel_details.get(key, {})
            self.require(isinstance(channel, dict) and integer(channel.get("descriptor"))
                         and integer(channel.get("size")) and channel["size"] > 0
                         and isinstance(channel.get("identity"), dict), "channel_identity", key)
        creation_names = []
        for key in ("evidence", "issued_token", "delivered_token"):
            creations = [event for event in self.index.get(("supervisor", "channel_resource"), [])
                         if self.details(event).get("channel") == key
                         and self.details(event).get("created_exclusively") is True]
            self.require(len(creations) == 1, "channel_creation", key)
            if len(creations) == 1:
                creation = self.details(creations[0])
                self.require(isinstance(creation.get("name"), str) and creation["name"].startswith("/")
                             and creation.get("owner_pid") == self.pids.get("supervisor")
                             and creation.get("unlink_rc") == 0 and integer(creation.get("unlink_errno"))
                             and creation.get("cleanup_pending") is False, "channel_creation_ownership", key)
                creation_names.append(creation.get("name"))
                self.before(creations[0], channels, "creation_before_channel_setup." + key)
        self.require(len(creation_names) == 3 and len(set(creation_names)) == 3,
                     "separate_channel_creations", "channel_setup")
        # POSIX shared-memory fstat metadata need not identify the object uniquely.
        # Distinct exclusive creations, live descriptors and the source's dup2
        # associations establish separation; metadata remains a consistency read-back.
        for left, right in (("evidence", "issued_token"), ("evidence", "delivered_token"),
                            ("issued_token", "delivered_token")):
            self.require(channel_details.get(left, {}).get("descriptor") != channel_details.get(right, {}).get("descriptor"),
                         "separate_channel_identities", left + "." + right)
        self.require(channel_details.get("issued_initial_zero") is True
                     and channel_details.get("delivered_initial_zero") is True,
                     "channels_initially_empty", "channel_setup")
        self.before(start, prepared, "start_before_targets")
        self.before(prepared, channels, "targets_before_channels")
        role_events = {}
        readiness = {}
        for role in ("issuer", "recipient"):
            launch = self.selected("supervisor", "child_launch", "child_role", role)
            launch_details = self.details(launch)
            self.require(launch_details.get("rc") == 0 and integer(launch_details.get("errno"))
                         and launch_details.get("child_pid") == self.pids.get(role), "child_launch", role)
            entry = self.event(role, "process_entry")
            process = self.process(self.details(entry).get("process"), role)
            processes[role] = process
            launch_process = self.process(launch_details.get("process"), role)
            identity_fields = ("pid", "ppid", "pgid", "uid", "euid", "gid", "egid", "start_identity",
                               "executable_path", "executable_identity")
            self.require(all(launch_process.get(key) == process.get(key) for key in identity_fields),
                         "launch_process_association", role)
            self.require(process.get("ppid") == self.pids.get("supervisor")
                         and process.get("pgid") == processes["supervisor"].get("pgid"), "child_topology", role)
            self.require(exact_environment(self.details(entry).get("environment")), "child_environment", role)
            core = self.details(entry).get("core_limit", {})
            self.require(core.get("rc") == 0 and integer(core.get("errno")), "core_dump_disabled", role)
            for field in ("uid", "euid", "gid", "egid", "executable_path", "executable_identity"):
                self.require(process.get(field) == processes["supervisor"].get(field), "shared_executable_credentials", role + "." + field)
            self.before(channels, launch, "channels_before_launch." + role)
            self.before(launch, entry, "launch_before_entry." + role)
            snapshots = [self.snapshot(role, boundary, targets) for boundary in
                         (("entry", "before_apply", "before_issue") if role == "issuer"
                          else ("entry", "before_apply", "before_read_before", "before_read_after"))]
            self.require(len(self.index.get((role, "fd_snapshot"), [])) == len(snapshots),
                         "snapshot_count", role)
            if self.attempted(snapshots[0]) and self.details(snapshots[0]).get("inspection_complete") is True:
                descriptor_map = {d.get("fd"): d for d in self.details(snapshots[0]).get("descriptors", []) if isinstance(d, dict)}
                for fd, channel_name in ((3, "evidence"), (4, "issued_token" if role == "issuer" else "delivered_token")):
                    self.require(fd in descriptor_map and object_equal(descriptor_map[fd].get("identity"), channel_details.get(channel_name, {}).get("identity")),
                                 "entry_mapping_descriptor_identity", role + "." + channel_name)
            mapped = self.event(role, "channel_mapped")
            for key in ("evidence", "token"):
                mapping = self.details(mapped).get(key, {})
                self.require(isinstance(mapping, dict) and integer(mapping.get("descriptor"))
                             and type(mapping.get("map_succeeded")) is bool,
                             "channel_mapping", role + "." + key)
                close = mapping.get("close", {})
                self.require(close.get("rc") == 0 and integer(close.get("errno")),
                             "mapping_descriptor_closed", role + "." + key)
            symbols = self.event(role, "symbols")
            symbol_details = self.details(symbols)
            relevant = ("issue", "compile", "apply") if role == "issuer" else ("consume", "compile", "apply")
            for name in relevant:
                lookup = symbol_details.get(name, {})
                self.require(isinstance(lookup, dict) and type(lookup.get("available")) is bool,
                             "symbol_lookup", role + "." + name)
                if lookup.get("available"):
                    self.require(isinstance(lookup.get("image"), str) and bool(lookup["image"])
                                 and integer(lookup.get("dladdr_rc")), "symbol_image", role + "." + name)
            images = self.event(role, "images")
            loaded = self.details(images).get("loaded_images")
            self.require(isinstance(loaded, list) and bool(loaded)
                         and all(isinstance(path, str) and path.startswith("/") for path in loaded)
                         and self.details(images).get("count") == len(loaded), "loaded_image_inventory", role)
            compile_event = self.event(role, "policy_compile")
            compile_details = self.details(compile_event)
            policy = issuer_policy if role == "issuer" else recipient_policy
            self.require(compile_details.get("policy") == policy, "compiled_policy_bytes", role)
            if self.attempted(compile_event):
                self.require(type(compile_details.get("nonnull")) is bool and integer(compile_details.get("errno")),
                             "compile_raw_result", role)
            apply = self.event(role, "apply")
            apply_details = self.details(apply)
            if row == "C0" and role == "issuer" and compile_details.get("nonnull") is True:
                self.require(apply is not None and apply["status"] == "omitted"
                             and apply_details.get("application_count") == 0
                             and apply_details.get("rc") is None, "C0_application_omission", role)
                apply_ok = True
            elif self.attempted(apply):
                self.require(integer(apply_details.get("rc")) and integer(apply_details.get("errno"))
                             and apply_details.get("application_count") == 1,
                             "application_raw_result", role)
                self.require(compile_details.get("nonnull") is True, "apply_without_compilation", role)
                apply_ok = apply_details.get("rc") == 0
            else:
                self.require(compile_details.get("nonnull") is not True
                             or not symbol_details.get("apply", {}).get("available"),
                             "unjustified_application_unavailable", role)
                apply_ok = False
            readiness[role] = (apply_ok and compile_details.get("nonnull") is True
                               and all(symbol_details.get(name, {}).get("available") is True for name in relevant))
            self.require(self.attempted(snapshots[0]), "entry_snapshot_unavailable", role)
            self.require(self.attempted(snapshots[1]) == (compile_details.get("nonnull") is True),
                         "application_snapshot_eligibility", role)
            for snapshot in snapshots[2:]:
                self.require(self.attempted(snapshot) == readiness[role], "operation_snapshot_eligibility", role)
            role_events[role] = {"entry": entry, "snapshots": snapshots, "mapped": mapped,
                                 "symbols": symbols, "images": images, "compile": compile_event, "apply": apply}
            chain = [entry, snapshots[0], mapped, symbols, images, compile_event, snapshots[1], apply]
            for first, second in zip(chain, chain[1:]):
                self.before(first, second, "preparation_order." + role)
            self.raw[role + "_apply"] = {"status": apply.get("status") if apply else None,
                                          **{key: apply_details.get(key) for key in ("rc", "errno", "application_count")}}
        pre_read = self.event("recipient", "read_before")
        self.before(role_events["recipient"]["apply"], role_events["recipient"]["snapshots"][2], "apply_before_first_snapshot")
        self.before(role_events["recipient"]["snapshots"][2], pre_read, "snapshot_before_first_open")
        self.access["before"] = self.access_observation(self.details(pre_read), targets["a"], "recipient.before", pre_read.get("status") if pre_read else None)
        self.require(self.attempted(pre_read) == readiness["recipient"], "first_read_eligibility", "recipient")
        query_cap = self.event("supervisor", "query_capability")
        supervisor_images = self.event("supervisor", "images")
        loaded = self.details(supervisor_images).get("loaded_images")
        self.require(isinstance(loaded, list) and bool(loaded)
                     and all(isinstance(path, str) and path.startswith("/") for path in loaded)
                     and self.details(supervisor_images).get("count") == len(loaded),
                     "loaded_image_inventory", "supervisor")
        cap = self.details(query_cap)
        query_available = True
        for key in ("api", "flag"):
            lookup = cap.get(key, {})
            self.require(isinstance(lookup, dict) and type(lookup.get("available")) is bool,
                         "query_capability_observation", key)
            query_available = query_available and lookup.get("available") is True
            if lookup.get("available"):
                self.require(isinstance(lookup.get("image"), str) and bool(lookup["image"]), "query_lookup_image", key)
        if query_available:
            self.require(integer(cap.get("no_report_flag")), "exported_query_flag", "query_capability")
        queries = self.index.get(("supervisor", "query"), [])
        self.require(len(queries) == 2, "query_count", "supervisor")
        self.raw["queries"] = []
        for filter_id in (0, 1):
            query = self.selected("supervisor", "query", "filter_id", filter_id)
            details = self.details(query)
            self.require(details.get("operation") == "file-issue-extension"
                         and details.get("filter_value") == (None if filter_id == 0 else targets["a"].get("path"))
                         and details.get("caller_pid") == self.pids.get("supervisor")
                         and details.get("target_pid") == self.pids.get("issuer"), "query_arguments", str(filter_id))
            label = "unavailable"
            if self.attempted(query):
                self.require(query_available and integer(details.get("rc")) and integer(details.get("errno")),
                             "query_raw_result", str(filter_id))
                flag = cap.get("no_report_flag")
                self.require(integer(flag) and details.get("no_report_flag") == flag
                             and details.get("type_argument") == (filter_id | flag), "query_type_argument", str(filter_id))
                label = query_label(details.get("rc"), details.get("errno"))
            else:
                self.require(not query_available or not readiness["issuer"], "unjustified_query_unavailable", str(filter_id))
            self.query_counts[label] += 1
            self.raw["queries"].append({"filter_id": filter_id, "status": query.get("status") if query else None,
                                         "rc": details.get("rc"), "errno": details.get("errno"),
                                         "type_argument": details.get("type_argument"), "derived_label": label})
            self.before(query_cap, query, "query_lookup_before_call")
            self.before(role_events["issuer"]["apply"], query, "issuer_application_before_query")
            self.before(role_events["recipient"]["apply"], query, "recipient_application_before_query")
        release = self.event("supervisor", "issue_release")
        release_details = self.details(release)
        self.require(release_details.get("issuer_pid") == self.pids.get("issuer")
                     and release_details.get("recipient_pid") == self.pids.get("recipient")
                     and release_details.get("queries_collected") == 2,
                     "issue_release_association", "supervisor")
        self.before(pre_read, release, "first_read_before_issuance_release")
        for query in queries:
            self.before(query, release, "query_collection_before_release")
        issuer_snapshot = role_events["issuer"]["snapshots"][2]
        self.before(release, issuer_snapshot, "release_before_issuer_snapshot")
        issue_begin = self.event("issuer", "issue_begin")
        issue = self.event("issuer", "issue_result")
        issue_details = self.details(issue)
        self.before(issuer_snapshot, issue_begin, "snapshot_before_issue_begin")
        self.before(issue_begin, issue, "issue_begin_before_result")
        self.require(self.attempted(issue) == readiness["issuer"], "issue_eligibility", "issuer")
        self.require(self.attempted(issue_begin) == self.attempted(issue), "issue_begin_result_pair", "issuer")
        if self.attempted(issue):
            self.require(type(issue_details.get("nonnull")) is bool and integer(issue_details.get("errno")),
                         "issue_raw_result", "issuer")
            begin_details = self.details(issue_begin)
            self.require(begin_details.get("extension_class") == READ_CLASS
                         and begin_details.get("flags") == 0 and begin_details.get("path") == targets["a"].get("path"),
                         "actual_issue_call_arguments", "issuer")
        self.raw["issue"] = {"status": issue.get("status") if issue else None,
                              "nonnull": issue_details.get("nonnull"), "errno": issue_details.get("errno")}
        raw_erasure = self.event("issuer", "raw_token_erasure")
        publication = self.event("issuer", "token_publication")
        publication_details = self.details(publication)
        self.before(issue, raw_erasure, "issue_result_before_raw_erasure")
        self.before(raw_erasure, publication, "raw_erasure_before_publication")
        if issue_details.get("nonnull") is True:
            erasure_details = self.details(raw_erasure)
            self.require(self.attempted(raw_erasure) and erasure_details.get("zero_confirmed") is True
                         and integer(erasure_details.get("inspected_bytes"))
                         and integer(erasure_details.get("erased_bytes"))
                         and erasure_details["erased_bytes"] >= erasure_details["inspected_bytes"],
                         "raw_token_erasure", "issuer")
        publication_ok = self.attempted(publication) and publication_details.get("published") is True
        if self.attempted(publication):
            self.require(type(publication_details.get("published")) is bool
                         and integer(publication_details.get("length")), "token_publication_result", "issuer")
        if publication_ok:
            self.require(issue_details.get("nonnull") is True
                         and 0 < publication_details.get("length", 0) < 16384,
                         "publication_requires_issuance", "issuer")
            self.require(all(publication_details.get(key) is True for key in
                             ("length_valid", "terminator_valid", "embedded_nul_absent")),
                         "publication_framing", "issuer")
        elif issue_details.get("nonnull") is not True:
            self.require(not publication_ok, "publication_after_null_issue", "issuer")
        transfer = self.event("supervisor", "transfer_ready")
        acceptance = self.event("recipient", "transfer_acceptance")
        equality = self.event("supervisor", "transfer_equality")
        consume_release = self.event("supervisor", "consume_release")
        transfer_details = self.details(transfer)
        acceptance_details = self.details(acceptance)
        equality_details = self.details(equality)
        ready = self.attempted(transfer) and transfer_details.get("ready") is True
        accepted = self.attempted(acceptance) and acceptance_details.get("accepted") is True
        for event, details, positive, context in ((transfer, transfer_details, ready, "transfer_ready"),
                                                 (acceptance, acceptance_details, accepted, "transfer_acceptance")):
            if self.attempted(event):
                for key in ("header_valid", "length_valid", "terminator_valid", "embedded_nul_absent"):
                    self.require(type(details.get(key)) is bool, "transfer_framing_observation", context + "." + key)
                    if positive:
                        self.require(details[key], "accepted_invalid_framing", context + "." + key)
                self.require(integer(details.get("length")), "transfer_length", context)
            if positive:
                self.require(publication_ok and details.get("length") == publication_details.get("length"),
                             "transfer_publication_association", context)
        if ready:
            self.require(transfer_details.get("issuer_publication_producer_seq") == (publication or {}).get("producer_seq"),
                         "transfer_publication_reference", "transfer_ready")
        self.require(not accepted or ready, "acceptance_without_readiness", "recipient")
        if accepted:
            self.require(self.attempted(equality) and type(equality_details.get("equal")) is bool
                         and equality_details.get("length") == acceptance_details.get("length"),
                         "accepted_transfer_equality", "supervisor")
        elif not publication_ok:
            self.require(not ready and not accepted, "invented_delivery", "supervisor")
        chain = [publication, transfer, acceptance, equality, consume_release]
        for first, second in zip(chain, chain[1:]):
            self.before(first, second, "transfer_chain")
        self.require(self.details(consume_release).get("recipient_pid") == self.pids.get("recipient"),
                     "consume_release_association", "recipient")
        self.require(self.details(consume_release).get("accepted") is accepted
                     and self.details(consume_release).get("equality_confirmed") is (equality_details.get("equal") is True),
                     "consume_release_transfer_association", "recipient")
        consume_begin = self.event("recipient", "consume_begin")
        consume = self.event("recipient", "consume_result")
        consume_details = self.details(consume)
        self.before(consume_release, consume_begin, "consume_release_before_begin")
        self.before(consume_begin, consume, "consume_begin_before_result")
        if row == "C6":
            self.require(consume is not None and consume["status"] == "omitted"
                         and consume_begin is not None and consume_begin["status"] == "omitted",
                         "C6_consume_omission", "recipient")
        elif accepted and readiness["recipient"] and equality_details.get("equal") is True:
            self.require(self.attempted(consume_begin) and self.attempted(consume),
                         "consumption_result_missing", "recipient")
        else:
            self.require(not self.attempted(consume_begin) and not self.attempted(consume),
                         "consume_without_delivery", "recipient")
        if self.attempted(consume):
            self.require(integer(consume_details.get("rc")) and -(1 << 63) <= consume_details["rc"] < (1 << 63)
                         and integer(consume_details.get("errno")), "consume_signed64_result", "recipient")
        else:
            self.require(consume_details.get("rc") is None and consume_details.get("errno") is None,
                         "invented_consume_result", "recipient")
        self.raw["consume"] = {"status": consume.get("status") if consume else None,
                                "rc": consume_details.get("rc"), "errno": consume_details.get("errno")}
        self.raw["transfer"] = {"status": acceptance.get("status") if acceptance else None,
                                 "published": publication_details.get("published"), "ready": ready,
                                 "accepted": accepted, "equal": equality_details.get("equal"),
                                 "length": acceptance_details.get("length")}
        after_snapshot = role_events["recipient"]["snapshots"][3]
        after_read = self.event("recipient", "read_after")
        self.before(consume, after_snapshot, "consume_result_before_second_snapshot")
        self.before(after_snapshot, after_read, "snapshot_before_second_open")
        self.require(self.attempted(after_read) == readiness["recipient"], "second_read_eligibility", "recipient")
        self.access["after"] = self.access_observation(self.details(after_read), targets["a"], "recipient.after", after_read.get("status") if after_read else None)
        self.finish_cleanup(processes, targets, after_read, publication)

    def finish_cleanup(self, processes, targets, after_read, publication):
        reaps = []
        for role, last in (("issuer", publication), ("recipient", after_read)):
            erasure = self.event(role, "token_erasure")
            details = self.details(erasure)
            self.require(self.attempted(erasure) and isinstance(details.get("buffer"), str)
                         and integer(details.get("capacity")) and details["capacity"] > 0
                         and details.get("zero_confirmed") is True, "child_token_erasure", role)
            exit_event = self.event(role, "child_exit")
            exit_details = self.details(exit_event)
            self.require(integer(exit_details.get("exit_code")), "child_exit_publication", role)
            reap = self.selected("supervisor", "child_reap", "child_role", role)
            reaps.append(reap)
            reap_details = self.details(reap)
            self.require(reap_details.get("child_pid") == self.pids.get(role)
                         and reap_details.get("rc") == self.pids.get(role)
                         and integer(reap_details.get("errno")) and integer(reap_details.get("wait_status"))
                         and reap_details.get("reaped") is True, "child_reap_association", role)
            self.require(reap_details.get("exit_code") == exit_details.get("exit_code")
                         and reap_details.get("term_signal") is None, "exit_publication_reap_consistency", role)
            self.before(last, erasure, "terminal_erasure_order." + role)
            self.before(erasure, exit_event, "erasure_before_exit." + role)
            self.before(exit_event, reap, "exit_publication_before_reap." + role)
        targets_after = self.event("supervisor", "targets_after")
        for reap in reaps:
            self.before(reap, targets_after, "reap_before_target_check")
        for name, target in targets.items():
            after = self.details(targets_after).get(name, {})
            self.require(after.get("path") == target.get("path"), "post_trial_target_path", name)
            observation = self.access_observation(after.get("read", {}), target, "after." + name)
            self.access["after_" + name] = observation
            if not observation["known_bytes"]:
                self.integrity_findings.append({"code": "post_trial_target_not_known_bytes", "context": name})
        erasure = self.event("supervisor", "supervisor_token_erasure")
        for buffer in ("issued", "delivered"):
            erased = self.details(erasure).get(buffer, {})
            self.require(isinstance(erased, dict) and integer(erased.get("capacity"))
                         and erased["capacity"] >= 16384 and erased.get("zero_confirmed") is True,
                         "supervisor_erasure_observation", buffer)
        self.require(self.details(erasure).get("children_absent") is True,
                     "supervisor_erasure_child_absence", "supervisor")
        complete = self.event("supervisor", "supervisor_complete")
        details = self.details(complete)
        self.require(details.get("all_children_reaped") is True
                     and details.get("issuer_reaped") is True and details.get("recipient_reaped") is True,
                     "independent_reaping", "supervisor_complete")
        self.require(details.get("deadline_reached") is False and details.get("equipment_failure") is False
                     and details.get("output_failed") is False, "native_equipment_incomplete", "supervisor_complete")
        self.require(isinstance(details.get("elapsed_seconds"), (int, float))
                     and details["elapsed_seconds"] >= 0, "native_elapsed", "supervisor_complete")
        self.before(targets_after, erasure, "targets_before_supervisor_erasure")
        self.before(erasure, complete, "erasure_before_supervisor_complete")
        driver = self.document.get("driver", {})
        self.require(isinstance(driver, dict), "driver_observation", "driver")
        ownership = driver.get("ownership", {})
        supervisor = ownership.get("supervisor", {})
        self.require(supervisor.get("pid") == self.pids.get("supervisor")
                     and supervisor.get("pgid") == processes["supervisor"].get("pgid")
                     and supervisor.get("start_identity") == processes["supervisor"].get("start_identity")
                     and supervisor.get("executable") == processes["supervisor"].get("executable_path"),
                     "driver_supervisor_association", "driver")
        directory = ownership.get("temporary_directory", {})
        self.require(isinstance(directory, dict) and isinstance(directory.get("path"), str)
                     and directory["path"].startswith("/private/tmp/")
                     and all(integer(directory.get(key)) for key in ("device", "inode", "uid", "mode")),
                     "temporary_directory_ownership", "driver")
        if isinstance(directory.get("path"), str):
            for target in targets.values():
                self.require(str(Path(target.get("path", "")).parent) == directory["path"],
                             "target_directory_ownership", "driver")
        execution = driver.get("execution", {})
        self.require(execution.get("returncode") == 0 and execution.get("deadline_reached") is False
                     and not execution.get("cancel_signal") and not execution.get("stream_errors"),
                     "driver_execution_incomplete", "driver")
        cleanup = driver.get("cleanup", {})
        self.require(cleanup.get("supervisor_reaped") is True and cleanup.get("process_group_absent") is True
                     and cleanup.get("resources_removed") is True and cleanup.get("pending") is False,
                     "driver_cleanup_incomplete", "driver")
        self.require(isinstance(cleanup.get("group_observations"), list) and bool(cleanup["group_observations"]),
                     "group_absence_observation", "driver")
        if isinstance(cleanup.get("group_observations"), list) and cleanup["group_observations"]:
            group = cleanup["group_observations"][-1]
            self.require(group.get("pgid") == supervisor.get("pgid") and group.get("absent") is True
                         and group.get("kill_zero_rc") == -1 and group.get("kill_zero_errno") == 3
                         and group.get("list_complete") is True and group.get("members") == [],
                         "group_absence_raw_observation", "driver")

    def result(self):
        if not self.scan():
            return self.finish(False)
        self.acknowledge()
        self.validate_chain()
        return self.finish(True)

    def finish(self, scanned):
        complete = scanned and not self.errors
        interrupted = any(event.get("status") == "interrupted" for event in self.events)
        complete = complete and not interrupted
        before = self.access.get("before", {})
        after = self.access.get("after", {})
        issue = self.raw.get("issue", {})
        consume = self.raw.get("consume", {})
        transfer = self.raw.get("transfer", {})
        sequence = (complete and not self.limits and not self.integrity_findings and issue.get("status") == "attempted"
                    and issue.get("nonnull") is True and transfer.get("accepted") is True and transfer.get("equal") is True
                    and consume.get("status") == "attempted" and integer(consume.get("rc"))
                    and consume["rc"] != -1 and before.get("attempted") is True
                    and before.get("known_bytes") is False and after.get("known_bytes") is True
                    and after.get("descriptor_closed") is True)
        document = self.document if isinstance(self.document, dict) else {}
        trial = document.get("trial") if isinstance(document.get("trial"), dict) else {}
        return {"schema_version": 1, "trial_id": trial.get("id"),
                "arrangement": trial.get("arrangement"),
                "apparatus_revision": trial.get("revision"),
                "complete_evidence": complete, "consistent_record": scanned and not self.errors,
                "connected_apparatus": complete,
                "complete_delegation_sequence": bool(sequence),
                "errors": self.errors, "limits": self.limits,
                "integrity_findings": self.integrity_findings,
                "query_counts": self.query_counts, "raw_outcomes": self.raw,
                "access_observations": self.access,
                "interpretation": "Native returns, transfer, consumption and fresh access are separate observations; no prediction/enforcement agreement or kernel-cause inference."}


def read_document(document):
    reader = Reader(document)
    try:
        return reader.result()
    except (KeyError, TypeError, ValueError, IndexError, OverflowError, AttributeError) as exc:
        reader.errors.append({"code": "malformed_record", "context": type(exc).__name__})
        return {"schema_version": 1, "complete_evidence": False,
                "connected_apparatus": False, "complete_delegation_sequence": False,
                "errors": reader.errors, "limits": reader.limits,
                "query_counts": reader.query_counts, "raw_outcomes": reader.raw}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.record.read_text())
        result = read_document(document)
    except (OSError, UnicodeError, json.JSONDecodeError):
        result = {"schema_version": 1, "complete_evidence": False,
                  "connected_apparatus": False, "complete_delegation_sequence": False,
                  "errors": [{"code": "unreadable_record", "context": "input"}]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["complete_evidence"] else 1


if __name__ == "__main__":
    sys.exit(main())
