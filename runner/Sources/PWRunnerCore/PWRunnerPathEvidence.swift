import Foundation
import Darwin

struct PWFileIdentity {
    // BEGIN GENERATED PORCELAIN PWFileIdentity
    var device: UInt64
    var inode: UInt64
    var mode: UInt32
    var uid: UInt32
    var gid: UInt32
    // END GENERATED PORCELAIN PWFileIdentity
}

// Path forms observed by the unsandboxed runner host after orchestration.
// They are not validator/worker resolutions or comparison inputs.
//
// Wire form: `input` plus the two forms named in `formNames`. A form with the
// same UTF-8 bytes as `input` is listed in `same_as_input` and its key omitted; a form
// that differs is a string; a form the host could not derive is an explicit
// null. Each form is therefore in exactly one of those three states.
struct PWRunnerPathDiagnostics {
    static let formNames = ["realpath_resolved", "firmlink_resolved"]

    // BEGIN GENERATED PORCELAIN PWRunnerPathDiagnostics
    var observer: String?
    var stage: String?
    var input: String
    var realpath_resolved: String?
    var firmlink_resolved: String?
    // END GENERATED PORCELAIN PWRunnerPathDiagnostics

    init(
        input: String,
        realpath_resolved: String? = nil,
        firmlink_resolved: String? = nil,
        observer: String? = nil,
        stage: String? = nil
    ) {
        self.observer = observer
        self.stage = stage
        self.input = input
        self.realpath_resolved = realpath_resolved
        self.firmlink_resolved = firmlink_resolved
    }


}

// The unsandboxed host's after-orchestration resolution of a file or exec
// attempt target. `realpath_resolved` follows the leaf; `parent_realpath_resolved`
// resolves the parent and keeps the leaf literal, the form the kernel names for
// a created or unlinked path. Neither establishes what the worker's own syscall
// resolved: these diagnostics describe later resolution by the host, not the
// identity of an object accessed by the worker.
struct PWRunnerAttemptPathDiagnostics {
    static let formNames = ["realpath_resolved", "parent_realpath_resolved"]

    // BEGIN GENERATED PORCELAIN PWRunnerAttemptPathDiagnostics
    var observer: String?
    var stage: String?
    var input: String
    var realpath_resolved: String?
    var parent_realpath_resolved: String?
    // END GENERATED PORCELAIN PWRunnerAttemptPathDiagnostics

    init(
        input: String,
        realpath_resolved: String? = nil,
        parent_realpath_resolved: String? = nil,
        observer: String? = nil,
        stage: String? = nil
    ) {
        self.observer = observer
        self.stage = stage
        self.input = input
        self.realpath_resolved = realpath_resolved
        self.parent_realpath_resolved = parent_realpath_resolved
    }


}
