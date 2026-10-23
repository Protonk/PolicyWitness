# Runtime summary: 20261023T212050Z-short-b841

Execution context: `operator`. Raw evidence is gitignored and local-only.

Cleanup: `complete`. Counts: `{"completed": 1452}`.
Unattested files: 0. Excluded observations: 0.

Durations below are milliseconds. Each row has one outcome stratum; warm-ups remain separate.

| Cell | Warm-up | Outcome / capture / stops / exit | n | W median | W p90 | C median | L median |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| file_read_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 132 | 671.707 | 682.212 | 37.000 | 632.000 |
| mach_deny/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 132 | 673.896 | 684.287 | 38.000 | 632.000 |
| sysctl_read/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 132 | 671.980 | 681.301 | 37.000 | 632.000 |
| exec_spawn/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 132 | 673.346 | 683.006 | 38.000 | 632.000 |
| path_diagnostics_strict/capture | False | ok / captured / received / done / reaped_during_grace / 0 | 132 | 671.993 | 682.098 | 38.000 | 630.000 |
| file_read_deny/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 132 | 41.024 | 44.074 | 38.000 | — |
| mach_deny/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 132 | 38.401 | 41.473 | 36.000 | — |
| sysctl_read/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 132 | 37.269 | 40.356 | 35.000 | — |
| exec_spawn/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 132 | 39.244 | 42.231 | 37.000 | — |
| path_diagnostics_strict/no-capture | False | ok / None / received / done / reaped_during_grace / 0 | 132 | 38.753 | 41.884 | 37.000 | — |
| version | False | None / None / None / None / None / 0 | 132 | 2.098 | 2.169 | — | — |

All per-measure spreads, absent/invalid/inapplicable counts, exclusions, sequence numbers,
and cleanup steps are retained in summary.json. Negative residuals remain observations.
