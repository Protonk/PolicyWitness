# Path-query native target

`target.c` is independent experimental equipment. It compiles/applies one SBPL
policy in a fresh process, reports readiness and accepts bounded read, create,
unlink and stat commands on an inherited pipe. It records raw syscall returns,
errno snapshots, descriptor identity, bytes and close observations. It has no
PW result classifier, phase protocol or shared worker ABI.

The owning opt-in `witness_contract/path_query_observations` case signs the
target with the configured Developer ID and empty entitlements, queries it
through the shipped validator, then releases an operation. Policies allow
default and add narrow file denials; this fixture does not support bare
deny-default coordination. Native calls are real, not substituted. The fixture
uses PW's compile/apply API signatures, but it is not the shipped worker.

The parent retains query and syscall observations separately, including host
`realpath` errors and independently observed target state. Fresh processes own
each policy; a dedicated transition case keeps one policy and PID through
unlink/recreate. Core dumps are disabled. No sandbox extensions, tokens, services
or privileged helpers are involved. Known owned children are reaped before the
temporary directory is removed; uncertain cleanup retains its ownership record.

`validator_observer.py` is a separate integration observer. It forwards each
host-requested query to an unchanged copy of the shipped validator, appends
independent extra queries, saves the full native transcript, and returns only
the originally requested records to PW. The opt-in `path_query_integrated` case
uses the normal validator-path override to observe actual PW workers while
preserving the planner's excluded-query reports. Extra queries perturb collection
duration; this is an instrumented observation, not an unchanged whole-system run.
No query answer is synthesized. Receipts live in an owned temporary directory
until confirmed worker/validator cleanup and archival.
