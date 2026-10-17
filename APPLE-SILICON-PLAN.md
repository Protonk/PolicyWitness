# Investigate native arm64 build enforcement

We intend to document and enforce native arm64 builds and execution on Apple
Silicon. Investigate the enforcement design; build changes are outside this task.

Follow [CONTRIBUTING.md](CONTRIBUTING.md#planning-a-change) and read
[BUILD.md](docs/BUILD.md). Trace [build.sh](build.sh), [meson.build](meson.build),
Cargo target selection, reused caches and artifact inspection. Meson currently
derives its target from the host CPU. Determine whether Rosetta or explicit
target overrides can produce signed x86_64 outputs; retain observations using
isolated output directories.

Recommend the earliest reliable refusal and artifact verification, with native
success and translated/forced-x86_64 rejection controls. Identify documentation,
[build.json](docs/build.json), generator, worker-identity and test updates needed.
Deliver an executable enforcement plan with evidence and explicit equipment
gaps. Keep this investigation independent of the
[worker timing repair](runner/SAFE-WAIT-TIME-PLAN.md).
