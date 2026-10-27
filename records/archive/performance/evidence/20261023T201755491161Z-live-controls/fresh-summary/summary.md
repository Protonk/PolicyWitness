# Runtime summary: 20261023T201755491161Z-pilot

Execution context: `interactive`. Raw evidence is gitignored and local-only.

Cleanup: `complete`. Counts: `{"completed": 70}`.
Unattested files: 0. Excluded observations: 0.

Durations below are milliseconds. Each row has one outcome stratum; warm-ups remain separate.

| Cell | Warm-up | Outcome / capture / stops / exit | n | W median | W p90 | C median | L median |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| file_read_deny/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 682.814 | 905.923 | 41.000 | 638.000 |
| mach_deny/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 680.662 | 691.816 | 40.000 | 638.000 |
| sysctl_read/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 679.609 | 684.512 | 39.000 | 637.000 |
| exec_spawn/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 685.917 | 687.981 | 42.000 | 641.000 |
| path_diagnostics_strict/capture | True | ok / captured / received / done / reaped_during_grace / 0 | 3 | 681.733 | 683.564 | 41.000 | 637.000 |
| file_read_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 679.604 | 684.873 | 40.000 | 636.000 |
| mach_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 684.644 | 685.664 | 41.000 | 640.000 |
| sysctl_read/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 685.567 | 689.704 | 40.000 | 642.000 |
| exec_spawn/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 684.238 | 685.458 | 41.000 | 639.000 |
| path_diagnostics_strict/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 5 | 681.794 | 686.099 | 41.000 | 637.000 |
| file_read_deny/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 43.965 | 44.284 | 41.000 | — |
| mach_deny/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 41.171 | 41.320 | 39.000 | — |
| sysctl_read/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 39.847 | 39.923 | 38.000 | — |
| exec_spawn/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 41.942 | 41.997 | 39.000 | — |
| path_diagnostics_strict/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 5 | 41.765 | 41.986 | 39.000 | — |
| version | False | None / None / None / None / None / 0 | 5 | 2.017 | 2.084 | — | — |

All per-measure spreads, absent/invalid/inapplicable counts, exclusions, sequence numbers,
and cleanup steps are retained in summary.json. Negative residuals remain observations.
