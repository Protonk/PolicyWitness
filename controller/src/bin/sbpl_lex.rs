//! Minimal SBPL surface lexer for `(param "NAME")` and `(import "NAME")`
//! references.
//!
//! Hand-rolled instead of pulling a Scheme parser because the surface we care
//! about is tiny: paren-balanced, double-quoted strings, semicolon line
//! comments. Returns deduplicated sets at the source level. Anything more
//! structural (param-value typing, import scope, macro expansion) is
//! libsandbox's job.

use std::collections::BTreeSet;

/// Result of a `(param ...)` scan.
///
/// `refs` is the set of literal names captured. `scan_complete` is false when
/// the source contains at least one `(param X)` form where `X` is not a
/// quoted string — that case is typically macro-indirected (`(define (f n)
/// (subpath (param n)))` with `(f "FOO")` at the call site) and is beyond
/// the surface lexer's reach. Consumers should treat `params_missing: []`
/// with `scan_complete = false` as "we don't actually know" rather than
/// "no params are needed".
pub struct ParamScanResult {
    pub refs: BTreeSet<String>,
    pub scan_complete: bool,
}

/// Scan an SBPL source for `(param "NAME")` references and report whether
/// the static scan can stand on its own — see [`ParamScanResult`].
///
/// String literals and `;` line comments are skipped — a `(param "X")` spelled
/// inside a string or a comment does not count.
pub fn param_scan(source: &str) -> ParamScanResult {
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
            b'(' => match try_match_param_form(bytes, i) {
                Some(ParamFormMatch::Literal { name, next }) => {
                    refs.insert(name);
                    i = next;
                }
                Some(ParamFormMatch::NonLiteral { next }) => {
                    scan_complete = false;
                    i = next;
                }
                None => i += 1,
            },
            _ => i += 1,
        }
    }
    ParamScanResult { refs, scan_complete }
}

/// Scan an SBPL source for `(import "NAME")` references and return the
/// deduplicated set of names found, sorted. Same scanning discipline as
/// [`param_scan`].
pub fn import_refs(source: &str) -> BTreeSet<String> {
    scan_keyword_refs(source, b"import")
}

fn scan_keyword_refs(source: &str, keyword: &[u8]) -> BTreeSet<String> {
    let bytes = source.as_bytes();
    let mut out = BTreeSet::new();
    let mut i = 0usize;
    while i < bytes.len() {
        match bytes[i] {
            b';' => {
                // Line comment runs to the next newline.
                while i < bytes.len() && bytes[i] != b'\n' {
                    i += 1;
                }
            }
            b'"' => {
                i = skip_string(bytes, i);
            }
            b'(' => {
                if let Some((name, next)) = try_match_keyword_form(bytes, i, keyword) {
                    out.insert(name);
                    i = next;
                } else {
                    i += 1;
                }
            }
            _ => i += 1,
        }
    }
    out
}

enum ParamFormMatch {
    /// `(param "NAME")` — argument is a string literal we can capture.
    Literal { name: String, next: usize },
    /// `(param X)` where X is a non-string token (typically a macro
    /// parameter from an enclosing `define`). We advance past the form so
    /// the outer walk doesn't re-scan its interior.
    NonLiteral { next: usize },
}

fn try_match_param_form(bytes: &[u8], start: usize) -> Option<ParamFormMatch> {
    debug_assert_eq!(bytes[start], b'(');
    let mut i = start + 1;
    i = skip_ws(bytes, i);

    const KW: &[u8] = b"param";
    if i + KW.len() > bytes.len() || &bytes[i..i + KW.len()] != KW {
        return None;
    }
    i += KW.len();

    if i >= bytes.len() || !is_ws(bytes[i]) {
        return None;
    }
    i = skip_ws(bytes, i);

    if i >= bytes.len() {
        return None;
    }
    if bytes[i] == b'"' {
        // Literal-form path: reuse the keyword-form matcher's tail logic.
        if let Some((name, next)) = try_match_keyword_form(bytes, start, b"param") {
            return Some(ParamFormMatch::Literal { name, next });
        }
        return None;
    }

    // Non-literal argument — walk to the matching ')' so the outer scanner
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
    Some(ParamFormMatch::NonLiteral { next: i })
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
fn try_match_keyword_form(
    bytes: &[u8],
    start: usize,
    keyword: &[u8],
) -> Option<(String, usize)> {
    debug_assert_eq!(bytes[start], b'(');
    let mut i = start + 1;
    i = skip_ws(bytes, i);

    if i + keyword.len() > bytes.len() || &bytes[i..i + keyword.len()] != keyword {
        return None;
    }
    i += keyword.len();

    // Require whitespace after the keyword so we don't match identifiers like
    // `param-default` or `import-default`.
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

    fn names(source: &str) -> Vec<String> {
        param_scan(source).refs.into_iter().collect()
    }

    #[test]
    fn finds_single_reference() {
        assert_eq!(
            names("(allow file-read-data (subpath (param \"HOME\")))"),
            vec!["HOME".to_string()]
        );
    }

    #[test]
    fn finds_inside_string_append() {
        assert_eq!(
            names("(string-append (param \"A\") \"/\" (param \"B\"))"),
            vec!["A".to_string(), "B".to_string()]
        );
    }

    #[test]
    fn ignores_param_form_inside_string_literal() {
        // The literal contains the text `(param "FAKE")` but it's inside a
        // double-quoted string and must not count.
        assert!(names("(allow default \"(param \\\"FAKE\\\")\")").is_empty());
    }

    #[test]
    fn ignores_param_form_inside_line_comment() {
        let src = "; (param \"FAKE\")\n(allow file-read-data)\n";
        assert!(names(src).is_empty());
    }

    #[test]
    fn dedupes_repeated_references() {
        let src = "(subpath (param \"X\")) (subpath (param \"X\"))";
        assert_eq!(names(src), vec!["X".to_string()]);
    }

    #[test]
    fn returns_sorted_order() {
        let src = "(param \"Z\") (param \"M\") (param \"A\")";
        assert_eq!(
            names(src),
            vec!["A".to_string(), "M".to_string(), "Z".to_string()]
        );
    }

    #[test]
    fn empty_source_returns_empty_set() {
        assert!(names("").is_empty());
    }

    #[test]
    fn skips_param_with_extra_whitespace() {
        let src = "(  param   \"WITH_WS\"  )";
        assert_eq!(names(src), vec!["WITH_WS".to_string()]);
    }

    #[test]
    fn does_not_match_param_lookalikes() {
        // `parameterize` and `param-default` are not the `(param "...")` form.
        let src = "(parameterize \"X\") (param-default \"Y\")";
        assert!(names(src).is_empty());
    }

    #[test]
    fn rejects_empty_name() {
        // libsandbox would reject this too; we just don't record it.
        let src = "(param \"\")";
        assert!(names(src).is_empty());
    }

    #[test]
    fn handles_runaway_string_without_panic() {
        // No closing quote — must terminate, not loop.
        let src = "(param \"X\") (allow default \"unterminated";
        assert_eq!(names(src), vec!["X".to_string()]);
    }

    #[test]
    fn handles_escaped_quote_in_name() {
        // `(param "X\"Y")` — escaped quote inside the name. The resulting name
        // is `X"Y`, which libsandbox would likely reject; we faithfully record
        // what's in the source.
        let src = "(param \"X\\\"Y\")";
        assert_eq!(names(src), vec!["X\"Y".to_string()]);
    }

    fn imports(source: &str) -> Vec<String> {
        import_refs(source).into_iter().collect()
    }

    #[test]
    fn import_refs_finds_single() {
        assert_eq!(
            imports("(version 1)\n(import \"system.sb\")\n"),
            vec!["system.sb".to_string()]
        );
    }

    #[test]
    fn import_refs_dedupes() {
        let src = "(import \"a.sb\") (import \"a.sb\") (import \"b.sb\")";
        assert_eq!(
            imports(src),
            vec!["a.sb".to_string(), "b.sb".to_string()]
        );
    }

    #[test]
    fn import_refs_ignores_strings_and_comments() {
        let src = "; (import \"FAKE.sb\")\n(allow default \"(import \\\"OTHER.sb\\\")\")";
        assert!(imports(src).is_empty());
    }

    #[test]
    fn import_refs_skips_param_keyword() {
        // Ensure the keyword discrimination works both ways: `(param ...)` must
        // not be picked up as an import.
        assert!(imports("(param \"X\")").is_empty());
        assert!(param_scan("(import \"X.sb\")").refs.is_empty());
    }

    #[test]
    fn param_scan_complete_for_pure_literal_source() {
        let r = param_scan("(allow file-read-data (subpath (param \"HOME\")))");
        assert!(r.scan_complete);
        assert_eq!(
            r.refs.into_iter().collect::<Vec<_>>(),
            vec!["HOME".to_string()]
        );
    }

    #[test]
    fn param_scan_flags_macro_indirected_param() {
        // The form on the downstream report:
        //   (define (helper pn) (subpath (param pn)))
        //   (allow file-read-data (helper "FOO"))
        // The (param pn) form has an identifier arg, not a literal — we can't
        // resolve it without macro expansion, so scan_complete must drop.
        let src = "(define (helper pn) (subpath (param pn)))\n\
                   (allow file-read-data (helper \"FOO\"))\n";
        let r = param_scan(src);
        assert!(!r.scan_complete, "non-literal (param pn) must mark scan incomplete");
        assert!(
            r.refs.is_empty(),
            "no literal names to capture in this profile"
        );
    }

    #[test]
    fn param_scan_mixed_literal_and_indirected() {
        // A literal and a macro-indirected form together: we capture the
        // literal and still flag scan_complete=false.
        let src = "(define (h x) (param x))\n(subpath (param \"DIRECT\"))\n";
        let r = param_scan(src);
        assert!(!r.scan_complete);
        assert_eq!(
            r.refs.into_iter().collect::<Vec<_>>(),
            vec!["DIRECT".to_string()]
        );
    }

    #[test]
    fn param_scan_ignores_string_with_param_word() {
        // A string that happens to contain the text `(param x)` must not flip
        // the completeness flag.
        let r = param_scan("(allow default \"contains (param x) literally\")");
        assert!(r.scan_complete);
        assert!(r.refs.is_empty());
    }
}
