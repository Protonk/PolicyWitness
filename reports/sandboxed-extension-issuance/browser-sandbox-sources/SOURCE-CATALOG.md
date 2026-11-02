# Source catalog

Each entry describes one complete retained upstream file. Paths are relative to this archive. Line numbers refer to the unmodified file, not to an extracted fragment. The manifest supplies SHA-256 in addition to the Git blob identities below.

## Chromium (Chrome-relevant source)

Repository: `chromium/chromium`. Commit: `9730a558013325c410dc6a36e0f73c9cd851f3ae`.

Chromium source at the fixed commit, not an installed Chrome configuration. Policy fragments depend on construction context; wrapper comments are not native API specifications.

### `LICENSE`

Upstream source license.

[Local file](sources/chromium/LICENSE) · [Pinned upstream file](https://github.com/chromium/chromium/blob/9730a558013325c410dc6a36e0f73c9cd851f3ae/LICENSE)

1,536 bytes; 27 lines. Git blob: `2249a28657f86c645f8978b75babc1bd52aca318`.

### `chrome/app/chrome_exe_main_mac.cc`

macOS executable entry point, preserving helper/renderer/branding guards and the sandbox-initialization call preceding framework loading..

[Local file](sources/chromium/chrome/app/chrome_exe_main_mac.cc) · [Pinned upstream file](https://github.com/chromium/chromium/blob/9730a558013325c410dc6a36e0f73c9cd851f3ae/chrome/app/chrome_exe_main_mac.cc)

10,226 bytes; 228 lines. Git blob: `f812b05fd7df5f0401cbc064ee03333ade18cd02`.

### `sandbox/mac/seatbelt_extension.cc`

Native issue/consume/release wrapper implementation.

[Local file](sources/chromium/sandbox/mac/seatbelt_extension.cc) · [Pinned upstream file](https://github.com/chromium/chromium/blob/9730a558013325c410dc6a36e0f73c9cd851f3ae/sandbox/mac/seatbelt_extension.cc)

2,780 bytes; 94 lines. Git blob: `79edca9ca521d1bc2ff343967348eb98039b292a`.

### `sandbox/mac/seatbelt_extension.h`

Extension API declarations and wrapper claims.

[Local file](sources/chromium/sandbox/mac/seatbelt_extension.h) · [Pinned upstream file](https://github.com/chromium/chromium/blob/9730a558013325c410dc6a36e0f73c9cd851f3ae/sandbox/mac/seatbelt_extension.h)

3,253 bytes; 91 lines. Git blob: `f7a1d24fcc10d124bc17fca693ae504e0b4f126e`.

### `sandbox/mac/seatbelt_sandbox_design.md`

Chromium Mac Sandbox V2 design document; project copy checked against pinned Git blob.

[Local file](sources/chromium/sandbox/mac/seatbelt_sandbox_design.md) · [Pinned upstream file](https://github.com/chromium/chromium/blob/9730a558013325c410dc6a36e0f73c9cd851f3ae/sandbox/mac/seatbelt_sandbox_design.md)

10,712 bytes; 249 lines. Git blob: `bab51992f22c2dfaa30b7caea89687da3806eca4`.

### `sandbox/policy/mac/common.sb`

Shared SBPL definitions, parameters and Metal issuance allowances.

[Local file](sources/chromium/sandbox/policy/mac/common.sb) · [Pinned upstream file](https://github.com/chromium/chromium/blob/9730a558013325c410dc6a36e0f73c9cd851f3ae/sandbox/policy/mac/common.sb)

13,916 bytes; 359 lines. Git blob: `428385df29277071cf5c330ae54852527c3907ee`.

### `sandbox/policy/mac/gpu.sb`

GPU process SBPL fragment; common.sb is implicit input.

[Local file](sources/chromium/sandbox/policy/mac/gpu.sb) · [Pinned upstream file](https://github.com/chromium/chromium/blob/9730a558013325c410dc6a36e0f73c9cd851f3ae/sandbox/policy/mac/gpu.sb)

6,004 bytes; 153 lines. Git blob: `e65ce84753ad966d671d1cb1fbd7cefefbbcad7f`.

## Firefox / Gecko

Repository: `mozilla-firefox/firefox`. Commit: `a5df22d986d4b626f771b4f8885241941601c35c`.

Parameterized C++ policy source and selected construction code; not an extracted profile or a complete inventory of Firefox process sandboxes.

### `security/sandbox/mac/Sandbox.h`

Sandbox process types and configuration inputs.

[Local file](sources/firefox/security/sandbox/mac/Sandbox.h) · [Pinned upstream file](https://github.com/mozilla-firefox/firefox/blob/a5df22d986d4b626f771b4f8885241941601c35c/security/sandbox/mac/Sandbox.h)

3,383 bytes; 111 lines. Git blob: `d93420c478dcbb64447907e03400fec1bbebe23e`.

### `security/sandbox/mac/Sandbox.mm`

Complete macOS policy assembly, parameterization and sandbox application module.

[Local file](sources/firefox/security/sandbox/mac/Sandbox.mm) · [Pinned upstream file](https://github.com/mozilla-firefox/firefox/blob/a5df22d986d4b626f771b4f8885241941601c35c/security/sandbox/mac/Sandbox.mm)

29,540 bytes; 919 lines. Git blob: `4afe49faacc51236c56cd5cb2eb3f6dd281954ff`.

### `security/sandbox/mac/SandboxPolicyContent.h`

Full content-process policy header, including file/audio addends and comments on font-extension access; a parameterized source string, not an applied profile..

[Local file](sources/firefox/security/sandbox/mac/SandboxPolicyContent.h) · [Pinned upstream file](https://github.com/mozilla-firefox/firefox/blob/a5df22d986d4b626f771b4f8885241941601c35c/security/sandbox/mac/SandboxPolicyContent.h)

14,546 bytes; 391 lines. Git blob: `a256f6a7a37682a07629c3e34b25355eed24c0bc`.

### `security/sandbox/mac/SandboxPolicyGPU.h`

GPU profile C++ source, OS guard and issuance clause.

[Local file](sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h) · [Pinned upstream file](https://github.com/mozilla-firefox/firefox/blob/a5df22d986d4b626f771b4f8885241941601c35c/security/sandbox/mac/SandboxPolicyGPU.h)

9,746 bytes; 263 lines. Git blob: `48394846c6682ad316dffed8fbc4458bb61df67c`.

### `security/sandbox/mac/moz.build`

macOS sandbox build declaration and policy inventory.

[Local file](sources/firefox/security/sandbox/mac/moz.build) · [Pinned upstream file](https://github.com/mozilla-firefox/firefox/blob/a5df22d986d4b626f771b4f8885241941601c35c/security/sandbox/mac/moz.build)

688 bytes; 28 lines. Git blob: `4259b5ecdc0e566f13464551710aa01b047bec2b`.

## WebKit (Safari-relevant source)

Repository: `WebKit/WebKit`. Commit: `b7d052336f276b45dc5733ed89d13606e08cb214`.

WebKit public source, not a complete Safari build. Preprocessor conditions and omitted build/addition inputs remain unresolved.

### `Source/WTF/wtf/darwin/DarwinExtras.h`

UTF-8 wrapper functions connecting the Cocoa extension implementation to native sandbox SPI declarations..

[Local file](sources/webkit/Source/WTF/wtf/darwin/DarwinExtras.h) · [Pinned upstream file](https://github.com/WebKit/WebKit/blob/b7d052336f276b45dc5733ed89d13606e08cb214/Source/WTF/wtf/darwin/DarwinExtras.h)

6,380 bytes; 170 lines. Git blob: `235b61c42146efaa2495152c4bbdfecc8bfbf83a`.

### `Source/WTF/wtf/spi/darwin/SandboxSPI.h`

Darwin private sandbox declarations and external flag symbols used by WebKit; not implementations of Apple APIs..

[Local file](sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h) · [Pinned upstream file](https://github.com/WebKit/WebKit/blob/b7d052336f276b45dc5733ed89d13606e08cb214/Source/WTF/wtf/spi/darwin/SandboxSPI.h)

4,358 bytes; 103 lines. Git blob: `e836c807604448c780fcb28480ead0609eb28377`.

### `Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm`

Cocoa sandbox-extension implementation: native issuance choices, path preparation, audit-token handling, consumption, release and lifetime wrappers..

[Local file](sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm) · [Pinned upstream file](https://github.com/WebKit/WebKit/blob/b7d052336f276b45dc5733ed89d13606e08cb214/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)

16,169 bytes; 437 lines. Git blob: `083c1eec73e129d0c3fb2564c9c4b1bcf5c17f1d`.

### `Source/WebKit/Shared/Sandbox/common.sb`

Shared preprocessed SBPL functions for access and issuance.

[Local file](sources/webkit/Source/WebKit/Shared/Sandbox/common.sb) · [Pinned upstream file](https://github.com/WebKit/WebKit/blob/b7d052336f276b45dc5733ed89d13606e08cb214/Source/WebKit/Shared/Sandbox/common.sb)

4,043 bytes; 95 lines. Git blob: `fcde054ce62306b00433c12cc84608ec52f9de8f`.

### `Source/WebKit/Shared/Sandbox/macOS/common.sb`

macOS-specific shared policy input; platform guards, home-path helpers and conditional WebKitAdditions dependency..

[Local file](sources/webkit/Source/WebKit/Shared/Sandbox/macOS/common.sb) · [Pinned upstream file](https://github.com/WebKit/WebKit/blob/b7d052336f276b45dc5733ed89d13606e08cb214/Source/WebKit/Shared/Sandbox/macOS/common.sb)

2,355 bytes; 51 lines. Git blob: `46e598f6f6920206582b598e934e2f9ab0538b33`.

### `Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb`

macOS WebContent policy helper definitions included by the WebProcess template; retains message-filter and deployment-target conditions..

[Local file](sources/webkit/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb) · [Pinned upstream file](https://github.com/WebKit/WebKit/blob/b7d052336f276b45dc5733ed89d13606e08cb214/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb)

15,926 bytes; 390 lines. Git blob: `0e5d93ba439f5fcaf99a710822df2136ffec9e9c`.

### `Source/WebKit/Shared/Sandbox/preferences.sb`

Shared preference-policy definitions directly included by the WebProcess template..

[Local file](sources/webkit/Source/WebKit/Shared/Sandbox/preferences.sb) · [Pinned upstream file](https://github.com/WebKit/WebKit/blob/b7d052336f276b45dc5733ed89d13606e08cb214/Source/WebKit/Shared/Sandbox/preferences.sb)

2,731 bytes; 52 lines. Git blob: `e0f3998413c3f33ef12f6101ea2e1fd217300490`.

### `Source/WebKit/WebProcess/com.apple.WebProcess.sb.in`

Complete WebProcess policy template with includes, preprocessor conditions, signing-identifier and runtime-state predicates; not an expanded or extracted Safari profile..

[Local file](sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in) · [Pinned upstream file](https://github.com/WebKit/WebKit/blob/b7d052336f276b45dc5733ed89d13606e08cb214/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in)

59,735 bytes; 1,638 lines. Git blob: `f1bbcd7313fe46e5beee655e10c59d8efacd7925`.

## Ladybird

Repository: `LadybirdBrowser/ladybird`. Commit: `663dfced22b526ad8645561ca399f6e95cfd3741`.

Generator and selected macOS constructors; no generated profile or runtime input values are supplied. Other-platform code is retained only as part of complete files.

### `LICENSE`

Repository license accompanying the selected Ladybird sources..

[Local file](sources/ladybird/LICENSE) · [Pinned upstream file](https://github.com/LadybirdBrowser/ladybird/blob/663dfced22b526ad8645561ca399f6e95cfd3741/LICENSE)

1,342 bytes; 25 lines. Git blob: `e6ea97f9739333c4320a3a2e42be50ccaf8626a6`.

### `Libraries/LibSandbox/Sandbox.cpp`

Complete cross-platform sandbox generator; macOS clauses retained with their original guards.

[Local file](sources/ladybird/Libraries/LibSandbox/Sandbox.cpp) · [Pinned upstream file](https://github.com/LadybirdBrowser/ladybird/blob/663dfced22b526ad8645561ca399f6e95cfd3741/Libraries/LibSandbox/Sandbox.cpp)

31,491 bytes; 915 lines. Git blob: `1fe0a424ad20d8fc7b0ba19133e68c271201bf81`.

### `Libraries/LibSandbox/Sandbox.h`

Structured inputs to the policy generator: path access, network access and system-service flags..

[Local file](sources/ladybird/Libraries/LibSandbox/Sandbox.h) · [Pinned upstream file](https://github.com/LadybirdBrowser/ladybird/blob/663dfced22b526ad8645561ca399f6e95cfd3741/Libraries/LibSandbox/Sandbox.h)

2,973 bytes; 99 lines. Git blob: `dfe4ac08c1c13dc398891d60f14683aaaf17ec10`.

### `Services/Compositor/SandboxMacOS.cpp`

macOS compositor-specific construction of paths, Metal-cache inputs and system-service flags before calling the shared generator..

[Local file](sources/ladybird/Services/Compositor/SandboxMacOS.cpp) · [Pinned upstream file](https://github.com/LadybirdBrowser/ladybird/blob/663dfced22b526ad8645561ca399f6e95cfd3741/Services/Compositor/SandboxMacOS.cpp)

3,617 bytes; 79 lines. Git blob: `aa2dc50c05397402a81b915d458735bc7ca2a381`.

### `Services/RendererSandboxMacOS.cpp`

macOS renderer-specific construction of the shared SeatbeltProfile inputs..

[Local file](sources/ladybird/Services/RendererSandboxMacOS.cpp) · [Pinned upstream file](https://github.com/LadybirdBrowser/ladybird/blob/663dfced22b526ad8645561ca399f6e95cfd3741/Services/RendererSandboxMacOS.cpp)

1,471 bytes; 38 lines. Git blob: `fc2cee731ff73b623d8708af347432674ac44e58`.
