import Darwin
import Foundation
import Security
@testable import PWRunnerCore

// This driver changes only per-actor launch paths after production translation.
// Planning, actor protocol, native workers, scheduling and reply assembly remain
// the repository's implementations. It is not an XPC or public-admission test.
let args = CommandLine.arguments
let parsed = try pwRunnerDecodeJSON(PWRunnerRunSpec.self, from: Data(contentsOf: URL(fileURLWithPath: args[1])))
guard case .success(let plan) = normalizeActorPlan(parsed) else { fatalError("plan refused") }
let translation = ActorTranslation(plan: plan, parsed: parsed, workerExecutablePath: args[2])
var inputs = translation.inputs
for i in inputs.indices { inputs[i].workerExecutablePath = args[2 + i] }
let validator = args[2 + inputs.count]
let input = ActorScheduleInput(actors: inputs, applies: plan.actors.map { $0.applies },
                              schedule: translation.schedule, authority: translation.authority)
var queries = plan.phases.map { _ in [ValidatorQueryDecision]() }
var results = plan.phases.map { _ -> ValidatorClientResult? in nil }
var statuses = plan.phases.map { _ in "not_reached" }
var processObservations: [[String: Any]] = []
let outcome = ActorScheduler.run(input) { phase, actor, pid in
    var observation: [String: Any] = ["phase": phase, "actor": actor, "pid": pid]
    var code: SecCode?
    let attributes = [kSecGuestAttributePid as String: NSNumber(value: pid)] as CFDictionary
    let rc = SecCodeCopyGuestWithAttributes(nil, attributes, SecCSFlags(), &code)
    observation["guest_rc"] = rc
    if let code {
        observation["validity_rc"] = SecCodeCheckValidity(code, SecCSFlags(), nil)
        var staticCode: SecStaticCode?
        let staticRC = SecCodeCopyStaticCode(code, SecCSFlags(), &staticCode)
        observation["static_code_rc"] = staticRC
        var info: CFDictionary?
        let infoRC = staticCode.map { SecCodeCopySigningInformation($0, SecCSFlags(rawValue: kSecCSSigningInformation), &info) } ?? errSecParam
        observation["signing_rc"] = infoRC
        if let info = info as? [String: Any] {
            observation["entitlements"] = info[kSecCodeInfoEntitlementsDict as String] ?? [:]
            observation["identifier"] = info[kSecCodeInfoIdentifier as String]
            observation["team_id"] = info[kSecCodeInfoTeamIdentifier as String]
            if let path = info[kSecCodeInfoMainExecutable as String] as? URL { observation["path"] = path.path }
            if let hash = info[kSecCodeInfoUnique as String] as? Data {
                observation["cdhash"] = hash.map { String(format: "%02x", $0) }.joined()
            }
        }
    }
    processObservations.append(observation)
    queries[phase] = planValidatorQueries(plan.phases[phase].actions.compactMap { $0.probe })
    let probes = queries[phase].compactMap { $0.probe }
    if probes.isEmpty { statuses[phase] = "not_needed"; return }
    results[phase] = runValidator(ValidatorClientInput(executablePath: validator, targetPid: pid,
                                  probes: probes, verdictReadTimeoutMs: 5_000))
    statuses[phase] = "collected"
}
var reply = assembleActorReply(parsed: parsed, plan: plan, translation: translation, outcome: outcome,
                              queryPlans: queries, validatorResults: results,
                              collectionStatuses: statuses, bundleId: "authority-prototype")
reply.steps = enrichPathDiagnostics(steps: reply.steps)
let replyObject = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(reply))
let result: [String: Any] = ["reply": replyObject, "live_processes": processObservations,
                           "launch_paths": inputs.map { $0.workerExecutablePath },
                           "host_pid": getpid(), "quiescence": outcome.actors.map { $0.quiescence }]
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]))
