//! Installed teaching inputs. Publication and independent `run` admission differ.
use std::ffi::OsString;
use std::io::Write;
use std::path::Path;

use serde_json::Value;

use crate::json_contract::BUILD_CONTRACT;
use crate::request_patch::{parse_request, validate_contract};

const CREATE: &str = include_str!("lessons/create.json");
const CAPTURE_TYPO: &str = include_str!("lessons/capture_typo.json");

#[derive(Debug, PartialEq, Eq)]
enum Refusal {
    Usage,
    Target,
    NoPublicIdentity,
    Render,
    Write,
}

fn render(args: &[OsString], identity: &str) -> Result<String, Refusal> {
    if args.len() != 3 || args[1] != "--target" {
        return Err(Refusal::Usage);
    }
    let document = match args[0].to_str() {
        Some("create") => CREATE,
        Some("capture_typo") => CAPTURE_TYPO,
        _ => return Err(Refusal::Usage),
    };
    let target = args[2].to_str().ok_or(Refusal::Target)?;
    if target.is_empty() || target.contains('\0') || !Path::new(target).is_absolute() {
        return Err(Refusal::Target);
    }
    if identity.is_empty() || identity == "unbound" {
        return Err(Refusal::NoPublicIdentity);
    }
    let mut value = parse_request(document).map_err(|_| Refusal::Render)?;
    value["contract"] = Value::String(identity.into());
    value["probe_plan"][0]["sandbox_check"]["filter"]["value"] = Value::String(target.into());
    value["probe_plan"][0]["attempt"]["target"] = Value::String(target.into());
    // Only the preparatory identity gate runs here. The typo remains intentional.
    validate_contract(&value, identity).map_err(|_| Refusal::Render)?;
    let mut text = serde_json::to_string_pretty(&value).map_err(|_| Refusal::Render)?;
    text.push('\n');
    Ok(text)
}

fn emit(args: &[OsString], identity: &str, out: &mut dyn Write) -> Result<(), Refusal> {
    let text = render(args, identity)?;
    out.write_all(text.as_bytes())
        .and_then(|()| out.flush())
        .map_err(|_| Refusal::Write)
}

pub fn cmd_lesson(args: &[OsString]) -> i32 {
    match emit(args, BUILD_CONTRACT, &mut std::io::stdout().lock()) {
        Ok(()) => 0,
        Err(refusal) => {
            let reason = match refusal {
                Refusal::Usage => "expected lesson <create|capture_typo> --target PATH",
                Refusal::Target => "target must be an absolute UTF-8 path without NUL",
                Refusal::NoPublicIdentity => "this build has no public identity",
                Refusal::Render => "could not render the teaching input",
                Refusal::Write => "failed to write stdout",
            };
            let _ = writeln!(std::io::stderr(), "policy-witness lesson: {reason}");
            2
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io;
    use std::os::unix::ffi::OsStringExt;

    fn args(selector: &str, target: &str) -> Vec<OsString> {
        [selector, "--target", target]
            .into_iter()
            .map(Into::into)
            .collect()
    }

    #[test]
    fn both_inputs_preserve_target_identity_and_intentional_difference() {
        let target = "/missing/../quote\"\\ newline\n tab\t é";
        for identity in [BUILD_CONTRACT, "test:quote\"\\\nidentity"] {
            let create = render(&args("create", target), identity).unwrap();
            let typo = render(&args("capture_typo", target), identity).unwrap();
            assert!(create.ends_with('\n') && !create.ends_with("\n\n"));
            let mut good: Value = serde_json::from_str(&create).unwrap();
            let bad: Value = serde_json::from_str(&typo).unwrap();
            assert_eq!(good["contract"], identity);
            assert_eq!(good["specimen_id"], "request-grammar");
            assert_eq!(good["probe_plan"][0]["step_id"], "create");
            assert_eq!(good["policy"]["format"], "sbpl");
            assert_eq!(good["policy"]["sbpl_source"], "(version 1) (allow default)");
            assert_eq!(good["probe_plan"].as_array().unwrap().len(), 1);
            assert_eq!(
                good["probe_plan"][0]["sandbox_check"]["operation"],
                "file-write-create"
            );
            assert_eq!(
                good["probe_plan"][0]["sandbox_check"]["filter"]["kind"],
                "path"
            );
            assert_eq!(good["probe_plan"][0]["attempt"]["kind"], "file");
            assert_eq!(good["probe_plan"][0]["attempt"]["action"], "create");
            assert_eq!(good["probe_plan"][0]["attempt"]["target"], target);
            assert_eq!(
                good["probe_plan"][0]["sandbox_check"]["filter"]["value"],
                target
            );
            assert!(good["policy"].get("capture_nonce").is_none());
            assert!(good["policy"].get("capture_compiled_profile").is_none());
            good["policy"]["capture_compiled_profiel"] = Value::Bool(true);
            assert_eq!(good, bad);
        }
    }

    #[test]
    fn argument_target_and_identity_refusals_write_nothing() {
        let valid = args("create", "/absent");
        let mut invalid_utf8 = valid.clone();
        invalid_utf8[2] = OsString::from_vec(vec![b'/', 255]);
        let mut extra = valid.clone();
        extra.push("extra".into());
        let mut duplicate = valid.clone();
        duplicate.extend([OsString::from("--target"), OsString::from("/other")]);
        for (arguments, identity, expected) in [
            (vec![], BUILD_CONTRACT, Refusal::Usage),
            (vec!["create".into()], BUILD_CONTRACT, Refusal::Usage),
            (args("unknown", "/x"), BUILD_CONTRACT, Refusal::Usage),
            (
                vec!["create".into(), "--unknown".into(), "/x".into()],
                BUILD_CONTRACT,
                Refusal::Usage,
            ),
            (extra, BUILD_CONTRACT, Refusal::Usage),
            (duplicate, BUILD_CONTRACT, Refusal::Usage),
            (args("create", ""), BUILD_CONTRACT, Refusal::Target),
            (args("create", "relative"), BUILD_CONTRACT, Refusal::Target),
            (
                args("create", "/nul\0path"),
                BUILD_CONTRACT,
                Refusal::Target,
            ),
            (invalid_utf8, BUILD_CONTRACT, Refusal::Target),
            (valid.clone(), "", Refusal::NoPublicIdentity),
            (valid, "unbound", Refusal::NoPublicIdentity),
        ] {
            let mut output = Vec::new();
            assert_eq!(emit(&arguments, identity, &mut output), Err(expected));
            assert!(output.is_empty());
        }
    }

    struct Writer {
        bytes: Vec<u8>,
        fail_after: Option<usize>,
        fail_flush: bool,
        flushed: bool,
    }
    impl Write for Writer {
        fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
            let remaining = self
                .fail_after
                .unwrap_or(usize::MAX)
                .saturating_sub(self.bytes.len());
            if remaining == 0 {
                return Err(io::Error::other("controlled write failure"));
            }
            let count = bytes.len().min(7).min(remaining);
            self.bytes.extend_from_slice(&bytes[..count]);
            Ok(count)
        }
        fn flush(&mut self) -> io::Result<()> {
            if self.fail_flush {
                return Err(io::Error::other("controlled flush failure"));
            }
            self.flushed = true;
            Ok(())
        }
    }

    #[test]
    fn complete_publication_requires_all_writes_and_flush() {
        for selector in ["create", "capture_typo"] {
            let arguments = args(selector, "/absent");
            let expected = render(&arguments, BUILD_CONTRACT).unwrap().into_bytes();
            for (fail_after, fail_flush) in [(None, false), (Some(30), false), (None, true)] {
                let mut writer = Writer {
                    bytes: vec![],
                    fail_after,
                    fail_flush,
                    flushed: false,
                };
                let result = emit(&arguments, BUILD_CONTRACT, &mut writer);
                if fail_after.is_some() || fail_flush {
                    assert_eq!(result, Err(Refusal::Write));
                    assert!(!writer.flushed);
                } else {
                    assert_eq!(result, Ok(()));
                    assert!(writer.flushed);
                }
                assert_eq!(
                    writer.bytes,
                    expected[..fail_after.unwrap_or(expected.len())]
                );
            }
        }
    }
}
