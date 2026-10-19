# Documentation revision and branch-build verification

This record accompanies [the Markdown guidance plan](../MARKDOWN-GUIDANCE-PLAN.md).
The review base is `a7cf758` on `main`; implementation and verification take place
on `doc-rework`. Build and test evidence linked below is gitignored and available
only in this local checkout.

## Baseline

The clean baseline was `df7365ccf334bbc05bdbe9b1a1e5c5ed17500adc`,
`v0.3.1-67-gdf7365c`, build number `751`. The signed build completed on the new
branch and embedded that commit, describe string and build number with
`dirty: false`. The build used Developer ID Application: Adam Hyland
(42D369QV8E), the Xcode macOS 27.0 SDK, Apple clang 21.0.0, Swift 6.4,
Cargo 1.99.0, Meson 1.12.1 and Ninja 1.13.2.

The baseline [test run](../tests/out/runs/doc-rework-baseline-20261019/run.json)
passed `preflight/build_provenance_controls` and
`preflight/signed_artifact_controls`, including 29 real signature controls.
Its run ID is `20261019T201847Z_cbd7e783`. The inspected app remained unchanged.

## Build issues and resolutions

| Observation | Cause and resolution | Validation |
| --- | --- | --- |
| Signing identity discovery reported zero valid identities in the automation sandbox. | Repeating the same `security find-identity -v -p codesigning` command outside that sandbox found the configured Developer ID. Run signing and compiler discovery through the documented unsandboxed entry point. No signing or verification rule was relaxed. | The baseline signed build and real signature controls passed outside the sandbox. |
| The baseline Rust build warned that `capture_reserving` was unused in the production controller. | `log_capture.rs` is shared by the controller and observer binaries. The observer calls this helper in production; controller receiver tests also call it, while the production controller does not. Add a local `allow(dead_code)` annotation explaining those consumers, matching the existing treatment of `CollectionBudget::from_argument`. Preserve the helper and its behavior. | Candidate build and Rust batch verification are pending below. |

## Editorial verification

The initial 112 canonical source documents were inventoried independently of
retained output. This record is the additional source target. The original
prompt was retired after its requirements became self-contained in the plan.
Symlink aliases continue to resolve to their owning `AGENTS.md` files.

The initial whole-inventory link check reported 78 findings, including absent
historical evidence and stale references in earlier plans. These are the
comparison baseline, not evidence of regressions from this change. The revised
documents' links and generator checks passed during editing. Final comparison,
mutation controls and source search are pending.

## Candidate and branch-name controls

Candidate build receipts, source identities, integrated test results and the
controlled branch-name comparison will be recorded here before merge review.
