# Sequential BYOXPC requests: retirement, waiting and deadlines

Investigation, 2026-10-06. No product changes.

Status: the wait observed here was bounded on 2026-10-06; the generated plist sets `ThrottleInterval` to one second (limit `byoxpc_throttle_interval`), and the guide describes what follows `runner verify`.

## Observations

Sequential requests to one installed runner did not all behave like requests
to an immediately available fresh host. With a fixed allow-all specimen and
an empty probe plan, the observations were:

| Sequence | Result | CLI wall time |
| --- | --- | --- |
| First run, then immediately another | `already_ran` on the second | 0.051 s |
| A run after an 11-second pause | `ok` | 0.329 s |
| First run, then 0.4-second pause and a 30-second client budget | `ok` on the second | 10.277 s |
| Fresh installation, first run, then 0.4-second pause and a 2-second client budget | `xpc_timeout` on the second | 2.072 s |

The generated plist contained no `ThrottleInterval`. The live job listing
reported `minimum runtime = 10`. Before the short-budget second request,
launchd reported `state = not running`, `runs = 1`, and `last exit code = 0`.
That receipt distinguishes a retired host from the still-admitted host in
the immediate-refusal case. All received envelopes validated.

The observed branches include admission refusal during retirement, a delayed
successful launch, and expiration of the caller's budget. The experiment did
not produce the plan's suggested `xpc_error`, and no such outcome is asserted
as necessary. A timeout supplies no completed operation evidence and does not
prove cancellation of work. The short-budget specimen had no probe steps;
the owned service was subsequently removed through the normal cleanup path.

The guide already mentions the respawn throttle in its copied Questions
section. The documentation question is therefore how much timing and
retirement context consumers need, rather than whether the throttle is
mentioned anywhere.

## Reproduction and receipts

Use an owned Developer ID user-scope installation and the shipped CLI. Avoid
an implicit `runner verify` immediately before the experiment, since that
command itself consumes a host. Run the same specimen with
`--no-log-capture` and explicit `--timeout-ms` values. Measure elapsed time
around the CLI with a monotonic clock. Preserve both its envelope and the
launchd listing for the exact owned service.

The [timing series](../tests/out/runs/byoxpc-investigation-20261006/timing/)
contains first/immediate/spaced and long-budget pairs. The
[short-budget series](../tests/out/runs/byoxpc-investigation-20261006/timing-short/)
contains `before-second/stdout`, the exact retired-job observation, and
`short-second/stdout`, its timeout envelope. Each command's `command.json`
records argv, elapsed time, return code and whether an outer harness timeout
occurred. No outer harness timeout occurred. The retained
[driver](../tests/out/runs/byoxpc-investigation-20261006/investigate.py)
records the intentional pauses and verifies removal after each installation.

## Scope

These are individual timing observations, not a latency distribution, an
exact ten-second service guarantee, or a promise about every immediate run.
macOS 14.8.9 (23J631), arm64, user scope, Team `42D369QV8E`; checkout
`e2115cf`, selected app build `435`, `33ad847-dirty`, identified by the
[retained inventory](../tests/out/runs/byoxpc-investigation-20261006/baseline/source-inventory.json).
The app remained unchanged and both installations were removed with absence
verified. Linked receipts are gitignored local evidence, pinned in
`tests/RETAINED.json`.
