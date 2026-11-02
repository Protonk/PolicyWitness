# Migration record

The archival move preserves the accepted conclusions. All original evidence,
source snapshots, apparatus/reader/control sources, and the entire browser source
packet remain byte-for-byte unchanged. The acceptance decision was committed
separately before relocation. No original narrative wording was revised. Changes
to existing narrative bytes are the Markdown destinations below and removal of
one pre-existing trailing space at the end of `PLAN.md` line 10. That whitespace
cleanup makes the relocated link line pass Git's whitespace check.

The plan is now `PLAN.md`; the investigation and its source packet have the
original-to-archive mappings recorded in `ARCHIVE.json`. Tracked material was
relocated with Git moves. The obsolete local-product ignore rule was replaced
by `/reports/sandboxed-extension-issuance/local/`, and optional local products
were carried to that ignored directory. Old command strings and paths in frozen
sources/evidence were intentionally retained as provenance.

The archive README, context account, preservation verifier/manifests and
preservation record are new archival material. They do not change the experiment.

## Link destination repairs

| Document | Original destination | Archived destination |
| --- | --- | --- |
| `PLAN.md` | `records/browser-sandbox-sources/README.md` | `browser-sandbox-sources/README.md` |
| `PLAN.md` | `docs/WORKER.md#supplied-extension-authority` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/WORKER.md#supplied-extension-authority` |
| `PLAN.md` | `docs/PolicyWitness.md#sandbox-extensions` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/PolicyWitness.md#sandbox-extensions` |
| `PLAN.md` | `docs/PolicyWitness.md#extension-and-fresh-read-output` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/PolicyWitness.md#extension-and-fresh-read-output` |
| `PLAN.md` | `docs/QUESTIONS.md#can-policywitness-test-sandbox-extension-behavior` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/QUESTIONS.md#can-policywitness-test-sandbox-extension-behavior` |
| `PLAN.md` | `docs/WORKER.md#supplied-extension-authority` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/WORKER.md#supplied-extension-authority` |
| `PLAN.md` | `docs/WORKER.md#known-gaps` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/WORKER.md#known-gaps` |
| `PLAN.md` | `docs/LIMITS.md#specimen-admission` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/LIMITS.md#specimen-admission` |
| `PLAN.md` | `docs/LIMITS.md#interactions-that-matter` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/LIMITS.md#interactions-that-matter` |
| `PLAN.md` | `controller/tools/pw_probe_runner/pw_extension_issuer.c` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/controller/tools/pw_probe_runner/pw_extension_issuer.c` |
| `PLAN.md` | `controller/tools/pw_probe_runner/pw_extension_channel.h` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/controller/tools/pw_probe_runner/pw_extension_channel.h` |
| `PLAN.md` | `controller/tools/pw_probe_runner/pw_probe_runner.c` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/controller/tools/pw_probe_runner/pw_probe_runner.c` |
| `PLAN.md` | `controller/tools/pw_probe_runner/pw_probe_runner.c` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/controller/tools/pw_probe_runner/pw_probe_runner.c` |
| `PLAN.md` | `runner/Sources/PWRunnerCore/ExtensionIssuer.swift` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/runner/Sources/PWRunnerCore/ExtensionIssuer.swift` |
| `PLAN.md` | `controller/tools/sb_api_validator/sb_api_validator.c` | `pw-context/controller/tools/sb_api_validator/sb_api_validator.c` |
| `PLAN.md` | `tests/suites/sandbox_extensions_native/README.md` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/suites/sandbox_extensions_native/README.md` |
| `PLAN.md` | `tests/fixtures/sandbox_extensions/README.md` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/fixtures/sandbox_extensions/README.md` |
| `PLAN.md` | `tests/suites/witness_contract/README.md#native-extension-boundaries` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/suites/witness_contract/README.md#native-extension-boundaries` |
| `PLAN.md` | `tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence` |
| `PLAN.md` | `tests/CHANGE-VERIFICATION.md#native-sandbox-extensions` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/CHANGE-VERIFICATION.md#native-sandbox-extensions` |
| `PLAN.md` | `docs/ARCHITECTURE.md#process-topology` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/ARCHITECTURE.md#process-topology` |
| `PLAN.md` | `docs/architecture.json` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/architecture.json` |
| `PLAN.md` | `docs/REQUEST-GRAMMAR.md` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/REQUEST-GRAMMAR.md` |
| `PLAN.md` | `records/browser-trace-investigations/TRACES.md` | `TRACES.md` |
| `PLAN.md` | `records/browser-sandbox-sources/README.md` | `browser-sandbox-sources/README.md` |
| `PLAN.md` | `records/browser-trace-investigations/TRACES.md#questions` | `TRACES.md#questions` |
| `PLAN.md` | `tests/fixtures/sandbox_extensions/native.c` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/fixtures/sandbox_extensions/native.c` |
| `PLAN.md` | `records/AGENTS.md` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/records/AGENTS.md` |
| `PLAN.md` | `tests/README.md#retention-ownership-and-execution-locking` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/README.md#retention-ownership-and-execution-locking` |
| `PLAN.md` | `tests/fixtures/sandbox_extensions/build.sh` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/fixtures/sandbox_extensions/build.sh` |
| `PLAN.md` | `records/browser-trace-investigations/TRACES.md#t7-context-only-traces` | `TRACES.md#t7-context-only-traces` |
| `PLAN.md` | `controller/tools/sb_api_validator/sb_api_validator.c` | `pw-context/controller/tools/sb_api_validator/sb_api_validator.c` |
| `PLAN.md` | `docs/WORKER.md#known-gaps` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/WORKER.md#known-gaps` |
| `PLAN.md` | `docs/QUESTIONS.md` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/QUESTIONS.md` |
| `PLAN.md` | `docs/LIMITS.md#premises-behind-the-interactions` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/LIMITS.md#premises-behind-the-interactions` |
| `PLAN.md` | `tests/AGENTS.md#add-or-change-tests` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/AGENTS.md#add-or-change-tests` |
| `PLAN.md` | `docs/CONTRACT.md` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/CONTRACT.md` |
| `PLAN.md` | `docs/REQUEST-GRAMMAR.md` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/REQUEST-GRAMMAR.md` |
| `PLAN.md` | `docs/architecture.json` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/docs/architecture.json` |
| `PLAN.md` | `tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls` | `https://github.com/Protonk/PolicyWitness/blob/6ea196363dd5007f3d98d72424e0ffd044524ddb/tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls` |
| `PLAN.md` | `records/browser-trace-investigations/TRACES.md#t6-non-file-extension-classes-boundary-not-a-starting-point` | `TRACES.md#t6-non-file-extension-classes-boundary-not-a-starting-point` |
| `REPORT.md` | `../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md` | `PLAN.md` |
| `REPORT.md` | `../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md#fixed-contrasts-and-positive-controls` | `PLAN.md#fixed-contrasts-and-positive-controls` |
| `REPORT.md` | `../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md#ordering-and-query-protocol` | `PLAN.md#ordering-and-query-protocol` |
| `REPORT.md` | `../../controller/tools/sb_api_validator/sb_api_validator.c` | `pw-context/controller/tools/sb_api_validator/sb_api_validator.c` |
| `REPORT.md` | `../../tests/out/release-acceptance/run-3ab7e31af74345dfa87d1948c56ecb27/` | `../../tests/out/release-acceptance/run-3ab7e31af74345dfa87d1948c56ecb27` |
| `REPORT.md` | `../../tests/out/runs/workset-native-crossed-01/suites/sandbox_extensions_native/feasibility/artifacts/` | `../../tests/out/runs/workset-native-crossed-01/suites/sandbox_extensions_native/feasibility/artifacts` |
| `TRACES.md` | `../browser-sandbox-sources/sources/chromium/sandbox/policy/mac/gpu.sb` | `browser-sandbox-sources/sources/chromium/sandbox/policy/mac/gpu.sb` |
| `TRACES.md` | `../browser-sandbox-sources/sources/chromium/sandbox/policy/mac/common.sb` | `browser-sandbox-sources/sources/chromium/sandbox/policy/mac/common.sb` |
| `TRACES.md` | `../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h` | `browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/common.sb` | `browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/common.sb` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in` | `browser-sandbox-sources/sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in` |
| `TRACES.md` | `../browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp` | `browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp` |
| `TRACES.md` | `../browser-sandbox-sources/sources/ladybird/Services/Compositor/SandboxMacOS.cpp` | `browser-sandbox-sources/sources/ladybird/Services/Compositor/SandboxMacOS.cpp` |
| `TRACES.md` | `../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyContent.h` | `browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyContent.h` |
| `TRACES.md` | `../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h` | `browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h` |
| `TRACES.md` | `../browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.h` | `browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.h` |
| `TRACES.md` | `../browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.cc` | `browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.cc` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` | `browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` | `browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h` | `browser-sandbox-sources/sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h` |
| `TRACES.md` | `../browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp` | `browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h` | `browser-sandbox-sources/sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` | `browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WTF/wtf/darwin/DarwinExtras.h` | `browser-sandbox-sources/sources/webkit/Source/WTF/wtf/darwin/DarwinExtras.h` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb` | `browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb` |
| `TRACES.md` | `../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` | `browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` |
| `TRACES.md` | `../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md#boundaries-owned-elsewhere` | `PLAN.md#boundaries-owned-elsewhere` |
| `TRACES.md` | `../browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_sandbox_design.md` | `browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_sandbox_design.md` |
| `TRACES.md` | `../browser-sandbox-sources/sources/chromium/chrome/app/chrome_exe_main_mac.cc` | `browser-sandbox-sources/sources/chromium/chrome/app/chrome_exe_main_mac.cc` |
| `TRACES.md` | `../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h` | `browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h` |
| `TRACES.md` | `../browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm` | `browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm` |
| `TRACES.md` | `../browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm` | `browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm` |
| `TRACES.md` | `../browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp` | `browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp` |
| `ACCEPTANCE.md` | `../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md` | `PLAN.md` |
