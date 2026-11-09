//! Shape goldens: per object path, every key a document carries and its JSON
//! type. The goldens under `tests/fixtures/contract/` are the readers'
//! allowlists; `tests/lib/consumer.py` rejects an unknown key at a recorded
//! path and a present key of another type.
//!
//! The collector follows the same rules as the Python reader of the reply
//! golden (`tests/suites/runner_unit/porcelain_replies.py`): an array is
//! typed `array` and every object element contributes to the `path[]` entry; a
//! key seen as null in one place and typed in another records the type; two
//! different types at one path are a producer conflict. A golden type of
//! `null` constrains nothing.

use serde_json::{Map, Value};
use std::collections::BTreeMap;

pub type Shape = BTreeMap<String, BTreeMap<String, String>>;

pub fn json_type(value: &Value) -> &'static str {
    match value {
        Value::Null => "null",
        Value::Bool(_) => "boolean",
        Value::Number(_) => "number",
        Value::String(_) => "string",
        Value::Array(_) => "array",
        Value::Object(_) => "object",
    }
}

fn record(into: &mut Shape, path: &str, key: &str, kind: &str) -> Result<(), String> {
    let keys = into.entry(path.to_string()).or_default();
    match keys.get(key) {
        Some(existing) if existing == kind || kind == "null" => Ok(()),
        Some(existing) if existing == "null" => {
            keys.insert(key.to_string(), kind.to_string());
            Ok(())
        }
        Some(existing) => Err(format!(
            "shape conflict at {path}.{key}: {existing} and {kind}"
        )),
        None => {
            keys.insert(key.to_string(), kind.to_string());
            Ok(())
        }
    }
}

/// Collect `value`'s shape under `path`. A child path listed in `opaque` is
/// typed where it appears but not entered: another golden owns its contents.
pub fn collect(value: &Value, path: &str, opaque: &[&str], into: &mut Shape) -> Result<(), String> {
    let Some(object) = value.as_object() else {
        return Ok(());
    };
    into.entry(path.to_string()).or_default();
    for (key, child) in object {
        record(into, path, key, json_type(child))?;
        let child_path = format!("{path}.{key}");
        if opaque.contains(&child_path.as_str()) {
            continue;
        }
        match child {
            Value::Object(_) => collect(child, &child_path, opaque, into)?,
            Value::Array(items) => {
                let element_path = format!("{child_path}[]");
                for item in items.iter().filter(|item| item.is_object()) {
                    collect(item, &element_path, opaque, into)?;
                }
            }
            _ => {}
        }
    }
    Ok(())
}

fn shape_from_value(value: &Value) -> Shape {
    let mut shape = Shape::new();
    if let Some(paths) = value.as_object() {
        for (path, keys) in paths {
            let entry = shape.entry(path.clone()).or_default();
            if let Some(keys) = keys.as_object() {
                for (key, kind) in keys {
                    entry.insert(key.clone(), kind.as_str().unwrap_or("null").to_string());
                }
            }
        }
    }
    shape
}

pub fn shape_to_value(shape: &Shape) -> Value {
    let mut paths = Map::new();
    for (path, keys) in shape {
        let mut object = Map::new();
        for (key, kind) in keys {
            object.insert(key.clone(), Value::String(kind.clone()));
        }
        paths.insert(path.clone(), Value::Object(object));
    }
    Value::Object(paths)
}

#[derive(Debug, PartialEq)]
pub enum Verdict {
    Ok,
    MissingGolden,
    /// Review the changed shape and update its golden.
    Update(String),
}

/// A changed shape requires review of its golden and normative definition.
pub fn classify(golden: Option<&Value>, current: &Shape) -> Verdict {
    let Some(recorded) = golden.and_then(|g| g.get("shape")) else {
        return Verdict::MissingGolden;
    };
    let expected = shape_from_value(recorded);
    if expected == *current {
        Verdict::Ok
    } else {
        Verdict::Update(
            same_shape(&expected, current)
                .err()
                .unwrap_or_else(|| "nullable field shape changed".into()),
        )
    }
}

/// The golden's entries at and under `prefix`, re-rooted at `root`, so a
/// helper binary can compare the shape it emits with the subtree the
/// controller envelope records for it.
pub fn golden_subtree(golden: &Value, prefix: &str, root: &str) -> Shape {
    let mut subtree = Shape::new();
    for (path, keys) in shape_from_value(golden.get("shape").unwrap_or(&Value::Null)) {
        let rest = if path == prefix {
            Some("")
        } else {
            path.strip_prefix(prefix)
                .filter(|rest| rest.starts_with('.') || rest.starts_with('['))
        };
        if let Some(rest) = rest {
            subtree.insert(format!("{root}{rest}"), keys);
        }
    }
    subtree
}

/// Equal key sets at every path; a type of `null` on either side constrains
/// nothing. The error lists every difference.
pub fn same_shape(expected: &Shape, actual: &Shape) -> Result<(), String> {
    let mut problems = Vec::new();
    for (path, keys) in expected {
        match actual.get(path) {
            None => problems.push(format!("missing path {path}")),
            Some(now) => {
                for (key, kind) in keys {
                    match now.get(key) {
                        None => problems.push(format!("missing key {path}.{key}")),
                        Some(t) if t != kind && t != "null" && kind != "null" => {
                            problems.push(format!("{path}.{key}: golden {kind}, emitted {t}"))
                        }
                        Some(_) => {}
                    }
                }
                for key in now.keys() {
                    if !keys.contains_key(key) {
                        problems.push(format!("unrecorded key {path}.{key}"));
                    }
                }
            }
        }
    }
    for path in actual.keys() {
        if !expected.contains_key(path) {
            problems.push(format!("unrecorded path {path}"));
        }
    }
    if problems.is_empty() {
        Ok(())
    } else {
        Err(problems.join("; "))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn shape(entries: &[(&str, &[(&str, &str)])]) -> Shape {
        entries
            .iter()
            .map(|(path, keys)| {
                (
                    path.to_string(),
                    keys.iter()
                        .map(|(k, t)| (k.to_string(), t.to_string()))
                        .collect(),
                )
            })
            .collect()
    }

    #[test]
    fn collector_types_every_element_and_stops_at_opaque_paths() {
        let value = json!({
            "a": 1,
            "list": [{"x": null, "y": "s"}, {"x": 2, "z": true}, 7],
            "inner": {"k": {"deep": []}},
            "foreign": {"not": "entered"},
        });
        let mut collected = Shape::new();
        collect(&value, "root", &["root.foreign"], &mut collected).unwrap();
        assert_eq!(
            collected,
            shape(&[
                (
                    "root",
                    &[
                        ("a", "number"),
                        ("foreign", "object"),
                        ("inner", "object"),
                        ("list", "array")
                    ]
                ),
                ("root.inner", &[("k", "object")]),
                ("root.inner.k", &[("deep", "array")]),
                (
                    "root.list[]",
                    &[("x", "number"), ("y", "string"), ("z", "boolean")]
                ),
            ])
        );
        let conflict = json!({"list": [{"x": 1}, {"x": "one"}]});
        let error = collect(&conflict, "root", &[], &mut Shape::new()).unwrap_err();
        assert!(error.contains("shape conflict at root.list[].x"), "{error}");
    }

    #[test]
    fn changed_shapes_require_review_without_a_revision_counter() {
        let base = shape(&[("root", &[("key", "number")])]);
        let golden = json!({"shape":shape_to_value(&base)});
        assert_eq!(classify(None, &base), Verdict::MissingGolden);
        assert_eq!(classify(Some(&golden), &base), Verdict::Ok);
        for changed in [
            shape(&[("root", &[])]),
            shape(&[("root", &[("key", "string")])]),
            shape(&[("root", &[("key", "number"), ("added", "string")])]),
        ] {
            assert!(matches!(
                classify(Some(&golden), &changed),
                Verdict::Update(_)
            ));
        }
    }

    #[test]
    fn subtrees_are_rerooted_and_compared_with_null_tolerance() {
        let golden = json!({"v": 1, "shape": {
            "envelope": {"data": "object"},
            "envelope.data.helper": {"kind": "string", "result": "object"},
            "envelope.data.helper.result": {"rc": "number", "error": "null"},
            "envelope.data.helpers[]": {"n": "number"},
            "envelope.data.helper_other": {"x": "number"},
        }});
        let subtree = golden_subtree(&golden, "envelope.data.helper", "helper");
        assert_eq!(
            subtree,
            shape(&[
                ("helper", &[("kind", "string"), ("result", "object")]),
                ("helper.result", &[("error", "null"), ("rc", "number")]),
            ])
        );
        let emitted = shape(&[
            ("helper", &[("kind", "string"), ("result", "object")]),
            ("helper.result", &[("error", "string"), ("rc", "null")]),
        ]);
        same_shape(&subtree, &emitted).unwrap();
        let mut drifted = emitted.clone();
        drifted
            .get_mut("helper")
            .unwrap()
            .insert("extra".into(), "number".into());
        drifted.get_mut("helper.result").unwrap().remove("rc");
        let error = same_shape(&subtree, &drifted).unwrap_err();
        assert!(
            error.contains("unrecorded key helper.extra")
                && error.contains("missing key helper.result.rc"),
            "{error}"
        );
    }
}
