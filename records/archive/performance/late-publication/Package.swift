// swift-tools-version: 5.10
//
// Measurement fixture for the late-publication investigation. It drives the
// shipped C worker through the runner's internal driver seam
// (`runCWorker(_:processCalls:phaseBoundary:)`), reached with `@testable import`
// exactly as runner/Tests/PWRunnerCoreTests does. Nothing here is part of the app bundle
// or the runner package. Build intermediates belong under .tmp/:
//
//   swift build --package-path records/performance/late-publication \
//     --scratch-path .tmp/late-publication-build

import PackageDescription

let package = Package(
    name: "LatePublicationProbe",
    platforms: [
        .macOS("26.0"),
    ],
    dependencies: [
        .package(path: "../../../runner"),
    ],
    targets: [
        .executableTarget(
            name: "LatePublicationProbe",
            dependencies: [.product(name: "PWRunnerCore", package: "runner")],
            path: "Sources"
        ),
    ]
)
