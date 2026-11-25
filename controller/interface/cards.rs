//! The help cards: what each card selects, and its rendering.
//!
//! Each card has an explicit layout and selects typed definitions. Rendering
//! records those references alongside the text; inventory generation assigns
//! their external identifiers. No card carries independent wording.

use serde::{Deserialize, Serialize};

use crate::interface::commands::{Address, Command, Example, Topic};
use crate::interface::result::{Disposition, Label, Outcome, Refusal, Row, select};
use crate::interface::run_args::{RunOption, Value};
use crate::interface::runner_kind::{Reader, Rule, Word};
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

/// The option selected by the run card; its value reader supplies the words.
pub const RUN_OPTION: RunOption = RunOption::RunnerMode;

/// The definitions a rendered card uses. These remain typed until the
/// inventory writer assigns identifiers.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Reference {
    Command(Command),
    Topic(Topic),
    Option(RunOption),
    Word(Word, Reader),
    ExampleName(Example),
    ExampleDocument(Example),
    ResultFields,
    ResultRow(Row),
}

pub struct Rendered {
    pub topic: Option<Topic>,
    pub text: String,
    /// The inventory entries the card's elements reference.
    pub references: Vec<Reference>,
}

/// The members of a published example that its card shows, nested as the
/// document nests them. Deserialization drops every other member; the
/// inventory records each dropped member as omitted.
#[derive(Deserialize, Serialize)]
pub struct Shown {
    #[serde(skip_serializing_if = "Option::is_none")]
    actors: Option<Vec<Actor>>,
    phases: Vec<Phase>,
}
#[derive(Deserialize, Serialize)]
struct Actor {
    actor_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    equipment: Option<String>,
    sandbox: Sandbox,
}
#[derive(Deserialize, Serialize)]
struct Sandbox {
    mode: String,
}
#[derive(Deserialize, Serialize)]
struct Phase {
    phase_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    actor_id: Option<String>,
    actions: Vec<Step>,
}
#[derive(Deserialize, Serialize)]
struct Step {
    step_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    sandbox_check: Option<Query>,
    #[serde(skip_serializing_if = "Option::is_none")]
    attempt: Option<Attempt>,
    #[serde(skip_serializing_if = "Option::is_none")]
    extension: Option<Extension>,
}
#[derive(Deserialize, Serialize)]
struct Query {
    operation: String,
    filter: Filter,
}
#[derive(Deserialize, Serialize)]
struct Filter {
    value: String,
}
#[derive(Deserialize, Serialize)]
struct Attempt {
    action: String,
    target: String,
}
#[derive(Deserialize, Serialize)]
struct Extension {
    operation: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    family: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    authority: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    target: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    recipient: Option<String>,
}

/// The key the document gives a shown member: the one member of `parent`
/// whose serialization is `part`'s.
fn member_key<P: Serialize, T: Serialize>(parent: &P, part: &T) -> Result<String, String> {
    let parent = serde_json::to_value(parent).map_err(|error| error.to_string())?;
    let part = serde_json::to_value(part).map_err(|error| error.to_string())?;
    let keys: Vec<&String> = parent
        .as_object()
        .into_iter()
        .flatten()
        .filter(|(_, value)| **value == part)
        .map(|(key, _)| key)
        .collect();
    match keys.as_slice() {
        [key] => Ok((*key).clone()),
        _ => Err(format!("an example card member has no single key: {part}")),
    }
}

fn words(parts: &[Option<&String>]) -> String {
    let present: Vec<&str> = parts.iter().flatten().map(|word| word.as_str()).collect();
    present.join(" ")
}

impl Step {
    /// One line for each half of a probe or for an extension action: the
    /// member's key in the document, then its shown values.
    fn lines(&self) -> Result<Vec<String>, String> {
        let mut lines = Vec::new();
        if let Some(query) = &self.sandbox_check {
            let shown = words(&[Some(&query.operation), Some(&query.filter.value)]);
            lines.push(format!("{} {shown}", member_key(self, query)?));
        }
        if let Some(attempt) = &self.attempt {
            let shown = words(&[Some(&attempt.action), Some(&attempt.target)]);
            lines.push(format!("{} {shown}", member_key(self, attempt)?));
        }
        if let Some(event) = &self.extension {
            let shown = words(&[
                Some(&event.operation),
                event.family.as_ref(),
                event.authority.as_ref(),
                event.target.as_ref(),
                event.recipient.as_ref(),
            ]);
            lines.push(format!("{} {shown}", member_key(self, event)?));
        }
        if lines.is_empty() {
            return Err(format!("step {} shows no member", self.step_id));
        }
        Ok(lines)
    }
}

pub fn example_shown(example: Example) -> Result<Shown, String> {
    serde_json::from_str(example.document())
        .map_err(|error| format!("cannot project the {example:?} example card: {error}"))
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
    references: Vec<Reference>,
}

impl Output {
    fn line(&mut self, depth: usize, text: &str) {
        self.lines.push(format!("{}{text}", "  ".repeat(depth)));
    }

    fn command(&mut self, topic: Topic, command: Command) -> Result<(), String> {
        if topic.source() != Address::Command(command) {
            return Err(format!(
                "{command:?} heads a card whose topic is not that command"
            ));
        }
        self.line(0, command.def().spelling);
        self.references.push(Reference::Command(command));
        Ok(())
    }
}

fn render(card: Option<Topic>) -> Result<Rendered, String> {
    let mut out = Output {
        lines: Vec::new(),
        references: Vec::new(),
    };
    match card {
        None => {
            for topic in Topic::ALL.iter().copied() {
                out.line(0, topic.address());
                out.references.push(Reference::Topic(topic));
            }
        }
        Some(Topic::Run) => {
            out.command(Topic::Run, Command::Run)?;
            let option = RUN_OPTION;
            out.line(1, option.def().spelling);
            out.references.push(Reference::Option(option));
            let Value::Kind(reader) = option.def().value else {
                return Err(format!("{option:?} does not take a runner-kind word"));
            };
            for word in Word::ALL.iter().copied() {
                if word.rule(reader) == Some(Rule::Admits) {
                    out.line(2, word.spelling());
                    out.references.push(Reference::Word(word, reader));
                }
            }
        }
        Some(Topic::Example) => {
            out.command(Topic::Example, Command::Example)?;
            for example in Example::ALL.iter().copied() {
                if let Some(name) = example.name() {
                    out.line(0, &format!("{} {name}", Command::Example.def().spelling));
                    out.references.push(Reference::ExampleName(example));
                }
                let shown = example_shown(example)?;
                if let Some(actors) = &shown.actors {
                    out.line(1, &member_key(&shown, actors)?);
                    for actor in actors {
                        let mode = Some(&actor.sandbox.mode);
                        let shown = words(&[Some(&actor.actor_id), actor.equipment.as_ref(), mode]);
                        out.line(2, &shown);
                    }
                }
                for phase in &shown.phases {
                    out.line(1, &words(&[Some(&phase.phase_id), phase.actor_id.as_ref()]));
                    for step in &phase.actions {
                        out.line(2, &step.step_id);
                        for line in step.lines()? {
                            out.line(3, &line);
                        }
                    }
                }
                out.references.push(Reference::ExampleDocument(example));
            }
        }
        Some(Topic::Result) => {
            out.line(0, Topic::Result.address());
            out.references.push(Reference::Topic(Topic::Result));
            let names = RESULT_FIELDS
                .iter()
                .map(|field| result_key(*field))
                .collect::<Result<Vec<_>, _>>()?;
            out.line(1, &names.join(" "));
            out.references.push(Reference::ResultFields);
            for (row, disposition) in fixed_dispositions() {
                let selection = select(&disposition);
                if selection.row != row {
                    return Err(format!("{row:?} does not select its own disposition"));
                }
                let result = serde_json::to_value(run_result(&selection, None))
                    .map_err(|error| error.to_string())?;
                let mut cells = Vec::new();
                for name in &names {
                    cells.push(scalar(&result[name])?);
                }
                out.line(1, &cells.join(" "));
                let reference = Reference::ResultRow(row);
                if !out.references.contains(&reference) {
                    out.references.push(reference);
                }
            }
        }
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
        topic: card,
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
