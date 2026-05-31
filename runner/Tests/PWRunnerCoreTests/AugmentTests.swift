import Foundation
@testable import PWRunnerCore

// The `augments` field on PWRunnerPolicySpec exists on the wire so
// callers can opt into named controller-resolved augments without the
// runner needing augment-aware code. By the time the runner sees the
// request, the controller has already stripped the field. These tests
// pin the Codable round-trip so a future refactor that changes the
// field's optionality (e.g. defaulting to []) doesn't accidentally
// surface the field on the runner's parsed view of an
// already-resolved request.

func runAugmentTests(_ tk: TestKit) {
    tk.group("PWRunnerPolicySpec.augments: Codable round-trip") {

        tk.run("absent field decodes as nil") {
            let json = #"{"format":"sbpl","sbpl_source":"(version 1)\n"}"#
            let data = Data(json.utf8)
            let spec = try pwRunnerDecodeJSON(PWRunnerPolicySpec.self, from: data)
            try expectNil(spec.augments)
        }

        tk.run("explicit null decodes as nil") {
            let json = #"{"format":"sbpl","sbpl_source":"(version 1)\n","augments":null}"#
            let data = Data(json.utf8)
            let spec = try pwRunnerDecodeJSON(PWRunnerPolicySpec.self, from: data)
            try expectNil(spec.augments)
        }

        tk.run("populated array round-trips") {
            let spec = PWRunnerPolicySpec(
                format: PWRunnerWire.policyFormatSbpl,
                sbpl_source: "(version 1)\n",
                augments: ["exec_baseline", "another"]
            )
            let data = try pwRunnerEncodeJSON(spec)
            let decoded = try pwRunnerDecodeJSON(PWRunnerPolicySpec.self, from: data)
            try expectEqual(decoded.augments ?? [], ["exec_baseline", "another"])
        }

        tk.run("nil augments omits or nulls the wire key (consumer-visible)") {
            // Synthesized Codable omits nil optionals. If a future
            // custom encoder emits explicit null instead, the
            // semantic contract still holds: callers see "no
            // augments." Pin the absent-or-null behavior so a
            // regression that emits `"augments":[]` (which would
            // misrepresent "no augments" as "empty list of
            // augments applied") is caught.
            let spec = PWRunnerPolicySpec(
                format: PWRunnerWire.policyFormatSbpl,
                sbpl_source: "(version 1)\n"
            )
            let data = try pwRunnerEncodeJSON(spec)
            let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            try expectNotNil(obj)
            if let value = obj?["augments"] {
                // If the key is present at all, it must be NSNull —
                // never an empty array, which would conflate the two
                // states.
                try expectTrue(value is NSNull, "augments key, if emitted, must be null (got \(type(of: value)))")
            }
        }
    }
}
