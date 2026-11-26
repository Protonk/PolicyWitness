//! The interface inventory: every definition the governing tables hold,
//! whether or not a card selects it, with the cards that reference it.
//!
//! Identifiers come from the typed identities the card specifications
//! reference. Facts about the result relation that are not row fields are
//! computed by evaluating `select`; none is written here by hand.

use std::collections::BTreeSet;
use std::fmt::Debug;

use serde_json::{Value, json};

use crate::cards::{self, RESULT_FIELDS, Reference, Rendered};
use crate::interface::commands::{Address, Command, Example, Tail, TestInputForm, Topic};
use crate::interface::result::{
    Class, Disposition, Host, Label, Outcome, Refusal, Row, Selection, select,
};
use crate::interface::run_args::{
    Control, ControlValue, FLAG_PREFIX, Form, RunOption, TERMINATOR, Token, Value as OptionValue,
    classify,
};
use crate::interface::runner::{Removal, RunnerForm, Selector};
use crate::interface::runner_kind::{Reader, Rule, Word};

/// `TimeoutMs` as `timeout_ms`.
pub fn snake(value: &dyn Debug) -> String {
    let name = format!("{value:?}");
    let mut text = String::new();
    for (index, character) in name.chars().enumerate() {
        if character.is_ascii_uppercase() && index > 0 {
            text.push('_');
        }
        text.push(character.to_ascii_lowercase());
    }
    text
}

/// A definition's stable identifier: its table and its variant.
pub trait Identified: Debug {
    const TABLE: &'static str;
}
impl Identified for Command {
    const TABLE: &'static str = "command";
}
impl Identified for Example {
    const TABLE: &'static str = "example.name";
}
impl Identified for Topic {
    const TABLE: &'static str = "topic";
}
impl Identified for TestInputForm {
    const TABLE: &'static str = "test_input.form";
}
impl Identified for RunnerForm {
    const TABLE: &'static str = "runner.form";
}
impl Identified for Selector {
    const TABLE: &'static str = "runner.selector";
}
impl Identified for RunOption {
    const TABLE: &'static str = "run.option";
}
impl Identified for Control {
    const TABLE: &'static str = "run.control";
}
impl Identified for Word {
    const TABLE: &'static str = "runner_kind";
}
impl Identified for Row {
    const TABLE: &'static str = "result";
}

pub fn id<T: Identified>(value: &T) -> String {
    format!("{}.{}", T::TABLE, snake(value))
}

/// Internal card file/key name; never printed on a card.
pub fn card_name(topic: Option<Topic>) -> String {
    topic.map_or_else(|| "base".to_string(), |topic| snake(&topic))
}

fn reference_id(reference: &Reference) -> String {
    match reference {
        Reference::Command(command) => id(command),
        Reference::Topic(topic) => id(topic),
        Reference::RunnerForm(form) => id(form),
        Reference::Selector(selector) => id(selector),
        Reference::Removal => "runner.removal".into(),
        Reference::Option(option) => id(option),
        Reference::Word(word, reader) => format!("{}@{}", id(word), snake(reader)),
        Reference::ExampleName(example) => id(example),
        Reference::ExampleDocument(example) => document_id(*example),
        Reference::ResultFields => "result.fields".into(),
        Reference::ResultRow(row) => id(row),
    }
}

/// The admission kinds an entry can carry, named for the value dispatch or
/// parsing acts on.
const ADMITS: &str = "admits";
const REFUSES_ALWAYS: &str = "refuses_always";
const DISCARDS: &str = "discards";
const ALIAS: &str = "alias";
const UNENUMERATED: &str = "unenumerated";

/// The code that consumes a table, cited the way the generators cite source.
fn reader(path: &str, symbol: &str) -> Value {
    json!({"path": path, "symbol": symbol})
}
fn dispatch() -> Value {
    reader("controller/src/cli.rs", "pub fn run")
}
fn help() -> Value {
    reader("controller/src/interface/commands.rs", "pub fn select")
}
fn form_selection() -> Value {
    reader("controller/src/interface/commands.rs", "pub fn select_form")
}
fn test_input_dispatch() -> Value {
    reader("controller/src/test_input.rs", "pub fn cmd_test_input")
}
fn run_parser() -> Value {
    reader("controller/src/run_flow.rs", "fn parse_arguments")
}
fn kind_reader(reader_id: Reader) -> Value {
    let (path, symbol) = match reader_id {
        Reader::RunOption => ("controller/src/run_flow.rs", "fn runner_mode_kind"),
        Reader::RequestSelector => ("controller/src/runner_select.rs", "fn parse_runner_mode"),
        Reader::InstallOption => ("controller/src/runner_commands.rs", "fn install_kind"),
        Reader::Registry => (
            "controller/src/runner_manager.rs",
            "Deserialize<'de> for RunnerKind",
        ),
    };
    json!({"path": path, "symbol": symbol, "reader": snake(&reader_id)})
}

fn entry(
    identifier: String,
    kind: &str,
    read_by: Value,
    spellings: &[&str],
    relationships: Value,
) -> Value {
    json!({
        "id": identifier,
        "kind": kind,
        "reader": read_by,
        "spellings": spellings,
        "relationships": relationships,
    })
}

fn command_entries() -> Vec<Value> {
    let mut entries = Vec::new();
    for command in Command::ALL.iter().copied() {
        let def = command.def();
        entries.push(entry(
            id(&command),
            ADMITS,
            dispatch(),
            &[def.spelling],
            json!({"tail": snake(&def.tail)}),
        ));
        // What dispatch does with the arguments after the command.
        let (kind, relationships) = match def.tail {
            Tail::RunArguments => continue,
            Tail::RunnerForm => {
                entries.extend(runner_entries(command));
                continue;
            }
            Tail::Form => {
                entries.extend(test_input_entries(command));
                continue;
            }
            Tail::ExampleName => {
                let select = reader(
                    "controller/src/interface/commands.rs",
                    "pub fn from_arguments",
                );
                for example in Example::ALL.iter().copied() {
                    if let Some(name) = example.name() {
                        entries.push(entry(
                            id(&example),
                            ADMITS,
                            select.clone(),
                            &[name],
                            json!({"command": id(&command), "document": document_id(example)}),
                        ));
                    }
                }
                entries.push(entry(
                    format!("tail.{}", snake(&command)),
                    REFUSES_ALWAYS,
                    select,
                    &[],
                    json!({"command": id(&command), "rule": "unknown_name_or_extra_operand"}),
                ));
                continue;
            }
            Tail::Topic => (
                DISCARDS,
                json!({"except_first_argument": Topic::ALL.iter().map(id).collect::<Vec<_>>()}),
            ),
            Tail::RefusesAny => (REFUSES_ALWAYS, json!({})),
            Tail::Unenumerated => (UNENUMERATED, json!({})),
        };
        let mut relationships = relationships;
        relationships["command"] = json!(id(&command));
        relationships["rule"] = json!(snake(&def.tail));
        entries.push(entry(
            format!("tail.{}", snake(&command)),
            kind,
            dispatch(),
            &[],
            relationships,
        ));
    }
    for topic in Topic::ALL.iter().copied() {
        let source = match topic.source() {
            Address::Command(command) => json!({"shares_spelling_of": id(&command)}),
            Address::Own(_) => json!({"shares_spelling_of": null}),
        };
        entries.push(entry(
            id(&topic),
            ADMITS,
            help(),
            &[topic.address()],
            source,
        ));
    }
    entries
}

/// The forms of `test-input`: each form, what the command does with any
/// other first argument, and a form's tail where its own parser holds the
/// definitions.
fn test_input_entries(command: Command) -> Vec<Value> {
    assert_eq!(command, Command::TestInput, "one command has forms");
    let name = snake(&command);
    let mut entries = Vec::new();
    for form in TestInputForm::ALL.iter().copied() {
        let def = form.def();
        entries.push(entry(
            id(&form),
            ADMITS,
            form_selection(),
            &[def.spelling],
            json!({"command": id(&command), "tail": snake(&def.tail)}),
        ));
        match def.tail {
            Tail::RunArguments => {}
            Tail::Unenumerated => entries.push(entry(
                format!("tail.{name}.{}", snake(&form)),
                UNENUMERATED,
                test_input_dispatch(),
                &[],
                json!({"form": id(&form), "rule": snake(&def.tail)}),
            )),
            other => panic!("{form:?} has the tail rule {other:?}, which no form uses"),
        }
    }
    entries.push(entry(
        format!("{name}.unknown_form"),
        REFUSES_ALWAYS,
        test_input_dispatch(),
        &[],
        json!({"command": id(&command), "rule": snake(&command.def().tail)}),
    ));
    entries
}

fn runner_entries(command: Command) -> Vec<Value> {
    let dispatch = reader("controller/src/runner_commands.rs", "pub fn cmd_runner(");
    let mut entries = vec![entry(
        "runner.unknown_form".into(),
        REFUSES_ALWAYS,
        dispatch.clone(),
        &[],
        json!({"command": id(&command)}),
    )];
    for &form in RunnerForm::ALL {
        let tail = if form.takes_arguments() {
            if form == RunnerForm::Status {
                "selectors"
            } else {
                UNENUMERATED
            }
        } else {
            "refuses_any"
        };
        entries.push(entry(
            id(&form),
            ADMITS,
            dispatch.clone(),
            &[form.spelling()],
            json!({
                "command": id(&command), "tail": tail,
                "description": form.description(), "takes_selector": form.takes_selector()
            }),
        ));
        entries.push(entry(
            format!("tail.runner.{}", snake(&form)),
            if tail == UNENUMERATED {
                UNENUMERATED
            } else {
                REFUSES_ALWAYS
            },
            if form == RunnerForm::Status {
                reader("controller/src/runner_commands.rs", "fn cmd_runner_status(")
            } else {
                dispatch.clone()
            },
            &[],
            json!({"form": id(&form), "rule": tail}),
        ));
    }
    for &selector in Selector::ALL {
        let forms = RunnerForm::ALL
            .iter()
            .filter(|form| form.takes_selector())
            .map(id)
            .collect::<Vec<_>>();
        entries.push(entry(
            id(&selector),
            ADMITS,
            reader("controller/src/runner_commands.rs", "fn consume("),
            &[selector.spelling()],
            json!({"operand": selector.operand(), "forms": forms}),
        ));
    }
    entries
}

fn run_entries() -> Vec<Value> {
    let run = id(&Command::Run);
    let prefix = FLAG_PREFIX.to_string();
    let mut entries = Vec::new();
    // One entry per token class, with the kind the parser's own classifier
    // gives a spelling of that class.
    let unlisted_flag = format!("{prefix}{prefix}{prefix}");
    for (identifier, sample, spellings) in [
        ("run.request_path", String::new(), Vec::new()),
        ("run.terminator", TERMINATOR.to_string(), vec![TERMINATOR]),
        ("run.unknown_flag", unlisted_flag, Vec::new()),
    ] {
        let kind = match classify(&sample, Form::Run) {
            Token::RequestPath | Token::Option(_) | Token::Control(_) => ADMITS,
            Token::Terminator => DISCARDS,
            Token::UnknownFlag => REFUSES_ALWAYS,
        };
        entries.push(entry(
            identifier.to_string(),
            kind,
            run_parser(),
            &spellings,
            json!({"command": run, "flag_prefix": prefix, "classified_as": snake(&classify(&sample, Form::Run))}),
        ));
    }
    for option in RunOption::ALL.iter().copied() {
        let def = option.def();
        let value = match def.value {
            OptionValue::Milliseconds { min } => json!({"milliseconds": {"min": min}}),
            OptionValue::Kind(reader_id) => json!({"runner_kind_reader": snake(&reader_id)}),
        };
        let kind = match classify(def.spelling, Form::Run) {
            Token::Option(found) if found == option => ADMITS,
            other => panic!("{option:?} is classified as {other:?}"),
        };
        entries.push(entry(
            id(&option),
            kind,
            run_parser(),
            &[def.spelling],
            json!({"command": run, "value": value}),
        ));
    }
    // A control is an argument of the one form whose rule is `run`'s with
    // the controls; under `run` itself its spelling is an unknown flag.
    let form = id(&TestInputForm::Run);
    for control in Control::ALL.iter().copied() {
        let def = control.def();
        let value = match def.value {
            ControlValue::Integer => json!({"integer": "i64"}),
            ControlValue::Text => json!({"text": "utf8"}),
        };
        let kind = match (
            classify(def.spelling, Form::TestInputRun),
            classify(def.spelling, Form::Run),
        ) {
            (Token::Control(found), Token::UnknownFlag) if found == control => ADMITS,
            other => panic!("{control:?} is classified as {other:?}"),
        };
        entries.push(entry(
            id(&control),
            kind,
            run_parser(),
            &[def.spelling],
            json!({"form": form, "key": def.key, "value": value, "repeated": "refused"}),
        ));
    }
    entries
}

fn kind_entries() -> Vec<Value> {
    let mut entries = Vec::new();
    for word in Word::ALL.iter().copied() {
        for reader_id in Reader::ALL.iter().copied() {
            let kind = match word.rule(reader_id) {
                None => continue,
                Some(Rule::Admits) => ADMITS,
                Some(Rule::Alias) => ALIAS,
            };
            entries.push(entry(
                format!("{}@{}", id(&word), snake(&reader_id)),
                kind,
                kind_reader(reader_id),
                &[word.spelling()],
                json!({"kind": word.kind().as_str()}),
            ));
        }
    }
    entries
}

/// The dispositions `select` is evaluated on to compute the relation's
/// derived facts: every class, every refusal, and for an admitted capture an
/// absent host label, every label the controller itself spells, and one
/// label it spells nowhere.
fn evaluation_grid(unlisted: &str) -> Vec<(Disposition<'_>, Value)> {
    let mut grid = vec![
        (
            Disposition::LocalRequestRefusal,
            json!({"class": snake(&Class::LocalRequestRefusal)}),
        ),
        (
            Disposition::ToolFailure,
            json!({"class": snake(&Class::ToolFailure)}),
        ),
    ];
    for refusal in Refusal::ALL.iter().copied() {
        grid.push((
            Disposition::AdmissionRefusal(refusal),
            json!({"class": snake(&Class::AdmissionRefusal), "refusal": refusal.spelling()}),
        ));
    }
    let mut hosts: Vec<(Option<&str>, Value)> = vec![(None, Value::Null)];
    hosts.extend(
        Label::ALL
            .iter()
            .map(|label| (Some(label.spelling()), json!(label.spelling()))),
    );
    hosts.extend(
        Refusal::ALL
            .iter()
            .map(|refusal| (Some(refusal.spelling()), json!(refusal.spelling()))),
    );
    hosts.push((Some(unlisted), json!({"unlisted": true})));
    for (host_outcome, shown) in hosts {
        for integrity_issues in [0usize, 1] {
            grid.push((
                Disposition::Admitted { host_outcome, integrity_issues },
                json!({"class": snake(&Class::Admitted), "host_outcome": shown, "integrity_issues": integrity_issues}),
            ));
        }
    }
    grid
}

fn outputs(selection: &Selection, unlisted: &str) -> Value {
    let outcome = if selection.outcome == unlisted {
        json!({"unlisted": true})
    } else {
        json!(selection.outcome)
    };
    json!([outcome, selection.ok, selection.exit])
}

fn result_section() -> Value {
    let field_names: Vec<String> = RESULT_FIELDS
        .iter()
        .map(|field| cards::result_key(*field).unwrap_or_else(|error| panic!("{error}")))
        .collect();
    let rows: Vec<Value> = Row::ALL
        .iter()
        .copied()
        .enumerate()
        .map(|(order, row)| {
            let def = row.def();
            let host = match def.host {
                Host::Unread => json!("unread"),
                Host::Is(label) => json!({"is": label.spelling()}),
                Host::Present => json!("present"),
                Host::Absent => json!("absent"),
            };
            let outcome = match def.outcome {
                Outcome::Fixed(label) => json!({"fixed": label.spelling()}),
                Outcome::Refusal => {
                    json!({"refusal": Refusal::ALL.iter().map(|refusal| refusal.spelling()).collect::<Vec<_>>()})
                }
                Outcome::HostLabel => json!("host_label"),
            };
            json!({
                "id": id(&row),
                "order": order,
                "inputs": {"class": snake(&def.class), "host_outcome": host},
                "outputs": {"normalized_outcome": outcome, "ok": def.ok, "exit_code": def.exit},
            })
        })
        .collect();

    // Derived by evaluation.
    let unlisted: String = Label::ALL.iter().map(|label| label.spelling()).collect();
    let grid = evaluation_grid(&unlisted);
    let evaluated: Vec<(Row, Value, Value)> = grid
        .iter()
        .map(|(disposition, inputs)| {
            let selection = select(disposition);
            (
                selection.row,
                inputs.clone(),
                outputs(&selection, &unlisted),
            )
        })
        .collect();

    // An input that never changes an output while the others are held.
    let mut integrity_changes = false;
    for (_, first_inputs, first) in &evaluated {
        if first_inputs.get("integrity_issues").and_then(Value::as_u64) != Some(0) {
            continue;
        }
        let (_, _, second) = evaluated
            .iter()
            .find(|(_, inputs, _)| {
                inputs.get("integrity_issues").and_then(Value::as_u64) == Some(1)
                    && inputs["class"] == first_inputs["class"]
                    && inputs["host_outcome"] == first_inputs["host_outcome"]
            })
            .expect("every zero-issue sample has a matching one-issue sample");
        integrity_changes |= first != second;
    }
    let unselecting = if integrity_changes {
        json!([])
    } else {
        json!([{"input": "integrity_issues", "class": snake(&Class::Admitted), "changes_an_output": false}])
    };

    // Which output determines which other output across the grid.
    let mut functions = Vec::new();
    for (from_index, from) in field_names.iter().enumerate() {
        for (to_index, to) in field_names.iter().enumerate() {
            if from_index == to_index {
                continue;
            }
            let counterexample = evaluated.iter().find_map(|(_, _, first)| {
                evaluated.iter().find_map(|(_, _, second)| {
                    (first[from_index] == second[from_index] && first[to_index] != second[to_index])
                        .then(|| json!([first, second]))
                })
            });
            functions.push(json!({
                "of": from,
                "output": to,
                "is_a_function": counterexample.is_none(),
                "counterexample": counterexample,
            }));
        }
    }

    // Pairs of rows that some inputs send to the same outputs.
    let mut indistinguishable = Vec::new();
    for (first_index, first_row) in Row::ALL.iter().copied().enumerate() {
        for second_row in Row::ALL.iter().copied().skip(first_index + 1) {
            let witness = evaluated.iter().find_map(|(row, _, first)| {
                (*row == first_row
                    && evaluated
                        .iter()
                        .any(|(other, _, second)| *other == second_row && first == second))
                .then(|| first.clone())
            });
            if let Some(witness) = witness {
                indistinguishable.push(json!({
                    "rows": [id(&first_row), id(&second_row)],
                    "shared_outputs": witness,
                }));
            }
        }
    }

    json!({
        "reader": reader("controller/src/interface/result.rs", "pub fn select"),
        "selection": "first_match",
        "fields": RESULT_FIELDS.iter().zip(&field_names).map(|(field, name)| json!({"id": format!("result.field.{}", snake(field)), "name": name})).collect::<Vec<_>>(),
        "rows": rows,
        "derived": {
            "outputs": field_names,
            "inputs_that_change_no_output": unselecting,
            "output_functions": functions,
            "rows_sharing_outputs": indistinguishable,
        },
    })
}

fn document_id(example: Example) -> String {
    match example {
        Example::Default => "example.document".into(),
        named => format!("example.document.{}", snake(&named)),
    }
}

fn example_section(example: Example, rendered: &[Rendered]) -> Value {
    let identifier = document_id(example);
    let shown = serde_json::to_value(
        cards::example_shown(example).unwrap_or_else(|error| panic!("{error}")),
    )
    .expect("the shown members serialize");
    let document: Value =
        serde_json::from_str(example.document()).expect("the example document is JSON");
    let (mut published, mut carded) = (BTreeSet::new(), BTreeSet::new());
    member_paths(&document, "", &mut published);
    member_paths(&shown, "", &mut carded);
    let omitted: Vec<&String> = published.difference(&carded).collect();
    json!({
        "id": identifier,
        "cards": cards_referencing(&identifier, rendered),
        "name": example.name(),
        "reader": reader("controller/src/example.rs", "pub fn render"),
        "source": reader("controller/src/example_document.rs", example.symbol()),
        "shown": shown,
        "omitted": omitted,
    })
}

/// The path of every scalar member, with array positions collapsed.
fn member_paths(value: &Value, prefix: &str, paths: &mut BTreeSet<String>) {
    match value {
        Value::Object(map) => {
            for (key, member) in map {
                let path = if prefix.is_empty() {
                    key.clone()
                } else {
                    format!("{prefix}.{key}")
                };
                member_paths(member, &path, paths);
            }
        }
        Value::Array(items) => {
            for item in items {
                member_paths(item, &format!("{prefix}[]"), paths);
            }
        }
        _ => {
            paths.insert(prefix.into());
        }
    }
}

fn cards_referencing(identifier: &str, rendered: &[Rendered]) -> Vec<String> {
    rendered
        .iter()
        .filter(|card| {
            card.references
                .iter()
                .any(|reference| reference_id(reference) == identifier)
        })
        .map(|card| card_name(card.topic))
        .collect()
}

/// The inventory document: sorted keys, two-space indentation, one newline.
pub fn render(rendered: &[Rendered]) -> String {
    let mut entries = command_entries();
    entries.extend(run_entries());
    entries.extend(kind_entries());
    let mut known: Vec<String> = Vec::new();
    for item in &mut entries {
        let identifier = item["id"].as_str().unwrap().to_string();
        item["cards"] = json!(cards_referencing(&identifier, rendered));
        assert!(
            !known.contains(&identifier),
            "duplicate inventory identifier {identifier}"
        );
        known.push(identifier);
    }
    let mut result = result_section();
    for row in result["rows"].as_array_mut().unwrap() {
        let identifier = row["id"].as_str().unwrap().to_string();
        row["cards"] = json!(cards_referencing(&identifier, rendered));
        known.push(identifier);
    }
    result["cards"] = json!(cards_referencing("result.fields", rendered));
    known.push("result.fields".into());
    let examples: Vec<_> = Example::ALL
        .iter()
        .map(|example| {
            known.push(document_id(*example));
            example_section(*example, rendered)
        })
        .collect();

    let removal_id = "runner.removal";
    known.push(removal_id.into());
    let removal = json!({"id": removal_id, "field": Removal::FIELD,
        "rows": Removal::ALL.iter().map(|state| json!({"retained": state.retained(), "guidance": state.guidance()})).collect::<Vec<_>>(),
        "cards": cards_referencing(removal_id, rendered)});
    let cards: serde_json::Map<String, Value> = rendered
        .iter()
        .map(|card| {
            let name = card_name(card.topic);
            let references: Vec<String> = card.references.iter().map(reference_id).collect();
            for reference in &references {
                assert!(
                    known.contains(reference),
                    "card {name} references no entry: {reference}",
                );
            }
            (name, json!({"text": card.text, "references": references}))
        })
        .collect();
    let document = json!({
        "schema": 4,
        "entries": entries,
        "result": result,
        "examples": examples,
        "removal": removal,
        "cards": cards,
    });
    let mut text = serde_json::to_string_pretty(&document).expect("the inventory serializes");
    text.push('\n');
    text
}
