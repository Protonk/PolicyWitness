import Foundation
import Darwin

struct PWFileIdentity: Codable {
    var device: UInt64
    var inode: UInt64
    var mode: UInt32
    var uid: UInt32
    var gid: UInt32
}

// Path forms observed by the unsandboxed runner host after orchestration.
// They are not validator/worker resolutions or comparison inputs.
//
// Wire form: `input` plus the two forms named in `formNames`. A form with the
// same UTF-8 bytes as `input` is listed in `same_as_input` and its key omitted; a form
// that differs is a string; a form the host could not derive is an explicit
// null. Each form is therefore in exactly one of those three states.
struct PWRunnerPathDiagnostics: Codable {
    static let formNames = ["realpath_resolved", "firmlink_resolved"]

    var observer: String?
    var stage: String?
    var input: String
    var realpath_resolved: String?
    var firmlink_resolved: String?

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

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: PathFormKey.self)
        try container.encodeIfPresent(observer, forKey: .observer)
        try container.encodeIfPresent(stage, forKey: .stage)
        try container.encode(input, forKey: .input)
        try encodePathForms(&container, input: input,
            forms: [("realpath_resolved", realpath_resolved), ("firmlink_resolved", firmlink_resolved)])
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: PathFormKey.self)
        observer = try container.decodeIfPresent(String.self, forKey: .observer)
        stage = try container.decodeIfPresent(String.self, forKey: .stage)
        input = try container.decode(String.self, forKey: .input)
        let decoded = try decodePathForms(container, input: input, formNames: Self.formNames)
        realpath_resolved = decoded["realpath_resolved"] ?? nil
        firmlink_resolved = decoded["firmlink_resolved"] ?? nil
    }
}

/// Dynamic key for the shared three-state path-form wire rule, so the query
/// and attempt blocks differ only in their form-name lists.
struct PathFormKey: CodingKey {
    var stringValue: String
    var intValue: Int? { nil }
    init(stringValue: String) { self.stringValue = stringValue }
    init?(intValue: Int) { nil }
    static let observer = PathFormKey(stringValue: "observer")
    static let stage = PathFormKey(stringValue: "stage")
    static let input = PathFormKey(stringValue: "input")
    static let sameAsInput = PathFormKey(stringValue: "same_as_input")
}

/// Encode `forms` beside `input`: a form with the same UTF-8 bytes as `input`
/// is listed in `same_as_input` and omitted, a different form is a string, an
/// underivable form is an explicit null.
func encodePathForms(_ container: inout KeyedEncodingContainer<PathFormKey>, input: String,
                     forms: [(String, String?)]) throws {
    var sameAsInput: [String] = []
    for (name, value) in forms {
        let key = PathFormKey(stringValue: name)
        if let value, value.utf8.elementsEqual(input.utf8) {
            sameAsInput.append(name)
        } else if let value {
            try container.encode(value, forKey: key)
        } else {
            // Explicit null: the host computed this form and got nothing.
            try container.encodeNil(forKey: key)
        }
    }
    try container.encode(sameAsInput, forKey: .sameAsInput)
}

/// Decode the forms in `formNames` under the same rule. The compact marker is
/// required: each form is listed, a string or an explicit null, exclusively.
func decodePathForms(_ container: KeyedDecodingContainer<PathFormKey>, input: String,
                     formNames: [String]) throws -> [String: String?] {
    guard container.contains(.sameAsInput) else {
        throw DecodingError.dataCorruptedError(forKey: .sameAsInput, in: container,
            debugDescription: "path diagnostics require same_as_input")
    }
    let sameAsInput = try container.decode([String].self, forKey: .sameAsInput)
    if Set(sameAsInput).count != sameAsInput.count || !Set(sameAsInput).isSubset(of: Set(formNames)) {
        throw DecodingError.dataCorruptedError(forKey: .sameAsInput, in: container,
            debugDescription: "same_as_input must contain unique supported form names")
    }
    var values: [String: String?] = [:]
    for name in formNames {
        let key = PathFormKey(stringValue: name)
        let listed = sameAsInput.contains(name)
        if listed == container.contains(key) {
            throw DecodingError.dataCorruptedError(forKey: key, in: container,
                debugDescription: "form must be either listed in same_as_input or present, exclusively")
        }
        if listed {
            values[name] = .some(input)
            continue
        }
        let value = try container.decodeIfPresent(String.self, forKey: key)
        if let value, value.utf8.elementsEqual(input.utf8) {
            throw DecodingError.dataCorruptedError(forKey: key, in: container,
                debugDescription: "a form with identical UTF-8 bytes must be listed in same_as_input")
        }
        values[name] = .some(value)
    }
    return values
}

// The unsandboxed host's after-orchestration resolution of a file or exec
// attempt target. `realpath_resolved` follows the leaf; `parent_realpath_resolved`
// resolves the parent and keeps the leaf literal, the form the kernel names for
// a created or unlinked path. Neither establishes what the worker's own syscall
// resolved: these diagnostics describe later resolution by the host, not the
// identity of an object accessed by the worker.
struct PWRunnerAttemptPathDiagnostics: Codable {
    static let formNames = ["realpath_resolved", "parent_realpath_resolved"]

    var observer: String?
    var stage: String?
    var input: String
    var realpath_resolved: String?
    var parent_realpath_resolved: String?

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

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: PathFormKey.self)
        try container.encodeIfPresent(observer, forKey: .observer)
        try container.encodeIfPresent(stage, forKey: .stage)
        try container.encode(input, forKey: .input)
        try encodePathForms(&container, input: input,
            forms: [("realpath_resolved", realpath_resolved), ("parent_realpath_resolved", parent_realpath_resolved)])
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: PathFormKey.self)
        observer = try container.decodeIfPresent(String.self, forKey: .observer)
        stage = try container.decodeIfPresent(String.self, forKey: .stage)
        input = try container.decode(String.self, forKey: .input)
        let decoded = try decodePathForms(container, input: input, formNames: Self.formNames)
        realpath_resolved = decoded["realpath_resolved"] ?? nil
        parent_realpath_resolved = decoded["parent_realpath_resolved"] ?? nil
    }
}
