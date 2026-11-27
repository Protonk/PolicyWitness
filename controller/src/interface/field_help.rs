//! Whole-argument lookup in the capacity vocabulary used by the host.
use super::admission_fields::FIELDS;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Entry {
    pub id: &'static str,
    pub key: &'static str,
    pub node: &'static str,
    pub limit: &'static str,
    pub body: &'static str,
    pub destination: &'static str,
}

pub struct Admission {
    pub pattern: &'static str,
    /// Lookup spellings no refusal emits: the field's place in a step and
    /// its joined `request_failure.path`.
    pub aliases: &'static [&'static str],
    pub entry: Option<Entry>,
}

/// What the run card and the usage diagnostic call the selector.
pub const OPERAND: &str = "<key>";

fn matches(pattern: &str, argument: &str) -> bool {
    let mut input = argument.split('.');
    for component in pattern.split('.') {
        let Some(value) = input.next() else {
            return false;
        };
        if component == "{role}" {
            // The final dictionary key is opaque and may contain dots or be empty.
            return true;
        }
        if component.starts_with('{') {
            if value.is_empty()
                || (value.len() > 1 && value.starts_with('0'))
                || !value.bytes().all(|byte| byte.is_ascii_digit())
                || value.parse::<isize>().is_err()
            {
                return false;
            }
        } else if value != component {
            return false;
        }
    }
    input.next().is_none()
}

pub fn select_field(argument: &str) -> Option<&'static Admission> {
    FIELDS.iter().find(|field| {
        field.entry.is_some_and(|entry| entry.key == argument)
            || matches(field.pattern, argument)
            || field.aliases.iter().any(|alias| matches(alias, argument))
    })
}
