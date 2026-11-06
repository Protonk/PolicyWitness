# Extension boundary controls

`control.c` includes the production actor worker and substitutes selected native
entrypoints at compile time. Separate role overrides supply an unentitled issuer
and selected subject. Pre-call, in-call and post-return interruptions preserve
completed ordinary attempts and withhold unpublished native results. The in-call
control establishes position inside the replacement, not the kernel API.
Other modes supply issue refusal, empty/oversized/maximum tokens, missing issue,
consume or release symbols, outbound assignment/framing faults, and recipient
framing interruption. Mode 10 replaces token bytes at the published length so
framing and custody lengths remain consistent while native consume rejects the
corrupted authority. Publication and native call results remain separate.

Worker modes 107–115 substitute authority setup calls or inspectable header
fields. Required failure must terminate before policy processing; the reply
retains the primary setup cell and any independent cleanup failure. Modes
116–117 reject inbound token framing after setup. Mode 118 retains missing
consume support beside a terminal descriptor-close failure. The terminal fixture
independently counts policy read/compile/apply calls for pre-policy refusals.

Modes 18–20 observe final-phase completion and `done` immediately before a
controlled native exit. One process stays alive for a second; one remains alive
past the gate deadline; one exits abnormally. The gate must respectively await
natural owned reap, retain timeout despite later cleanup, and accept the observed
abnormal termination. Source activation, owned reap and gate capture ordinals
establish their order without treating `done` as termination.

A unique test-owned POSIX shared-memory object receives independent intervention
receipts and a copy of the real issued token. The checking process compares
captured output with those bytes in memory, then erases and unlinks the object
after child cleanup is established and the named object matches its retained
object descriptor. No raw token is printed or written to a
retained fixture. The observer channel and its pre-application mapping belong
only to these test binaries; they are not evidence of production descriptor
inheritance. Separate receipts check closure of the production channel descriptor
and disabled core dumps at the observed native boundaries.

Each channel has a case-local ownership receipt and a duplicate recovery record
in a uniquely created temporary directory, outside prunable run output. The
target is an owned regular file in that same directory. Executable fixtures also
run there, with retained copies in the artifacts, avoiding Desktop access by
the actors.
The record is retained when native child cleanup is unknown. After owner exit, the name and receipt alone cannot establish the current
object identity. Recovery stays unresolved/manual unless retained object evidence
establishes identity; no automatic unlink follows from a name or session label. Successful cleanup removes
the duplicate while preserving the case receipt.

The fixture is a clang `-O2` build with `PW_EXTENSION_OBSERVE`, outside the
inspected app; it does not establish interruption of the shipped executable
bytes. Its worker retains the current
production ABI/source identity for transport, but the executable override and
role-keyed equipment bindings and independent binary hashes identify the instrumentation.
Binding and live executable paths must identify the same filesystem object as
the requested fixture, allowing the macOS `/tmp` and `/private/tmp` aliases.
Live signature identity must match the binding, and execution/observer PIDs
must match the owning actor launch whenever the observer reached its boundary. These substitutions
establish boundary handling and publication, not policy effects of fabricated
native return values. The ordinary signed run establishes native success.


The worker erasure observer holds the mapped inbound slot independently and scans
`PW_EXTENSION_TOKEN_BYTES`, never the length passed to the erase function. It
seeds nonzero bytes after the token's valid terminating NUL through the last
buffer byte and retains only capacity/zeroization receipts. Issuer strings are
separate allocations with their own bounded erasure observation.

`terminal_control.c` uses synthetic token bytes and a parent-owned authority region to
exercise ordinary departures in the production C source. Its test-only gate
holds the worker immediately after the actual `done` store, allowing the parent
to acquire that publication and inspect the full settled inbound buffer before subsequent
cleanup can run. The parent also scans after independent reap and erases only
then. Anonymous mappings and immediately unlinked temporary files have no
persistent token contents. Sandbox/extension calls are controlled; these tests
establish cleanup and publication order, not native authority. The registered
`runner_c_worker_harness/terminal_erasure` case retains original and mutated
source/build logs and byte-free observations, and rejects shortened erasure and
erasure moved after the publication boundary, and removal of the required-setup
terminal branch. Outbound and unsettled inbound bytes must remain unchanged
until their owners can erase them.

`write_control.c` includes the production fresh-write actions with independent
native substitutes. It checks call order and arguments, each failure boundary,
short writes without an invented errno, combined failures and diagnostic
pre-open metadata. These controls do not issue or consume extensions and make
no kernel policy claim. The `runner_c_worker_harness/fresh_write` case owns
compilation and execution; public directory witnesses own real file effects.

`authority_binding.c` exercises production recipient preparation and service
with synthetic token bytes and a counted consume replacement. The host view
changes one assigned source/action/delivery field after preparation. Rejected
frames must never reach the consume boundary; the matched control must reach it.

The authority binding control also maps a maximum-inbound POSIX shared-memory
object with its actual page-rounded length and verifies recipient preparation.

`operation_control.c` retains direct production issue, consume, release and
fresh-read body controls, then submits distinct slots through `run_attempt` for
actual issue/consume/release dispatch coverage. Independent callback counts,
nonzero resource indices and different native handle values establish each
route and association. The `runner_c_worker_harness/actor_operations` case
requires successfully compiled omitted/misrouted dispatcher mutations and
crossed-handle mutations to fail their named independent observations, alongside
the retained omitted-body-call, crossed-delivery and descriptor-reuse controls.
Synthetic tokens and handles do not establish native sandbox authority.
