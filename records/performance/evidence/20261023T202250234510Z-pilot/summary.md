# Runtime summary: 20261023T202250234510Z-pilot

Execution context: `interactive`. Raw evidence is gitignored and local-only.

Cleanup: `complete`. Counts: `{"completed": 70}`.
Unattested files: 0. Excluded observations: 0.

Durations below are milliseconds. Each row has one outcome stratum; warm-ups remain separate.

| Cell | Warm-up | Outcome / capture / stops / exit | n | W median | W p90 | C median | L median |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| file_read_deny/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 682.507 | 684.297 | 41.000 | 638.000 |
| mach_deny/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 683.291 | 684.116 | 41.000 | 638.000 |
| sysctl_read/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 676.147 | 682.532 | 39.000 | 633.000 |
| exec_spawn/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 678.311 | 685.991 | 41.000 | 634.000 |
| path_diagnostics_strict/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 680.650 | 681.583 | 41.000 | 636.000 |
| file_read_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 675.582 | 682.383 | 40.000 | 633.000 |
| mach_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 677.914 | 682.455 | 41.000 | 633.000 |
| sysctl_read/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 677.255 | 680.336 | 40.000 | 634.000 |
| exec_spawn/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 680.394 | 686.555 | 41.000 | 636.000 |
| path_diagnostics_strict/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 679.983 | 691.118 | 41.000 | 635.000 |
| file_read_deny/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 43.905 | 44.020 | 41.000 | — |
| mach_deny/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 41.386 | 41.427 | 39.000 | — |
| sysctl_read/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 39.790 | 39.926 | 38.000 | — |
| exec_spawn/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 41.794 | 41.876 | 39.000 | — |
| path_diagnostics_strict/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 41.589 | 41.840 | 39.000 | — |
| version | False | None / None / None / None / None / 0 | 5 | 2.061 | 2.085 | — | — |

All per-measure spreads, absent/invalid/inapplicable counts, exclusions, sequence numbers,
and cleanup steps are retained in summary.json. Negative residuals remain observations.
