# Runtime summary: 20261023T202250234510Z-missing-request

Execution context: `interactive`. Raw evidence is gitignored and local-only.

Cleanup: `complete`. Counts: `{"completed": 3}`.
Unattested files: 0. Excluded observations: 0.

Durations below are milliseconds. Each row has one outcome stratum; warm-ups remain separate.

| Cell | Warm-up | Outcome / capture / stops / exit | n | W median | W p90 | C median | L median |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| file_read_deny/capture | False | tool_error / None / None / None / None / 2 | 1 | 2.344 | 2.344 | — | — |
| mach_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 1 | 675.916 | 675.916 | 39.000 | 634.000 |
| sysctl_read/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 1 | 678.146 | 678.146 | 39.000 | 635.000 |

All per-measure spreads, absent/invalid/inapplicable counts, exclusions, sequence numbers,
and cleanup steps are retained in summary.json. Negative residuals remain observations.
