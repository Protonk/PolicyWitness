//! Independent interpretation of actor setup, equipment and scheduling evidence.
//! This reader does not resolve requests, inspect binaries, or invoke helpers.
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};

fn bounded(v: &Value, bytes: usize) -> bool {
    v.as_str()
        .is_some_and(|s| !s.is_empty() && s.len() <= bytes && !s.contains('\0'))
}
fn hex(v: &Value, bytes: usize) -> bool {
    v.as_str().is_some_and(|s| {
        s.len() == bytes
            && s.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    })
}
fn array(v: &Value) -> &[Value] {
    v.as_array().map(Vec::as_slice).unwrap_or(&[])
}
fn keys(v: &Value, allowed: &[&str]) -> bool {
    v.as_object()
        .is_some_and(|o| o.keys().all(|k| allowed.contains(&k.as_str())))
}
fn issue(out: &mut Vec<String>, condition: bool, detail: &str) {
    if !condition {
        out.push(detail.into());
    }
}
fn unique<'a>(rows: &'a [Value], key: &str) -> Option<BTreeMap<&'a str, &'a Value>> {
    let mut result = BTreeMap::new();
    for row in rows {
        let name = row[key].as_str()?;
        if result.insert(name, row).is_some() {
            return None;
        }
    }
    Some(result)
}

// The native plist parser reads bounded in-memory XML. No child process,
// temporary file, registry fact or production equipment classifier participates.
mod plist {
    use std::{
        collections::BTreeSet,
        ffi::{c_char, c_void},
    };
    type Ref = *const c_void;
    #[link(name = "CoreFoundation", kind = "framework")]
    unsafe extern "C" {
        fn CFDataCreate(allocator: Ref, bytes: *const u8, length: isize) -> Ref;
        fn CFPropertyListCreateWithData(
            allocator: Ref,
            data: Ref,
            options: usize,
            format: *mut isize,
            error: *mut Ref,
        ) -> Ref;
        fn CFRelease(value: Ref);
        fn CFGetTypeID(value: Ref) -> usize;
        fn CFDictionaryGetTypeID() -> usize;
        fn CFStringGetTypeID() -> usize;
        fn CFBooleanGetTypeID() -> usize;
        fn CFBooleanGetValue(value: Ref) -> u8;
        fn CFDictionaryGetCount(value: Ref) -> isize;
        fn CFDictionaryGetKeysAndValues(value: Ref, keys: *mut Ref, values: *mut Ref);
        fn CFStringGetLength(value: Ref) -> isize;
        fn CFStringGetMaximumSizeForEncoding(length: isize, encoding: u32) -> isize;
        fn CFStringGetCString(value: Ref, bytes: *mut c_char, capacity: isize, encoding: u32)
        -> u8;
        fn CFEqual(a: Ref, b: Ref) -> u8;
    }
    pub struct Dictionary(Ref);
    impl Drop for Dictionary {
        fn drop(&mut self) {
            unsafe { CFRelease(self.0) }
        }
    }
    impl Dictionary {
        pub fn read(text: &str) -> Option<Self> {
            if text.len() > 65_536
                || !text.trim_start().starts_with("<?xml")
                    && !text.trim_start().starts_with("<plist")
            {
                return None;
            }
            unsafe {
                let data = CFDataCreate(std::ptr::null(), text.as_ptr(), text.len() as isize);
                if data.is_null() {
                    return None;
                }
                let mut error = std::ptr::null();
                let value = CFPropertyListCreateWithData(
                    std::ptr::null(),
                    data,
                    0,
                    std::ptr::null_mut(),
                    &mut error,
                );
                CFRelease(data);
                if !error.is_null() {
                    CFRelease(error);
                }
                if value.is_null() {
                    return None;
                }
                if CFGetTypeID(value) != CFDictionaryGetTypeID() {
                    CFRelease(value);
                    return None;
                }
                Some(Self(value))
            }
        }
        pub fn equal(&self, other: &Self) -> bool {
            unsafe { CFEqual(self.0, other.0) != 0 }
        }
        pub fn empty(&self) -> bool {
            unsafe { CFDictionaryGetCount(self.0) == 0 }
        }
        pub fn granted(&self) -> BTreeSet<String> {
            unsafe {
                let count = CFDictionaryGetCount(self.0) as usize;
                let mut names = vec![std::ptr::null(); count];
                let mut values = vec![std::ptr::null(); count];
                CFDictionaryGetKeysAndValues(self.0, names.as_mut_ptr(), values.as_mut_ptr());
                names
                    .into_iter()
                    .zip(values)
                    .filter_map(|(key, value)| {
                        if CFGetTypeID(key) != CFStringGetTypeID()
                            || CFGetTypeID(value) != CFBooleanGetTypeID()
                            || CFBooleanGetValue(value) == 0
                        {
                            return None;
                        }
                        let capacity =
                            CFStringGetMaximumSizeForEncoding(CFStringGetLength(key), 0x0800_0100)
                                + 1;
                        let mut bytes = vec![0u8; capacity as usize];
                        if CFStringGetCString(key, bytes.as_mut_ptr().cast(), capacity, 0x0800_0100)
                            == 0
                        {
                            return None;
                        }
                        let end = bytes.iter().position(|b| *b == 0)?;
                        String::from_utf8(bytes[..end].to_vec()).ok()
                    })
                    .collect()
            }
        }
    }
}

const WORKER_OPS: &[&str] = &[
    "issue_symbol",
    "consume_symbol",
    "release_symbol",
    "core_limit",
    "descriptor_presence",
    "fstat",
    "page_size",
    "object_size",
    "mmap",
    "descriptor_close",
    "header_binding",
    "terminal_owned_inbound_clear",
    "rejected_mapping_munmap",
];
const REGION_OPS: &[&str] = &[
    "shm_open",
    "shm_unlink",
    "fd_cloexec",
    "ftruncate",
    "mmap",
    "header_initialize",
    "authority_duplicate",
    "authority_spawn_dup2",
    "close_launch_duplicate",
    "close_original_descriptor",
    "shared_clear",
    "munmap",
];
const CUSTODY_OPS: &[&str] = &["mmap", "final_erase", "munmap"];

fn scope(scope: &Value, names: &[&str], family: &str, out: &mut Vec<String>) {
    if let Some(errors) = scope.get("integrity_errors") {
        issue(
            out,
            errors
                .as_array()
                .is_some_and(|items| items.len() <= 16 && items.iter().all(|v| bounded(v, 64)))
                && (array(errors).is_empty()
                    || !matches!(
                        scope["disposition"].as_str(),
                        Some("ready" | "not_required")
                    )),
            "invalid setup cells cannot establish readiness",
        );
    }
    let Some(operations) = scope["operations"].as_array() else {
        out.push("setup scope lacks operation cells".into());
        return;
    };
    issue(
        out,
        operations.len() <= names.len(),
        "setup operation capacity",
    );
    let mut seen = BTreeSet::new();
    for op in operations {
        let Some(slot) = op["slot"].as_u64().and_then(|v| usize::try_from(v).ok()) else {
            out.push("invalid setup operation slot".into());
            continue;
        };
        issue(
            out,
            seen.insert(slot) && names.get(slot).is_some_and(|name| op["operation"] == *name),
            "setup operation slot or identity",
        );
        issue(
            out,
            keys(
                op,
                &[
                    "slot",
                    "operation",
                    "role",
                    "state",
                    "native_kind",
                    "native_rc",
                    "errno",
                    "detail",
                    "value",
                ],
            ),
            "unknown setup operation field",
        );
        let cleanup = match family {
            "worker" => slot >= 11,
            "region" => slot >= 8,
            "custody" => slot >= 1,
            _ => false,
        };
        issue(
            out,
            op["role"] == if cleanup { "cleanup" } else { "setup" }
                || family == "worker" && slot == 9 && op["role"] == "cleanup",
            "setup operation role",
        );
        let state = op["state"].as_str().unwrap_or("");
        let rc = op["native_rc"].as_i64();
        let errno = op["errno"].as_i64();
        issue(
            out,
            op["value"].is_null() || op["value"].as_u64().is_some(),
            "invalid setup operation value",
        );
        issue(
            out,
            op["detail"].is_null() || bounded(&op["detail"], 64),
            "invalid setup detail",
        );
        if state == "not_attempted" {
            issue(
                out,
                op["native_rc"].is_null() && op["errno"].is_null() && op["value"].is_null(),
                "unattempted setup operation fabricates result",
            );
            continue;
        }
        let name = op["operation"].as_str().unwrap_or("");
        let expected_kind = if name.ends_with("_symbol") {
            "symbol"
        } else if name == "mmap" {
            "mapping"
        } else if [
            "header_initialize",
            "shared_clear",
            "final_erase",
            "terminal_owned_inbound_clear",
        ]
        .contains(&name)
        {
            "memory"
        } else if ["descriptor_presence", "object_size", "header_binding"].contains(&name) {
            "validation"
        } else if name == "authority_spawn_dup2" {
            "error_code"
        } else {
            "integer"
        };
        issue(
            out,
            op["native_kind"] == expected_kind,
            "setup operation native kind",
        );
        match op["native_kind"].as_str() {
            Some("integer") => issue(
                out,
                matches!(state, "succeeded" | "failed")
                    && rc.is_some()
                    && if state == "failed" {
                        rc == Some(-1) && errno.is_some_and(|n| n >= 0 && n <= i32::MAX as i64)
                    } else {
                        rc.is_some_and(|n| n >= 0) && op["errno"].is_null()
                    },
                "setup native result or errno",
            ),
            Some("error_code") => issue(
                out,
                matches!(state, "succeeded" | "failed")
                    && rc.is_some_and(|n| n >= 0 && (n == 0) == (state == "succeeded"))
                    && op["errno"].is_null(),
                "setup error-code result",
            ),
            Some("mapping") => issue(
                out,
                matches!(state, "succeeded" | "failed")
                    && op["native_rc"].is_null()
                    && if state == "failed" {
                        errno.is_some_and(|n| n >= 0 && n <= i32::MAX as i64)
                    } else {
                        op["errno"].is_null()
                    },
                "setup mapping invents native integer result",
            ),
            Some("symbol") => issue(
                out,
                matches!(state, "available" | "unavailable")
                    && op["native_rc"].is_null()
                    && op["errno"].is_null(),
                "setup symbol invents native result",
            ),
            Some("validation") => issue(
                out,
                matches!(state, "accepted" | "rejected")
                    && op["native_rc"].is_null()
                    && op["errno"].is_null(),
                "setup validation invents native result",
            ),
            Some("memory") => issue(
                out,
                state == "performed" && op["native_rc"].is_null() && op["errno"].is_null(),
                "setup memory operation invents native result",
            ),
            _ => out.push("unknown setup native kind".into()),
        }
    }
    if let Some(primary) = scope["primary_operation"].as_u64() {
        issue(
            out,
            operations.iter().any(|op| {
                op["slot"].as_u64() == Some(primary)
                    && op["role"] == "setup"
                    && matches!(op["state"].as_str(), Some("failed" | "rejected"))
            }),
            "setup primary operation lacks independent failure",
        );
    } else {
        issue(
            out,
            scope["primary_operation"].is_null(),
            "invalid primary setup operation",
        );
    }
    if let Some(ownership) = scope["ownership"].as_object() {
        for (name, state) in ownership {
            let erase = name == "shared_erasure" || name == "private_erasure";
            issue(
                out,
                state.as_str().is_some_and(|s| {
                    if erase {
                        [
                            "not_present",
                            "performed",
                            "withheld_not_quiescent",
                            "unobserved",
                        ]
                        .contains(&s)
                    } else {
                        ["object_name", "descriptor", "mapping"].contains(&name.as_str())
                            && ["not_acquired", "held", "released", "unresolved"].contains(&s)
                    }
                }),
                "invalid setup ownership state",
            );
            if state == "released" {
                let ops: &[&str] = match name.as_str() {
                    "object_name" => &["shm_unlink"],
                    "mapping" => &["munmap", "rejected_mapping_munmap"],
                    "descriptor" if family == "worker" => &["descriptor_close"],
                    "descriptor" => &["close_original_descriptor"],
                    _ => &[],
                };
                issue(
                    out,
                    operations.iter().any(|op| {
                        ops.contains(&op["operation"].as_str().unwrap_or(""))
                            && op["state"] == "succeeded"
                    }),
                    "released setup ownership lacks successful cleanup",
                );
            }
            if erase && state == "performed" {
                issue(
                    out,
                    operations.iter().any(|op| {
                        matches!(
                            op["operation"].as_str(),
                            Some("shared_clear" | "final_erase" | "terminal_owned_inbound_clear")
                        ) && op["state"] == "performed"
                    }),
                    "setup erasure lacks performed observation",
                );
            }
        }
    }
    if let Some(reference) = scope.get("cleanup_reference") {
        issue(
            out,
            family == "region"
                && reference["kind"] == "posix_shm_name"
                && bounded(&reference["name"], 31)
                && reference["name"]
                    .as_str()
                    .is_some_and(|s| s.is_ascii() && s.starts_with('/'))
                && reference["host_pid"].as_i64().is_some_and(|v| v > 0)
                && reference["session_nonce"].as_u64().is_some()
                && reference["recovery_state"] == "unresolved_manual"
                && scope["ownership"]["object_name"] == "unresolved"
                && operations
                    .iter()
                    .any(|op| op["operation"] == "shm_open" && op["state"] == "succeeded"),
            "unresolved setup cleanup lacks owned creation",
        );
    }
}

fn setup(runner: &Value, actors: &[Value], out: &mut Vec<String>) {
    let setup = &runner["authority_setup"];
    issue(
        out,
        setup.is_object(),
        "actor form lacks automatic authority setup",
    );
    scope(&setup["host"]["run"], &["core_limit"], "run", out);
    let regions = array(&setup["host"]["regions"]);
    let custody = array(&setup["host"]["custody"]);
    let workers = array(&setup["workers"]);
    issue(
        out,
        setup["host"]["regions"].is_array()
            && setup["host"]["custody"].is_array()
            && setup["workers"].is_array()
            && regions.len() <= 8
            && custody.len() <= 32
            && workers.len() == actors.len(),
        "authority setup table capacity",
    );
    let tokens = array(&runner["resources"]["tokens"]);
    let mut seen_regions = BTreeSet::new();
    for row in regions {
        scope(row, REGION_OPS, "region", out);
        issue(
            out,
            row["actor_index"]
                .as_u64()
                .and_then(|i| actors.get(i as usize))
                .is_some_and(|a| a["actor_id"] == row["actor_id"])
                && seen_regions.insert(row["actor_index"].as_u64()),
            "host setup actor association",
        );
    }
    let mut seen_tokens = BTreeSet::new();
    for row in custody {
        scope(row, CUSTODY_OPS, "custody", out);
        issue(
            out,
            row["token_index"]
                .as_u64()
                .and_then(|i| tokens.get(i as usize))
                .is_some_and(|t| t["token_ref"] == row["token_ref"])
                && seen_tokens.insert(row["token_index"].as_u64()),
            "custody setup token association",
        );
    }
    for (index, row) in workers.iter().enumerate() {
        scope(row, WORKER_OPS, "worker", out);
        issue(
            out,
            actors
                .get(index)
                .is_some_and(|a| a["actor_id"] == row["actor_id"])
                && row["actor_index"].as_u64() == Some(index as u64)
                && row["required"].is_boolean(),
            "worker setup actor association",
        );
        issue(
            out,
            matches!(
                row["publication"].as_str(),
                Some("observed" | "not_observed")
            ),
            "worker setup publication",
        );
        if row["publication"] == "not_observed" {
            issue(
                out,
                row["disposition"].is_null() && row["primary_operation"].is_null(),
                "unpublished setup decision carries values",
            );
        } else {
            issue(
                out,
                matches!(
                    row["disposition"].as_str(),
                    Some("ready" | "not_required" | "terminal_required_failure")
                ),
                "worker setup disposition",
            );
            if row["disposition"] == "terminal_required_failure" {
                issue(
                    out,
                    row["required"] == true && row["primary_operation"].as_u64().is_some(),
                    "terminal setup refusal lacks required primary failure",
                );
            }
        }
    }
}

fn application(actor: &Value, setup: &Value, out: &mut Vec<String>) {
    let assessment = &actor["application"];
    issue(
        out,
        keys(assessment, &["state", "basis"]),
        "invalid application assessment",
    );
    let state = assessment["state"].as_str().unwrap_or("");
    let basis = assessment["basis"].as_str().unwrap_or("");
    let applied = actor["applied"] == true;
    issue(
        out,
        matches!(actor["application_count"].as_u64(), Some(0 | 1))
            && (actor["application_count"] == 1) == applied,
        "application count contradicts successful publication",
    );
    let evidence = &actor["subprocess"]["worker_evidence"];
    let failure = &evidence["failure"];
    let published = evidence["failure_state"] == "published";
    let op = failure["operation"].as_u64();
    let code = failure["code"].as_u64();
    let kind = failure["native_kind"].as_u64();
    let input_refusal = published
        && ((op == Some(1) && matches!(code, Some(4 | 7 | 10 | 12)) && kind == Some(0))
            || (op == Some(2) && matches!(code, Some(2 | 3 | 9 | 13))));
    let parameter_refusal = published
        && ((op == Some(1) && code == Some(5) && kind == Some(0))
            || (op == Some(3) && code == Some(1) && kind == Some(2))
            || (op == Some(4)
                && (code == Some(1) && kind == Some(1) || code == Some(6) && kind == Some(0))));
    let compile_refusal = published && op == Some(5) && code == Some(1) && kind == Some(2);
    let timing_refusal = published
        && op == Some(12)
        && (code == Some(1) && kind == Some(1)
            || code == Some(14) && kind == Some(0)
            || code == Some(15) && failure["detail"] == 1 && kind == Some(0));
    let supported = match (state, basis) {
        ("not_requested", "unapplied_declaration") => actor["mode"] == "unapplied" && !applied,
        ("not_attempted", "worker_not_launched") => {
            actor["mode"] == "apply"
                && matches!(
                    actor["setup_status"].as_str(),
                    Some("launch_refused" | "setup_timeout" | "not_launched")
                )
                && !applied
                && actor["subprocess"].is_null()
                && actor["launch"].is_null()
        }
        ("not_attempted", "terminal_authority_setup_refusal") => {
            actor["mode"] == "apply"
                && setup["publication"] == "observed"
                && setup["disposition"] == "terminal_required_failure"
                && !applied
        }
        ("not_attempted", "terminal_input_refusal") => {
            actor["mode"] == "apply" && input_refusal && !applied
        }
        ("not_attempted", "terminal_parameter_refusal") => {
            actor["mode"] == "apply" && parameter_refusal && !applied
        }
        ("not_attempted", "terminal_compile_refusal") => {
            actor["mode"] == "apply" && compile_refusal && !applied
        }
        ("not_attempted", "terminal_timing_refusal") => {
            actor["mode"] == "apply" && timing_refusal && !applied
        }
        ("observed", "applied_publication") => actor["mode"] == "apply" && applied,
        ("observed", "apply_failure_publication") => {
            actor["mode"] == "apply"
                && published
                && op == Some(8)
                && code == Some(1)
                && kind == Some(1)
                && failure["native_result"].as_i64().is_some_and(|v| v != 0)
                && !applied
        }
        ("unobserved", "apply_call_boundary_without_result") => {
            actor["mode"] == "apply"
                && actor["subprocess"]["worker_evidence"]["progress"]["operation"] == 8
                && matches!(evidence["progress"]["stage"].as_u64(), Some(1 | 2))
                && !applied
        }
        ("unobserved", "no_eligible_apply_publication") => {
            actor["mode"] == "apply"
                && !applied
                && !(setup["publication"] == "observed"
                    && setup["disposition"] == "terminal_required_failure")
        }
        _ => false,
    };
    issue(
        out,
        supported,
        "application assessment lacks its eligible source",
    );
}

fn equipment(runner: &Value, actors: &[Value], out: &mut Vec<String>) {
    let inventory = &runner["equipment_inventory"];
    let bindings = array(&runner["equipment_bindings"]);
    let reads = array(&runner["equipment_entitlements"]);
    issue(
        out,
        inventory.is_object()
            && matches!(
                inventory["status"].as_str(),
                Some("verified" | "refused" | "unobserved")
            )
            && runner["equipment_bindings"].is_array()
            && runner["equipment_entitlements"].is_array()
            && bindings.len() <= 4
            && reads.len() <= 12,
        "equipment table type or capacity",
    );
    if inventory["status"] == "verified" {
        issue(
            out,
            inventory["schema_version"] == 1
                && hex(&inventory["sha256"], 64)
                && hex(&inventory["worker_identity"], 64)
                && hex(&inventory["unsigned_worker_sha256"], 64)
                && inventory["seal_osstatus"] == 0,
            "verified equipment inventory lacks sealed identity",
        );
    }
    let Some(by_binding) = unique(bindings, "binding_id") else {
        out.push("duplicate equipment binding".into());
        return;
    };
    let Some(by_read) = unique(reads, "entitlements_id") else {
        out.push("duplicate equipment read-back".into());
        return;
    };
    let mut dictionaries = BTreeMap::new();
    for row in reads {
        let id = row["entitlements_id"].as_str().unwrap_or("");
        let binding = row["binding_ref"].as_str().unwrap_or("");
        issue(
            out,
            [
                "selected",
                "unentitled",
                "override-selected",
                "override-unentitled",
            ]
            .contains(&binding),
            "entitlement read-back binding",
        );
        let expected = match row["source"].as_str() {
            Some("binding") => Some(format!("binding-{binding}")),
            Some("execution") => actors
                .iter()
                .position(|a| a["actor_id"] == row["actor_id"])
                .map(|i| format!("execution-{i}")),
            _ => None,
        };
        issue(
            out,
            expected.as_deref() == Some(id),
            "entitlement read-back actor or identity",
        );
        if row["status"] == "observed" {
            if let Some(dictionary) = row["raw_plist"].as_str().and_then(plist::Dictionary::read) {
                dictionaries.insert(id, dictionary);
            } else {
                out.push("invalid or oversized entitlement plist".into());
            }
        } else {
            issue(
                out,
                row["status"] == "failed" && row["raw_plist"].is_null(),
                "failed entitlement observation invents plist",
            );
        }
    }
    for (id, binding) in &by_binding {
        let role = id.strip_prefix("override-").unwrap_or(id);
        let instrumented = id.starts_with("override-");
        issue(
            out,
            ["selected", "unentitled"].contains(&role) && binding["role"] == role,
            "equipment role association",
        );
        let expected_path = if role == "selected" {
            "Contents/MacOS/pw-probe-runner"
        } else {
            "Contents/MacOS/pw-probe-runner-unentitled"
        };
        issue(
            out,
            bounded(&binding["path"], 1023)
                && if instrumented {
                    binding["source"] == "test_override"
                        && binding["implementation_identity"] == "unverified_fixture"
                        && binding["relative_path"].is_null()
                        && binding["expected_sha256"].is_null()
                        && binding["expected_cdhash"].is_null()
                } else {
                    binding["source"] == "packaged"
                        && binding["implementation_identity"] == "inventory_verified"
                        && binding["relative_path"] == expected_path
                },
            "equipment fixed path association",
        );
        if binding["status"] == "bound" {
            let reference = format!("binding-{id}");
            issue(
                out,
                inventory["status"] == "verified"
                    && hex(&binding["sha256"], 64)
                    && (instrumented || binding["sha256"] == binding["expected_sha256"])
                    && hex(&binding["cdhash"], 40)
                    && (instrumented || binding["cdhash"] == binding["expected_cdhash"])
                    && binding["signature_osstatus"] == 0
                    && (instrumented || binding["entitlements_match"] == true)
                    && binding["entitlements_ref"] == reference
                    && dictionaries.contains_key(reference.as_str()),
                "bound equipment lacks inspected identity",
            );
            if role == "unentitled" && !instrumented {
                issue(
                    out,
                    dictionaries
                        .get(reference.as_str())
                        .is_some_and(plist::Dictionary::empty),
                    "unentitled worker carries entitlements",
                );
            }
        } else {
            issue(
                out,
                binding["status"] == "refused",
                "invalid equipment binding status",
            );
        }
    }
    let mut runtime_failed = false;
    for (index, actor) in actors.iter().enumerate() {
        let equipment = &actor["equipment"];
        let resolved = equipment["resolved"].as_str().unwrap_or("");
        let bound_id = equipment["binding_ref"].as_str().unwrap_or("");
        issue(
            out,
            ["selected", "unentitled"].contains(&resolved)
                && (bound_id == resolved || bound_id == format!("override-{resolved}"))
                && (equipment["requested"].is_null() && resolved == "selected"
                    || equipment["requested"] == resolved),
            "actor equipment selector association",
        );
        let binding = by_binding.get(bound_id).copied().unwrap_or(&Value::Null);
        let requirements = array(&equipment["required_entitlements"]);
        let required: BTreeSet<&str> = requirements.iter().filter_map(Value::as_str).collect();
        issue(
            out,
            equipment["required_entitlements"].is_array()
                && requirements.len() <= 64
                && required.len() == requirements.len()
                && requirements.iter().all(|v| bounded(v, 255)),
            "invalid actor entitlement requirements",
        );
        let binding_ref = format!("binding-{bound_id}");
        let granted = dictionaries
            .get(binding_ref.as_str())
            .map(plist::Dictionary::granted);
        let expected_missing: BTreeSet<&str> = required
            .iter()
            .copied()
            .filter(|key| !granted.as_ref().is_some_and(|g| g.contains(*key)))
            .collect();
        match equipment["requirements_status"].as_str() {
            Some("satisfied" | "unsatisfied") => {
                let missing = array(&equipment["missing_requirements"]);
                issue(
                    out,
                    granted.is_some()
                        && equipment["missing_requirements"].is_array()
                        && missing.len() == expected_missing.len()
                        && missing
                            .iter()
                            .all(|key| key.as_str().is_some_and(|k| expected_missing.contains(k)))
                        && (equipment["requirements_status"] == "satisfied")
                            == expected_missing.is_empty(),
                    "actor requirements disagree with observed entitlements",
                );
            }
            Some("unobserved") => issue(
                out,
                equipment["missing_requirements"].is_null(),
                "unobserved actor requirements invent result",
            ),
            _ => out.push("invalid actor requirement disposition".into()),
        }
        let execution = &equipment["execution"];
        let status = execution["status"].as_str().unwrap_or("");
        issue(
            out,
            ["matched", "mismatched", "inspection_failed", "unobserved"].contains(&status),
            "invalid execution equipment status",
        );
        if status == "matched" {
            let reference = format!("execution-{index}");
            let read = by_read
                .get(reference.as_str())
                .copied()
                .unwrap_or(&Value::Null);
            let static_plist = dictionaries.get(binding_ref.as_str());
            let live_plist = dictionaries.get(reference.as_str());
            let live_granted = live_plist.map(plist::Dictionary::granted);
            issue(
                out,
                binding["status"] == "bound"
                    && equipment["requirements_status"] == "satisfied"
                    && execution["eligible"] == true
                    && execution["reason"].is_null()
                    && execution["pid"] == actor["launch"]["pid"]
                    && execution["pid"].as_i64().is_some_and(|n| n > 0)
                    && execution["path"] == binding["path"]
                    && execution["cdhash"] == binding["cdhash"]
                    && execution["identifier"] == binding["identifier"]
                    && execution["team_id"] == binding["team_id"]
                    && execution["entitlements_ref"] == reference
                    && read["binding_ref"] == bound_id
                    && read["actor_id"] == actor["actor_id"]
                    && static_plist
                        .zip(live_plist)
                        .is_some_and(|(s, l)| s.equal(l))
                    && live_granted
                        .as_ref()
                        .is_some_and(|keys| required.iter().all(|key| keys.contains(*key))),
                "execution equipment does not match its owned binding",
            );
            let calls = array(&execution["native_observations"]);
            issue(
                out,
                calls.len() == 4
                    && [
                        "guest_code",
                        "dynamic_validity",
                        "associated_static_code",
                        "signing_information",
                    ]
                    .iter()
                    .zip(calls)
                    .all(|(name, call)| {
                        call["operation"] == *name
                            && call["attempted"] == true
                            && call["osstatus"] == 0
                    }),
                "matched execution lacks native inspection results",
            );
        } else {
            issue(
                out,
                execution["eligible"] == false,
                "unmatched equipment permits activation",
            );
            runtime_failed |=
                actor["launch"].is_object() && matches!(status, "mismatched" | "inspection_failed");
        }
    }
    if runtime_failed {
        issue(
            out,
            runner["normalized_outcome"] != "ok"
                && runner["preparation_failure"].is_null()
                && runner["schedule"]["cancelled"]
                    .as_str()
                    .is_some_and(|s| !s.is_empty())
                && array(&runner["phases"]).iter().all(|p| {
                    p["ordering"]["proceed_set"] != true
                        && p["ordering"]["proceed_observed"] != true
                        && p["activation_observation"].is_null()
                        && p["arrival_observed"] == false
                        && p["completion_observed"] == false
                        && p["validator_subprocess"].is_null()
                        && p["collection_status"] == "not_reached"
                }),
            "runtime equipment refusal lost evidence or enabled schedule",
        );
    }
}

fn owned_reap_valid(actor: &Value) -> bool {
    let reap = &actor["owned_reap"];
    let sub = &actor["subprocess"];
    let Some(pid) = reap["pid"]
        .as_i64()
        .filter(|v| *v > 0 && *v <= i32::MAX as i64)
    else {
        return false;
    };
    let Some(status) = reap["raw_status"]
        .as_i64()
        .and_then(|v| i32::try_from(v).ok())
    else {
        return false;
    };
    let status_matches = if libc::WIFEXITED(status) {
        sub["exit_code"].as_i64() == Some(i64::from(libc::WEXITSTATUS(status)))
            && sub["term_signal"].is_null()
    } else if libc::WIFSIGNALED(status) {
        sub["term_signal"].as_i64() == Some(i64::from(libc::WTERMSIG(status)))
            && sub["exit_code"].is_null()
    } else {
        false
    };
    reap.is_object()
        && reap["native_rc"].as_i64() == Some(pid)
        && actor["launch"]["pid"].as_i64() == Some(pid)
        && sub["pid"].as_i64() == Some(pid)
        && sub["reaped"] == true
        && status_matches
        && reap["capture_ordinal"].as_u64().is_some_and(|v| v > 0)
        && (reap["observed_ns"].is_null() || reap["observed_ns"].as_u64().is_some())
        && reap["ownership_unbroken"].is_boolean()
        && reap["departure_requested"].is_boolean()
        && bounded(&reap["stage"], 64)
}

fn gates(runner: &Value, actors: &[Value], out: &mut Vec<String>) {
    let phases = array(&runner["phases"]);
    for actor in actors {
        if actor.get("owned_reap").is_some() {
            issue(
                out,
                owned_reap_valid(actor),
                "owned reap disagrees with child identity or wait status",
            );
        }
    }
    for (index, phase) in phases.iter().enumerate() {
        if let Some(activation) = phase.get("activation_observation") {
            issue(
                out,
                keys(activation, &["capture_ordinal", "observed_ns"])
                    && activation["capture_ordinal"]
                        .as_u64()
                        .is_some_and(|v| v > 0)
                    && (activation["observed_ns"].is_null()
                        || activation["observed_ns"].as_u64().is_some()),
                "invalid phase activation observation",
            );
        }
        let Some(gate) = phase.get("termination_gate") else {
            continue;
        };
        let source = actors
            .iter()
            .find(|a| a["actor_id"] == gate["source_actor_id"]);
        let final_phase = phases
            .iter()
            .position(|p| p["phase_id"] == gate["source_final_phase_id"]);
        issue(
            out,
            gate.is_object()
                && gate["condition"] == "terminated"
                && source.is_some()
                && gate["source_actor_id"] != phase["actor_id"]
                && final_phase.is_some_and(|i| {
                    i < index
                        && phases[i]["actor_id"] == gate["source_actor_id"]
                        && !phases[i + 1..]
                            .iter()
                            .any(|p| p["actor_id"] == gate["source_actor_id"])
                }),
            "termination dependency source or ordering",
        );
        let outcome = gate["outcome"].as_str().unwrap_or("");
        issue(
            out,
            [
                "not_reached",
                "satisfied",
                "timed_out",
                "ownership_lost",
                "clock_unavailable",
                "source_unavailable",
                "source_departure_requested",
                "execution_allowance_exhausted",
            ]
            .contains(&outcome),
            "termination gate outcome",
        );
        if outcome != "not_reached" {
            let wait = &gate["wait"];
            issue(
                out,
                wait["budget_ms"].as_u64().is_some_and(|v| v <= 5000)
                    && wait["clock_fault"].is_boolean()
                    && (wait["elapsed_ms"].is_null() || wait["elapsed_ms"].as_u64().is_some())
                    && wait["stop"] == outcome
                    && wait["excluded_ms"].is_null(),
                "termination gate wait budget or accounting",
            );
        }
        if !gate["observation"].is_null() {
            let reap = source.map(|a| &a["owned_reap"]).unwrap_or(&Value::Null);
            issue(
                out,
                keys(&gate["observation"], &["capture_ordinal"])
                    && gate["observation"]["capture_ordinal"]
                        .as_u64()
                        .is_some_and(|v| v > 0)
                    && gate["observation"]["capture_ordinal"] == reap["capture_ordinal"]
                    && source.is_some_and(owned_reap_valid)
                    && matches!((reap["capture_ordinal"].as_u64(), gate["capture_ordinal"].as_u64()), (Some(r), Some(g)) if r < g),
                "termination gate observation does not resolve to its source owned reap",
            );
        }
        if outcome == "satisfied" {
            let wait = &gate["wait"];
            let reap = source.map(|a| &a["owned_reap"]).unwrap_or(&Value::Null);
            let activation = final_phase
                .map(|i| &phases[i]["activation_observation"])
                .unwrap_or(&Value::Null);
            let order = matches!((activation["capture_ordinal"].as_u64(),reap["capture_ordinal"].as_u64(),gate["capture_ordinal"].as_u64()),(Some(a),Some(r),Some(g)) if a<r && r<g);
            let time = matches!((activation["observed_ns"].as_u64(),reap["observed_ns"].as_u64()),(Some(a),Some(r)) if a<=r);
            issue(
                out,
                source.is_some_and(owned_reap_valid)
                    && reap["ownership_unbroken"] == true
                    && reap["departure_requested"] == false
                    && matches!(
                        reap["stage"].as_str(),
                        Some("schedule" | "termination_gate")
                    )
                    && keys(&gate["observation"], &["capture_ordinal"])
                    && gate["observation"]["capture_ordinal"] == reap["capture_ordinal"]
                    && order
                    && time,
                "satisfied termination gate lacks natural owned reap after final activation",
            );
            issue(
                out,
                wait["budget_ms"]
                    .as_u64()
                    .is_some_and(|v| v > 0 && v <= 5000)
                    && wait["clock_fault"] == false
                    && wait["native_errno"].is_null()
                    && matches!((wait["elapsed_ms"].as_u64(),wait["budget_ms"].as_u64()),(Some(e),Some(b)) if e<=b),
                "satisfied termination gate lacks a timely clocked wait",
            );
            if let Some(dependent) = phase.get("activation_observation") {
                issue(
                    out,
                    dependent["observed_ns"].is_null()
                        || matches!((reap["observed_ns"].as_u64(),dependent["observed_ns"].as_u64()),(Some(r),Some(a)) if r<=a),
                    "dependent activation precedes owned termination",
                );
            }
        } else {
            issue(
                out,
                gate["activation_eligible"] == false
                    && phase.get("activation_observation").is_none()
                    && phase["ordering"]["proceed_set"] != true
                    && phase["ordering"]["proceed_observed"] != true
                    && phase["collection_status"] == "not_reached",
                "failed termination gate enabled collection or release",
            );
        }
        if gate["activation_eligible"] == true {
            issue(
                out,
                outcome == "satisfied"
                    && actors.iter().any(|a| {
                        a["actor_id"] == phase["actor_id"]
                            && matches!(
                                a["setup_status"].as_str(),
                                Some("applied" | "unapplied_declared")
                            )
                            && a["equipment"]["execution"]["eligible"] == true
                    }),
                "termination gate eligibility lacks independent setup",
            );
        }
    }
}

fn preparation_failure_valid(runner: &Value) -> bool {
    let failure = &runner["preparation_failure"];
    let pair = (failure["stage"].as_str(), failure["code"].as_str());
    let actors = array(&runner["actors"]);
    let phases = array(&runner["phases"]);
    let identities: Vec<&Value> = phases
        .iter()
        .flat_map(|p| array(&p["action_ids"]))
        .collect();
    matches!(
        pair,
        (Some("resolved_plan"), Some("inconsistent_assignment"))
            | (Some("equipment"), Some("equipment_binding_refused"))
    ) && runner["execution_form"] == "actors"
        && runner["normalized_outcome"] == "runner_failed"
        && runner["rc"] == 1
        && !actors.is_empty()
        && actors.iter().all(|a| {
            a["setup_status"] == "launch_refused"
                && a["launch"].is_null()
                && a["subprocess"].is_null()
        })
        && ["steps", "extension_events", "transfers"]
            .iter()
            .all(|key| runner[*key].as_array().is_some_and(Vec::is_empty))
        && ["tokens", "deliveries", "handles"]
            .iter()
            .all(|key| array(&runner["resources"][*key]).is_empty())
        && runner["authority_setup"]["host"]["run"]["disposition"] == "not_attempted"
        && runner["request_failure"].is_null()
        && phases.iter().all(|p| {
            p["collection_status"] == "not_reached"
                && p["ordering"]["proceed_set"] != true
                && p["ordering"]["proceed_observed"] != true
        })
        && identities.len() <= 256
        && identities.iter().all(|id| bounded(id, 63))
        && identities
            .iter()
            .filter_map(|id| id.as_str())
            .collect::<BTreeSet<_>>()
            .len()
            == identities.len()
}

pub(super) fn validate(runner: &Value) -> Vec<String> {
    let mut out = Vec::new();
    if runner.get("extensions").is_some() {
        out.push("removed declaration reply field".into());
    }
    if runner["execution_form"] != "actors" {
        issue(
            &mut out,
            array(&runner["extension_events"]).is_empty()
                && !runner["authority_setup"].is_object()
                && !runner["equipment_inventory"].is_object(),
            "ordinary reply carries actor authority evidence",
        );
        return out;
    }
    if runner.get("preparation_failure").is_some() {
        issue(
            &mut out,
            preparation_failure_valid(runner),
            "invalid before-launch preparation failure",
        );
    }
    let actors = array(&runner["actors"]);
    setup(runner, actors, &mut out);
    equipment(runner, actors, &mut out);
    for (index, actor) in actors.iter().enumerate() {
        application(
            actor,
            &runner["authority_setup"]["workers"][index],
            &mut out,
        );
    }
    gates(runner, actors, &mut out);
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn fixture(name: &str) -> Value {
        serde_json::from_str(match name {
            "actor_authority_reply.json" => {
                include_str!("../../tests/fixtures/contract/actor_authority_reply.json")
            }
            "actor_setup_failure_reply.json" => {
                include_str!("../../tests/fixtures/contract/actor_setup_failure_reply.json")
            }
            "actor_gate_reply.json" => {
                include_str!("../../tests/fixtures/contract/actor_gate_reply.json")
            }
            "actor_override_reply.json" => {
                include_str!("../../tests/fixtures/contract/actor_override_reply.json")
            }
            "actor_unclocked_reply.json" => {
                include_str!("../../tests/fixtures/contract/actor_unclocked_reply.json")
            }
            "actor_required_reply.json" => {
                include_str!("../../tests/fixtures/contract/actor_required_reply.json")
            }
            "actor_compound_failure_reply.json" => {
                include_str!("../../tests/fixtures/contract/actor_compound_failure_reply.json")
            }
            other => panic!("unknown independently authored fixture {other}"),
        })
        .unwrap()
    }

    #[test]
    fn actor_evidence_rejects_independent_substitutions_and_preserves_partial_facts() {
        let cases: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/actor_evidence.json"
        ))
        .unwrap();
        for case in array(&cases) {
            let mut reply = fixture(
                case["fixture"]
                    .as_str()
                    .unwrap_or("actor_authority_reply.json"),
            );
            let original = reply.clone();
            for patch in array(&case["patches"]) {
                let (parent, key) = patch["path"].as_str().unwrap().rsplit_once('/').unwrap();
                let target = reply.pointer_mut(parent).unwrap();
                if let Some(values) = target.as_array_mut() {
                    values[key.parse::<usize>().unwrap()] = patch["value"].clone();
                } else {
                    target[key] = patch["value"].clone();
                }
            }
            if !array(&case["patches"]).is_empty() {
                assert_ne!(reply, original, "inert mutation {}", case["name"]);
            }
            let before = reply.clone();
            let errors = validate(&reply);
            assert_eq!(reply, before, "reader mutated {}", case["name"]);
            assert_eq!(
                errors.is_empty(),
                case["accepted"] == true,
                "{}: {errors:?}",
                case["name"]
            );
            if let Some(diagnostic) = case["diagnostic"].as_str() {
                assert!(
                    errors.iter().any(|error| error.contains(diagnostic)),
                    "{}: {errors:?}",
                    case["name"]
                );
            }
        }
    }

    #[test]
    fn entitlement_requirements_use_boolean_true_and_semantic_dictionary_equality() {
        let a = plist::Dictionary::read("<plist version=\"1.0\"><dict><key>yes</key><true/><key>no</key><false/><key>number</key><integer>1</integer></dict></plist>").unwrap();
        let b = plist::Dictionary::read("<plist version=\"1.0\"><dict><key>number</key><integer>1</integer><key>no</key><false/><key>yes</key><true/></dict></plist>").unwrap();
        assert!(a.equal(&b));
        assert_eq!(a.granted(), BTreeSet::from(["yes".to_string()]));
        assert!(plist::Dictionary::read("<plist><array/></plist>").is_none());
        assert!(plist::Dictionary::read("not a plist").is_none());
        assert!(plist::Dictionary::read(&"x".repeat(65_537)).is_none());
    }

    #[test]
    fn declaration_fields_are_not_an_alternate_current_reply_language() {
        let base = json!({"schema_version":26,"steps":[],"phases":[]});
        assert!(validate(&base).is_empty());
        for removed in [Value::Null, json!([]), json!([{"token_ref":"old"}])] {
            let mut reply = base.clone();
            reply["extensions"] = removed;
            assert!(
                validate(&reply)
                    .iter()
                    .any(|e| e.contains("removed declaration"))
            );
        }
    }
}
