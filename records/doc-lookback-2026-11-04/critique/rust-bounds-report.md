# Rust diagnostic path coverage

Source patch is confined to the existing `#[cfg(test)]` module in
`controller/src/request_patch.rs`. `RequestError::new` and its production
literal limits are unchanged. No test, build, generator, formatting command or
probe was executed by this agent; the coordinator owns serialized execution.

New test symbols:

- `documented_request_failure_path_limits_match_retained_paths` observes the
  production constructor over independently bounded candidate depths and ASCII
  component byte lengths, then compares observed maxima and units with every
  limits row declaring this Rust file as a value owner. It requires exactly the
  two intended row IDs and refuses reaching either search ceiling.
- `request_failure_path_depth_retains_eight_and_withholds_nine` uses literal
  eight/nine-component mixed key/index paths and checks both the retained Rust
  field and exact serialized failure object. Nine components must produce
  explicit JSON null, never a shortened path.
- `request_failure_path_components_use_utf8_bytes_and_withhold_the_whole_path`
  checks literal ASCII and multibyte 63/64-byte cases, with the tested component
  between valid mixed key/index components. It compares complete retained paths
  and exact serialized objects; oversize withholds the whole location. The
  multibyte controls use 31 two-byte characters plus ASCII (63 bytes) and 32
  two-byte characters (64 bytes), distinguishing UTF-8 bytes from character
  counts. Diagnostic codes and messages survive withheld locations.

Both boundary tests are independent of `docs/limits.json` and production limit
constants; changing inventory values cannot change their expected decisions.

Coordinator manifest integration:

1. Add `controller/src/request_patch.rs` to `docs/generate_limits.py`'s
   `VALUE_OWNERS` using the established Rust owner convention.
2. For both `request_failure_path_components` and
   `request_failure_path_component`, append this value check:

   ```json
   {
     "path": "controller/src/request_patch.rs",
     "symbol": "documented_request_failure_path_limits_match_retained_paths",
     "kind": "value",
     "form": "test"
   }
   ```

3. Append a boundary check to each corresponding row, using the same `path`,
   `kind: "boundary"`, `form: "test"`, and the depth or component test symbol
   above. Replace the source-inspected Rust parity coverage note with the
   constructed Rust constructor observations and independent serialized
   all-or-null controls; preserve the distinction from live runner evidence.

Required validation: run the repository `unit` suite (including `rust.unit`
and `rust.fmt`) after manifest integration; run limits generation and the
applicable `source_drift` checks under coordinator ownership. Review the
generated coverage citations. These tests observe constructor behavior and
serialization only, not live XPC delivery or Swift execution.
