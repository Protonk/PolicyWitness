# Runtime summary: 20261023T202250234510Z-short-rehearsal

Execution context: `interactive`. Raw evidence is gitignored and local-only.

Cleanup: `complete`. Counts: `{"completed": 11}`.
Unattested files: 0. Excluded observations: 0.

Durations below are milliseconds. Each row has one outcome stratum; warm-ups remain separate.

| Cell | Warm-up | Outcome / capture / stops / exit | n | W median | W p90 | C median | L median |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| file_read_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 1 | 678.719 | 678.719 | 40.000 | 636.000 |
| mach_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 1 | 679.147 | 679.147 | 41.000 | 635.000 |
| sysctl_read/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 1 | 650.826 | 650.826 | 37.000 | 610.000 |
| exec_spawn/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 1 | 687.202 | 687.202 | 41.000 | 643.000 |
| path_diagnostics_strict/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 1 | 675.176 | 675.176 | 41.000 | 631.000 |
| file_read_deny/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 1 | 44.292 | 44.292 | 41.000 | — |
| mach_deny/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 1 | 37.864 | 37.864 | 36.000 | — |
| sysctl_read/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 1 | 39.942 | 39.942 | 37.000 | — |
| exec_spawn/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 1 | 42.003 | 42.003 | 40.000 | — |
| path_diagnostics_strict/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 1 | 41.646 | 41.646 | 39.000 | — |
| version | False | None / None / None / None / None / 0 | 1 | 2.249 | 2.249 | — | — |

All per-measure spreads, absent/invalid/inapplicable counts, exclusions, sequence numbers,
and cleanup steps are retained in summary.json. Negative residuals remain observations.
