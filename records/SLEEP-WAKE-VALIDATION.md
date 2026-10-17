# Sleep/wake timing evidence

Recorded 2026-10-17, following the worker timing repair in commit `085e23e`.

PolicyWitness's timing protections are intended to remain meaningful across
system sleep and wake. The C worker's [release waits and exec accounting](../docs/LIMITS.md#execution-budgets)
use continuous Mach time.
Sleep counts toward those allowances. Each acknowledged phase-release wait is
excluded from the shared exec budget once, using its exact tick interval;
sleep outside that interval remains charged. Host, validator and controller
clocks remain separately owned, with no cross-clock timestamp comparison.

The intended sleep behavior has two distinct cases. A release-wait sample taken
after its allowance expires prevents acknowledgement and actions, even when
release is already visible. A valid release wait, including any sleep and
scheduling delay, fits within the existing 60-second maximum and contributes
its measured tick exclusion. The shared exec budget is 115 seconds. These are
sampled-time decisions: a pre-expiry sample followed by descheduling can still
produce a late acknowledgement. They do not establish a total runtime bound.

The accepted native arm64 candidate, worker identity `33890392…` and SHA-256
`cdfdbf9c…`, passed 81 core cases and the 190-case default battery on macOS
26.7.1 (25G241). Native controls recorded 36 million usable continuous-clock
samples at timebase 125/3. Deterministic counter advances exercise expiry and
exclusion accounting; those controls, process delays and `SIGSTOP` do not
establish behavior through actual system sleep. The platform scope is native
Apple Silicon; Intel and translated x86_64 clock behavior are outside it.

The first default run overlapped an uncontrolled 232-second idle sleep on
battery, from 08:24:09 to 08:28:01 local time. The second exec step was refused
after the shared budget was exhausted, and the host sentinel also expired.
That observation is consistent with charging sleep, but does not establish the
planned release-boundary and valid-exclusion cases. The accepted rerun used
`caffeinate -i` to inhibit idle sleep while the command ran, changed no persistent
power settings, and recorded no system sleep.

A battery spanning system sleep can exhaust worker allowances or the host
sentinel without a timing implementation defect. `pmset -g log` supplied the
sleep/wake bracket for this observation.

Controlled sleep/wake validation remains unperformed, rather than a skipped
passing check. Its absence was explicitly outside the local delivery gate.
No dedicated equipment, wake arrangement or permission to interrupt the
development session was established for that observation.

The [retention index](../tests/RETAINED.json) identifies the runs. The
[uncontrolled run](../tests/out/runs/safe-wait-repair-default-20261017/run.json)
and [accepted run and source snapshot](../tests/out/runs/safe-wait-repair-default-final-20261017/acceptance/snapshot.json)
are gitignored evidence available only in the local checkout.
