# Common retained-evidence applicability assessment

Coordinator read the original run/review metadata and reconstructed three retained dirty snapshots from base `a54da01263472b38036ed9e524a1a9d143c1cc34` plus their exact patches in an isolated temporary directory. `snapshot-comparison.json` records patch hashes, paths and all differences; `artifact-comparison.json` records app hash comparison. Reconstruction did not alter the checkout, retained evidence or app. It is not a new test execution.

The source.patch hashes for default and final-control runs match their identities in retained verification.json. All patch-touched paths and all base-to-current changed paths were compared bytewise (91 paths per snapshot); all other tracked paths are unchanged between base and current. No compared existing file mode differs. This is file identity, not proof of complete dependency reachability or compiler correctness.

## Run and artifact identity

- Default: `20261104T180136Z_5ef8b568`, `tests/out/runs/actor-passes-default-02`. Case outcomes are 215 pass / 1 fail out of 216; the run's legacy-report counts 214/1 have a different stated scope. The failure remains recorded, not rewritten.
- Final controls: `20261104T201833Z_59c91237`, `tests/out/runs/actor-passes-final-controls-02`, 10 passing cases.
- Both retained before/after app inventories are identical. Every one of 21 file hashes in each retained inventory matches the current `dist/PolicyWitness.app`, including native binaries and evidence/provenance resources. No current codesign verification was run; this is byte identity to the app recorded valid/unchanged by those executions, not a new signature or execution claim.

All these runs and their review/snapshot data are gitignored, checkout-local materials.

## Differences and allowed applicability judgments

The final-control source snapshot differs from current only in the documentation lookback plan, retained-resource records and test-retention index. Runtime/test source, case inputs and shared helpers in the repository are identical. Where an investigator identifies a case's actual dependency closure within those files and checks its original configuration/assertions/raw observations, current-source reuse is supported. Do not credit a case merely because it is listed as pass.

The default source snapshot additionally differs in:

- `controller/src/runner_client.rs`: only the capacity-owner assertion in `#[cfg(test)] mod tests` (starts 950–951); a direct equality assertion was replaced by exact owner enumeration. Production code is unchanged. Use the final-control Rust unit rerun for the changed assertion, or explicitly restrict any default-run reuse to unaffected paths.
- `tests/suites/source_drift/limits.py`: adds runner_client.rs to the independent value-owner list. The default limits-documentation failure is replaced by the final-control passing case; do not reuse its failed outcome as pass.
- `tests/suites/runner_byoxpc/opt_in/registry_recovery.py`: protocol fixture markers corrected from current 2 / old 1 / future 3 to current 3 / old 2 / future 4. Use final-control registry recovery for this behavior.
- Working guidance and retention/document records; these are not runtime inputs for the native/public cases under consideration.

Thus the named default public admission, actor composition/redelegation/timing, native worker controls, Swift core/client tests and ABI checks have unchanged runtime, test, helper and fixture bytes, subject to each investigator's stated dependency/configuration review. A broad assertion about all tests is not made. Default Rust tests needing the changed capacity assertion use the final rerun.

The app-build 1116 snapshot differs from current runtime source only by that cfg(test) assertion. Other differences are subsequent live-fixture refreshes, coverage/limits metadata, registry fixture correction and documentation/retention. Source/build provenance records its dirty base and worker identity; neither the later repair commit nor current HEAD is relabeled as its build source. Current tests can be read against the unchanged product implementation with these distinctions preserved.

## Limits of credit

A unit/native seam control establishes its injected or constructed conditions, not kernel policy behavior. A public native case establishes the recorded policies, operations, environment and observations. A clock-control test can establish expiry logic without exercising production duration. Source paths and matching hashes do not establish that a cited assertion covers a prose claim; investigators must read the assertion and observation. The finite actor qualification cannot be promoted to all admitted compositions. Report any untracked/external dependency or apparatus uncertainty that this comparison does not settle.
