//! Typed actor setup, equipment, scheduling and authority-custody admission.
use super::*;

fn require(out: &mut Vec<IntegrityIssue>, condition: bool, detail: &str) {
    if !condition {
        issue(out, "actor_evidence", detail);
    }
}
fn bounded(s: &str, bytes: usize) -> bool {
    !s.is_empty() && s.len() <= bytes && !s.contains('\0')
}
/// A digest is its bytes; only its length can be wrong here.
fn digest(value: Option<&[u8]>, bytes: usize) -> bool {
    value.is_some_and(|value| value.len() == bytes)
}
fn pid(p: i64) -> bool {
    (1..=i64::from(i32::MAX)).contains(&p)
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

fn scope(s: &PWRunnerAuthorityScope, names: &[&str], family: &str, out: &mut Vec<IntegrityIssue>) {
    if let Some(errors) = &s.integrity_errors {
        require(out, false, "setup publication retains integrity errors");
        require(
            out,
            errors.len() <= 16
                && errors.iter().all(|e| bounded(e, 64))
                && (errors.is_empty()
                    || !matches!(s.disposition.as_deref(), Some("ready" | "not_required"))),
            "invalid setup cells cannot establish readiness",
        );
    }
    require(
        out,
        s.operations.len() <= names.len(),
        "setup operation capacity",
    );
    let mut seen = BTreeSet::new();
    for op in &s.operations {
        let slot = usize::try_from(op.slot).ok();
        require(
            out,
            slot.is_some_and(|i| seen.insert(i) && names.get(i) == Some(&op.operation.as_str())),
            "setup operation slot or identity",
        );
        let cleanup = slot.is_some_and(|i| match family {
            "worker" => i >= 11,
            "region" => i >= 8,
            "custody" => i >= 1,
            _ => false,
        });
        require(
            out,
            op.role == if cleanup { "cleanup" } else { "setup" }
                || family == "worker" && slot == Some(9) && op.role == "cleanup",
            "setup operation role",
        );
        require(
            out,
            op.detail.as_deref().is_none_or(|d| bounded(d, 64)),
            "invalid setup detail",
        );
        let name = op.operation.as_str();
        let expected = if name.ends_with("_symbol") {
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
        require(
            out,
            op.native_kind.as_deref() == Some(expected),
            "setup operation native kind",
        );
        if op.state == "not_attempted" {
            require(
                out,
                op.native_rc.is_none() && op.errno.is_none() && op.value.is_none(),
                "unattempted setup operation fabricates result",
            );
            continue;
        }
        let valid = match op.native_kind.as_deref() {
            Some("integer") => {
                matches!(op.state.as_str(), "succeeded" | "failed")
                    && if op.state == "failed" {
                        op.native_rc == Some(-1) && op.errno.is_some_and(|e| e >= 0)
                    } else {
                        op.native_rc.is_some_and(|r| r >= 0) && op.errno.is_none()
                    }
            }
            Some("error_code") => {
                matches!(op.state.as_str(), "succeeded" | "failed")
                    && op.native_rc.is_some_and(|r| {
                        (0..=i64::from(i32::MAX)).contains(&r)
                            && (r == 0) == (op.state == "succeeded")
                    })
                    && op.errno.is_none()
            }
            Some("mapping") => {
                matches!(op.state.as_str(), "succeeded" | "failed")
                    && op.native_rc.is_none()
                    && if op.state == "failed" {
                        op.errno.is_some_and(|e| e >= 0)
                    } else {
                        op.errno.is_none()
                    }
            }
            Some("symbol") => {
                matches!(op.state.as_str(), "available" | "unavailable")
                    && op.native_rc.is_none()
                    && op.errno.is_none()
            }
            Some("validation") => {
                matches!(op.state.as_str(), "accepted" | "rejected")
                    && op.native_rc.is_none()
                    && op.errno.is_none()
            }
            Some("memory") => {
                op.state == "performed" && op.native_rc.is_none() && op.errno.is_none()
            }
            _ => false,
        };
        require(out, valid, "setup native result or errno");
    }
    if let Some(primary) = s.primary_operation {
        require(
            out,
            primary >= 0
                && s.operations.iter().any(|op| {
                    op.slot == primary
                        && op.role == "setup"
                        && matches!(op.state.as_str(), "failed" | "rejected")
                }),
            "setup primary operation lacks independent failure",
        );
    }
    let mut owners = BTreeSet::new();
    for (name, state) in &s.ownership.0 {
        let erase = matches!(name.as_str(), "shared_erasure" | "private_erasure");
        require(
            out,
            owners.insert(name)
                && if erase {
                    [
                        "not_present",
                        "performed",
                        "withheld_not_quiescent",
                        "unobserved",
                    ]
                    .contains(&state.as_str())
                } else {
                    ["object_name", "descriptor", "mapping"].contains(&name.as_str())
                        && ["not_acquired", "held", "released", "unresolved"]
                            .contains(&state.as_str())
                },
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
            require(
                out,
                s.operations
                    .iter()
                    .any(|op| ops.contains(&op.operation.as_str()) && op.state == "succeeded"),
                "released setup ownership lacks successful cleanup",
            );
        }
        if erase && state == "performed" {
            require(
                out,
                s.operations.iter().any(|op| {
                    matches!(
                        op.operation.as_str(),
                        "shared_clear" | "final_erase" | "terminal_owned_inbound_clear"
                    ) && op.state == "performed"
                }),
                "setup erasure lacks performed observation",
            );
        }
    }
    if let Some(r) = &s.cleanup_reference {
        require(
            out,
            family == "region"
                && r.kind == "posix_shm_name"
                && bounded(&r.name, 31)
                && r.name.is_ascii()
                && r.name.starts_with('/')
                && pid(r.host_pid)
                && r.recovery_state == "unresolved_manual"
                && s.ownership
                    .0
                    .iter()
                    .any(|(n, s)| n == "object_name" && s == "unresolved")
                && s.operations
                    .iter()
                    .any(|op| op.operation == "shm_open" && op.state == "succeeded")
                && s.operations
                    .iter()
                    .any(|op| op.operation == "shm_unlink" && op.state == "failed"),
            "unresolved setup cleanup lacks owned creation",
        );
    }
}
fn setup(reply: &PWRunnerRunResult, actors: &[PWRunnerActorResult], out: &mut Vec<IntegrityIssue>) {
    let Some(s) = &reply.authority_setup else {
        require(out, false, "actor form lacks automatic authority setup");
        return;
    };
    scope(&s.host.run, &["core_limit"], "run", out);
    require(
        out,
        s.host.regions.len() <= 8 && s.host.custody.len() <= 32 && s.workers.len() == actors.len(),
        "authority setup table capacity",
    );
    let tokens = reply
        .resources
        .as_ref()
        .map(|r| r.tokens.as_slice())
        .unwrap_or(&[]);
    let mut seen = BTreeSet::new();
    for r in &s.host.regions {
        scope(r, REGION_OPS, "region", out);
        require(
            out,
            r.actor_index
                .and_then(|i| usize::try_from(i).ok())
                .and_then(|i| actors.get(i))
                .is_some_and(|a| Some(a.actor_id.as_str()) == r.actor_id.as_deref())
                && seen.insert(r.actor_index),
            "host setup actor association",
        );
    }
    let mut seen = BTreeSet::new();
    for r in &s.host.custody {
        scope(r, CUSTODY_OPS, "custody", out);
        require(
            out,
            r.token_index
                .and_then(|i| usize::try_from(i).ok())
                .and_then(|i| tokens.get(i))
                .is_some_and(|t| Some(t.token_ref.as_str()) == r.token_ref.as_deref())
                && seen.insert(r.token_index),
            "custody setup token association",
        );
    }
    for (i, r) in s.workers.iter().enumerate() {
        scope(r, WORKER_OPS, "worker", out);
        require(
            out,
            actors
                .get(i)
                .is_some_and(|a| Some(a.actor_id.as_str()) == r.actor_id.as_deref())
                && r.actor_index == Some(i as i64)
                && r.required.is_some(),
            "worker setup actor association",
        );
        require(
            out,
            matches!(r.publication.as_deref(), Some("observed" | "not_observed")),
            "worker setup publication",
        );
        if r.publication.as_deref() == Some("not_observed") {
            require(
                out,
                r.disposition.is_none() && r.primary_operation.is_none(),
                "unpublished setup decision carries values",
            );
        } else {
            require(
                out,
                matches!(
                    r.disposition.as_deref(),
                    Some("ready" | "not_required" | "terminal_required_failure")
                ),
                "worker setup disposition",
            );
            if r.disposition.as_deref() == Some("terminal_required_failure") {
                require(
                    out,
                    r.required == Some(true) && r.primary_operation.is_some_and(|p| p >= 0),
                    "terminal setup refusal lacks required primary failure",
                );
            }
        }
    }
}
fn application(
    a: &PWRunnerActorResult,
    s: Option<&PWRunnerAuthorityScope>,
    out: &mut Vec<IntegrityIssue>,
) {
    let Some(assessment) = &a.application else {
        require(out, false, "invalid application assessment");
        return;
    };
    let applied = a.applied == Some(true);
    require(
        out,
        matches!(a.application_count, 0 | 1) && (a.application_count == 1) == applied,
        "application count contradicts successful publication",
    );
    let evidence = a
        .subprocess
        .as_ref()
        .and_then(|s| s.worker_evidence.as_ref());
    let failure = evidence.and_then(|e| e.failure.as_ref());
    let published = evidence.is_some_and(|e| e.failure_state == "published");
    let matches_failure = |op, code, kind| {
        published
            && failure.is_some_and(|f| f.operation == op && f.code == code && f.native_kind == kind)
    };
    let input_refusal = published
        && failure.is_some_and(|f| {
            f.operation == 1 && matches!(f.code, 4 | 7 | 10 | 12) && f.native_kind == 0
                || f.operation == 2 && matches!(f.code, 2 | 3 | 9 | 13)
        });
    let parameter_refusal = matches_failure(1, 5, 0)
        || matches_failure(3, 1, 2)
        || matches_failure(4, 1, 1)
        || matches_failure(4, 6, 0);
    let timing_refusal = matches_failure(12, 1, 1)
        || matches_failure(12, 14, 0)
        || matches_failure(12, 15, 0) && failure.is_some_and(|f| f.detail == 1);
    let terminal = s.is_some_and(|s| {
        s.publication.as_deref() == Some("observed")
            && s.disposition.as_deref() == Some("terminal_required_failure")
    });
    let valid = match (assessment.state.as_str(), assessment.basis.as_str()) {
        ("not_requested", "unapplied_declaration") => a.mode == "unapplied" && !applied,
        ("not_attempted", "worker_not_launched") => {
            a.mode == "apply"
                && matches!(
                    a.setup_status.as_str(),
                    "launch_refused" | "setup_timeout" | "not_launched"
                )
                && !applied
                && a.subprocess.is_none()
                && a.launch.is_none()
        }
        ("not_attempted", "terminal_authority_setup_refusal") => {
            a.mode == "apply" && terminal && !applied
        }
        ("not_attempted", "terminal_input_refusal") => {
            a.mode == "apply" && input_refusal && !applied
        }
        ("not_attempted", "terminal_parameter_refusal") => {
            a.mode == "apply" && parameter_refusal && !applied
        }
        ("not_attempted", "terminal_compile_refusal") => {
            a.mode == "apply" && matches_failure(5, 1, 2) && !applied
        }
        ("not_attempted", "terminal_timing_refusal") => {
            a.mode == "apply" && timing_refusal && !applied
        }
        ("observed", "applied_publication") => a.mode == "apply" && applied,
        ("observed", "apply_failure_publication") => {
            a.mode == "apply"
                && matches_failure(8, 1, 1)
                && failure.is_some_and(|f| f.native_result.is_some_and(|r| r != 0))
                && !applied
        }
        ("unobserved", "apply_call_boundary_without_result") => {
            a.mode == "apply"
                && evidence
                    .and_then(|e| e.progress.as_ref())
                    .is_some_and(|p| p.operation == 8 && matches!(p.stage, 1 | 2))
                && !applied
        }
        ("unobserved", "no_eligible_apply_publication") => {
            a.mode == "apply" && !applied && !terminal
        }
        _ => false,
    };
    require(
        out,
        valid,
        "application assessment lacks its eligible source",
    );
    let terminal_eligible = terminal && s.is_some_and(|s| s.integrity_errors.is_none());
    let expected = if a.mode == "unapplied" {
        ("not_requested", "unapplied_declaration")
    } else if a.launch.is_none() {
        ("not_attempted", "worker_not_launched")
    } else if applied {
        ("observed", "applied_publication")
    } else if terminal_eligible {
        ("not_attempted", "terminal_authority_setup_refusal")
    } else if matches_failure(8, 1, 1)
        && failure.is_some_and(|f| f.native_result.is_some_and(|r| r != 0))
    {
        ("observed", "apply_failure_publication")
    } else if input_refusal {
        ("not_attempted", "terminal_input_refusal")
    } else if parameter_refusal {
        ("not_attempted", "terminal_parameter_refusal")
    } else if matches_failure(5, 1, 2) {
        ("not_attempted", "terminal_compile_refusal")
    } else if timing_refusal {
        ("not_attempted", "terminal_timing_refusal")
    } else if evidence
        .and_then(|e| e.progress.as_ref())
        .is_some_and(|p| p.operation == 8 && matches!(p.stage, 1 | 2))
    {
        ("unobserved", "apply_call_boundary_without_result")
    } else {
        ("unobserved", "no_eligible_apply_publication")
    };
    require(
        out,
        (assessment.state.as_str(), assessment.basis.as_str()) == expected,
        "application assessment violates source precedence",
    );
    require(
        out,
        !applied
            || (a.mode != "unapplied"
                && a.launch.is_some()
                && !terminal
                && !(published
                    && failure.is_some_and(|f| matches!(f.operation, 1 | 2 | 3 | 4 | 5 | 8 | 12)))),
        "contradictory application publication",
    );
}
fn equipment(
    reply: &PWRunnerRunResult,
    actors: &[PWRunnerActorResult],
    out: &mut Vec<IntegrityIssue>,
) {
    let (Some(inv), Some(bindings), Some(reads)) = (
        &reply.equipment_inventory,
        &reply.equipment_bindings,
        &reply.equipment_entitlements,
    ) else {
        require(out, false, "equipment table type or capacity");
        return;
    };
    require(
        out,
        matches!(inv.status.as_str(), "verified" | "refused" | "unobserved")
            && bindings.len() <= 4
            && reads.len() <= 12,
        "equipment table type or capacity",
    );
    if inv.status == "verified" {
        require(
            out,
            inv.schema_version == Some(1)
                && digest(inv.sha256.as_deref(), 32)
                && digest(inv.worker_identity.as_deref(), 32)
                && digest(inv.unsigned_worker_sha256.as_deref(), 32)
                && inv.seal_osstatus == Some(0),
            "verified equipment inventory lacks sealed identity",
        );
    }
    equipment_bounds(reply, actors, out);
    // Rows are named by table position. A binding is identified by its role
    // and source; a read-back by the binding row or the actor it belongs to.
    let mut identities = BTreeSet::new();
    for b in bindings {
        require(
            out,
            identities.insert((b.role.as_str(), b.source.as_str())),
            "duplicate equipment binding",
        );
    }
    let mut owners = BTreeSet::new();
    let mut dictionaries = BTreeMap::new();
    for (index, r) in reads.iter().enumerate() {
        let binding = bindings.get(r.binding_ref as usize);
        require(out, binding.is_some(), "entitlement read-back binding");
        let owner = match r.source.as_str() {
            "binding" => (r.actor_id.is_none()
                && binding.is_some_and(|b| b.entitlements_ref == Some(index as u32)))
            .then_some(("binding", r.binding_ref as usize)),
            "execution" => actors
                .iter()
                .position(|a| Some(a.actor_id.as_str()) == r.actor_id.as_deref())
                .map(|i| ("execution", i)),
            _ => None,
        };
        require(
            out,
            owner.is_some(),
            "entitlement read-back actor or identity",
        );
        if let Some(owner) = owner {
            require(out, owners.insert(owner), "duplicate equipment read-back");
        }
        if r.status == "observed" {
            if let Some(d) = r.raw_plist.as_deref().and_then(plist::Dictionary::read) {
                dictionaries.insert(index, d);
            } else {
                require(out, false, "invalid or oversized entitlement plist");
            }
        } else {
            require(
                out,
                r.status == "failed" && r.raw_plist.is_none(),
                "failed entitlement observation invents plist",
            );
        }
    }
    for (index, b) in bindings.iter().enumerate() {
        let instrumented = b.source == "test_override";
        let role = b.role.as_str();
        require(
            out,
            ["selected", "unentitled"].contains(&role),
            "equipment role association",
        );
        let expected = if role == "selected" {
            "Contents/MacOS/pw-probe-runner"
        } else {
            "Contents/MacOS/pw-probe-runner-unentitled"
        };
        require(
            out,
            bounded(&b.path, 1023)
                && if instrumented {
                    b.implementation_identity == "unverified_fixture"
                        && b.relative_path.is_none()
                        && b.expected_sha256.is_none()
                        && b.expected_cdhash.is_none()
                } else {
                    b.source == "packaged"
                        && b.implementation_identity == "inventory_verified"
                        && b.relative_path.as_deref() == Some(expected)
                },
            "equipment fixed path association",
        );
        if b.status == "bound" {
            let own = b.entitlements_ref.map(|n| n as usize);
            require(
                out,
                inv.status == "verified"
                    && digest(b.sha256.as_deref(), 32)
                    && (instrumented || b.sha256 == b.expected_sha256)
                    && digest(b.cdhash.as_deref(), 20)
                    && (instrumented || b.cdhash == b.expected_cdhash)
                    && b.signature_osstatus == Some(0)
                    && (instrumented || b.entitlements_match == Some(true))
                    && own
                        .and_then(|n| reads.get(n))
                        .is_some_and(|r| r.source == "binding" && r.binding_ref as usize == index)
                    && own.is_some_and(|n| dictionaries.contains_key(&n)),
                "bound equipment lacks inspected identity",
            );
            if role == "unentitled" && !instrumented {
                require(
                    out,
                    own.and_then(|n| dictionaries.get(&n))
                        .is_some_and(plist::Dictionary::empty),
                    "unentitled worker carries entitlements",
                );
            }
        } else {
            require(
                out,
                b.status == "refused",
                "invalid equipment binding status",
            );
        }
    }
    let mut runtime_failed = false;
    for a in actors.iter() {
        let Some(e) = &a.equipment else {
            require(out, false, "actor equipment selector association");
            continue;
        };
        // The actor names its binding row when one exists for its role.
        let b = e.binding_ref.and_then(|n| bindings.get(n as usize));
        require(
            out,
            ["selected", "unentitled"].contains(&e.resolved.as_str())
                && (b.is_some_and(|b| b.role == e.resolved)
                    || e.binding_ref.is_none() && !bindings.iter().any(|b| b.role == e.resolved))
                && (e.requested.is_none() && e.resolved == "selected"
                    || e.requested.as_deref() == Some(e.resolved.as_str())),
            "actor equipment selector association",
        );
        let required: BTreeSet<&str> = e.required_entitlements.iter().map(String::as_str).collect();
        require(
            out,
            e.required_entitlements.len() <= 64
                && required.len() == e.required_entitlements.len()
                && e.required_entitlements.iter().all(|s| bounded(s, 255)),
            "invalid actor entitlement requirements",
        );
        let static_ref = b.and_then(|b| b.entitlements_ref).map(|n| n as usize);
        let granted = static_ref
            .and_then(|n| dictionaries.get(&n))
            .map(plist::Dictionary::granted);
        let missing: BTreeSet<&str> = required
            .iter()
            .copied()
            .filter(|key| !granted.as_ref().is_some_and(|g| g.contains(*key)))
            .collect();
        match e.requirements_status.as_str() {
            "satisfied" | "unsatisfied" => require(
                out,
                granted.is_some()
                    && e.missing_requirements.as_ref().is_some_and(|m| {
                        m.len() == missing.len()
                            && m.iter().map(String::as_str).collect::<BTreeSet<_>>() == missing
                    })
                    && (e.requirements_status == "satisfied") == missing.is_empty(),
                "actor requirements disagree with observed entitlements",
            ),
            "unobserved" => require(
                out,
                e.missing_requirements.is_none(),
                "unobserved actor requirements invent result",
            ),
            _ => require(out, false, "invalid actor requirement disposition"),
        }
        let x = &e.execution;
        require(
            out,
            ["matched", "mismatched", "inspection_failed", "unobserved"]
                .contains(&x.status.as_str()),
            "invalid execution equipment status",
        );
        if x.status == "matched" {
            let live_ref = x.entitlements_ref.map(|n| n as usize);
            let read = live_ref.and_then(|n| reads.get(n));
            let static_plist = static_ref.and_then(|n| dictionaries.get(&n));
            let live_plist = live_ref.and_then(|n| dictionaries.get(&n));
            let live_granted = live_plist.map(plist::Dictionary::granted);
            require(
                out,
                b.is_some_and(|b| {
                    b.status == "bound"
                        && x.path.as_deref() == Some(b.path.as_str())
                        && x.cdhash == b.cdhash
                        && x.identifier == b.identifier
                        && x.team_id == b.team_id
                }) && e.requirements_status == "satisfied"
                    && x.eligible
                    && x.reason.is_none()
                    && x.pid.is_some_and(pid)
                    && x.pid == a.launch.as_ref().map(|l| l.pid)
                    && read.is_some_and(|r| {
                        r.source == "execution"
                            && Some(r.binding_ref) == e.binding_ref
                            && r.actor_id.as_deref() == Some(a.actor_id.as_str())
                    })
                    && static_plist
                        .zip(live_plist)
                        .is_some_and(|(s, l)| s.equal(l))
                    && live_granted
                        .as_ref()
                        .is_some_and(|keys| required.iter().all(|k| keys.contains(*k))),
                "execution equipment does not match its owned binding",
            );
            require(
                out,
                x.native_observations.len() == 4
                    && [
                        "guest_code",
                        "dynamic_validity",
                        "associated_static_code",
                        "signing_information",
                    ]
                    .iter()
                    .zip(&x.native_observations)
                    .all(|(name, c)| c.operation == *name && c.attempted && c.osstatus == Some(0)),
                "matched execution lacks native inspection results",
            );
        } else {
            require(out, !x.eligible, "unmatched equipment permits activation");
            runtime_failed |= a.launch.is_some()
                && matches!(x.status.as_str(), "mismatched" | "inspection_failed");
        }
    }
    if runtime_failed {
        require(
            out,
            reply.normalized_outcome != "finished"
                && reply.preparation_failure.is_none()
                && reply
                    .schedule
                    .as_ref()
                    .and_then(|s| s.cancelled.as_deref())
                    .is_some_and(|s| bounded(s, 64))
                && reply.phases.iter().all(|p| {
                    !p.ordering
                        .as_ref()
                        .is_some_and(|o| o.proceed_set || o.proceed_observed)
                        && p.activation_observation.is_none()
                        && !p.arrival_observed
                        && !p.completion_observed
                        && p.validator_subprocess.is_none()
                        && p.collection_status == "not_reached"
                }),
            "runtime equipment refusal lost evidence or enabled schedule",
        );
    }
}
fn owned_reap_valid(a: &PWRunnerActorResult) -> bool {
    let (Some(r), Some(s), Some(l)) = (&a.owned_reap, &a.subprocess, &a.launch) else {
        return false;
    };
    let matches = if libc::WIFEXITED(r.raw_status) {
        s.exit_code == Some(i64::from(libc::WEXITSTATUS(r.raw_status))) && s.term_signal.is_none()
    } else if libc::WIFSIGNALED(r.raw_status) {
        s.term_signal == Some(i64::from(libc::WTERMSIG(r.raw_status))) && s.exit_code.is_none()
    } else {
        false
    };
    pid(r.pid)
        && r.raw_status >= 0
        && i64::from(r.native_rc) == r.pid
        && l.pid == r.pid
        && s.pid == r.pid
        && s.reaped == Some(true)
        && matches
        && r.capture_ordinal > 0
        && bounded(&r.stage, 64)
}
fn gates(reply: &PWRunnerRunResult, actors: &[PWRunnerActorResult], out: &mut Vec<IntegrityIssue>) {
    for a in actors {
        if a.owned_reap.is_some() {
            require(
                out,
                owned_reap_valid(a),
                "owned reap disagrees with child identity or wait status",
            );
        }
    }
    for (i, p) in reply.phases.iter().enumerate() {
        if let Some(a) = &p.activation_observation {
            require(
                out,
                a.capture_ordinal > 0,
                "invalid phase activation observation",
            );
        }
        let Some(g) = &p.termination_gate else {
            continue;
        };
        if g.outcome == "not_reached" {
            require(
                out,
                g.observation.is_none() && g.capture_ordinal.is_none() && g.wait.is_none(),
                "unreached termination gate fabricates capture",
            );
        }
        if let Some(wait) = &g.wait {
            require(
                out,
                (0..=5000).contains(&wait.budget_ms) && wait.excluded_ms.is_none(),
                "termination gate wait budget or accounting",
            );
        }
        require(
            out,
            g.activation_eligible
                || (p.activation_observation.is_none()
                    && p.visit_timing.is_none()
                    && !p.arrival_observed
                    && p.collection_status == "not_reached"
                    && !p
                        .ordering
                        .as_ref()
                        .is_some_and(|o| o.proceed_set || o.proceed_observed)),
            "activation before termination gate eligibility",
        );
        let source = actors.iter().find(|a| a.actor_id == g.source_actor_id);
        let final_phase = reply
            .phases
            .iter()
            .position(|p| p.phase_id == g.source_final_phase_id);
        require(
            out,
            g.condition == "terminated"
                && source.is_some()
                && Some(g.source_actor_id.as_str()) != p.actor_id.as_deref()
                && final_phase.is_some_and(|j| {
                    j < i
                        && reply.phases[j].actor_id.as_deref() == Some(g.source_actor_id.as_str())
                        && !reply.phases[j + 1..]
                            .iter()
                            .any(|p| p.actor_id.as_deref() == Some(g.source_actor_id.as_str()))
                }),
            "termination dependency source or ordering",
        );
        require(
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
            .contains(&g.outcome.as_str()),
            "termination gate outcome",
        );
        if g.outcome != "not_reached" {
            require(
                out,
                g.wait.as_ref().is_some_and(|w| {
                    (0..=5000).contains(&w.budget_ms)
                        && w.stop == g.outcome
                        && w.excluded_ms.is_none()
                }),
                "termination gate wait budget or accounting",
            );
        }
        let reap = source.and_then(|a| a.owned_reap.as_ref());
        if let Some(observation) = &g.observation {
            require(
                out,
                observation.capture_ordinal > 0
                    && reap.is_some_and(|r| {
                        r.capture_ordinal == observation.capture_ordinal
                            && g.capture_ordinal.is_some_and(|g| r.capture_ordinal < g)
                    })
                    && source.is_some_and(owned_reap_valid),
                "termination gate observation does not resolve to its source owned reap",
            );
        }
        if g.outcome == "satisfied" {
            let activation =
                final_phase.and_then(|j| reply.phases[j].activation_observation.as_ref());
            let order = activation.zip(reap).is_some_and(|(a, r)| {
                a.capture_ordinal < r.capture_ordinal
                    && g.capture_ordinal.is_some_and(|g| r.capture_ordinal < g)
            });
            let time = activation
                .and_then(|a| a.observed_ns)
                .zip(reap.and_then(|r| r.observed_ns))
                .is_some_and(|(a, r)| a <= r);
            require(
                out,
                source.is_some_and(owned_reap_valid)
                    && reap.is_some_and(|r| {
                        r.ownership_unbroken
                            && !r.departure_requested
                            && matches!(r.stage.as_str(), "schedule" | "termination_gate")
                    })
                    && g.observation
                        .as_ref()
                        .zip(reap)
                        .is_some_and(|(o, r)| o.capture_ordinal == r.capture_ordinal)
                    && order
                    && time,
                "satisfied termination gate lacks natural owned reap after final activation",
            );
            require(
                out,
                g.wait.as_ref().is_some_and(|w| {
                    (1..=5000).contains(&w.budget_ms)
                        && !w.clock_fault
                        && w.native_errno.is_none()
                        && w.elapsed_ms.is_some_and(|e| e <= w.budget_ms as u64)
                }),
                "satisfied termination gate lacks a timely clocked wait",
            );
            if let Some(a) = &p.activation_observation {
                require(
                    out,
                    a.observed_ns.is_none()
                        || reap
                            .and_then(|r| r.observed_ns)
                            .zip(a.observed_ns)
                            .is_some_and(|(r, a)| r <= a),
                    "dependent activation precedes owned termination",
                );
            }
        } else {
            require(
                out,
                !g.activation_eligible
                    && p.activation_observation.is_none()
                    && !p
                        .ordering
                        .as_ref()
                        .is_some_and(|o| o.proceed_set || o.proceed_observed)
                    && p.collection_status == "not_reached",
                "failed termination gate enabled collection or release",
            );
        }
        if g.activation_eligible {
            require(
                out,
                g.outcome == "satisfied"
                    && actors.iter().any(|a| {
                        Some(a.actor_id.as_str()) == p.actor_id.as_deref()
                            && matches!(a.setup_status.as_str(), "applied" | "unapplied_declared")
                            && a.equipment.as_ref().is_some_and(|e| e.execution.eligible)
                    }),
                "termination gate eligibility lacks independent setup",
            );
        }
    }
}
fn preparation_failure_valid(reply: &PWRunnerRunResult) -> bool {
    let Some(f) = &reply.preparation_failure else {
        return false;
    };
    let actors = reply.actors.as_deref().unwrap_or(&[]);
    let identities: Vec<&str> = reply
        .phases
        .iter()
        .flat_map(|p| p.action_ids.iter().map(String::as_str))
        .collect();
    matches!(
        (f.stage.as_str(), f.code.as_str()),
        ("resolved_plan", "inconsistent_assignment") | ("equipment", "equipment_binding_refused")
    ) && reply.execution_form.as_deref() == Some("actors")
        && reply.normalized_outcome == "runner_failed"
        && reply.rc == 1
        && !actors.is_empty()
        && actors.iter().all(|a| {
            a.setup_status == "launch_refused" && a.launch.is_none() && a.subprocess.is_none()
        })
        && reply.steps.is_empty()
        && reply.extension_events.as_ref().is_some_and(Vec::is_empty)
        && reply.transfers.as_ref().is_some_and(Vec::is_empty)
        && reply
            .resources
            .as_ref()
            .is_none_or(|r| r.tokens.is_empty() && r.deliveries.is_empty() && r.handles.is_empty())
        && reply
            .authority_setup
            .as_ref()
            .is_some_and(|s| s.host.run.disposition.as_deref() == Some("not_attempted"))
        && reply.request_failure.is_none()
        && reply.phases.iter().all(|p| {
            p.collection_status == "not_reached"
                && !p
                    .ordering
                    .as_ref()
                    .is_some_and(|o| o.proceed_set || o.proceed_observed)
        })
        && reply
            .authority_setup
            .as_ref()
            .is_some_and(|s| s.host.regions.is_empty() && s.host.custody.is_empty())
        && reply
            .phases
            .iter()
            .all(|p| !p.arrival_observed && !p.completion_observed)
        && identities.len() <= 256
        && identities.iter().all(|id| bounded(id, 63))
        && identities.iter().collect::<BTreeSet<_>>().len() == identities.len()
}
fn unpublished_status(e: &PWRunnerExtensionEvent) -> &'static str {
    if e.lifecycle.as_ref().is_some_and(|l| {
        l.boundary.state == "supported" && l.boundary.answer.as_deref() == Some("not_reached")
    }) && !e.call_boundary_observed
    {
        "not_reached"
    } else {
        "unresolved"
    }
}
fn transfer_status(s: &str) -> bool {
    matches!(
        s,
        "none"
            | "delivered"
            | "custody_unavailable"
            | "recipient_rejected"
            | "recipient_timeout"
            | "recipient_unavailable"
            | "request_invalid"
            | "host_timeout"
            | "clock_fault"
            | "copy_mismatch"
    )
}
fn custody(
    reply: &PWRunnerRunResult,
    actors: &[PWRunnerActorResult],
    out: &mut Vec<IntegrityIssue>,
) {
    let (Some(resources), Some(transfers)) = (&reply.resources, &reply.transfers) else {
        require(
            out,
            false,
            "actor form lacks actor, resource or transfer tables",
        );
        return;
    };
    let events = reply.extension_events.as_deref().unwrap_or(&[]);
    require(
        out,
        reply.runner_subprocess.is_none()
            && reply.policy_sha256.is_none()
            && reply.sandboxed_after_apply.is_none(),
        "actor form carries singular projections",
    );
    if actors.is_empty()
        || actors.len() > 8
        || resources.tokens.len() > 32
        || resources.deliveries.len() > 64
        || resources.handles.len() > 64
        || transfers.len() > 64
        || events.len() > 288
    {
        require(out, false, "actor extension record capacity");
        return;
    }
    for a in actors {
        require(
            out,
            matches!(a.application_count, 0 | 1)
                && (a.application_count == 1) == (a.applied == Some(true))
                && (a.setup_status != "applied" || a.applied == Some(true)),
            "application count contradicts application publication",
        );
    }
    let mut references = BTreeSet::new();
    for t in &resources.tokens {
        require(
            out,
            bounded(&t.token_ref, 63) && references.insert(t.token_ref.as_str()),
            "resource and transfer references must be unique",
        );
    }
    references.clear();
    for d in &resources.deliveries {
        require(
            out,
            bounded(&d.delivery_ref, 63) && references.insert(d.delivery_ref.as_str()),
            "resource and transfer references must be unique",
        );
    }
    references.clear();
    for h in &resources.handles {
        require(
            out,
            bounded(&h.handle_ref, 63) && references.insert(h.handle_ref.as_str()),
            "resource and transfer references must be unique",
        );
    }
    references.clear();
    for t in transfers {
        require(
            out,
            bounded(&t.delivery_ref, 63) && references.insert(t.delivery_ref.as_str()),
            "resource and transfer references must be unique",
        );
    }
    let ids: Vec<&str> = reply
        .phases
        .iter()
        .flat_map(|p| p.action_ids.iter().map(String::as_str))
        .collect();
    let before = |a: &str, b: &str| {
        ids.iter()
            .position(|id| *id == a)
            .zip(ids.iter().position(|id| *id == b))
            .is_some_and(|(a, b)| a < b)
    };
    let reference = |s: Option<&str>| s.is_some_and(|s| bounded(s, 63));
    let mut consumed: BTreeMap<&str, &PWRunnerExtensionEvent> = BTreeMap::new();
    let mut released = BTreeSet::new();
    for e in events {
        let Some(a) = actors
            .iter()
            .find(|a| Some(a.actor_id.as_str()) == e.actor_id.as_deref())
        else {
            require(out, false, "extension event actor");
            continue;
        };
        let Some(p) = reply.phases.iter().find(|p| {
            p.phase_id == e.phase_id
                && p.action_ids.contains(&e.step_id)
                && p.actor_id == e.actor_id
        }) else {
            require(out, false, "extension event phase association");
            continue;
        };
        if e.family.as_deref() != Some("file") {
            require(out, false, "extension event family");
            continue;
        }
        match e.operation.as_str() {
            "issue" => {
                require(
                    out,
                    reference(e.token_ref.as_deref())
                        && resources.tokens.iter().any(|t| {
                            Some(t.token_ref.as_str()) == e.token_ref.as_deref()
                                && t.actor_id == a.actor_id
                                && t.step_id == e.step_id
                        })
                        && e.handle_ref.is_none()
                        && e.delivery_ref.is_none(),
                    "issue reference",
                );
                if e.status == "returned" {
                    require(
                        out,
                        matches!(e.native_result, Some(0 | 1))
                            && e.native_nonnull == Some(e.native_result == Some(1)),
                        "issue nonnull disagrees with native result",
                    );
                }
            }
            "transfer" => {
                require(
                    out,
                    reference(e.token_ref.as_deref())
                        && reference(e.delivery_ref.as_deref())
                        && resources.deliveries.iter().any(|d| {
                            Some(d.delivery_ref.as_str()) == e.delivery_ref.as_deref()
                                && Some(d.token_ref.as_str()) == e.token_ref.as_deref()
                                && d.source_actor_id == a.actor_id
                                && d.step_id == e.step_id
                        })
                        && e.handle_ref.is_none(),
                    "transfer reference",
                );
                require(
                    out,
                    resources.tokens.iter().any(|t| {
                        Some(t.token_ref.as_str()) == e.token_ref.as_deref()
                            && t.actor_id == a.actor_id
                            && before(&t.step_id, &e.step_id)
                    }),
                    "transfer token owner/order",
                );
                require(
                    out,
                    !e.call_boundary_observed && e.native_result.is_none() && e.errno.is_none(),
                    "transfer carries a native result",
                );
                require(
                    out,
                    if e.status == "unresolved" {
                        !e.result_published
                    } else {
                        e.result_published && transfer_status(&e.status)
                    },
                    "transfer status",
                );
            }
            "consume" => {
                require(
                    out,
                    reference(e.delivery_ref.as_deref())
                        && reference(e.handle_ref.as_deref())
                        && resources.handles.iter().any(|h| {
                            Some(h.handle_ref.as_str()) == e.handle_ref.as_deref()
                                && Some(h.delivery_ref.as_str()) == e.delivery_ref.as_deref()
                                && h.actor_id == a.actor_id
                                && h.step_id == e.step_id
                        })
                        && e.token_ref.is_none()
                        && !consumed.contains_key(e.handle_ref.as_deref().unwrap_or("")),
                    "consume reference",
                );
                require(
                    out,
                    resources.deliveries.iter().any(|d| {
                        Some(d.delivery_ref.as_str()) == e.delivery_ref.as_deref()
                            && d.recipient_actor_id == a.actor_id
                            && before(&d.step_id, &e.step_id)
                    }),
                    "consume delivery recipient/order",
                );
                if let Some(handle) = e.handle_ref.as_deref() {
                    consumed.insert(handle, e);
                }
            }
            "release" => {
                let handle = e.handle_ref.as_deref().unwrap_or("");
                let prior = consumed.get(handle).copied();
                require(
                    out,
                    reference(e.handle_ref.as_deref())
                        && e.token_ref.is_none()
                        && e.delivery_ref.is_none()
                        && resources.handles.iter().any(|h| {
                            h.handle_ref == handle
                                && h.actor_id == a.actor_id
                                && h.release_step_id.as_deref() == Some(e.step_id.as_str())
                        })
                        && !released.contains(handle)
                        && prior.is_some_and(|p| before(&p.step_id, &e.step_id)),
                    "release reference/order",
                );
                released.insert(handle);
                if e.status == "returned" {
                    require(
                        out,
                        prior.is_some_and(|p| {
                            p.status == "returned" && p.native_result.is_some_and(|r| r != -1)
                        }),
                        "release lacks an observed consume handle",
                    );
                }
            }
            _ => {
                require(out, false, "unknown extension operation");
                continue;
            }
        }
        if e.operation != "transfer" {
            let valid = match e.status.as_str() {
                "returned" => {
                    e.result_published
                        && e.call_boundary_observed
                        && e.native_result.is_some()
                        && e.errno.is_some_and(|e| e >= 0)
                        && e.unavailable_reason.is_none()
                }
                "unavailable" => {
                    e.result_published
                        && !e.call_boundary_observed
                        && e.native_result.is_none()
                        && e.errno.is_none()
                        && matches!(
                            e.unavailable_reason.as_deref(),
                            Some(
                                "token_unavailable"
                                    | "handle_unavailable"
                                    | "native_api_unavailable"
                                    | "repeated_action"
                                    | "authority_channel_unavailable"
                                    | "delivery_unavailable"
                            )
                        )
                }
                "unresolved" => {
                    !e.result_published
                        && e.native_result.is_none()
                        && e.errno.is_none()
                        && e.unavailable_reason.is_none()
                }
                _ => false,
            };
            require(
                out,
                valid,
                "extension status contradicts native call or publication",
            );
        }
        let record = a
            .subprocess
            .as_ref()
            .and_then(|s| s.disposition.as_ref())
            .and_then(|d| d.steps.iter().find(|s| s.step_id == e.step_id));
        if let Some(d) = record {
            require(
                out,
                e.result_published == (d.slot == "completed")
                    && e.lifecycle.as_ref().is_some_and(|l| {
                        Some(&l.boundary) == d.questions.step_boundary_reached.as_ref()
                            && Some(&l.result) == d.questions.step_result_published.as_ref()
                    }),
                "extension publication disagrees with disposition",
            );
        } else {
            require(
                out,
                a.subprocess.is_none()
                    && !e.call_boundary_observed
                    && !e.result_published
                    && e.lifecycle.is_none(),
                "extension event lacks disposition",
            );
        }
        if e.result_published || e.call_boundary_observed {
            require(
                out,
                p.ordering.as_ref().is_some_and(|o| o.proceed_observed)
                    && matches!(a.setup_status.as_str(), "applied" | "unapplied_declared"),
                "extension publication lacks setup and phase acknowledgement",
            );
        }
    }
    for t in transfers {
        require(
            out,
            resources.deliveries.iter().any(|d| {
                d.delivery_ref == t.delivery_ref
                    && d.token_ref == t.token_ref
                    && d.source_actor_id == t.source_actor_id
                    && d.recipient_actor_id == t.recipient_actor_id
                    && d.step_id == t.step_id
            }) && transfer_status(&t.status),
            "transfer record association",
        );
        require(
            out,
            events.iter().any(|e| {
                e.operation == "transfer"
                    && e.delivery_ref.as_deref() == Some(t.delivery_ref.as_str())
                    && e.phase_id == t.phase_id
                    && e.lifecycle == t.lifecycle
            }),
            "transfer source phase/lifecycle association",
        );
        if t.status == "delivered" {
            require(
                out,
                t.request_published
                    && t.custody_status == "held"
                    && t.copy_status == "copied"
                    && t.equality == "equal"
                    && t.recipient_acknowledged,
                "delivered transfer lacks custody, copy or recipient acknowledgement",
            );
        }
        if t.source_acknowledged {
            require(
                out,
                events.iter().any(|e| {
                    e.operation == "transfer"
                        && e.step_id == t.step_id
                        && e.actor_id.as_deref() == Some(t.source_actor_id.as_str())
                        && e.result_published
                        && e.status == t.status
                }),
                "source acknowledgement lacks matching publication",
            );
        }
    }
    for t in &resources.tokens {
        let matching: Vec<_> = events
            .iter()
            .filter(|e| {
                e.operation == "issue" && e.token_ref.as_deref() == Some(t.token_ref.as_str())
            })
            .collect();
        if matching.len() != 1 {
            require(out, false, "resource lacks unique producing event");
            continue;
        }
        let e = matching[0];
        let valid = if !e.result_published {
            t.status == unpublished_status(e)
        } else if e.status == "unavailable" {
            t.status == "unavailable"
        } else if e.native_result == Some(0) {
            t.status == "null"
        } else {
            matches!(t.status.as_str(), "issued" | "issued_uncustodied")
        };
        require(out, valid, "token status contradicts issue");
        require(
            out,
            t.family == "file"
                && t.token_length == e.token_length
                && (t.status != "issued"
                    || t.token_length.is_some_and(|n| (1..16384).contains(&n))),
            "token metadata contradicts issue",
        );
    }
    for h in &resources.handles {
        let matching: Vec<_> = events
            .iter()
            .filter(|e| {
                e.operation == "consume" && e.handle_ref.as_deref() == Some(h.handle_ref.as_str())
            })
            .collect();
        if matching.len() != 1 {
            require(out, false, "resource lacks unique producing event");
            continue;
        }
        let e = matching[0];
        let status = if !e.result_published {
            unpublished_status(e)
        } else if e.status == "unavailable" {
            "unavailable"
        } else if e.native_result == Some(-1) {
            "consume_failed"
        } else {
            "produced"
        };
        require(
            out,
            h.status == status
                && h.native_handle
                    == if status == "produced" {
                        e.native_result
                    } else {
                        None
                    },
            "handle status or value contradicts consume",
        );
        let release = events.iter().find(|e| {
            e.operation == "release" && e.handle_ref.as_deref() == Some(h.handle_ref.as_str())
        });
        require(
            out,
            h.release_step_id.as_deref() == release.map(|e| e.step_id.as_str())
                && h.release_attempted == release.is_some_and(|e| e.call_boundary_observed),
            "handle release projection contradicts event",
        );
        let equal: BTreeSet<&str> = resources
            .handles
            .iter()
            .filter(|other| {
                other.handle_ref != h.handle_ref
                    && other.actor_id == h.actor_id
                    && h.native_handle.is_some()
                    && other.native_handle == h.native_handle
            })
            .map(|h| h.handle_ref.as_str())
            .collect();
        let observed: BTreeSet<&str> = h.raw_equal_handles.iter().map(String::as_str).collect();
        require(
            out,
            h.raw_equal_handles.len() == observed.len() && observed == equal,
            "handle equality projection contradicts native handles",
        );
    }
    for d in &resources.deliveries {
        let matching: Vec<_> = events
            .iter()
            .filter(|e| {
                e.operation == "transfer"
                    && e.delivery_ref.as_deref() == Some(d.delivery_ref.as_str())
            })
            .collect();
        if matching.len() != 1 {
            require(out, false, "resource lacks unique producing event");
            continue;
        }
        let e = matching[0];
        require(
            out,
            actors.iter().any(|a| a.actor_id == d.recipient_actor_id),
            "delivery recipient does not exist",
        );
        if let Some(host) = transfers.iter().find(|t| t.delivery_ref == d.delivery_ref) {
            require(
                out,
                d.status == host.status && d.equality.as_deref() == Some(host.equality.as_str()),
                "delivery projection contradicts host transfer",
            );
            if host.status == "delivered" {
                require(
                    out,
                    d.delivered_length.is_some_and(|n| (1..16384).contains(&n))
                        && resources
                            .tokens
                            .iter()
                            .find(|t| t.token_ref == d.token_ref)
                            .is_none_or(|t| {
                                t.token_length.is_none() || t.token_length == d.delivered_length
                            }),
                    "delivered length contradicts custody",
                );
            } else {
                require(
                    out,
                    d.delivered_length.is_none(),
                    "undelivered resource carries delivered length",
                );
            }
            // Host custody is independent of the source worker's later result
            // publication. Never replace it with an inferred unpublished state.
            continue;
        }
        require(
            out,
            d.equality.is_none()
                && d.delivered_length.is_none()
                && matches!(
                    e.status.as_str(),
                    "none" | "host_timeout" | "clock_fault" | "unresolved"
                ),
            "delivery claims host observation without transfer",
        );
        if e.result_published {
            require(
                out,
                d.status == e.unavailable_reason.as_deref().unwrap_or("unrequested"),
                "unobserved delivery status contradicts source",
            );
        } else {
            require(
                out,
                d.status == unpublished_status(e),
                "unpublished resource status contradicts lifecycle",
            );
        }
    }
}
pub(super) fn validate(reply: &PWRunnerRunResult, out: &mut Vec<IntegrityIssue>) {
    if reply.execution_form.as_deref() != Some("actors") {
        require(
            out,
            reply.extension_events.as_ref().is_none_or(Vec::is_empty)
                && reply.actors.is_none()
                && reply.transfers.is_none()
                && reply.resources.is_none()
                && reply.schedule.is_none()
                && reply.preparation_failure.is_none()
                && reply.authority_setup.is_none()
                && reply.equipment_inventory.is_none()
                && reply.equipment_bindings.is_none()
                && reply.equipment_entitlements.is_none(),
            "ordinary reply carries actor authority evidence",
        );
        return;
    }
    let Some(actors) = reply.actors.as_deref() else {
        require(out, false, "actor form lacks actor table");
        return;
    };
    if reply.preparation_failure.is_some() {
        require(
            out,
            preparation_failure_valid(reply),
            "invalid before-launch preparation failure",
        );
    }
    identity(reply, actors, out);
    setup(reply, actors, out);
    equipment(reply, actors, out);
    for (i, a) in actors.iter().enumerate() {
        application(
            a,
            reply
                .authority_setup
                .as_ref()
                .and_then(|s| s.workers.get(i)),
            out,
        );
    }
    gates(reply, actors, out);
    custody(reply, actors, out);
}
fn error_valid(e: &PWRunnerEquipmentError) -> bool {
    [
        "service_seal",
        "inventory_read",
        "inventory_decode",
        "worker_path",
        "worker_hash",
        "worker_signature",
        "worker_entitlements",
        "guest_code",
        "dynamic_validity",
        "associated_static_code",
        "signing_information",
    ]
    .contains(&e.operation.as_str())
        && e.domain.as_ref().is_none_or(|d| d.len() <= 128)
        && e.message.as_ref().is_none_or(|m| m.len() <= 1024)
        && e.domain.is_none() == e.code.is_none()
}
fn metadata_fits<'a>(fields: impl IntoIterator<Item = Option<&'a str>>) -> bool {
    let mut remaining = 32768usize;
    fields.into_iter().flatten().all(|s| {
        if let Some(r) = remaining.checked_sub(s.len()) {
            remaining = r;
            true
        } else {
            false
        }
    })
}
fn equipment_bounds(
    reply: &PWRunnerRunResult,
    actors: &[PWRunnerActorResult],
    out: &mut Vec<IntegrityIssue>,
) {
    let bindings = reply.equipment_bindings.as_deref().unwrap_or(&[]);
    if let Some(i) = &reply.equipment_inventory {
        require(
            out,
            i.path.starts_with('/')
                && bounded(&i.path, 1023)
                && i.error.as_ref().is_none_or(error_valid),
            "equipment inventory path or error",
        );
        if i.status == "verified" {
            require(
                out,
                i.reason.is_none()
                    && i.error.is_none()
                    && bindings
                        .iter()
                        .filter(|b| b.source == "packaged")
                        .map(|b| b.role.as_str())
                        .collect::<BTreeSet<_>>()
                        == BTreeSet::from(["selected", "unentitled"]),
                "equipment complete packaged pair or inventory refusal",
            );
        }
    }
    for r in reply.equipment_entitlements.iter().flatten() {
        require(
            out,
            r.error.as_ref().is_none_or(error_valid)
                && if r.status == "observed" {
                    r.error.is_none()
                } else {
                    r.error.is_some()
                },
            "equipment read-back error association",
        );
        if r.source == "binding" {
            require(
                out,
                r.actor_id.is_none(),
                "equipment static read-back identity",
            );
        }
    }
    for b in bindings {
        let e = b.error.as_ref();
        require(
            out,
            metadata_fits([
                Some(b.role.as_str()),
                Some(b.source.as_str()),
                Some(b.implementation_identity.as_str()),
                b.relative_path.as_deref(),
                Some(b.path.as_str()),
                Some(b.status.as_str()),
                b.reason.as_deref(),
                b.identifier.as_deref(),
                b.team_id.as_deref(),
                e.map(|e| e.operation.as_str()),
                e.and_then(|e| e.domain.as_deref()),
                e.and_then(|e| e.message.as_deref()),
            ]),
            "equipment binding metadata bound",
        );
        require(
            out,
            b.path.starts_with('/')
                && bounded(&b.path, 1023)
                && b.expected_sha256.as_deref().is_none_or(|s| s.len() == 32)
                && b.expected_cdhash.as_deref().is_none_or(|s| s.len() == 20)
                && b.sha256.as_deref().is_none_or(|s| s.len() == 32)
                && b.cdhash.as_deref().is_none_or(|s| s.len() == 20)
                && b.identifier.as_deref().is_none_or(|s| bounded(s, 255))
                && b.team_id.as_deref().is_none_or(|s| bounded(s, 255))
                && e.is_none_or(error_valid),
            "equipment binding path, identity or error bound",
        );
        if b.status == "bound" {
            require(
                out,
                b.reason.is_none()
                    && e.is_none()
                    && b.identifier.as_ref().is_some_and(|s| !s.is_empty()),
                "equipment bound observations",
            );
        } else {
            require(
                out,
                matches!(
                    b.reason.as_deref(),
                    Some(
                        "missing"
                            | "not_regular"
                            | "not_executable"
                            | "outside_bundle"
                            | "signature_invalid"
                            | "signature_unreadable"
                            | "entitlements_unreadable"
                            | "worker_identity_mismatch"
                            | "inspection_failed"
                    )
                ),
                "equipment refusal reason",
            );
        }
    }
    let mut failed_inspection = false;
    for a in actors {
        let Some(e) = &a.equipment else { continue };
        let x = &e.execution;
        require(
            out,
            metadata_fits(
                [
                    Some(x.status.as_str()),
                    x.path.as_deref(),
                    x.identifier.as_deref(),
                    x.team_id.as_deref(),
                    x.reason.as_deref(),
                ]
                .into_iter()
                .chain(
                    x.native_observations
                        .iter()
                        .map(|o| Some(o.operation.as_str())),
                ),
            ),
            "equipment execution metadata bound",
        );
        require(
            out,
            x.path
                .as_deref()
                .is_none_or(|s| s.starts_with('/') && bounded(s, 1023))
                && x.cdhash.as_deref().is_none_or(|s| s.len() == 20)
                && x.identifier.as_deref().is_none_or(|s| bounded(s, 255))
                && x.team_id.as_deref().is_none_or(|s| bounded(s, 255)),
            "equipment execution path or identity bound",
        );
        require(
            out,
            x.native_observations.len() <= 4
                && x.native_observations
                    .iter()
                    .zip([
                        "guest_code",
                        "dynamic_validity",
                        "associated_static_code",
                        "signing_information",
                    ])
                    .all(|(o, n)| o.operation == n && o.attempted && o.osstatus.is_some()),
            "equipment native observation order/result",
        );
        if let Some(p) = x.pid {
            require(
                out,
                pid(p) && a.launch.as_ref().is_some_and(|l| l.pid == p),
                "equipment execution PID association",
            );
        }
        if x.status == "matched" {
            require(
                out,
                x.observed_at_monotonic_ns.is_some(),
                "equipment matched live observations",
            );
        } else {
            require(
                out,
                matches!(
                    x.reason.as_deref(),
                    Some(
                        "not_launched"
                            | "setup_unavailable"
                            | "process_unavailable"
                            | "ownership_unresolved"
                            | "code_lookup_failed"
                            | "dynamic_validation_failed"
                            | "signing_readback_failed"
                            | "executable_mismatch"
                            | "signature_identity_mismatch"
                            | "entitlement_mismatch"
                            | "requirements_unsatisfied"
                            | "inspection_deadline"
                    )
                ),
                "equipment ineligible execution",
            );
        }
        failed_inspection |= matches!(x.status.as_str(), "mismatched" | "inspection_failed")
            || x.status == "unobserved"
                && !matches!(
                    x.reason.as_deref(),
                    Some("not_launched" | "setup_unavailable")
                );
    }
    if failed_inspection {
        require(
            out,
            reply
                .schedule
                .as_ref()
                .and_then(|s| s.cancelled.as_ref())
                .is_some_and(|s| !s.is_empty())
                && reply.phases.iter().all(|p| {
                    !p.arrival_observed
                        && !p.completion_observed
                        && p.visit_timing.is_none()
                        && p.activation_observation.is_none()
                        && p.collection_status == "not_reached"
                        && !p
                            .ordering
                            .as_ref()
                            .is_some_and(|o| o.proceed_set || o.proceed_observed)
                }),
            "equipment execution failure did not cancel all activation",
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{Value, json};

    // These older independently authored fixtures isolate setup/equipment/gates.
    // Their missing unrelated wire fields are authored here explicitly; this is
    // not a runtime default or a claim that these sparse documents are complete
    // run replies. Custody and integrated reply controls below use separate facts.
    fn fixture(name: &str) -> Value {
        let text = match name {
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
            _ => panic!("unknown authored actor fixture {name}"),
        };
        let mut v: Value = serde_json::from_str(text).unwrap();
        v["producer"] = crate::reply_fixtures::producer();
        for phase in v["phases"].as_array_mut().unwrap() {
            phase["action_ids"] = json!([]);
        }
        for actor in v["actors"].as_array_mut().unwrap() {
            if actor["launch"].is_object() {
                actor["launch"]["environment"] = json!("empty");
                actor["launch"]["standard_streams"] = json!("dev_null");
                actor["launch"]["inherited_descriptors"] = json!([0, 1, 2, 3, 4]);
            }
            if actor["subprocess"].is_object() {
                actor["subprocess"]["partial_steps"] = json!(false);
            }
        }
        v["schedule"]["lifetime_budget_ms"] = json!(1000);
        v["schedule"]["collection_budget_ms"] = json!(1000);
        v
    }
    fn account_only(reply: &PWRunnerRunResult) -> Vec<IntegrityIssue> {
        let actors = reply.actors.as_deref().unwrap();
        let mut out = Vec::new();
        setup(reply, actors, &mut out);
        equipment(reply, actors, &mut out);
        for (i, a) in actors.iter().enumerate() {
            application(
                a,
                reply
                    .authority_setup
                    .as_ref()
                    .and_then(|s| s.workers.get(i)),
                &mut out,
            );
        }
        gates(reply, actors, &mut out);
        out
    }
    #[test]
    fn typed_setup_equipment_application_and_gate_corpus() {
        let cases: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/actor_evidence.json"
        ))
        .unwrap();
        for case in cases.as_array().unwrap() {
            let mut v = fixture(
                case["fixture"]
                    .as_str()
                    .unwrap_or("actor_authority_reply.json"),
            );
            for patch in case["patches"].as_array().unwrap() {
                let (parent, key) = patch["path"].as_str().unwrap().rsplit_once('/').unwrap();
                let target = v.pointer_mut(parent).unwrap();
                if let Some(a) = target.as_array_mut() {
                    a[key.parse::<usize>().unwrap()] = patch["value"].clone();
                } else {
                    target[key] = patch["value"].clone();
                }
            }
            if case["name"] == "timed_out_gate_retains_associated_late_owned_reap" {
                // This whole-phase gate patch has no action publication. Its
                // empty unrelated action plan is authored explicitly here.
                v["phases"][2]["action_ids"] = json!([]);
            }
            // A few original corpus patches replace the entire intentionally
            // sparse schedule. Its budgets are outside this account-only test;
            // author those two fixture fields after applying such a patch.
            if let Some(schedule) = v["schedule"].as_object_mut() {
                schedule.entry("lifetime_budget_ms").or_insert(json!(1000));
                schedule
                    .entry("collection_budget_ms")
                    .or_insert(json!(1000));
            }
            match serde_json::from_value::<PWRunnerRunResult>(v) {
                Ok(reply) => {
                    let before = reply.clone();
                    let issues = account_only(&reply);
                    assert_eq!(
                        issues.is_empty(),
                        case["accepted"] == true,
                        "{}: {issues:?}",
                        case["name"]
                    );
                    assert_eq!(
                        reply, before,
                        "admission changed independently retained facts: {}",
                        case["name"]
                    );
                }
                Err(error) => assert_eq!(
                    case["accepted"], false,
                    "accepted fixture {} cannot decode: {error}",
                    case["name"]
                ),
            }
        }
    }
    #[test]
    fn typed_equipment_metadata_counts_retained_utf8_and_inspection_is_independent() {
        let mut reply: PWRunnerRunResult =
            serde_json::from_value(fixture("actor_authority_reply.json")).unwrap();
        assert!(account_only(&reply).is_empty());
        let before = reply.actors.as_ref().unwrap()[0]
            .equipment
            .as_ref()
            .unwrap()
            .execution
            .clone();
        reply.equipment_bindings.as_mut().unwrap()[0].reason = Some("\"\\\n".repeat(11000));
        let issues = account_only(&reply);
        assert!(
            issues
                .iter()
                .any(|i| i.detail == "equipment binding metadata bound")
        );
        assert_eq!(
            reply.actors.as_ref().unwrap()[0]
                .equipment
                .as_ref()
                .unwrap()
                .execution,
            before
        );
        assert!(metadata_fits([Some("\"\\\n")]));
        assert!(metadata_fits([Some("é")]));
        assert!(!metadata_fits([Some("é".repeat(16385).as_str())]));
    }
    #[test]
    fn typed_authority_setup_requires_publication_kind_and_failed_cleanup_witness() {
        let reply: PWRunnerRunResult =
            serde_json::from_value(fixture("actor_authority_reply.json")).unwrap();
        let baseline = reply.authority_setup.as_ref().unwrap().workers[0].clone();
        let mut out = Vec::new();
        scope(&baseline, WORKER_OPS, "worker", &mut out);
        assert!(out.is_empty(), "{out:?}");
        let mut s = baseline.clone();
        s.integrity_errors = Some(vec![]);
        let raw = s.clone();
        let mut out = Vec::new();
        scope(&s, WORKER_OPS, "worker", &mut out);
        assert!(
            out.iter()
                .any(|i| i.detail == "setup publication retains integrity errors")
        );
        assert_eq!(s, raw);
        let mut s = baseline;
        s.operations[0].state = "not_attempted".into();
        s.operations[0].native_kind = Some("symbol".into());
        s.operations[0].native_rc = None;
        s.operations[0].errno = None;
        s.operations[0].value = None;
        let mut out = Vec::new();
        scope(&s, WORKER_OPS, "worker", &mut out);
        assert!(
            out.is_empty(),
            "not_attempted retains its declared cell kind: {out:?}"
        );
        s.operations[0].native_kind = None;
        let mut out = Vec::new();
        scope(&s, WORKER_OPS, "worker", &mut out);
        assert!(
            out.iter()
                .any(|i| i.detail == "setup operation native kind")
        );
        let operation =
            |slot, operation: &str, state: &str, native_rc, errno| PWRunnerAuthorityOperation {
                slot,
                operation: operation.into(),
                role: "setup".into(),
                state: state.into(),
                native_kind: Some("integer".into()),
                native_rc: Some(native_rc),
                errno,
                detail: None,
                value: None,
            };
        let s = PWRunnerAuthorityScope {
            actor_id: Some("issuer".into()),
            actor_index: Some(0),
            token_ref: None,
            token_index: None,
            required: Some(true),
            publication: None,
            disposition: Some("failed".into()),
            primary_operation: Some(1),
            operations: vec![
                operation(0, "shm_open", "succeeded", 5, None),
                operation(1, "shm_unlink", "failed", -1, Some(libc::EACCES)),
            ],
            ownership: crate::porcelain::OrderedMap(vec![(
                "object_name".into(),
                "unresolved".into(),
            )]),
            cleanup_reference: Some(PWAuthorityCleanupReference {
                kind: "posix_shm_name".into(),
                name: "/constructed-owned-region".into(),
                host_pid: 12000,
                session_nonce: 1,
                recovery_state: "unresolved_manual".into(),
            }),
            integrity_errors: None,
        };
        let mut out = Vec::new();
        scope(&s, REGION_OPS, "region", &mut out);
        assert!(out.is_empty(), "{out:?}");
        let mut changed = s.clone();
        changed.primary_operation = None;
        changed.operations.pop();
        let before = changed.clone();
        let mut out = Vec::new();
        scope(&changed, REGION_OPS, "region", &mut out);
        assert!(
            out.iter()
                .any(|i| i.detail == "unresolved setup cleanup lacks owned creation")
        );
        assert_eq!(changed, before);
        assert_eq!(changed.cleanup_reference, s.cleanup_reference);
    }
    #[test]
    fn typed_missing_entitlements_cannot_duplicate_one_name_to_hide_another() {
        let mut r: PWRunnerRunResult =
            serde_json::from_value(fixture("actor_authority_reply.json")).unwrap();
        let e = r.actors.as_mut().unwrap()[0].equipment.as_mut().unwrap();
        e.required_entitlements = vec!["a".into(), "b".into()];
        e.requirements_status = "unsatisfied".into();
        e.missing_requirements = Some(vec!["a".into(), "b".into()]);
        e.execution.status = "unobserved".into();
        e.execution.reason = Some("setup_unavailable".into());
        e.execution.eligible = false;
        let mut out = Vec::new();
        equipment(&r, r.actors.as_deref().unwrap(), &mut out);
        assert!(out.is_empty(), "{out:?}");
        let native = r.actors.as_ref().unwrap()[0]
            .equipment
            .as_ref()
            .unwrap()
            .execution
            .clone();
        r.actors.as_mut().unwrap()[0]
            .equipment
            .as_mut()
            .unwrap()
            .missing_requirements = Some(vec!["a".into(), "a".into()]);
        let mut out = Vec::new();
        equipment(&r, r.actors.as_deref().unwrap(), &mut out);
        assert!(
            out.iter()
                .any(|i| i.detail == "actor requirements disagree with observed entitlements")
        );
        assert_eq!(
            r.actors.as_ref().unwrap()[0]
                .equipment
                .as_ref()
                .unwrap()
                .execution,
            native
        );
    }
    #[test]
    fn typed_entitlements_require_boolean_true_and_semantic_dictionary_equality() {
        let a=plist::Dictionary::read("<plist version=\"1.0\"><dict><key>yes</key><true/><key>no</key><false/><key>number</key><integer>1</integer></dict></plist>").unwrap();
        let b=plist::Dictionary::read("<plist version=\"1.0\"><dict><key>number</key><integer>1</integer><key>no</key><false/><key>yes</key><true/></dict></plist>").unwrap();
        assert!(a.equal(&b));
        assert_eq!(a.granted(), BTreeSet::from(["yes".into()]));
        assert!(plist::Dictionary::read("<plist><array/></plist>").is_none());
        assert!(plist::Dictionary::read("not a plist").is_none());
        assert!(plist::Dictionary::read(&"x".repeat(65537)).is_none());
    }
}

fn identity(
    reply: &PWRunnerRunResult,
    actors: &[PWRunnerActorResult],
    out: &mut Vec<IntegrityIssue>,
) {
    let mut ids = BTreeSet::new();
    for (i, a) in actors.iter().enumerate() {
        require(
            out,
            bounded(&a.actor_id, 63) && ids.insert(a.actor_id.as_str()) && a.index == i as i64,
            "actor index or identity conflict",
        );
        require(
            out,
            matches!(a.mode.as_str(), "apply" | "unapplied")
                && matches!(
                    a.setup_status.as_str(),
                    "not_launched"
                        | "launch_refused"
                        | "transfer_failed"
                        | "applied"
                        | "unapplied_declared"
                        | "setup_failed"
                        | "exited_before_setup"
                        | "setup_timeout"
                        | "authority_setup_failed"
                ),
            "actor mode or setup status",
        );
        if a.mode == "unapplied" {
            require(
                out,
                a.applied.is_none()
                    && a.policy_sha256.is_none()
                    && a.policy_format.is_none()
                    && a.setup_status != "applied",
                "unapplied actor carries an application or policy claim",
            );
        }
        if a.mode == "apply" {
            require(
                out,
                a.setup_status != "unapplied_declared",
                "apply actor cannot declare an unapplied setup",
            );
        }
        match (&a.subprocess, &a.launch) {
            (Some(s), Some(l)) => require(
                out,
                pid(l.pid) && pid(l.parent_pid) && l.pid == s.pid,
                "actor subprocess lacks its matching native launch record",
            ),
            (Some(_), None) => require(
                out,
                false,
                "actor subprocess lacks its matching native launch record",
            ),
            (None, l) => require(
                out,
                l.is_none()
                    && !matches!(
                        a.setup_status.as_str(),
                        "applied"
                            | "unapplied_declared"
                            | "setup_failed"
                            | "authority_setup_failed"
                            | "exited_before_setup"
                            | "transfer_failed"
                    ),
                "actor setup claims a process without subprocess evidence",
            ),
        }
        let visits: Vec<i64> = reply
            .phases
            .iter()
            .enumerate()
            .filter(|(_, p)| p.actor_id.as_deref() == Some(a.actor_id.as_str()))
            .map(|(i, _)| i as i64 + 1)
            .collect();
        require(
            out,
            a.visits == visits,
            "actor visits disagree with schedule",
        );
    }
    let mut visits: BTreeMap<&str, i64> = BTreeMap::new();
    for p in &reply.phases {
        let Some(id) = p.actor_id.as_deref().filter(|id| ids.contains(id)) else {
            require(out, false, "phase actor is absent");
            continue;
        };
        let n = visits.entry(id).or_default();
        *n += 1;
        require(
            out,
            p.actor_visit == Some(*n),
            "phase actor_visit disagrees with that actor's visit order",
        );
    }
    for s in &reply.steps {
        require(
            out,
            s.actor_id.as_deref().is_some_and(|id| ids.contains(id))
                && reply.phases.iter().any(|p| {
                    p.phase_id == s.phase_id
                        && p.actor_id == s.actor_id
                        && p.action_ids.contains(&s.step_id)
                }),
            "step actor differs from phase actor",
        );
    }
}

#[cfg(test)]
mod custody_tests {
    use super::*;
    fn custody_reply() -> PWRunnerRunResult {
        let mut r = super::super::tests::actors();
        r.policy_sha256 = None;
        let actor = "issuer".to_string();
        let phase = &mut r.phases[0];
        phase.phase_id = "supply".into();
        phase.actor_id = Some(actor.clone());
        phase.action_ids = vec![
            "issue".into(),
            "transfer".into(),
            "consume".into(),
            "release".into(),
        ];
        let template = r.extension_events.as_ref().unwrap()[0].clone();
        let mut issue = template.clone();
        issue.phase_id = "supply".into();
        issue.step_id = "issue".into();
        issue.actor_id = Some(actor.clone());
        issue.operation = "issue".into();
        issue.family = Some("file".into());
        issue.token_ref = Some("t".into());
        issue.delivery_ref = None;
        let mut transfer = issue.clone();
        transfer.step_id = "transfer".into();
        transfer.operation = "transfer".into();
        transfer.delivery_ref = Some("d".into());
        let mut consume = issue.clone();
        consume.step_id = "consume".into();
        consume.operation = "consume".into();
        consume.token_ref = None;
        consume.handle_ref = Some("h".into());
        consume.delivery_ref = Some("d".into());
        let mut release = consume.clone();
        release.step_id = "release".into();
        release.operation = "release".into();
        release.delivery_ref = None;
        r.extension_events = Some(vec![issue, transfer, consume, release]);
        r.transfers = Some(vec![PWRunnerTransferRecord {
            phase_id: "supply".into(),
            step_id: "transfer".into(),
            source_actor_id: actor.clone(),
            recipient_actor_id: actor.clone(),
            token_ref: "t".into(),
            delivery_ref: "d".into(),
            request_published: true,
            custody_status: "held".into(),
            copy_status: "copied".into(),
            equality: "equal".into(),
            recipient_acknowledged: true,
            source_acknowledged: false,
            status: "delivered".into(),
            lifecycle: None,
            recipient_wait: None,
        }]);
        r.resources = Some(PWRunnerResourceTables {
            tokens: vec![PWRunnerTokenRecord {
                token_ref: "t".into(),
                actor_id: actor.clone(),
                step_id: "issue".into(),
                family: "file".into(),
                status: "unresolved".into(),
                token_length: None,
                last_use_step_id: Some("transfer".into()),
            }],
            deliveries: vec![PWRunnerDeliveryRecord {
                delivery_ref: "d".into(),
                token_ref: "t".into(),
                source_actor_id: actor.clone(),
                recipient_actor_id: actor.clone(),
                step_id: "transfer".into(),
                status: "delivered".into(),
                delivered_length: Some(200),
                equality: Some("equal".into()),
                last_use_step_id: Some("consume".into()),
            }],
            handles: vec![PWRunnerHandleRecord {
                handle_ref: "h".into(),
                delivery_ref: "d".into(),
                actor_id: actor,
                step_id: "consume".into(),
                status: "unresolved".into(),
                native_handle: None,
                raw_equal_handles: vec![],
                release_step_id: Some("release".into()),
                release_attempted: false,
            }],
        });
        r
    }
    #[test]
    fn typed_custody_host_delivery_survives_missing_source_publication() {
        let baseline = custody_reply();
        let actors = baseline.actors.as_deref().unwrap();
        let mut issues = Vec::new();
        custody(&baseline, actors, &mut issues);
        assert!(issues.is_empty(), "{issues:?}");
        assert!(!baseline.extension_events.as_ref().unwrap()[1].result_published);
        for mutation in [
            "copy",
            "ack",
            "source_ack",
            "length",
            "recipient",
            "release",
            "equal",
            "token_owner",
            "order",
        ] {
            let mut reply = baseline.clone();
            match mutation {
                "copy" => reply.transfers.as_mut().unwrap()[0].copy_status = "copy_mismatch".into(),
                "ack" => reply.transfers.as_mut().unwrap()[0].recipient_acknowledged = false,
                "source_ack" => reply.transfers.as_mut().unwrap()[0].source_acknowledged = true,
                "length" => {
                    reply.resources.as_mut().unwrap().deliveries[0].delivered_length = Some(0)
                }
                "recipient" => {
                    reply.resources.as_mut().unwrap().deliveries[0].recipient_actor_id =
                        "absent".into()
                }
                "release" => reply.resources.as_mut().unwrap().handles[0].release_attempted = true,
                "equal" => reply.resources.as_mut().unwrap().handles[0]
                    .raw_equal_handles
                    .push("invented".into()),
                "token_owner" => {
                    reply.resources.as_mut().unwrap().tokens[0].actor_id = "subject".into()
                }
                "order" => reply.phases[0].action_ids.swap(0, 1),
                _ => unreachable!(),
            }
            let before = reply.clone();
            let mut issues = Vec::new();
            custody(&reply, reply.actors.as_deref().unwrap(), &mut issues);
            assert!(!issues.is_empty(), "accepted {mutation}");
            assert_eq!(
                reply, before,
                "changed raw custody/native facts: {mutation}"
            );
            assert_eq!(reply.transfers.as_ref().unwrap()[0].status, "delivered");
            assert!(!reply.extension_events.as_ref().unwrap()[1].result_published);
        }
    }
}
