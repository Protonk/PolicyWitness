# Diagnostic transport inputs

`cases.json` is independent expected input for direct Swift decoding, Rust JSON
receivers and the CLI checker. `worker.h` holds separately maintained C literals
for the lifecycle fixture; the CLI compares the received fields to the JSON
oracle, not to a reconstructed production classification.

| Worker input | Operation / code | Other supplied fields |
| --- | --- | --- |
| alpha | unfamiliar operation 239 / code 4000000001 | unfamiliar native kind 77, signed result -123, errno 0 marked present, index 17, detail 7654321, UTF-8 snowman text |
| beta | known operation 8 / unfamiliar code 4000000179 | native kind 1, result -37, errno 13, absent index, detail 1234567890, UTF-8 café text |

These inputs report controlled payloads. They do not establish that native
operations ran. Worker producer identity and code domain are the containing
`runner_subprocess.pid` and ABI-6 `worker_evidence` channel; there is no invented
worker `producer` or `domain` field. The JSON diagnostic inputs have explicit
producer/domain/operation/code/detail fields and different payloads. Their values
are test data, never production registrations or outcome mappings.

The worker fixture uses the production release/acquire publication helpers.
`transport_alpha` and `transport_beta` publish complete records, then done, wait
for exit_requested and exit 23. It never claims policy application or completed
attempts. `close_transport_beta` publishes beta then closes its policy input,
producing independently observed host EPIPE for an admitted-size request.
The test owns a separate ten-second watchdog for normal fixture modes.

Controls:

- `transport_absent` and `transport_unpublished` leave poison fields behind
  state 0/2; they never publish a committed failure.
- `transport_malformed` publishes an invalid errno-presence flag.
- `transport_incompatible` changes the version word to 7 in the current layout;
  this establishes record rejection, not support for a hypothetical new layout.
- `transport_bad_text` retains the numeric failure while the text extent is invalid.
- `transport_beta_truncated` uses the real publisher to mark 4095 retained bytes
  from oversized text. Code preservation is checked independently of text loss.

The validator route uses the existing transcript producer, renders both JSON
diagnostics into separate valid records, and retains the emitted bytes and
received probes. Clean EOF is a positive control for existing per-step diagnostic
semantics. An invalid UTF-8 tail independently fails the run while both unfamiliar
records, a fixture-supplied allow record and an independently checked real-worker
file change remain available. The transcript producer never calls `sandbox_check`:
the allow record tests forwarding of supplied native-result fields. Receiver
faults, child disposition and the file change have their own observations; their
coexistence with the transcript records establishes no causal relationship.

Rust receiver controls use real subprocess bytes at the production parsing
functions for runner-client, sbpl-check and log-observer output. They preserve
both JSON diagnostics alongside a fixture-supplied failed report and contrast that
with locally truncated valid JSON. They do not force a real XPC loss or modify
shipped helpers to manufacture failures.
