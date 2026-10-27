// swift-tools-version: 5.10
//
// Measurement fixture for the phase-barrier investigation. It drives the
// shipped C worker through the runner's internal driver seam
// (`runCWorker(_:phaseBoundary:)`), reached with `@testable import` exactly as
// runner/Tests/PWRunnerCoreTests does. Nothing here is part of the app bundle
// or the runner package. Build intermediates belong under .tmp/:
//
//   swift build --package-path records/performance/phase-barrier \
//     --scratch-path .tmp/phase-barrier-build

import PackageDescription

let package = Package(
    name: "PhaseBarrierProbe",
    platforms: [
        .macOS("26.0"),
    ],
    dependencies: [
        .package(path: "../../../runner"),
    ],
    targets: [
        .executableTarget(
            name: "PhaseBarrierProbe",
            dependencies: [.product(name: "PWRunnerCore", package: "runner")],
            path: "Sources"
        ),
    ]
)
