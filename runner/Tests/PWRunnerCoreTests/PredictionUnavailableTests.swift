import Foundation
@testable import PWRunnerCore

// Covers the runSandboxCheck short-circuit for (operation, filter_kind)
// pairs whose sandbox_check verdict has been empirically verified to
// drift from kernel enforcement. The function must return without
// calling into libsandbox — the assertion that no syscall is made is
// implicit (sandbox_check requires libsandbox loading and a sandboxed
// process; a real call here would fail or hang under the test
// harness). What we verify is the wire envelope: outcome string,
// sentinel rc, nulled filter_type_id/errno, and that filter_value
// round-trips unchanged.

private func makeCheck(operation: String,
                       filterKind: String,
                       filterValue: String) -> PWRunnerSandboxCheck {
    return PWRunnerSandboxCheck(
        operation: operation,
        filter: PWRunnerSandboxFilter(kind: filterKind, value: filterValue)
    )
}

private func expectUnavailable(_ result: PWRunnerSandboxCheckResult,
                               operation: String,
                               filterKind: String,
                               filterValue: String) throws {
    try expectEqual(result.outcome, "prediction_unavailable",
                    "outcome for (\(operation), \(filterKind))")
    try expectEqual(result.rc, -1,
                    "rc sentinel for (\(operation), \(filterKind))")
    try expectEqual(result.operation, operation,
                    "operation echoed for (\(operation), \(filterKind))")
    try expectEqual(result.filter_kind, filterKind,
                    "filter_kind echoed for (\(operation), \(filterKind))")
    try expectEqual(result.filter_value, filterValue,
                    "filter_value echoed for (\(operation), \(filterKind))")
    try expectNil(result.filter_type_id,
                  "filter_type_id null for (\(operation), \(filterKind))")
    try expectNil(result.errno,
                  "errno null for (\(operation), \(filterKind))")
    try expectNil(result.error,
                  "error null for (\(operation), \(filterKind))")
    try expectNil(result.path_diagnostics,
                  "path_diagnostics null for (\(operation), \(filterKind))")
}

func runPredictionUnavailableTests(_ tk: TestKit) {
    tk.group("predictionUnavailable") {
        tk.run("iokit-open-service + iokit_registry_entry_class short-circuits") {
            let check = makeCheck(operation: "iokit-open-service",
                                  filterKind: "iokit_registry_entry_class",
                                  filterValue: "IOSurfaceRoot")
            try expectUnavailable(runSandboxCheck(check),
                                  operation: "iokit-open-service",
                                  filterKind: "iokit_registry_entry_class",
                                  filterValue: "IOSurfaceRoot")
        }

        tk.run("iokit-open-user-client + iokit_user_client_class short-circuits") {
            let check = makeCheck(operation: "iokit-open-user-client",
                                  filterKind: "iokit_user_client_class",
                                  filterValue: "IOSurfaceRootUserClient")
            try expectUnavailable(runSandboxCheck(check),
                                  operation: "iokit-open-user-client",
                                  filterKind: "iokit_user_client_class",
                                  filterValue: "IOSurfaceRootUserClient")
        }

        tk.run("sysctl-read + sysctl_name short-circuits") {
            let check = makeCheck(operation: "sysctl-read",
                                  filterKind: "sysctl_name",
                                  filterValue: "kern.osrelease")
            try expectUnavailable(runSandboxCheck(check),
                                  operation: "sysctl-read",
                                  filterKind: "sysctl_name",
                                  filterValue: "kern.osrelease")
        }

        tk.run("rc sentinel is non-zero so it can't be misread as allow") {
            // Pin the value itself, separately, so a future "just change
            // it to something else" gets a loud test failure flagging the
            // documented consumer-facing contract change.
            let check = makeCheck(operation: "iokit-open-service",
                                  filterKind: "iokit_registry_entry_class",
                                  filterValue: "IOSurfaceRoot")
            let result = runSandboxCheck(check)
            try expectTrue(result.rc != 0,
                           "rc must not be 0 (rc==0 is the 'allow' convention)")
            try expectEqual(result.rc, -1,
                            "rc sentinel value is documented in PolicyWitness.md")
        }
    }
}
