// The shipped Rust executables are macOS code for Apple Silicon: thin arm64
// Mach-O for one Cargo target, which build.sh selects with --target. TARGET is
// the platform this package is being compiled for; a build script's own cfg!
// describes the machine running the script, which may differ. Any other target,
// including a direct `cargo build --target x86_64-apple-darwin`, stops here,
// before the package compiles.
const OUTPUT_TRIPLE: &str = "aarch64-apple-darwin";

fn main() {
    let target = std::env::var("TARGET").unwrap_or_default();
    if target != OUTPUT_TRIPLE {
        eprintln!(
            "error: the controller package builds only for {OUTPUT_TRIPLE} (thin arm64 macOS executables); Cargo's TARGET is {target:?}"
        );
        std::process::exit(1);
    }
    // build.sh derives the build stamp from git and passes it through these
    // variables; without them (plain `cargo build`) every value reads "unknown".
    // Declaring them here makes cargo rebuild when only the stamp changed.
    for name in [
        "PW_BUILD_VERSION",
        "PW_BUILD_NUMBER",
        "PW_BUILD_DESCRIBE",
        "PW_BUILD_COMMIT",
    ] {
        println!("cargo:rerun-if-env-changed={name}");
    }
    println!("cargo:rerun-if-changed=../docs/contract.json");
}
