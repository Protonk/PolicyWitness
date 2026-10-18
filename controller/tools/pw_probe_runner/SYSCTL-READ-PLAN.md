# Investigate the sysctl read contract

[Parent and handoff scope](../../../WORKER-REDESIGN-PLAN.md).
Finding: WA-11 in the [initial audit](../../../records/worker-pass6/initial-report.md).
State: investigation complete and reviewed; the user selected preserving and
disclosing the bounded read. The [implementation plan](SYSCTL-DISCLOSURE-REFACTOR-PLAN.md)
and [acceptance record](../../../records/worker-sysctl-read/implementation-acceptance.md)
retain the implemented scope and passing signed acceptance. Optional raw length
metadata remains a separate choice.

The [investigation report](../../../records/worker-sysctl-read/report.md)
records eleven native observations, three rejected interpretation controls and
two signed-app compatibility cases at `503156f`. It recommends retaining the
single bounded value read, naming and disclosing its 4096-byte capacity, and
separately choosing optional capacity/raw post-call `oldlen` evidence. Native
failure could leave `oldlen` zero despite destination writes, or unchanged from
input capacity; it cannot serve as a required-size or copied-byte count. No
raw-length field or version change was selected; the naming/disclosure refactor
is implemented.

## Starting point

`attempt_sysctl_read` in [pw_probe_runner.c](pw_probe_runner.c) passes a fixed
4096-byte stack buffer to `sysctlbyname`, publishes call status and discards the
returned value and length. Its capacity is absent from the limits inventory.
The question is which native operation this attempt should promise, rather
than simply how to make more calls succeed.

Compare an explicitly bounded read, a size-only query, and size discovery
followed by an allocated read. A named capacity in the
[limits manifest](../../../docs/limits.json) and evidence of supplied capacity
and returned length may resolve the hidden-bound issue with little behavioral
change. A request-selectable capacity is a further choice, not a prerequisite.

## Questions that distinguish the designs

- Does the experimental question require fetching a value, or only requesting
  its size? Apple's [sysctl manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/sysctlbyname.3.html)
  distinguishes these operations. Verify applicable native behavior before
  treating them as equivalent under a specimen.
- What can return status and length establish when capacity is insufficient?
  Preserve native facts; ENOMEM alone may have other causes. Include fitting
  and oversized values and a way to reject a checker that mistakes one for the
  other. The size-limit path has not been observed by this audit.
- Would adaptive allocation introduce post-apply allocation, another call,
  changing sizes or retries? State the resulting experiment and bounds. Merely
  increasing a hidden constant retains the design question.
- Which proposed facts fit existing output, and which require changes to ABI,
  transport, consumers and the [wire contract](../../../docs/CONTRACT.md)?

The [sysctl-name suite](../../../tests/suites/runner_filter_sysctl_name/README.md)
checks a specific denial-shaped result and unavailable prediction. It supplies
a useful compatibility case, not size-boundary coverage.

## Outcome to bring back

Recommend the intended operation, its explicit capacity/length semantics and
the smallest representation change. Separate a source naming/limits repair
from any change to calls made or published evidence. Give the observations and
future controls needed to support that recommendation.
