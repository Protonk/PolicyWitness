# macOS browser sandbox sources: selection and boundaries

**Source packet dated October 31, 2026.** This report identifies a bounded set of source materials from Chromium, Firefox, WebKit and Ladybird, together with Chromium's Mac Sandbox V2 design document. The retained files are the inputs, not the results, of a comparative investigation. There is no proposed comparative procedure, experimental fixture, browser ranking, or PolicyWitness change in this packet.

## What is here

The archive contains **25 complete upstream files**: 22 implementation, policy or build-source files; the V2 design document; and two repository license files. The original repository-relative paths are preserved beneath `sources/<project>/`. Every retained upstream file has been checked against its recorded Git blob identity. The [source catalog](SOURCE-CATALOG.md) explains the individual selections and links each to its pinned upstream location; [MANIFEST.json](MANIFEST.json) records the complete commit, path, size and hash identities.

This is a curated reading corpus, **not four complete repositories, a buildable source distribution, or four complete browser sandboxes**. In particular, a complete file may contain only one fragment of a policy, or refer to inputs not included here. Completeness of each retained file and completeness of the surrounding system are different claims. Both the useful coverage and the missing context are identified below.

Nothing was taken from PAWL. No installed browser was inspected, and no browser installation is needed to read these materials. No profile was extracted, compiled, expanded, decompiled or applied. The files preserve source-level conditions rather than resolving them for an imagined host or release.

## Snapshot identity and product names

| Source group | Repository | Fixed commit | Branch observed during collection |
| --- | --- | --- | --- |
| Chromium | `chromium/chromium` | `9730a558013325c410dc6a36e0f73c9cd851f3ae` | `main` |
| Firefox | `mozilla-firefox/firefox` | `a5df22d986d4b626f771b4f8885241941601c35c` | `main` |
| WebKit | `WebKit/WebKit` | `b7d052336f276b45dc5733ed89d13606e08cb214` | `main` |
| Ladybird | `LadybirdBrowser/ladybird` | `663dfced22b526ad8645561ca399f6e95cfd3741` | `master` |

The commit, not a moving branch URL, identifies each selection. Branch heads can move during collection; the retained files continue to use the fixed commit listed above. These snapshots have not been matched to installed products, stable release versions, or a common macOS deployment target. Their collection on the same day does not establish that they describe equivalent shipping configurations.

**Chromium is the source identity, not an inspected Google Chrome build.** The retained executable entry point itself contains helper, renderer, architecture and Google Chrome branding conditions. Those conditions remain in the file; the packet does not select a branded release configuration for them. [[chrome_exe_main_mac.cc](sources/chromium/chrome/app/chrome_exe_main_mac.cc)]

**Firefox is sourced from `mozilla-firefox/firefox`, not the old `mozilla/gecko-dev` mirror.** The old repository identifies itself as archived and superseded by this replacement. That repository-identity check is recorded in the manifest; the old mirror contributes no source bytes to the packet. [Repository identity](https://github.com/mozilla/gecko-dev).

**WebKit is the Safari-relevant source selection, not “Safari's complete sandbox.”** WebKit describes itself as an open-source engine/framework used by Safari and other applications. The files here expose WebKit's own public macOS policy and extension machinery. They do not establish all of Safari's application-level choices, a shipping Safari binary's entitlements, or the exact source/build configuration used for an installed Safari release. [WebKit's own introduction](https://docs.webkit.org/Getting%20Started/Introduction.html).

That WebKit/Safari distinction is operationally important for these inputs. Public policy templates visibly refer to platform and feature switches, signing identifiers, runtime state and additional build inputs. An installed profile would be another kind of evidence, not a replacement for those source materials. No installed-profile evidence is requested or supplied here.

## Chromium: design rationale, policy fragments and extension machinery

### Why these files were selected

The [Mac Sandbox V2 Design Doc](sources/chromium/sandbox/mac/seatbelt_sandbox_design.md) supplies the design context requested for this packet. Its executable-structure discussion explains the motivation for applying restrictions before loading the larger framework and its dependent initializers. The retained [macOS executable entry point](sources/chromium/chrome/app/chrome_exe_main_mac.cc) is the corresponding source-level anchor: its helper path calls sandbox initialization before the later framework `dlopen`. The design account and the implementation remain separate files. [[seatbelt_sandbox_design.md](sources/chromium/sandbox/mac/seatbelt_sandbox_design.md), lines 79–96; [chrome_exe_main_mac.cc](sources/chromium/chrome/app/chrome_exe_main_mac.cc), lines 165–177 and 211–212]

The policy selection is deliberately specific: [common.sb](sources/chromium/sandbox/policy/mac/common.sb) and [gpu.sb](sources/chromium/sandbox/policy/mac/gpu.sb). The shared file retains parameter declarations, the Metal-cache helpers, their invocation conditions and the surrounding policy. The GPU file includes the read-extension issuance rule and explicitly states that the common policy is an implicit input. Keeping both prevents the GPU fragment from looking like a standalone policy. [[common.sb](sources/chromium/sandbox/policy/mac/common.sb), lines 108–142; [gpu.sb](sources/chromium/sandbox/policy/mac/gpu.sb), lines 5 and 115–123]

[seatbelt_extension.h](sources/chromium/sandbox/mac/seatbelt_extension.h) and [seatbelt_extension.cc](sources/chromium/sandbox/mac/seatbelt_extension.cc) supply the wrapper's vocabulary and its native issue, consume and release calls. They are useful input materials because they retain both the API's explanatory comments and the actual return-value handling. The presence of an issuance wrapper is distinct from identifying every caller or proving that a framework-mediated issuance path uses that wrapper.

### Boundaries of this selection

The V2 document carries an internal last-updated date of **January 30, 2025**. It also contains deployment-status language, including a statement about the GPU process. That wording is retained as part of the document, not adopted here as a current deployment inventory. The document is a design source; neither its date nor its presence at the pinned commit proves that every historical status sentence is current. [[seatbelt_sandbox_design.md](sources/chromium/sandbox/mac/seatbelt_sandbox_design.md), lines 1–2 and 109–115]

The shared policy's helper-bundle and cache parameters matter to the text that can be emitted or admitted. This packet does not retain the full policy-selection and parameter-population implementation, all process-specific fragments, the `SeatbeltExecServer` implementation, all extension call sites, or the extension unit tests. Thus it supports inspection of the selected rule definitions and wrappers, but not a complete account of Chromium's policy construction or every extension traffic path. The missing implementation is not supplied by the V2 prose.

Comments in the extension wrapper about token internals and kernel behavior remain **Chromium source comments**, not independently established macOS implementation facts. No reported browser test result or dated change narrative from the preceding conversation is used as evidence in this packet.

## Firefox: embedded policies plus their assembly and parameters

### Why these files were selected

The Firefox selection keeps two complete C++ policy headers, [SandboxPolicyGPU.h](sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h) and [SandboxPolicyContent.h](sources/firefox/security/sandbox/mac/SandboxPolicyContent.h), together with [Sandbox.mm](sources/firefox/security/sandbox/mac/Sandbox.mm), [Sandbox.h](sources/firefox/security/sandbox/mac/Sandbox.h) and [moz.build](sources/firefox/security/sandbox/mac/moz.build). These files are source strings and their supporting construction machinery, not text extracted from a Firefox binary.

The GPU header contains the selected file-extension issuance allowance, its path and vnode conditions, its version predicate, and the comment describing its motivation. The content header preserves extension-based font access as well as the separate file-content and audio addends. They provide relevant source in two process contexts without pretending those contexts exhaust Firefox's macOS policy. [[SandboxPolicyGPU.h](sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h), lines 159–171 and 229–247; [SandboxPolicyContent.h](sources/firefox/security/sandbox/mac/SandboxPolicyContent.h), lines 338–391]

The assembly module is essential context rather than incidental support. It defines how the macOS version becomes a parameter, selects process policy strings, appends addends and calls `sandbox_init_with_parameters`. Its GPU branch also supplies the cache-directory and bundle-related parameters used in the header. The declarations and build file show the input shape and the larger policy family without manufacturing a single “Firefox profile.” [[Sandbox.mm](sources/firefox/security/sandbox/mac/Sandbox.mm), lines 288–300, 450–487 and 555–582; [moz.build](sources/firefox/security/sandbox/mac/moz.build)]

### Boundaries of this selection

One detail deserves precise identification before this material is summarized elsewhere. The GPU policy comment describes observations on macOS 14 and earlier, but the adjacent source predicate is literally `(<= macosVersion 1500)`. The assembly code forms the value as `major * 100 + minor`. Consequently the comment's description and the encoded condition must not be substituted for one another; the source condition includes the encoded value for 15.0. This packet records the two pieces of source, without deciding whether the relationship is intentional, stale or defective. [[SandboxPolicyGPU.h](sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h), lines 159–171; [Sandbox.mm](sources/firefox/security/sandbox/mac/Sandbox.mm), lines 292–297]

`Sandbox.mm` references other policy headers that are **not retained**: GMP, RDD, utility, hardware-inference and PGO policies. Their names remain visible in the file and build inventory. The packet does not include all startup callers, process launch definitions, effective preferences, signatures, or tests. It therefore does not establish which path a shipping process takes, or its complete starting authority.

Nor does this selection establish the absence of Firefox issuance APIs elsewhere. The selected GPU policy discusses an Apple service dependency; a policy allowance does not by itself identify a Firefox-owned native issuance call or reveal the implementation of the Apple framework that uses it.

## WebKit: macOS policy templates and Darwin extension implementation

### Why these files were selected

The central policy file is the complete [com.apple.WebProcess.sb.in](sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in) template. Alongside it are its three top-level, directly named policy includes: macOS [common.sb](sources/webkit/Source/WebKit/Shared/Sandbox/macOS/common.sb), macOS [webcontent-defines.sb](sources/webkit/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb) and [preferences.sb](sources/webkit/Source/WebKit/Shared/Sandbox/preferences.sb). The shared [common.sb](sources/webkit/Source/WebKit/Shared/Sandbox/common.sb) that the macOS common file includes is also retained. These are complete source files with preprocessor guards intact, not a flattened policy. [[com.apple.WebProcess.sb.in](sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in), lines 24–26; [common.sb](sources/webkit/Source/WebKit/Shared/Sandbox/macOS/common.sb), lines 24–28]

The shared policy contains the read/write-and-issue helper definitions. The WebProcess template supplies actual uses of those helpers, including extension-based filter arguments. Retaining the definitions and the uses is necessary to identify the source relationship without turning it into a claim about effective re-delegation at runtime. [[common.sb](sources/webkit/Source/WebKit/Shared/Sandbox/common.sb), lines 63–74; [com.apple.WebProcess.sb.in](sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in), lines 730–746]

The complete [SandboxExtensionCocoa.mm](sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm) provides the extension implementation: path handling, native issuance choices, optional audit-token use and wrapper lifetime operations. [DarwinExtras.h](sources/webkit/Source/WTF/wtf/darwin/DarwinExtras.h) supplies the named UTF-8 wrappers used there, while [SandboxSPI.h](sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h) supplies native declarations and external flag symbols. Those layers remain separate. In particular, an SPI declaration is not the implementation of Apple's API. [[SandboxExtensionCocoa.mm](sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm), lines 86–120 and 155–203; [DarwinExtras.h](sources/webkit/Source/WTF/wtf/darwin/DarwinExtras.h); [SandboxSPI.h](sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h)]

### What is missing, and why Safari remains a qualified label

There is a concrete additional-input boundary in the retained source. The macOS common policy conditionally includes `<WebKitAdditions/SystemContentSandbox-macos.defs>`. That file is not in this packet. The existence of the conditional include is established; whether a particular Safari build enables it, and what it contributes there, is not. No conclusion about that build is reconstructed from the filename. [[common.sb](sources/webkit/Source/WebKit/Shared/Sandbox/macOS/common.sb), lines 26–28]

The WebProcess template also conditionally includes notification allow-list `.def` files near its end; those public source dependencies have not been copied. Platform configuration headers, the generated build configuration and policy-processing build rules are not present. Thus **even the retained WebProcess template is not a closed set of inputs from which this packet claims to reproduce a final policy**. The directly relevant shared policy definitions are present; transitive build completeness is not. [[com.apple.WebProcess.sb.in](sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in), lines 1604–1620]

The packet does not include WebKit's full GPU or networking policy families, the complete `SandboxExtension` class declaration, all call sites or IPC serializers, or the auxiliary-process initialization implementation. Those omissions bound the available source coverage; they are not claims that the corresponding material is inaccessible. A wrapper supporting a process-bound token does not establish which browser process calls it in a particular product flow.

WebKit's shared and Cocoa files contain branches for other Apple platforms. Their retention is for file integrity and context. An iOS-family condition, simulator branch or Mac Catalyst branch is not macOS evidence merely because it appears in a file also used on the Mac. Likewise the private-API declarations and internal-SDK conditions do not turn the public repository into a public specification of the macOS sandbox.

## Ladybird: policy generation and selected macOS callers

### Why these files were selected

Ladybird's complete [Sandbox.cpp](sources/ladybird/Libraries/LibSandbox/Sandbox.cpp) and [Sandbox.h](sources/ladybird/Libraries/LibSandbox/Sandbox.h) expose the structured inputs and policy generator. The macOS implementation contains path preparation, rule construction, extension-issuance rule generation, and the call that applies the resulting policy. Keeping the entire cross-platform file avoids silently deleting its compile-time guards or altering source line identities. [[Sandbox.cpp](sources/ladybird/Libraries/LibSandbox/Sandbox.cpp), lines 123–152, 256–280 and 726–760; [Sandbox.h](sources/ladybird/Libraries/LibSandbox/Sandbox.h)]

Two complete macOS callers make the generator's inputs less abstract: [RendererSandboxMacOS.cpp](sources/ladybird/Services/RendererSandboxMacOS.cpp) and the compositor's [SandboxMacOS.cpp](sources/ladybird/Services/Compositor/SandboxMacOS.cpp). The renderer source supplies its path and service selections. The compositor source includes the bundle-derived Darwin cache directory, directory creation, path selection and GPU-related service choices before calling the shared generator. These files identify concrete construction sites without requiring a locally generated profile. [[RendererSandboxMacOS.cpp](sources/ladybird/Services/RendererSandboxMacOS.cpp); [SandboxMacOS.cpp](sources/ladybird/Services/Compositor/SandboxMacOS.cpp), lines 21–35 and 38–76]

### Boundaries of this selection

The generator is not a static profile. Its output depends on the selected caller's arguments, path preparation and runtime conditions. It also includes an explicit macOS 27 availability branch. Nothing in this packet evaluates that branch for PW's host, fixes the input paths, or claims to reproduce a generated policy. [[Sandbox.cpp](sources/ladybird/Libraries/LibSandbox/Sandbox.cpp), lines 686–688 and 726–760]

Only the renderer and compositor policy-construction callers are included. Other service policy constructors, service `main` functions, browser-side brokers, file-descriptor transfer paths, build definitions and tests are outside this selection. The retained generator's `file-issue-extension` output is evidence of source-level allowance construction, not evidence that a Ladybird-owned call issues a native token. Linux code is present inside the complete source file but is not part of this macOS source selection's claims.

## What these inputs establish—and what remains outside them

The packet establishes the identity and contents of the selected files. It makes certain source relationships inspectable: definitions and uses, native wrapper calls, parameter construction, conditional compilation and explicit references to omitted inputs. Source comments also preserve the authors' explanations, but those explanations are a different kind of evidence from the adjacent implementation.

It does **not** establish effective permissions in a running browser; a sandboxed issuer's actual ability to create a usable token; the cause of a native failure; successful consumption, revocation or re-delegation; or the exact privileges of a process launched by a shipping browser. It contains no runtime observations with which to make those claims. Neither a rule's presence nor a wrapper's success-return condition supplies them.

Equal inclusion of four projects does not imply equal source coverage or four independent confirmations of macOS behavior. The selected surfaces have different shapes: policy fragments, embedded strings, preprocessed templates and a generator with structured inputs. Shared Apple framework dependencies can also make similar source text less independent than it looks. This is a boundary on how the input materials may be described, not a proposed comparative method.

## Provenance, integrity and offline use

All 25 retained upstream files match the Git blob SHA-1 recorded for them, using the Git `blob <byte-count>\0<bytes>` calculation, and also have local SHA-256 hashes. Most content was transported as text through the GitHub connector and saved locally. Where text retrieval required chunk assembly or restoration of a final newline, the complete resulting bytes were accepted only after the upstream blob identity matched. The V2 document was recovered from the project-supplied text in this way: its restored final newline produces the pinned upstream blob exactly.

The manifest records the repository and commit association returned by the source service. These checks detect truncation or altered bytes; they are not an independent verification of signed commits or an assertion about the authenticity of an installed binary. `SHA256SUMS` additionally covers the report, catalog, manifest, notices and verification utility.

All selected upstream content is physically in the archive. Online links in the report and catalog identify provenance; they are not download placeholders for the retained selection. Ordinary repository headers and general build dependencies are intentionally not bundled, so offline readability does not imply offline buildability. References inside original source comments, including bug links and historical design alternatives, remain as originally written and have not been expanded into additional reading materials.

Run `python3 VERIFY.py` from the extracted directory to check the packet locally. The utility makes no network requests and executes no browser code. See [NOTICES.md](NOTICES.md) for retained licenses and the separately supplied standard MPL 2.0 notice text.
