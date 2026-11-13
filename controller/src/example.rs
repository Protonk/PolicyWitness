//! The example specimen this build defines.
//!
//! `policy-witness example` prints the constant below with the binary's own
//! contract identity, through the parser, gate and serializer `run` uses for
//! its held request. The command reads no file and launches nothing.

use std::ffi::OsString;
use std::io::Write;

use serde_json::Value;

use crate::cli;
use crate::json_contract::BUILD_CONTRACT;
use crate::request_patch::{parse_request, validate_contract};

// The contract generator extracts this constant and accepts this one form: a
// single `r#"`...`"#` raw string holding a JSON object without `contract`.
pub const EXAMPLE_DOCUMENT: &str = r#"{"specimen_id":"example","policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default)"},"probe_plan":[{"step_id":"read-hosts","sandbox_check":{"operation":"file-read-data","filter":{"kind":"path","value":"/etc/hosts"}},"attempt":{"kind":"file","action":"open_read","target":"/etc/hosts"}}]}"#;

/// Why no document was printed. Every case is process exit 2.
#[derive(Debug, PartialEq, Eq)]
pub enum Refusal {
    Usage,
    /// The binary's identity is empty or `unbound`.
    NoPublicIdentity,
    /// The request-failure code from parsing or the contract gate.
    Request(String),
    Write,
}

/// The printed bytes: the document as `run` holds it, then one framing newline.
pub fn render(document: &str, identity: &str) -> Result<String, Refusal> {
    if identity.is_empty() || identity == "unbound" {
        return Err(Refusal::NoPublicIdentity);
    }
    let mut value =
        parse_request(document).map_err(|error| Refusal::Request(error.failure.code))?;
    value
        .as_object_mut()
        .expect("parse_request admits only objects")
        .insert("contract".into(), Value::String(identity.into()));
    validate_contract(&value, identity).map_err(|error| Refusal::Request(error.failure.code))?;
    let mut text = serde_json::to_string_pretty(&value)
        .map_err(|_| Refusal::Request("invalid_json".into()))?;
    text.push('\n');
    Ok(text)
}

/// Nothing is written unless the whole document rendered and passed the gate.
/// Only complete output with a successful flush is success.
fn emit(
    args: &[OsString],
    document: &str,
    identity: &str,
    out: &mut dyn Write,
) -> Result<(), Refusal> {
    if !args.is_empty() {
        return Err(Refusal::Usage);
    }
    let text = render(document, identity)?;
    out.write_all(text.as_bytes())
        .and_then(|()| out.flush())
        .map_err(|_| Refusal::Write)
}

pub fn cmd_example(args: &[OsString]) -> i32 {
    let mut out = std::io::stdout().lock();
    match emit(args, EXAMPLE_DOCUMENT, BUILD_CONTRACT, &mut out) {
        Ok(()) => 0,
        Err(refusal) => {
            let reason = match refusal {
                Refusal::Usage => cli::USAGE.to_string(),
                Refusal::NoPublicIdentity => {
                    "policy-witness example: this build has no public identity".into()
                }
                Refusal::Request(code) => {
                    format!("policy-witness example: the example is not admissible: {code}")
                }
                Refusal::Write => "policy-witness example: failed to write stdout".into(),
            };
            // The reason is for a person. An unwritable stderr leaves the
            // exit status as the whole report.
            let _ = writeln!(std::io::stderr(), "{reason}");
            2
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io;

    fn emitted(identity: &str) -> String {
        let mut out = Vec::new();
        emit(&[], EXAMPLE_DOCUMENT, identity, &mut out).unwrap();
        String::from_utf8(out).unwrap()
    }

    #[test]
    fn rendered_document_is_the_constant_with_the_given_identity() {
        let defined: Value = serde_json::from_str(EXAMPLE_DOCUMENT).unwrap();
        assert!(defined.get("contract").is_none());
        for identity in [
            BUILD_CONTRACT,
            "development:84448fb421a5a0e4acdbce236dae143e04df6d425c7a258c12df447e9b762444",
            "release:v1.0.0",
            "quote\" backslash\\ newline\n tab\t \u{1} é",
        ] {
            let text = emitted(identity);
            let body = text.strip_suffix('\n').expect("one framing newline");
            assert!(!body.ends_with('\n'));
            let mut value: Value = serde_json::from_str(body).unwrap();
            let contract = value.as_object_mut().unwrap().remove("contract");
            assert_eq!(contract, Some(Value::String(identity.into())));
            assert_eq!(value, defined);
        }
    }

    #[test]
    fn refusals_are_typed_and_write_nothing() {
        for (args, document, identity, expected) in [
            (
                vec![],
                EXAMPLE_DOCUMENT,
                "unbound",
                Refusal::NoPublicIdentity,
            ),
            (vec![], EXAMPLE_DOCUMENT, "", Refusal::NoPublicIdentity),
            (
                vec![],
                r#"{"specimen_id":"#,
                "test:bound",
                Refusal::Request("invalid_json".into()),
            ),
            (
                vec![],
                "[]",
                "test:bound",
                Refusal::Request("type_mismatch".into()),
            ),
            (
                vec![],
                "null",
                "test:bound",
                Refusal::Request("missing_value".into()),
            ),
            (
                vec![OsString::from("--help")],
                EXAMPLE_DOCUMENT,
                "test:bound",
                Refusal::Usage,
            ),
            (
                vec![OsString::from("read-hosts")],
                EXAMPLE_DOCUMENT,
                "test:bound",
                Refusal::Usage,
            ),
            // An argument is refused before the identity is consulted.
            (
                vec![OsString::from("x")],
                EXAMPLE_DOCUMENT,
                "unbound",
                Refusal::Usage,
            ),
        ] {
            let mut out = Vec::new();
            assert_eq!(emit(&args, document, identity, &mut out), Err(expected));
            assert!(out.is_empty());
        }
    }

    /// Accepts at most `step` bytes per write, fails the write that would pass
    /// `fail_after` accepted bytes, and optionally fails its flush.
    struct Limited {
        accepted: Vec<u8>,
        step: usize,
        fail_after: Option<usize>,
        fail_flush: bool,
        flushed: bool,
    }

    impl Limited {
        fn new(step: usize, fail_after: Option<usize>, fail_flush: bool) -> Self {
            Limited {
                accepted: Vec::new(),
                step,
                fail_after,
                fail_flush,
                flushed: false,
            }
        }
    }

    impl Write for Limited {
        fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
            if self
                .fail_after
                .is_some_and(|limit| self.accepted.len() >= limit)
            {
                return Err(io::Error::other("controlled write failure"));
            }
            let mut count = bytes.len().min(self.step);
            if let Some(limit) = self.fail_after {
                count = count.min(limit - self.accepted.len());
            }
            self.accepted.extend_from_slice(&bytes[..count]);
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
    fn only_complete_output_with_a_successful_flush_succeeds() {
        let complete = emitted(BUILD_CONTRACT).into_bytes();

        let mut short = Limited::new(7, None, false);
        assert_eq!(
            emit(&[], EXAMPLE_DOCUMENT, BUILD_CONTRACT, &mut short),
            Ok(())
        );
        assert_eq!(short.accepted, complete);
        assert!(short.flushed);

        let mut partial = Limited::new(7, Some(40), false);
        assert_eq!(
            emit(&[], EXAMPLE_DOCUMENT, BUILD_CONTRACT, &mut partial),
            Err(Refusal::Write)
        );
        assert_eq!(partial.accepted, complete[..40]);

        let mut unflushed = Limited::new(usize::MAX, None, true);
        assert_eq!(
            emit(&[], EXAMPLE_DOCUMENT, BUILD_CONTRACT, &mut unflushed),
            Err(Refusal::Write)
        );
        assert_eq!(unflushed.accepted, complete);
        assert!(!unflushed.flushed);
    }
}
