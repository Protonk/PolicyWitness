//! Build-owned specimens for the example command, help card and contract.

// The contract generator extracts each constant and accepts this one form: a
// single `r#"`...`"#` raw string holding a JSON object without `contract`.
pub const EXAMPLE_DOCUMENT: &str = r#"{"specimen_id":"example","policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default) (deny file-read-data (literal \"/usr/share/dict/propernames\") (with no-report))"},"phases":[{"phase_id":"initial-reads","actions":[{"step_id":"read-hosts","sandbox_check":{"operation":"file-read-data","filter":{"kind":"path","value":"/etc/hosts"}},"attempt":{"kind":"file","action":"open_read","target":"/etc/hosts"}},{"step_id":"metadata-propernames-read-connectives","sandbox_check":{"operation":"file-read-metadata","filter":{"kind":"path","value":"/usr/share/dict/propernames"}},"attempt":{"kind":"file","action":"read_fresh","target":"/usr/share/dict/connectives"}}]},{"phase_id":"restricted-read","actions":[{"step_id":"read-propernames","sandbox_check":{"operation":"file-read-data","filter":{"kind":"path","value":"/usr/share/dict/propernames"}},"attempt":{"kind":"file","action":"open_read","target":"/usr/share/dict/propernames"}}]}]}"#;

pub const EXTENSION_DOCUMENT: &str = r#"{
  "specimen_id": "extension",
  "actors": [
    {"actor_id": "issuer", "equipment": "unentitled", "sandbox": {"mode": "unapplied"}},
    {"actor_id": "Alice", "equipment": "selected", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default) (deny file-read-data) (deny file-write*) (allow file-read-data (extension \"com.apple.app-sandbox.read\"))"}}},
    {"actor_id": "Bob", "equipment": "selected", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default) (deny file-read-data) (deny file-write*) (allow file-read-data (extension \"com.apple.app-sandbox.read\"))"}}}
  ],
  "phases": [
    {"phase_id": "alice-before", "actor_id": "Alice", "actions": [
      {"step_id": "alice-baseline", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/private/etc/hosts"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "/private/etc/hosts"}}
    ]},
    {"phase_id": "bob-before", "actor_id": "Bob", "actions": [
      {"step_id": "bob-baseline", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/private/etc/hosts"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "/private/etc/hosts"}}
    ]},
    {"phase_id": "supply", "actor_id": "issuer", "actions": [
      {"step_id": "issue", "extension": {"operation": "issue", "family": "file", "authority": "read", "target": "/private/etc/hosts", "token_ref": "token"}},
      {"step_id": "deliver", "extension": {"operation": "transfer", "token_ref": "token", "recipient": "Alice", "delivery_ref": "delivery"}}
    ]},
    {"phase_id": "consume", "actor_id": "Alice", "actions": [
      {"step_id": "consume", "extension": {"operation": "consume", "delivery_ref": "delivery", "handle_ref": "handle"}}
    ]},
    {"phase_id": "alice-during", "actor_id": "Alice", "actions": [
      {"step_id": "alice-fresh", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/private/etc/hosts"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "/private/etc/hosts"}}
    ]},
    {"phase_id": "bob-during", "actor_id": "Bob", "actions": [
      {"step_id": "bob-fresh", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/private/etc/hosts"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "/private/etc/hosts"}}
    ]},
    {"phase_id": "release", "actor_id": "Alice", "actions": [
      {"step_id": "release", "extension": {"operation": "release", "handle_ref": "handle"}}
    ]}
  ]
}"#;

impl crate::interface::commands::Example {
    pub const fn document(self) -> &'static str {
        match self {
            Self::Default => EXAMPLE_DOCUMENT,
            Self::Extension => EXTENSION_DOCUMENT,
        }
    }

    /// The constant's name, which the inventory and the contract cite.
    #[allow(dead_code)]
    pub const fn symbol(self) -> &'static str {
        match self {
            Self::Default => stringify!(EXAMPLE_DOCUMENT),
            Self::Extension => stringify!(EXTENSION_DOCUMENT),
        }
    }
}
