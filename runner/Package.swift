// swift-tools-version: 5.10
//
// PolicyWitness Swift runner — test-only SwiftPM manifest.
//
// This package mirrors the source set that build.sh compiles into the
// PWRunner.xpc service binary, but as a plain library target so we can
// run unit tests against it. Production builds continue to go through
// build.sh; SwiftPM is *not* a parallel build path for the shipped app
// bundle.
//
// The test target is an executableTarget (not a testTarget) because XCTest
// is shipped with full Xcode, not Command Line Tools — and contributors
// frequently have only CLT. The hand-rolled TestKit harness under
// Tests/PWRunnerCoreTests gives us "$swift run PWRunnerCoreTests" that
// works against either toolchain. PWRunnerCore is built with
// -enable-testing so the executable can use `@testable import` to reach
// internal symbols, the same access level a testTarget would have.
//
// The C shim lives in its own target because SwiftPM 5.10 does not allow
// mixed C+Swift sources in a single target. include/PWSandboxCheckShim.h
// is a placeholder that satisfies SwiftPM's publicHeadersPath requirement;
// Swift call sites resolve the C symbols via @_silgen_name and do not
// `import PWSandboxCheckShim`.

import PackageDescription

let package = Package(
    name: "PWRunnerCore",
    platforms: [
        .macOS(.v14),
    ],
    products: [
        .library(name: "PWRunnerCore", targets: ["PWRunnerCore"]),
    ],
    targets: [
        .target(
            name: "PWSandboxCheckShim",
            path: ".",
            sources: ["PWSandboxCheckShim.c"],
            publicHeadersPath: "include"
        ),
        .target(
            name: "PWCWorkerShim",
            path: ".",
            sources: ["PWCWorkerShim.c"],
            publicHeadersPath: "include_cworker"
        ),
        .target(
            name: "PWRunnerCore",
            dependencies: ["PWSandboxCheckShim", "PWCWorkerShim"],
            path: ".",
            exclude: [
                "Package.swift",
                "README.md",
                "PWSandboxCheckShim.c",
                "PWCWorkerShim.c",
                "augments",
                "include",
                "include_cworker",
                "runner-client",
                "services",
                "Tests",
            ],
            sources: [
                "PWRunnerAPI.swift",
                "SandboxLib.swift",
                "SandboxApply.swift",
                "ProbeRunner.swift",
                "PathUtils.swift",
                "Signals.swift",
                "CWorker.swift",
                "ValidatorClient.swift",
                "CWorkerOrchestrator.swift",
                "PWRunnerService.swift",
            ],
            swiftSettings: [
                // Lets the test executable use `@testable import PWRunnerCore`
                // and reach internal symbols. This build flag does not affect
                // build.sh's PWRunner.xpc output, which is compiled separately.
                .unsafeFlags(["-enable-testing"]),
            ]
        ),
        .executableTarget(
            name: "PWRunnerCoreTests",
            dependencies: ["PWRunnerCore"],
            path: "Tests/PWRunnerCoreTests"
        ),
    ]
)
