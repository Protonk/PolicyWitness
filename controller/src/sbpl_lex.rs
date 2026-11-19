//! SBPL surface scanner for `(import "NAME")` forms.
//!
//! Hand-rolled instead of pulling a Scheme parser because the surface we care
//! about is tiny: tokens, lists, double-quoted strings and line comments.
//! Returns a deduplicated set at the source level. Anything more structural
//! (evaluation, scope, parameter binding, macro expansion) is libsandbox's
//! job, and the scan sees none of it.
//!
//! The token rules are the ones the system's reader was observed to apply on
//! macOS 26.7.1 (25G241), by compiling constructed sources:
//! - bytes 0x09 through 0x0D and the space separate tokens;
//! - `;`, and `#!` at the start of a token, begin a comment that ends at LF;
//! - `(`, `)`, `[` and `]` are list delimiters, and a list closes with the
//!   delimiter that matches its opener;
//! - `"` at the start of a token begins a string that ends at the next `"` not
//!   preceded by a backslash;
//! - `'`, `` ` `` and `,` at the start of a token are tokens of their own;
//! - `#\` at the start of a token takes the next byte, whatever it is;
//! - every other token runs to the next list delimiter, `;`, tab, LF, CR or
//!   space, so a `"`, form feed or vertical tab inside it is part of it.

use std::collections::BTreeSet;

/// Result of an import scan.
///
/// `refs` is the set of names from the forms the scan followed. `unfollowed`
/// is true when the source contains at least one form headed by `import` that
/// the scan did not follow, so `refs` cannot claim to hold every name such a
/// form supplies. A file can also reach the compilation with no form headed
/// by `import` (an aliased or applied `import`, `eval`, `load`); nothing here
/// reports that.
pub struct ImportScanResult {
    pub refs: BTreeSet<String>,
    pub unfollowed: bool,
}

/// Scan an SBPL source for forms headed by `import`.
///
/// A form is followed when it is a list opener, the token `import`, one
/// string and the matching closer, with any whitespace or comments between
/// them, and the string is not empty and uses no escape other than `\"` and
/// `\\`. Every other list whose first token is `import` is reported through
/// `unfollowed`, and the scan continues inside it. Forms are found in every
/// position, including ones the compiler never evaluates; text inside a
/// string or a comment is not a form.
///
/// Two binaries include this module by path: the controller's dossier and the
/// `sbpl-check` helper both walk the same closure through
/// `sbpl_imports::resolve_imports`.
pub fn import_scan(source: &str) -> ImportScanResult {
    let bytes = source.as_bytes();
    let mut refs = BTreeSet::new();
    let mut unfollowed = false;
    let mut i = 0usize;
    // The opener, when the previous token opened a list.
    let mut opened: Option<u8> = None;
    while let Some(token) = next_token(bytes, &mut i) {
        match (token, opened.take()) {
            (Token::Open(opener), _) => opened = Some(opener),
            (Token::Atom(b"import"), Some(opener)) => {
                let mut after = i;
                let name = match next_token(bytes, &mut after) {
                    Some(Token::Str(Some(name))) if !name.is_empty() => Some(name),
                    _ => None,
                };
                match (name, next_token(bytes, &mut after)) {
                    (Some(name), Some(Token::Close(closer))) if closer == closer_of(opener) => {
                        refs.insert(name);
                        i = after;
                    }
                    // Resume after the head, so forms inside this one are seen.
                    _ => unfollowed = true,
                }
            }
            _ => {}
        }
    }
    ImportScanResult { refs, unfollowed }
}

enum Token<'a> {
    /// `(` or `[`.
    Open(u8),
    /// `)` or `]`.
    Close(u8),
    /// A string's contents, or None when it has no closing quote, is not
    /// UTF-8 or uses an escape other than `\"` and `\\`.
    Str(Option<String>),
    Atom(&'a [u8]),
}

fn closer_of(opener: u8) -> u8 {
    if opener == b'(' { b')' } else { b']' }
}

fn is_ws(b: u8) -> bool {
    matches!(b, 0x09..=0x0D | b' ')
}

fn ends_atom(b: u8) -> bool {
    matches!(
        b,
        b'(' | b')' | b'[' | b']' | b';' | b'\t' | b'\n' | b'\r' | b' '
    )
}

/// The token starting at or after `*i`, with `*i` left just past it, or None
/// at the end of input.
fn next_token<'a>(bytes: &'a [u8], i: &mut usize) -> Option<Token<'a>> {
    loop {
        while *i < bytes.len() && is_ws(bytes[*i]) {
            *i += 1;
        }
        let start = *i;
        let first = *bytes.get(start)?;
        let second = bytes.get(start + 1).copied();
        if first == b';' || (first == b'#' && second == Some(b'!')) {
            while *i < bytes.len() && bytes[*i] != b'\n' {
                *i += 1;
            }
            continue;
        }
        *i += 1;
        return Some(match first {
            b'(' | b'[' => Token::Open(first),
            b')' | b']' => Token::Close(first),
            b'"' => Token::Str(read_string(bytes, i)),
            // Quote (0x27), backquote and comma.
            b'\x27' | b'`' | b',' => Token::Atom(&bytes[start..*i]),
            _ => {
                // A character literal takes the byte after its backslash. When
                // that byte is one that ends a token, the token ends with it.
                let third = bytes.get(start + 2).copied();
                let literal = first == b'#' && second == Some(b'\\');
                if literal {
                    *i = (start + 3).min(bytes.len());
                }
                if !(literal && third.is_some_and(ends_atom)) {
                    while *i < bytes.len() && !ends_atom(bytes[*i]) {
                        *i += 1;
                    }
                }
                Token::Atom(&bytes[start..*i])
            }
        });
    }
}

/// Read a string whose opening `"` is just before `*i`, leaving `*i` past the
/// closing `"`, or at the end of input when there is none.
fn read_string(bytes: &[u8], i: &mut usize) -> Option<String> {
    let mut name = Vec::new();
    let mut plain = true;
    while let Some(&b) = bytes.get(*i) {
        *i += 1;
        match b {
            b'"' => return plain.then(|| String::from_utf8(name).ok()).flatten(),
            b'\\' => {
                match bytes.get(*i) {
                    Some(&escaped @ (b'"' | b'\\')) => name.push(escaped),
                    _ => plain = false,
                }
                *i = (*i + 1).min(bytes.len());
            }
            _ => name.push(b),
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    fn imports(source: &str) -> Vec<String> {
        import_scan(source).refs.into_iter().collect()
    }

    /// The names followed and the unfollowed flag for one source.
    fn scan(source: &str) -> (Vec<String>, bool) {
        let result = import_scan(source);
        (result.refs.into_iter().collect(), result.unfollowed)
    }

    fn followed(names: &[&str]) -> (Vec<String>, bool) {
        (names.iter().map(|name| name.to_string()).collect(), false)
    }

    fn flagged(names: &[&str]) -> (Vec<String>, bool) {
        (names.iter().map(|name| name.to_string()).collect(), true)
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
        assert_eq!(
            scan("(allow default \"(import \\\"FAKE.sb\\\")\")"),
            followed(&[])
        );
    }

    #[test]
    fn ignores_form_inside_line_comment() {
        let src = "; (import \"FAKE.sb\")\n(allow file-read-data)\n";
        assert_eq!(scan(src), followed(&[]));
    }

    #[test]
    fn ignores_strings_and_comments_together() {
        let src = "; (import \"FAKE.sb\")\n(allow default \"(import \\\"OTHER.sb\\\")\")";
        assert_eq!(scan(src), followed(&[]));
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
        assert_eq!(scan(""), followed(&[]));
    }

    #[test]
    fn does_not_match_lookalike_keywords() {
        // `importer` and `import-default` are not the `(import "...")` form.
        let src = "(importer \"x.sb\") (import-default \"y.sb\")";
        assert_eq!(scan(src), followed(&[]));
    }

    #[test]
    fn handles_runaway_string_without_panic() {
        // No closing quote: must terminate, not loop.
        let src = "(import \"x.sb\") (allow default \"unterminated";
        assert_eq!(scan(src), followed(&["x.sb"]));
    }

    #[test]
    fn ignores_the_param_keyword() {
        // `(param ...)` is a different form and never an import.
        assert_eq!(
            scan("(param \"X\") (subpath (param \"HOME\"))"),
            followed(&[])
        );
    }

    #[test]
    fn string_containing_the_form_text_does_not_set_the_flag() {
        assert_eq!(
            scan("(allow default \"contains (import x) literally\")"),
            followed(&[])
        );
    }

    /// Literal spellings the system's compiler was observed to evaluate.
    #[test]
    fn follows_literal_forms_through_whitespace_comments_and_brackets() {
        for source in [
            "(import \"m.sb\")",
            "(  import   \"m.sb\"  )",
            "(\timport\r\n\t\"m.sb\"\r\n)",
            "(import\t\"m.sb\")",
            "(import\n\"m.sb\")",
            "(import\t\x0b\"m.sb\")",
            "(import \x0c\"m.sb\")",
            "(import ; note\n \"m.sb\")",
            "(import;c\n\"m.sb\")",
            "(import \"m.sb\" ; note\n)",
            "(import \"m.sb\";c\n)",
            "(import \"m.sb\"\x0c)",
            "(import \"m.sb\"\x0b)",
            "(\x0cimport \"m.sb\")",
            "( ; c\n import \"m.sb\")",
            "( #! c\n import \"m.sb\")",
            "[import \"m.sb\"]",
            "(let () (import \"m.sb\"))",
        ] {
            assert_eq!(scan(source), followed(&["m.sb"]), "{source:?}");
        }
    }

    /// Text before a form that the reader does not take as opening a string
    /// or a comment, so the form after it is still seen.
    #[test]
    fn follows_a_form_after_character_literals_quotes_inside_symbols_and_hash_bang_comments() {
        for source in [
            "(define q #\\\")\n(import \"m.sb\")",
            "(define s #\\;) (import \"m.sb\")",
            "(define p #\\()\n(import \"m.sb\")",
            "(define sp #\\ )\n(import \"m.sb\")",
            "(define nl #\\newline)\n(import \"m.sb\")",
            "(define y 'ab\"cd)\n(import \"m.sb\")",
            "(define w 'a\"b)(import \"m.sb\")",
            "(define z 'ab;cd\n)\n(import \"m.sb\")",
            "(define h 'a#!b)\n(import \"m.sb\")",
            "(define t '\"a b\")\n(import \"m.sb\")",
            "(define t `\"a b\")\n(import \"m.sb\")",
            "(define l (list \"a\"\"b\"))\n(import \"m.sb\")",
            "#! \"\n(import \"m.sb\")",
            "(define h 1) #! \"\n(import \"m.sb\")",
        ] {
            assert_eq!(scan(source), followed(&["m.sb"]), "{source:?}");
        }
    }

    #[test]
    fn decodes_only_the_quote_and_backslash_escapes() {
        assert_eq!(scan("(import \"x\\\"y.sb\")"), followed(&["x\"y.sb"]));
        assert_eq!(scan("(import \"x\\\\y.sb\")"), followed(&["x\\y.sb"]));
        // The reader decodes these to a byte, LF and TAB; the scan reports
        // the form instead of recording a name the compiler does not use.
        for source in [
            "(import \"mark\\x65r.sb\")",
            "(import \"n\\nl.sb\")",
            "(import \"t\\tab.sb\")",
            "(import \"m.sb\\\n\")",
        ] {
            assert_eq!(scan(source), flagged(&[]), "{source:?}");
        }
    }

    /// Forms headed by `import` that are not one string in one list.
    #[test]
    fn reports_every_other_form_headed_by_import() {
        for source in [
            "(import (string-append \"m\" \".sb\"))",
            "(import(string-append \"m\" \".sb\"))",
            "(import[string-append \"m\" \".sb\"])",
            "(define (pull n) (import n))\n(pull \"m.sb\")",
            "(import '\"m.sb\")",
            "(import . (\"m.sb\"))",
            "(import \"m.sb\" \"m.sb\")",
            "(import \"m.sb\"x)",
            "(import \"\")",
            "(import)",
            "(import \"m.sb\"]",
            "[import \"m.sb\")",
            "(import \"m.sb\"",
            "(import \"m.sb",
            "(import ",
            "(import",
        ] {
            assert_eq!(scan(source), flagged(&[]), "{source:?}");
        }
    }

    #[test]
    fn keeps_scanning_inside_a_form_it_did_not_follow() {
        assert_eq!(
            scan("(import (begin (import \"m.sb\") \"bsd.sb\"))"),
            flagged(&["m.sb"])
        );
        assert_eq!(
            scan("(define (pull n) (import n))\n(import \"direct.sb\")\n"),
            flagged(&["direct.sb"])
        );
    }

    /// Not `import` for the reader: the symbol is longer or spelled otherwise.
    #[test]
    fn does_not_take_a_longer_symbol_for_the_head() {
        for source in [
            "(IMPORT \"m.sb\")",
            "(import\"m.sb\")",
            "(import\x0c\"m.sb\")",
            "(import\x0b\"m.sb\")",
            "{import \"m.sb\"}",
            "('import \"m.sb\")",
        ] {
            assert_eq!(scan(source), followed(&[]), "{source:?}");
        }
    }

    /// Literal forms are collected wherever they stand, evaluated or not.
    #[test]
    fn follows_forms_the_compiler_does_not_evaluate() {
        for source in [
            "(if #f (import \"m.sb\"))",
            "(define d (quote (import \"m.sb\")))",
            "(define d '(import \"m.sb\"))",
            "(define (never) (import \"m.sb\"))",
            "#(import \"m.sb\")",
        ] {
            assert_eq!(scan(source), followed(&["m.sb"]), "{source:?}");
        }
        // A parameter list spelled `(import)` is a list headed by `import`.
        assert_eq!(
            scan("((lambda (import) (import \"m.sb\")) (lambda (x) #t))"),
            flagged(&["m.sb"])
        );
    }

    /// The limit of a scan for forms headed by `import`: the compiler was
    /// observed to evaluate the named file for each of these.
    #[test]
    fn sees_no_form_when_import_is_not_the_head() {
        for source in [
            "(define alias import)\n(alias \"m.sb\")",
            "(apply import (list \"m.sb\"))",
            "(eval (list (quote import) \"m.sb\"))",
            "(eval (list (string->symbol (string-append \"imp\" \"ort\")) \"m.sb\"))",
            "(load \"m.sb\")",
            "(define l load)\n(l \"m.sb\")",
        ] {
            assert_eq!(scan(source), followed(&[]), "{source:?}");
        }
    }

    #[test]
    fn a_hash_bang_comment_hides_a_form_as_a_semicolon_comment_does() {
        assert_eq!(scan("#! (import \"m.sb\")\n"), followed(&[]));
        assert_eq!(
            scan("(allow default) #! (import \"m.sb\")\n"),
            followed(&[])
        );
    }
}
