//! Minimal SBPL surface lexer for `(import "NAME")` references.
//!
//! Hand-rolled instead of pulling a Scheme parser because the surface we care
//! about is tiny: paren-balanced, double-quoted strings, semicolon line
//! comments. Returns a deduplicated set at the source level. Anything more
//! structural (import scope, parameter binding, macro expansion) is
//! libsandbox's job.

use std::collections::BTreeSet;

/// Result of an `(import ...)` scan.
///
/// `refs` is the set of literal names captured. `scan_complete` is false when
/// the source contains at least one `(import X)` form where `X` is not a
/// quoted string: the argument is computed at a level the surface lexer does
/// not expand, so the set cannot claim to be the whole closure. Consumers
/// treat an empty `refs` with `scan_complete = false` as "not followed" rather
/// than "no imports".
pub struct ImportScanResult {
    pub refs: BTreeSet<String>,
    pub scan_complete: bool,
}

/// Scan an SBPL source for `(import "NAME")` references and report whether
/// the static scan can stand on its own; see [`ImportScanResult`].
///
/// String literals and `;` line comments are skipped: an `(import "X")`
/// spelled inside a string or a comment does not count. Other keyword forms,
/// including `(param ...)`, are not imports and are never collected.
///
/// Two binaries include this module by path: the controller's dossier and the
/// `sbpl-check` helper both walk the same closure through
/// `sbpl_imports::resolve_imports`.
pub fn import_scan(source: &str) -> ImportScanResult {
    keyword_scan(source, b"import")
}

fn keyword_scan(source: &str, keyword: &[u8]) -> ImportScanResult {
    let bytes = source.as_bytes();
    let mut refs = BTreeSet::new();
    let mut scan_complete = true;
    let mut i = 0usize;
    while i < bytes.len() {
        match bytes[i] {
            b';' => {
                while i < bytes.len() && bytes[i] != b'\n' {
                    i += 1;
                }
            }
            b'"' => {
                i = skip_string(bytes, i);
            }
            b'(' => match try_match_form(bytes, i, keyword) {
                Some(FormMatch::Literal { name, next }) => {
                    refs.insert(name);
                    i = next;
                }
                Some(FormMatch::NonLiteral { next }) => {
                    scan_complete = false;
                    i = next;
                }
                None => i += 1,
            },
            _ => i += 1,
        }
    }
    ImportScanResult {
        refs,
        scan_complete,
    }
}

enum FormMatch {
    /// `(KEYWORD "NAME")`: the argument is a string literal we can capture.
    Literal { name: String, next: usize },
    /// `(KEYWORD X)` where X is a non-string token (typically a macro
    /// parameter from an enclosing `define`). We advance past the form so
    /// the outer walk doesn't re-scan its interior.
    NonLiteral { next: usize },
}

fn try_match_form(bytes: &[u8], start: usize, keyword: &[u8]) -> Option<FormMatch> {
    debug_assert_eq!(bytes[start], b'(');
    let mut i = start + 1;
    i = skip_ws(bytes, i);

    if i + keyword.len() > bytes.len() || &bytes[i..i + keyword.len()] != keyword {
        return None;
    }
    i += keyword.len();

    if i >= bytes.len() || !is_ws(bytes[i]) {
        return None;
    }
    i = skip_ws(bytes, i);

    if i >= bytes.len() {
        return None;
    }
    if bytes[i] == b'"' {
        // Literal-form path: reuse the keyword-form matcher's tail logic.
        if let Some((name, next)) = try_match_keyword_form(bytes, start, keyword) {
            return Some(FormMatch::Literal { name, next });
        }
        return None;
    }

    // Non-literal argument: walk to the matching ')' so the outer scanner
    // resumes after the whole form and we don't double-count the inner
    // tokens.
    let mut depth = 1usize;
    while i < bytes.len() && depth > 0 {
        match bytes[i] {
            b';' => {
                while i < bytes.len() && bytes[i] != b'\n' {
                    i += 1;
                }
            }
            b'"' => i = skip_string(bytes, i),
            b'(' => {
                depth += 1;
                i += 1;
            }
            b')' => {
                depth -= 1;
                i += 1;
            }
            _ => i += 1,
        }
    }
    Some(FormMatch::NonLiteral { next: i })
}

/// Skip a double-quoted string starting at `start` (which points at the opening
/// `"`). Returns the index just past the closing `"`. Handles `\"` escapes; on
/// a runaway string (no closing quote) returns the end of input.
fn skip_string(bytes: &[u8], start: usize) -> usize {
    let mut i = start + 1;
    while i < bytes.len() {
        match bytes[i] {
            b'\\' => i = (i + 2).min(bytes.len()),
            b'"' => return i + 1,
            _ => i += 1,
        }
    }
    bytes.len()
}

/// Try to match `(KEYWORD "NAME")` starting at `start` (which points at the
/// opening `(`). On success returns `(name, index just past the closing ')')`.
fn try_match_keyword_form(bytes: &[u8], start: usize, keyword: &[u8]) -> Option<(String, usize)> {
    debug_assert_eq!(bytes[start], b'(');
    let mut i = start + 1;
    i = skip_ws(bytes, i);

    if i + keyword.len() > bytes.len() || &bytes[i..i + keyword.len()] != keyword {
        return None;
    }
    i += keyword.len();

    // Require whitespace after the keyword so we don't match identifiers like
    // `import-default`.
    if i >= bytes.len() || !is_ws(bytes[i]) {
        return None;
    }
    i = skip_ws(bytes, i);

    if i >= bytes.len() || bytes[i] != b'"' {
        return None;
    }
    i += 1;

    let mut name = Vec::new();
    while i < bytes.len() {
        match bytes[i] {
            b'\\' if i + 1 < bytes.len() => {
                name.push(bytes[i + 1]);
                i += 2;
            }
            b'"' => {
                i += 1;
                break;
            }
            b => {
                name.push(b);
                i += 1;
            }
        }
    }

    i = skip_ws(bytes, i);
    if i >= bytes.len() || bytes[i] != b')' {
        return None;
    }
    i += 1;

    let s = String::from_utf8(name).ok()?;
    if s.is_empty() {
        return None;
    }
    Some((s, i))
}

fn is_ws(b: u8) -> bool {
    matches!(b, b' ' | b'\t' | b'\n' | b'\r')
}

fn skip_ws(bytes: &[u8], start: usize) -> usize {
    let mut i = start;
    while i < bytes.len() && is_ws(bytes[i]) {
        i += 1;
    }
    i
}

#[cfg(test)]
mod tests {
    use super::*;

    fn imports(source: &str) -> Vec<String> {
        import_scan(source).refs.into_iter().collect()
    }

    #[test]
    fn finds_single_reference() {
        assert_eq!(
            imports("(version 1)\n(import \"system.sb\")\n"),
            vec!["system.sb".to_string()]
        );
    }

    #[test]
    fn finds_references_nested_in_other_forms() {
        assert_eq!(
            imports("(if (param \"X\") (import \"a.sb\") (import \"b.sb\"))"),
            vec!["a.sb".to_string(), "b.sb".to_string()]
        );
    }

    #[test]
    fn ignores_form_inside_string_literal() {
        // The literal contains the text `(import "FAKE.sb")` but it's inside a
        // double-quoted string and must not count.
        assert!(imports("(allow default \"(import \\\"FAKE.sb\\\")\")").is_empty());
    }

    #[test]
    fn ignores_form_inside_line_comment() {
        let src = "; (import \"FAKE.sb\")\n(allow file-read-data)\n";
        assert!(imports(src).is_empty());
    }

    #[test]
    fn ignores_strings_and_comments_together() {
        let src = "; (import \"FAKE.sb\")\n(allow default \"(import \\\"OTHER.sb\\\")\")";
        assert!(imports(src).is_empty());
    }

    #[test]
    fn dedupes_repeated_references() {
        let src = "(import \"a.sb\") (import \"a.sb\") (import \"b.sb\")";
        assert_eq!(imports(src), vec!["a.sb".to_string(), "b.sb".to_string()]);
    }

    #[test]
    fn returns_sorted_order() {
        let src = "(import \"z.sb\") (import \"m.sb\") (import \"a.sb\")";
        assert_eq!(
            imports(src),
            vec!["a.sb".to_string(), "m.sb".to_string(), "z.sb".to_string()]
        );
    }

    #[test]
    fn empty_source_returns_empty_set() {
        let r = import_scan("");
        assert!(r.refs.is_empty());
        assert!(r.scan_complete);
    }

    #[test]
    fn skips_extra_whitespace_around_the_argument() {
        let src = "(  import   \"with ws.sb\"  )";
        assert_eq!(imports(src), vec!["with ws.sb".to_string()]);
    }

    #[test]
    fn does_not_match_lookalike_keywords() {
        // `importer` and `import-default` are not the `(import "...")` form.
        let src = "(importer \"x.sb\") (import-default \"y.sb\")";
        let r = import_scan(src);
        assert!(r.refs.is_empty());
        assert!(r.scan_complete);
    }

    #[test]
    fn rejects_empty_name() {
        // libsandbox would reject this too; we just don't record it.
        assert!(imports("(import \"\")").is_empty());
    }

    #[test]
    fn handles_runaway_string_without_panic() {
        // No closing quote: must terminate, not loop.
        let src = "(import \"x.sb\") (allow default \"unterminated";
        assert_eq!(imports(src), vec!["x.sb".to_string()]);
    }

    #[test]
    fn handles_unterminated_form_without_panic() {
        let src = "(import \"x.sb\") (import ";
        let r = import_scan(src);
        assert_eq!(
            r.refs.into_iter().collect::<Vec<_>>(),
            vec!["x.sb".to_string()]
        );
        assert!(r.scan_complete);
    }

    #[test]
    fn handles_escaped_quote_in_name() {
        // `(import "x\"y.sb")`: the escaped quote is part of the name. We
        // faithfully record what's in the source.
        let src = "(import \"x\\\"y.sb\")";
        assert_eq!(imports(src), vec!["x\"y.sb".to_string()]);
    }

    #[test]
    fn ignores_the_param_keyword() {
        // `(param ...)` is a different form and never an import.
        let r = import_scan("(param \"X\") (subpath (param \"HOME\"))");
        assert!(r.refs.is_empty());
        assert!(r.scan_complete);
    }

    #[test]
    fn scan_is_complete_for_pure_literal_source() {
        let r = import_scan("(import \"a.sb\")\n(import \"b.sb\")\n");
        assert!(r.scan_complete);
        assert_eq!(
            r.refs.into_iter().collect::<Vec<_>>(),
            vec!["a.sb".to_string(), "b.sb".to_string()]
        );
    }

    #[test]
    fn flags_macro_indirected_import() {
        // (define (pull name) (import name)) with (pull "x.sb") at the call
        // site: the `(import name)` form has an identifier argument, so the
        // scan cannot follow it and must say so.
        let src = "(define (pull name) (import name))\n(pull \"x.sb\")\n";
        let r = import_scan(src);
        assert!(
            !r.scan_complete,
            "non-literal (import name) must mark scan incomplete"
        );
        assert!(
            r.refs.is_empty(),
            "no literal names to capture in this profile"
        );
    }

    #[test]
    fn mixed_literal_and_indirected_imports() {
        // A literal and a macro-indirected form together: the literal is
        // captured and the scan is still flagged incomplete.
        let src = "(define (pull n) (import n))\n(import \"direct.sb\")\n";
        let r = import_scan(src);
        assert!(!r.scan_complete);
        assert_eq!(
            r.refs.into_iter().collect::<Vec<_>>(),
            vec!["direct.sb".to_string()]
        );
    }

    #[test]
    fn string_containing_the_form_text_does_not_flip_completeness() {
        let r = import_scan("(allow default \"contains (import x) literally\")");
        assert!(r.scan_complete);
        assert!(r.refs.is_empty());
    }
}
