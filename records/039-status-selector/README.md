# Can one positional key replace the two selectors for runner status?

Keep the explicit ID and service-name selectors. A reader holding an installation ID and a reader holding a service name can have exactly the same text and mean different records. The released CLI answered both questions. The positional trial could identify the ambiguity but could answer neither question from that text alone.

## Trial

The released guide asks callers to retain the installed ID, service name, scope and bundle path. The trial removes one choice from a read-only operation. A caller gives `runner status` one positional string. The controller searches both columns, returns the record for a unique match, and refuses a match across two records. Each record counts once even if both its fields match. Other commands keep their existing selectors. [External-runner workflow](../../docs/PolicyWitness.md#use-an-external-runner) · [Trial patch against v0.3.8](positional-status.patch)

The same private, constructed schema-1 registry supplied both binaries. One record's ID equals another's service name. Both IDs have the installer's generated form. The outside observation is the pair of named columns and bundle paths read directly from the fixture before either binary runs. The driver checks each returned identity against those values and checks the registry bytes after each lookup. This exercises registry selection. The two bundle paths are fixture data and no service was installed. [Registry](registry.json) · [Driver and assertions](observe.py)

| Text given to status | Caller's intended column | Released result | Positional result |
| --- | --- | --- | --- |
| First record's unique service name | service name | first bundle, exit 0 | first bundle, exit 0 |
| Second record's unique ID | ID | second bundle, exit 0 | second bundle, exit 0 |
| Shared text | ID | first bundle, exit 0 | ambiguous, exit 2 |
| Shared text | service name | second bundle, exit 0 | ambiguous, exit 2 |

The released executable came from the archived v0.3.8 ZIP, build 1676 at `1b6e82e7`. The signed positional build was 1677 at `2ce80b7a`, a single trial commit on that tag. Each capture contains its version envelope, binary and registry hashes, arguments, process status, stdout and stderr. The released guide is also available from the tag as `v0.3.8:docs/PolicyWitness.md`. [Released observations](released.json) · [Positional observations](positional.json)

## Work transferred to the caller

For a unique key the trial saves one option and PW supplies the column search. For the shared key, both intended lookups become the same invocation and the same refusal. The reader can still list the registry and filter the correct column, or find another unique key for that record. The driver performed the list and column filtering on both versions. An ID-first default would silently return the first bundle to the service-name caller. Filtering requires the caller to retain the distinction the option used to express. On a miss, the released envelope identifies the requested ID. The positional trial's miss omits the operand, so a reader needs the saved invocation to recover it.

## Existing assertions

The v0.3.8 acceptance battery `20261124T061817Z_9852c335` passed the integration case. The trial ran the same integration family as `20261126T000654Z_83af12d1` with 28 passing tests and these four failures. The trial run directory is disposable development output.

| Failing test | What rejected the trial |
| --- | --- |
| `runner_commands_report_ok_or_refuse_on_stderr_without_an_envelope` | The missing-operand diagnostic no longer names the two required flags. This pins the released syntax. |
| `interface_cases_hold_on_the_signed_controller` | The two `runner.status` help-flag cases changed from usage errors on stderr to well-formed lookup misses. A flag-shaped word became a positional key. |
| `registry_that_cannot_be_read_refuses_and_only_an_absent_path_is_empty` | Invocations using the released two-argument form stopped at parsing. Their assertions about missing and unreadable registry files no longer reached the reader. |
| `envelope_write_failures_exit_2_with_one_line_and_never_a_panic` | The old invocation stopped before writing an envelope. Its two closed-stdout controls no longer exercised the write. |

None of those diagnostics identified the loss of direct selection between the two bundle paths. The shared-key pair did. A single-key shorthand could only be an additional interface if both original intentions must remain expressible through status. This experiment adopts no shorthand.
