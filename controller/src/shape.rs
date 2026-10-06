//! Shape goldens: per object path, every key a document carries and its JSON
//! type. The goldens under `tests/fixtures/contract/` are the readers'
//! allowlists; `tests/lib/consumer.py` rejects an unknown key at a recorded
//! path and a present key of another type.
//!
//! The collector mirrors the Swift reader of the reply golden
//! (`runner/Tests/PWRunnerCoreTests/ContractVersionTests.swift`): an array is
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
    /// A key was removed or changed type under an unchanged number.
    NeedsBump(String),
    /// Additive, nullable or already-bumped: replace the golden after review.
    Update(String),
}

/// The Swift reader's classification: removed or retyped keys need a bump
/// unless the manifest already moved; added keys and nullable refinements are
/// acknowledged by replacing the golden.
pub fn classify(
    golden: Option<&Value>,
    version_key: &str,
    current: &Shape,
    manifest_version: u64,
) -> Verdict {
    let Some(recorded) = golden
        .and_then(|g| g.get(version_key))
        .and_then(Value::as_u64)
    else {
        return Verdict::MissingGolden;
    };
    let golden_shape = golden
        .and_then(|g| g.get("shape"))
        .map(shape_from_value)
        .unwrap_or_default();
    if golden_shape == *current && recorded == manifest_version {
        return Verdict::Ok;
    }
    let mut removed = Vec::new();
    let mut changed = Vec::new();
    let mut added = Vec::new();
    for (path, keys) in &golden_shape {
        for (key, kind) in keys {
            match current.get(path).and_then(|k| k.get(key)) {
                None => removed.push(format!("{path}.{key}")),
                Some(now) if now != kind && now != "null" && kind != "null" => {
                    changed.push(format!("{path}.{key}: {kind} -> {now}"))
                }
                Some(_) => {}
            }
        }
    }
    for (path, keys) in current {
        for key in keys.keys() {
            if golden_shape.get(path).and_then(|k| k.get(key)).is_none() {
                added.push(format!("{path}.{key}"));
            }
        }
    }
    if !removed.is_empty() || !changed.is_empty() {
        let detail = format!("reading rules changed (removed: {removed:?}; changed: {changed:?})");
        return if manifest_version <= recorded {
            Verdict::NeedsBump(detail)
        } else {
            Verdict::Update(format!("{detail}; the manifest already moved"))
        };
    }
    if recorded != manifest_version {
        return Verdict::Update(format!(
            "golden records {version_key} {recorded}; manifest says {manifest_version}"
        ));
    }
    if !added.is_empty() {
        return Verdict::Update(format!(
            "shape gained fields {added:?}; additive, no bump needed"
        ));
    }
    Verdict::Update("nullable fields changed their recorded type; no bump needed".to_string())
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
    fn classification_separates_additive_breaking_and_unacknowledged_changes() {
        let base = shape(&[
            ("e", &[("a", "number"), ("b", "null")]),
            ("e.o", &[("k", "string")]),
        ]);
        let golden = |s: &Shape, version: u64| json!({"shape": shape_to_value(s), "v": version});
        assert_eq!(classify(None, "v", &base, 8), Verdict::MissingGolden);
        assert_eq!(
            classify(Some(&golden(&base, 8)), "v", &base, 8),
            Verdict::Ok
        );
        let mut added = base.clone();
        added
            .get_mut("e")
            .unwrap()
            .insert("c".into(), "string".into());
        assert!(
            matches!(classify(Some(&golden(&base, 8)), "v", &added, 8), Verdict::Update(d) if d.contains("no bump needed"))
        );
        let mut removed = base.clone();
        removed.get_mut("e").unwrap().remove("a");
        assert!(matches!(
            classify(Some(&golden(&base, 8)), "v", &removed, 8),
            Verdict::NeedsBump(_)
        ));
        assert!(
            matches!(classify(Some(&golden(&base, 8)), "v", &removed, 9), Verdict::Update(d) if d.contains("already moved"))
        );
        let mut retyped = base.clone();
        retyped
            .get_mut("e")
            .unwrap()
            .insert("a".into(), "string".into());
        assert!(matches!(
            classify(Some(&golden(&base, 8)), "v", &retyped, 8),
            Verdict::NeedsBump(_)
        ));
        let mut nullable = base.clone();
        nullable
            .get_mut("e")
            .unwrap()
            .insert("b".into(), "object".into());
        assert!(
            matches!(classify(Some(&golden(&base, 8)), "v", &nullable, 8), Verdict::Update(d) if d.contains("nullable"))
        );
        assert!(matches!(
            classify(Some(&golden(&base, 7)), "v", &base, 8),
            Verdict::Update(_)
        ));
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
