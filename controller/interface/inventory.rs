//! The interface inventory: every definition the governing tables hold,
//! whether or not a card selects it, with the cards that reference it.
//!
//! Identifiers come from the typed identities the card specifications
//! reference. Facts about the result relation that are not row fields are
//! computed by evaluating `select`; none is written here by hand.

use std::fmt::Debug;

use serde_json::{Value, json};

use crate::cards::{self, RESULT_FIELDS, Rendered};
use crate::interface::commands::{Address, Command, Tail, Topic};
use crate::interface::result::{
    Class, Disposition, Host, Label, Outcome, Refusal, Row, Selection, select,
};
use crate::interface::run_args::{
    FLAG_PREFIX, RunOption, TERMINATOR, Token, Value as OptionValue, classify,
};
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
impl Identified for Topic {
    const TABLE: &'static str = "topic";
}
impl Identified for RunOption {
    const TABLE: &'static str = "run.option";
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
        let kind = match classify(&sample) {
            Token::RequestPath | Token::Option(_) => ADMITS,
            Token::Terminator => DISCARDS,
            Token::UnknownFlag => REFUSES_ALWAYS,
        };
        entries.push(entry(
            identifier.to_string(),
            kind,
            run_parser(),
            &spellings,
            json!({"command": run, "flag_prefix": prefix, "classified_as": snake(&classify(&sample))}),
        ));
    }
    for option in RunOption::ALL.iter().copied() {
        let def = option.def();
        let value = match def.value {
            OptionValue::Milliseconds { min } => json!({"milliseconds": {"min": min}}),
            OptionValue::Kind(reader_id) => json!({"runner_kind_reader": snake(&reader_id)}),
        };
        let kind = match classify(def.spelling) {
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
    for pair in evaluated.chunks(2) {
        if let [(_, first_inputs, first), (_, second_inputs, second)] = pair {
            if first_inputs.get("integrity_issues").is_some()
                && first_inputs["host_outcome"] == second_inputs["host_outcome"]
                && first != second
            {
                integrity_changes = true;
            }
        }
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

fn example_section() -> Value {
    let phases: Vec<Value> = cards::example_phases()
        .unwrap_or_else(|error| panic!("{error}"))
        .into_iter()
        .map(|(phase_id, attempts)| {
            json!({
                "phase_id": phase_id,
                "attempts": attempts.into_iter().map(|(action, target)| json!({"action": action, "target": target})).collect::<Vec<_>>(),
            })
        })
        .collect();
    json!({
        "id": "example.document",
        "reader": reader("controller/src/example.rs", "pub fn render"),
        "source": reader("controller/src/example_document.rs", "EXAMPLE_DOCUMENT"),
        "phases": phases,
    })
}

fn cards_referencing(identifier: &str, rendered: &[Rendered]) -> Vec<String> {
    rendered
        .iter()
        .filter(|card| {
            card.references
                .iter()
                .any(|reference| reference == identifier)
        })
        .map(|card| card.name.clone())
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
    let mut example = example_section();
    example["cards"] = json!(cards_referencing("example.document", rendered));
    known.push("example.document".into());

    let cards: serde_json::Map<String, Value> = rendered
        .iter()
        .map(|card| {
            for reference in &card.references {
                assert!(
                    known.contains(reference),
                    "card {} references no entry: {reference}",
                    card.name
                );
            }
            (
                card.name.clone(),
                json!({"text": card.text, "references": card.references}),
            )
        })
        .collect();
    let document = json!({
        "schema": 1,
        "entries": entries,
        "result": result,
        "example": example,
        "cards": cards,
    });
    let mut text = serde_json::to_string_pretty(&document).expect("the inventory serializes");
    text.push('\n');
    text
}
