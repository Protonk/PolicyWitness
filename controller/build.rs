// build.sh derives the build stamp from git and passes it through these
// variables; without them (plain `cargo build`) every value reads "unknown".
// Declaring them here makes cargo rebuild when only the stamp changed.
fn main() {
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
