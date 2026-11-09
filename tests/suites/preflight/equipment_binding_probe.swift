import Foundation
@testable import PWRunnerCore

// Invoke the production static binder without constructing a specimen,
// launching a worker, or replacing any Security/read-back call.
struct BindingObservation: PWPorcelainWritable {
    // Fixture-only record; independently described in tests/lib/porcelain_fixture.py.
    static let porcelainRecordID: UInt16 = 65001
    var compiled_identity: String
    var inventory: PWRunnerEquipmentInventory
    var bindings: [PWRunnerEquipmentBinding]
    var entitlements: [PWRunnerEquipmentEntitlements]
    var actors: [PWRunnerActorEquipment]
    var executable_paths: [String]?
    var failure_stage: String?
    var failure_code: String?
    var failure_reason: String?

    func porcelainWrite() throws -> Data {
        var writer = PWPorcelainRecordWriter(Self.porcelainRecordID)
        try writer.field(1, compiled_identity)
        try writer.field(2, inventory)
        try writer.field(3, bindings)
        try writer.field(4, entitlements)
        try writer.field(5, actors)
        try writer.field(6, executable_paths)
        try writer.field(7, failure_stage)
        try writer.field(8, failure_code)
        try writer.field(9, failure_reason)
        return try writer.finish()
    }
}

precondition(CommandLine.arguments.count == 2)
let preparation = ActorEquipmentPreparation.bind(
    bundleURL: URL(fileURLWithPath: CommandLine.arguments[1]),
    actors: [ActorEquipmentRequest(actorID: "subject", index: 0,
                                   requested: "selected", requiredEntitlements: [])])
let observation = BindingObservation(compiled_identity: PWShmLayout.abiIdentityHex,
    inventory: preparation.inventory, bindings: preparation.bindings,
    entitlements: preparation.entitlements, actors: preparation.actors,
    executable_paths: preparation.executablePaths,
    failure_stage: preparation.failure?.stage, failure_code: preparation.failure?.code,
    failure_reason: preparation.failure?.reason)
FileHandle.standardOutput.write(try pwPorcelainEncode(observation))
