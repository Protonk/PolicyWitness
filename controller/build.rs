// The shipped Rust executables are macOS code for Apple Silicon: thin arm64
// Mach-O for one Cargo target, which build.sh selects with --target. TARGET is
// the platform this package is being compiled for; a build script's own cfg!
// describes the machine running the script, which may differ. Any other target,
// including a direct `cargo build --target x86_64-apple-darwin`, stops here,
// before the package compiles.
//
// The script also renders the help cards and the interface inventory from the
// definitions the binary compiles: the modules below are the binary's own
// source files. The binary embeds the cards from OUT_DIR. The inventory is
// compared with the committed copy, and a stale copy stops the build.
// The binary uses items of the included modules that this script does not.
#![allow(dead_code)]

#[path = "src/example_document.rs"]
mod example_document;
#[path = "src/interface/mod.rs"]
mod interface;
#[path = "src/json_contract.rs"]
mod json_contract;
#[path = "src/run_result.rs"]
mod run_result;

#[path = "interface/cards.rs"]
mod cards;
#[path = "interface/inventory.rs"]
mod inventory;

use std::path::{Path, PathBuf};

const OUTPUT_TRIPLE: &str = "aarch64-apple-darwin";
/// The committed inventory, relative to the package.
const COMMITTED_INVENTORY: &str = "interface/inventory.json";
/// Set by the inventory generator's --refresh-inventory mode, which reads the
/// fresh copy from OUT_DIR and replaces the committed one itself.
const REFRESH: &str = "PW_INTERFACE_REFRESH";

fn stop(message: &str) -> ! {
    eprintln!("error: {message}");
    std::process::exit(1);
}

fn write(path: &Path, text: &str) {
    std::fs::create_dir_all(path.parent().unwrap())
        .and_then(|()| std::fs::write(path, text))
        .unwrap_or_else(|error| stop(&format!("cannot write {}: {error}", path.display())));
}

fn check_field_sources(root: &Path) {
    use sha2::{Digest, Sha256};
    // A copied Cargo package can use its checked-in export without a checkout.
    if !root.join("docs").is_dir() && !root.join("build.sh").exists() {
        return;
    }
    for (name, expected) in interface::admission_fields::SOURCE_DIGESTS {
        let path = root.join(name);
        println!("cargo:rerun-if-changed={}", path.display());
        let data = std::fs::read(&path).unwrap_or_else(|err| stop(&format!("{name}: {err}")));
        if format!("{:x}", Sha256::digest(data)) != *expected {
            stop(
                "stale request field export: run tests/lib/python.sh docs/generate_interface.py --refresh-inventory",
            );
        }
    }
}

// Only a release tag names a published page. Any other build cites its own tree.
fn documentation_base() -> String {
    const BASE: &str = "https://github.com/Protonk/PolicyWitness/blob";
    let contract = std::env::var("PW_BUILD_CONTRACT").unwrap_or_default();
    match contract.strip_prefix("release:") {
        Some(tag) => format!("{BASE}/{tag}/"),
        None => "Local: ".into(),
    }
}

fn write_field_help(out: &Path) {
    let base = documentation_base();
    let mut source = String::from("fn field_text(id: &str) -> &'static str { match id {\n");
    for entry in interface::admission_fields::FIELDS
        .iter()
        .filter_map(|f| f.entry)
    {
        let text = format!(
            "{}\n{}  {base}{}\n",
            entry.key, entry.body, entry.destination
        );
        source.push_str(&format!("{:?} => {:?},\n", entry.id, text));
    }
    source.push_str("_ => unreachable!(\"unregistered help entry\"), } }\n");
    source.push_str(&format!(
        "const ADMISSION_REFERENCE: &str = {:?};\n",
        format!("{base}docs/LIMITS.md#specimen-admission")
    ));
    write(&out.join("help/fields.rs"), &source);
}

fn main() {
    let target = std::env::var("TARGET").unwrap_or_default();
    if target != OUTPUT_TRIPLE {
        stop(&format!(
            "the controller package builds only for {OUTPUT_TRIPLE} (thin arm64 macOS executables); Cargo's TARGET is {target:?}"
        ));
    }
    // build.sh derives the build stamp from git and passes it through these
    // variables; without them (plain `cargo build`) every value reads "unknown".
    // Declaring them here makes cargo rebuild when only the stamp changed.
    for name in [
        "PW_BUILD_CONTRACT",
        "PW_BUILD_VERSION",
        "PW_BUILD_NUMBER",
        "PW_BUILD_DESCRIBE",
        "PW_BUILD_COMMIT",
        REFRESH,
    ] {
        println!("cargo:rerun-if-env-changed={name}");
    }
    println!("cargo:rerun-if-changed={COMMITTED_INVENTORY}");

    let out = PathBuf::from(std::env::var_os("OUT_DIR").expect("cargo sets OUT_DIR"));
    let package = PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap());
    check_field_sources(package.parent().unwrap());
    write_field_help(&out);
    let rendered =
        cards::render_all().unwrap_or_else(|error| stop(&format!("help cards: {error}")));
    for card in &rendered {
        write(
            &out.join("help")
                .join(format!("{}.txt", inventory::card_name(card.topic))),
            &card.text,
        );
    }
    let fresh = inventory::render(&rendered);
    write(&out.join("interface/inventory.json"), &fresh);

    if std::env::var_os(REFRESH).is_some() {
        return;
    }
    let committed =
        Path::new(&std::env::var_os("CARGO_MANIFEST_DIR").unwrap()).join(COMMITTED_INVENTORY);
    match std::fs::read_to_string(&committed) {
        Ok(text) if text == fresh => {}
        Ok(_) => stop(&format!(
            "controller/{COMMITTED_INVENTORY} is stale: the interface definitions or a help card changed. Regenerate with: tests/lib/python.sh docs/generate_interface.py --refresh-inventory"
        )),
        Err(error) => stop(&format!(
            "cannot read controller/{COMMITTED_INVENTORY}: {error}"
        )),
    }
}
