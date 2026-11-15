//! Build-bound developer input. Publication and independent `run` admission differ.
use std::ffi::OsString;
use std::io::Write;
use std::path::Path;

use serde_json::Value;

use crate::json_contract::BUILD_CONTRACT;
use crate::request_patch::{parse_request, validate_contract};

const READ: &str = include_str!("test_inputs/read.json");

#[derive(Debug, PartialEq, Eq)]
enum Refusal {
    Usage,
    Target,
    NoPublicIdentity,
    Render,
    Write,
}

fn render_template(args: &[OsString], identity: &str, document: &str) -> Result<String, Refusal> {
    if args.len() != 3 || args[1] != "--target" {
        return Err(Refusal::Usage);
    }
    if args[0] != "read" {
        return Err(Refusal::Usage);
    }
    let target = args[2].to_str().ok_or(Refusal::Target)?;
    if target.is_empty() || target.contains('\0') || !Path::new(target).is_absolute() {
        return Err(Refusal::Target);
    }
    if identity.is_empty() || identity == "unbound" {
        return Err(Refusal::NoPublicIdentity);
    }
    let mut value = parse_request(document).map_err(|_| Refusal::Render)?;
    // Validate the complete fixed body before indexing. A malformed embedded
    // template is a rendering refusal, never a panic or a partially bound input.
    let expected = serde_json::json!({
        "specimen_id": "test-input",
        "policy": {"format": "sbpl", "sbpl_source": "(version 1)\n(allow default)"},
        "probe_plan": [{"step_id": "read-target",
            "sandbox_check": {"operation": "file-read-data",
                "filter": {"kind": "path", "value": "$EFFECT"}},
            "attempt": {"kind": "file", "action": "read_fresh", "target": "$EFFECT"}}]
    });
    if value != expected {
        return Err(Refusal::Render);
    }
    value["contract"] = Value::String(identity.into());
    value["probe_plan"][0]["sandbox_check"]["filter"]["value"] = Value::String(target.into());
    value["probe_plan"][0]["attempt"]["target"] = Value::String(target.into());
    // Only the preparatory identity gate runs here; the host owns admission.
    validate_contract(&value, identity).map_err(|_| Refusal::Render)?;
    let mut text = serde_json::to_string_pretty(&value).map_err(|_| Refusal::Render)?;
    text.push('\n');
    Ok(text)
}

#[cfg(test)]
fn render(args: &[OsString], identity: &str) -> Result<String, Refusal> {
    render_template(args, identity, READ)
}

fn emit_template(
    args: &[OsString],
    identity: &str,
    document: &str,
    out: &mut dyn Write,
) -> Result<(), Refusal> {
    let text = render_template(args, identity, document)?;
    out.write_all(text.as_bytes())
        .and_then(|()| out.flush())
        .map_err(|_| Refusal::Write)
}

fn emit(args: &[OsString], identity: &str, out: &mut dyn Write) -> Result<(), Refusal> {
    emit_template(args, identity, READ, out)
}

pub fn cmd_test_input(args: &[OsString]) -> i32 {
    match emit(args, BUILD_CONTRACT, &mut std::io::stdout().lock()) {
        Ok(()) => 0,
        Err(refusal) => {
            let reason = match refusal {
                Refusal::Usage => "expected test-input read --target PATH",
                Refusal::Target => "target must be an absolute UTF-8 path without NUL",
                Refusal::NoPublicIdentity => "this build has no public identity",
                Refusal::Render => "could not render the developer input",
                Refusal::Write => "failed to write stdout",
            };
            let _ = writeln!(std::io::stderr(), "policy-witness test-input: {reason}");
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
    fn read_input_preserves_target_identity_and_fixed_workload() {
        let target = "/missing/../$EFFECT quote\"\\ newline\n tab\t é";
        for identity in [BUILD_CONTRACT, "test:quote\"\\\nidentity"] {
            let text = render(&args("read", target), identity).unwrap();
            assert!(text.ends_with('\n') && !text.ends_with("\n\n"));
            let value: Value = serde_json::from_str(&text).unwrap();
            let mut expected: Value = serde_json::from_str(READ).unwrap();
            expected["contract"] = identity.into();
            expected["probe_plan"][0]["sandbox_check"]["filter"]["value"] = target.into();
            expected["probe_plan"][0]["attempt"]["target"] = target.into();
            assert_eq!(value, expected);
        }
    }

    #[test]
    fn malformed_templates_refuse_before_output() {
        let baseline: Value = serde_json::from_str(READ).unwrap();
        let mut documents = vec!["{invalid".to_owned(), "null".to_owned(), "[]".to_owned()];
        // Each fixed scalar, container and operand is independently malformed.
        fn variants(value: &Value, root: &Value, path: &str, output: &mut Vec<String>) {
            if !path.is_empty() {
                let mut changed = root.clone();
                *changed.pointer_mut(path).unwrap() = Value::Null;
                output.push(serde_json::to_string(&changed).unwrap());
                let mut changed = root.clone();
                *changed.pointer_mut(path).unwrap() = Value::String("wrong".into());
                output.push(serde_json::to_string(&changed).unwrap());
            }
            match value {
                Value::Object(members) => {
                    for (key, child) in members {
                        let mut changed = root.clone();
                        changed
                            .pointer_mut(path)
                            .unwrap()
                            .as_object_mut()
                            .unwrap()
                            .remove(key);
                        output.push(serde_json::to_string(&changed).unwrap());
                        variants(child, root, &format!("{path}/{key}"), output);
                    }
                    let mut changed = root.clone();
                    changed
                        .pointer_mut(path)
                        .unwrap()
                        .as_object_mut()
                        .unwrap()
                        .insert("unexpected".into(), true.into());
                    output.push(serde_json::to_string(&changed).unwrap());
                }
                Value::Array(items) => {
                    let mut changed = root.clone();
                    changed
                        .pointer_mut(path)
                        .unwrap()
                        .as_array_mut()
                        .unwrap()
                        .clear();
                    output.push(serde_json::to_string(&changed).unwrap());
                    let mut changed = root.clone();
                    changed
                        .pointer_mut(path)
                        .unwrap()
                        .as_array_mut()
                        .unwrap()
                        .push(items[0].clone());
                    output.push(serde_json::to_string(&changed).unwrap());
                    for (index, child) in items.iter().enumerate() {
                        variants(child, root, &format!("{path}/{index}"), output);
                    }
                }
                _ => {}
            }
        }
        variants(&baseline, &baseline, "", &mut documents);
        for document in documents {
            let mut output = Vec::new();
            assert_eq!(
                emit_template(
                    &args("read", "/$EFFECT"),
                    BUILD_CONTRACT,
                    &document,
                    &mut output
                ),
                Err(Refusal::Render),
                "{document}"
            );
            assert!(output.is_empty());
        }
    }

    #[test]
    fn argument_target_and_identity_refusals_write_nothing() {
        let valid = args("read", "/absent");
        let mut invalid_utf8 = valid.clone();
        invalid_utf8[2] = OsString::from_vec(vec![b'/', 255]);
        let mut extra = valid.clone();
        extra.push("extra".into());
        let mut duplicate = valid.clone();
        duplicate.extend([OsString::from("--target"), OsString::from("/other")]);
        for (arguments, identity, expected) in [
            (vec![], BUILD_CONTRACT, Refusal::Usage),
            (vec!["read".into()], BUILD_CONTRACT, Refusal::Usage),
            (args("unknown", "/x"), BUILD_CONTRACT, Refusal::Usage),
            (
                vec!["read".into(), "--unknown".into(), "/x".into()],
                BUILD_CONTRACT,
                Refusal::Usage,
            ),
            (extra, BUILD_CONTRACT, Refusal::Usage),
            (duplicate, BUILD_CONTRACT, Refusal::Usage),
            (args("read", ""), BUILD_CONTRACT, Refusal::Target),
            (args("read", "relative"), BUILD_CONTRACT, Refusal::Target),
            (args("read", "/nul\0path"), BUILD_CONTRACT, Refusal::Target),
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
        for selector in ["read"] {
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
