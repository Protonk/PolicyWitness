# Sandbox extensions investigation

## Scope and status

M1 is in progress. The user limited this turn to M1; M0 remains pending.
Production phase and extension behavior is not implemented. This record is the
current account of findings and decisions, readable without commit history.
No native feasibility claim has yet been established.

## Baseline and equipment

- Source: `fb2750d5abddb81291086cc3ae590a9ca7d3e1d2`, initially clean.
- Host: macOS 26.7.1, build 25G241, arm64.
- Selected SDK: Xcode's MacOSX27.0.sdk under
  `/Applications/Xcode.app/Contents/Developer`.
- Development identity: `Developer ID Application: Adam Hyland (42D369QV8E)`,
  certificate SHA-1 `1A6E85D06FC762993C8BD3E932556DED3985F030`.
- `security find-identity -v -p codesigning` found no identities inside the
  automation sandbox and this identity when rerun outside it. This difference
  concerns keychain visibility, not native extension authority.
- The existing distribution is stamped v0.2.8 and is not M1 equipment or a new
  accepted product candidate. M1 will build its own independent fixture.
- Rust tools are installed under `/opt/homebrew/opt/rustup/bin`; add that path
  for later product builds. Pandoc and Graphviz are available for rendered review.

There are no active experiment processes or BYOXPC cleanup obligations.

## Native declarations and measurement basis

WebKit's [SandboxSPI.h](https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/spi/darwin/SandboxSPI.h)
declares file issuance with a class, path and unsigned flags, consumption with
a signed 64-bit return, and release taking that handle and returning an int.
Its [extension implementation](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
uses the read-only class, treats a consume return of -1 as failure, and frees
issued token storage. These sources inform the experiment; they do not establish
availability, authority or effects on this host.

Apple's [libmalloc source](https://github.com/apple-oss-distributions/libmalloc/blob/main/src/malloc.c)
exposes a malloc logging callback. The experiment will first establish that a
local allocation control reaches any instrumentation used. Measured callbacks
will not establish absence of all allocations, resource acquisition or activity
inside the kernel. Native first-call behavior remains to be measured.

## Work and evidence still owed

Build the signed native fixture and register its independent controls. Retain
source/build provenance, signature and entitlement read-backs, target identity,
fresh access observations, native lifecycle results, external queries, issuer
lifetime comparisons and allocation observations without retaining token bytes.
Then document the supported choices and limitations and complete M1's rendered
assessment. No M1 acceptance check is credited yet.
