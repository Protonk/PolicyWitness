//! The help cards: what each card selects, and its rendering.
//!
//! A card specification holds typed references to governing definitions and
//! to fields of the example document and the run result. It holds no
//! spelling. The renderer prints what each reference's definition spells and
//! lays children out two spaces deeper than their parent.

use serde::Deserialize;

use crate::example_document::EXAMPLE_DOCUMENT;
use crate::interface::commands::{Address, Command, Topic};
use crate::interface::result::{Disposition, Label, Outcome, Refusal, Row, select};
use crate::interface::run_args::{RunOption, Value};
use crate::interface::runner_kind::{Rule, Word};
use crate::inventory::{id, snake};
use crate::json_contract::JsonResult;
use crate::run_result::run_result;

/// A field of the run result, by its place in `JsonResult`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ResultField {
    NormalizedOutcome,
    Ok,
    ExitCode,
}

/// The fields the result card shows, in column order.
pub const RESULT_FIELDS: &[ResultField] = &[
    ResultField::NormalizedOutcome,
    ResultField::Ok,
    ResultField::ExitCode,
];

/// One selected element of a card.
#[derive(Clone, Copy, Debug)]
pub enum Element {
    /// Every registered topic address, one line each.
    TopicAddresses,
    /// The command a command topic describes.
    Command(Command),
    /// A topic's own address.
    Topic(Topic),
    Option(RunOption),
    /// The words the option's reader admits.
    AdmittedWords(RunOption),
    /// Each phase of the example document with its attempts.
    ExamplePhases,
    /// The serialized names of the selected result fields, on one line.
    ResultFieldNames,
    /// One line per result the relation selects with a fixed label: the
    /// selected fields of the result `run` constructs.
    ResultRows,
}

pub struct Node {
    pub element: Element,
    pub children: Vec<Node>,
}

fn node(element: Element, children: Vec<Node>) -> Node {
    Node { element, children }
}

fn leaf(element: Element) -> Node {
    node(element, Vec::new())
}

/// The editorial selection and order of each card.
pub fn specification(card: Option<Topic>) -> Vec<Node> {
    match card {
        None => vec![leaf(Element::TopicAddresses)],
        Some(Topic::Run) => vec![node(
            Element::Command(Command::Run),
            vec![node(
                Element::Option(RunOption::RunnerMode),
                vec![leaf(Element::AdmittedWords(RunOption::RunnerMode))],
            )],
        )],
        Some(Topic::Example) => vec![node(
            Element::Command(Command::Example),
            vec![leaf(Element::ExamplePhases)],
        )],
        Some(Topic::Result) => vec![node(
            Element::Topic(Topic::Result),
            vec![leaf(Element::ResultFieldNames), leaf(Element::ResultRows)],
        )],
    }
}

pub struct Rendered {
    /// The stored file's stem; never printed.
    pub name: String,
    pub text: String,
    /// The inventory entries the card's elements reference.
    pub references: Vec<String>,
}

#[derive(Deserialize)]
struct Document {
    phases: Vec<Phase>,
}
#[derive(Deserialize)]
struct Phase {
    phase_id: String,
    actions: Vec<Action>,
}
#[derive(Deserialize)]
struct Action {
    attempt: Attempt,
}
#[derive(Deserialize)]
struct Attempt {
    action: String,
    target: String,
}

/// The example document's phases as (phase_id, [(action, target)]).
pub fn example_phases() -> Result<Vec<(String, Vec<(String, String)>)>, String> {
    let document: Document = serde_json::from_str(EXAMPLE_DOCUMENT).map_err(|error| {
        format!("the example card's fields are not in EXAMPLE_DOCUMENT: {error}")
    })?;
    Ok(document
        .phases
        .into_iter()
        .map(|phase| {
            let attempts = phase
                .actions
                .into_iter()
                .map(|action| (action.attempt.action, action.attempt.target))
                .collect();
            (phase.phase_id, attempts)
        })
        .collect())
}

/// The name serialization gives a result field: the one key whose value
/// changes when the field does.
pub fn result_key(field: ResultField) -> Result<String, String> {
    let base = JsonResult::new(false, 0, None, None);
    let mut marked = base.clone();
    match field {
        ResultField::NormalizedOutcome => marked.normalized_outcome = Some(String::new()),
        ResultField::Ok => marked.ok = true,
        ResultField::ExitCode => marked.exit_code = Some(1),
    }
    let before = serde_json::to_value(&base).map_err(|error| error.to_string())?;
    let after = serde_json::to_value(&marked).map_err(|error| error.to_string())?;
    let (before, after) = (before.as_object().unwrap(), after.as_object().unwrap());
    let changed: Vec<&String> = after
        .iter()
        .filter(|(key, value)| before.get(*key) != Some(value))
        .map(|(key, _)| key)
        .collect();
    match changed.as_slice() {
        [key] if before.len() == after.len() => Ok((*key).clone()),
        _ => Err(format!("{field:?} does not serialize as one result key")),
    }
}

/// The dispositions whose selected label is fixed by the relation, in row
/// order, each with the row that selects it.
pub fn fixed_dispositions() -> Vec<(Row, Disposition<'static>)> {
    let mut samples = Vec::new();
    for row in Row::ALL.iter().copied() {
        let def = row.def();
        match (row, def.outcome) {
            (Row::LocalRequestRefusal, _) => samples.push((row, Disposition::LocalRequestRefusal)),
            (Row::ToolFailure, _) => samples.push((row, Disposition::ToolFailure)),
            (Row::AdmissionRefusal, _) => samples.extend(
                Refusal::ALL
                    .iter()
                    .map(|refusal| (row, Disposition::AdmissionRefusal(*refusal))),
            ),
            (Row::AdmittedFinished, _) => samples.push((
                row,
                Disposition::Admitted {
                    host_outcome: Some(Label::Finished.spelling()),
                    integrity_issues: 0,
                },
            )),
            // An open host label: no fixed line.
            (Row::AdmittedOther, Outcome::HostLabel) => {}
            (Row::AdmittedOther, _) => samples.push((
                row,
                Disposition::Admitted {
                    host_outcome: Some(""),
                    integrity_issues: 0,
                },
            )),
            (Row::AdmittedUnavailable, _) => samples.push((
                row,
                Disposition::Admitted {
                    host_outcome: None,
                    integrity_issues: 0,
                },
            )),
        }
    }
    samples
}

fn scalar(value: &serde_json::Value) -> Result<String, String> {
    match value {
        serde_json::Value::String(text) => Ok(text.clone()),
        serde_json::Value::Bool(_) | serde_json::Value::Number(_) => Ok(value.to_string()),
        other => Err(format!("a result card field is not a scalar: {other}")),
    }
}

struct Output {
    lines: Vec<String>,
    references: Vec<String>,
}

impl Output {
    fn line(&mut self, depth: usize, text: &str) {
        self.lines.push(format!("{}{text}", "  ".repeat(depth)));
    }
}

/// Renders one node and its children. `parent` is the enclosing element: a
/// child is rejected when its definition does not belong to that parent.
fn render_node(
    card: Option<Topic>,
    parent: Option<Element>,
    item: &Node,
    depth: usize,
    out: &mut Output,
) -> Result<(), String> {
    match item.element {
        Element::TopicAddresses => {
            for topic in Topic::ALL.iter().copied() {
                out.line(depth, topic.address());
                out.references.push(id(&topic));
            }
        }
        Element::Command(command) => {
            let describes = card.map(Topic::source);
            if describes != Some(Address::Command(command)) {
                return Err(format!(
                    "{command:?} heads a card whose topic is not that command"
                ));
            }
            out.line(depth, command.def().spelling);
            out.references.push(id(&command));
        }
        Element::Topic(topic) => {
            if card != Some(topic) {
                return Err(format!("{topic:?} heads another topic's card"));
            }
            out.line(depth, topic.address());
            out.references.push(id(&topic));
        }
        Element::Option(option) => {
            if !matches!(parent, Some(Element::Command(Command::Run))) {
                return Err(format!(
                    "{option:?} is not under the command that admits it"
                ));
            }
            out.line(depth, option.def().spelling);
            out.references.push(id(&option));
        }
        Element::AdmittedWords(option) => {
            let Value::Kind(reader) = option.def().value else {
                return Err(format!("{option:?} does not take a runner-kind word"));
            };
            if !matches!(parent, Some(Element::Option(under)) if under == option) {
                return Err(format!("the words of {option:?} are not under that option"));
            }
            for word in Word::ALL.iter().copied() {
                if word.rule(reader) == Some(Rule::Admits) {
                    out.line(depth, word.spelling());
                    out.references
                        .push(format!("{}@{}", id(&word), snake(&reader)));
                }
            }
        }
        Element::ExamplePhases => {
            if !matches!(parent, Some(Element::Command(Command::Example))) {
                return Err("the example phases are not under the example command".into());
            }
            for (phase_id, attempts) in example_phases()? {
                out.line(depth, &phase_id);
                for (action, target) in attempts {
                    out.line(depth + 1, &format!("{action} {target}"));
                }
            }
            out.references.push("example.document".into());
        }
        Element::ResultFieldNames => {
            if !matches!(parent, Some(Element::Topic(Topic::Result))) {
                return Err("the result fields are not under the result topic".into());
            }
            let names: Result<Vec<String>, String> = RESULT_FIELDS
                .iter()
                .map(|field| result_key(*field))
                .collect();
            out.line(depth, &names?.join(" "));
            out.references.push("result.fields".into());
        }
        Element::ResultRows => {
            if !matches!(parent, Some(Element::Topic(Topic::Result))) {
                return Err("the result rows are not under the result topic".into());
            }
            let mut rows: Vec<Row> = Vec::new();
            for (row, disposition) in fixed_dispositions() {
                let selection = select(&disposition);
                if selection.row != row {
                    return Err(format!("{row:?} does not select its own disposition"));
                }
                let result = serde_json::to_value(run_result(&selection, None))
                    .map_err(|error| error.to_string())?;
                let mut cells = Vec::new();
                for field in RESULT_FIELDS {
                    cells.push(scalar(&result[result_key(*field)?.as_str()])?);
                }
                out.line(depth, &cells.join(" "));
                if !rows.contains(&row) {
                    rows.push(row);
                }
            }
            out.references.extend(rows.iter().map(id));
        }
    }
    for child in &item.children {
        render_node(card, Some(item.element), child, depth + 1, out)?;
    }
    Ok(())
}

fn render(card: Option<Topic>) -> Result<Rendered, String> {
    let mut out = Output {
        lines: Vec::new(),
        references: Vec::new(),
    };
    for item in specification(card) {
        render_node(card, None, &item, 0, &mut out)?;
    }
    if out.lines.is_empty() || out.lines.iter().any(|line| line.trim().is_empty()) {
        return Err(format!("card {card:?} has an empty line or no line"));
    }
    if out.lines.iter().any(|line| line.contains('\n')) {
        return Err(format!("card {card:?} has a line break inside an element"));
    }
    let mut text = out.lines.join("\n");
    text.push('\n');
    Ok(Rendered {
        name: card.map_or_else(|| "base".to_string(), |topic| snake(&topic)),
        text,
        references: out.references,
    })
}

/// Every card, the base card first. Refuses a topic address the help
/// grammar cannot reach or that two topics share.
pub fn render_all() -> Result<Vec<Rendered>, String> {
    let mut addresses: Vec<&str> = Vec::new();
    for topic in Topic::ALL.iter().copied() {
        let address = topic.address();
        if address.is_empty() || address.starts_with(crate::interface::run_args::FLAG_PREFIX) {
            return Err(format!(
                "topic {topic:?} has an empty or flag-shaped address"
            ));
        }
        if addresses.contains(&address) {
            return Err(format!("two topics share the address of {topic:?}"));
        }
        addresses.push(address);
    }
    let mut cards = vec![render(None)?];
    for topic in Topic::ALL.iter().copied() {
        cards.push(render(Some(topic))?);
    }
    let base: Vec<&str> = cards[0].text.lines().collect();
    if base != addresses {
        return Err("the base card's lines are not the registered topic addresses".into());
    }
    Ok(cards)
}
