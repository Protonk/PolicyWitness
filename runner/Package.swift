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
// The layout follows SwiftPM convention, so the manifest does not
// enumerate sources: each target's files are auto-discovered under
// Sources/<TargetName>/ (and Tests/PWRunnerCoreTests for the test
// executable). Adding a Swift file to Sources/PWRunnerCore/ needs no
// manifest edit here — but it still must be added to build.sh's swiftc
// invocation, and the source_drift suite enforces that build.sh and the
// on-disk source set agree.
//
// The test target is an executableTarget (not a testTarget) because XCTest
// is shipped with full Xcode, not Command Line Tools — and contributors
// frequently have only CLT. The hand-rolled TestKit harness under
// Tests/PWRunnerCoreTests gives us "$swift run PWRunnerCoreTests" that
// works against either toolchain. PWRunnerCore is built with
// -enable-testing so the executable can use `@testable import` to reach
// internal symbols, the same access level a testTarget would have.
//
// Each C shim lives in its own target because SwiftPM 5.10 does not allow
// mixed C+Swift sources in a single target. Its header sits under the
// target's default publicHeadersPath (Sources/<Shim>/include/) and is a
// placeholder that satisfies SwiftPM's public-headers requirement; Swift
// call sites resolve the C symbols via @_silgen_name and do not `import`
// the shim module.

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
        .target(name: "PWSandboxCheckShim"),
        .target(name: "PWCWorkerShim"),
        .target(
            name: "PWRunnerCore",
            dependencies: ["PWSandboxCheckShim", "PWCWorkerShim"],
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
            // An executableTarget's default search path is Sources/<name>,
            // not Tests/<name> (that default is testTarget-only), so this
            // one path stays explicit.
            path: "Tests/PWRunnerCoreTests"
        ),
    ]
)
