import Foundation
@testable import PWRunnerCore

// Invoke the production static binder without constructing a specimen,
// launching a worker, or replacing any Security/read-back call.
struct BindingObservation: Encodable {
    var compiled_identity: String
    var inventory: PWRunnerEquipmentInventory
    var bindings: [PWRunnerEquipmentBinding]
    var entitlements: [PWRunnerEquipmentEntitlements]
    var actors: [PWRunnerActorEquipment]
    var executable_paths: [String]?
    var failure_stage: String?
    var failure_code: String?
    var failure_reason: String?
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
let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys]
FileHandle.standardOutput.write(try encoder.encode(observation))
FileHandle.standardOutput.write(Data([10]))
