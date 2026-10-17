# Compiled-profile capture

Replace the misleading applied-profile request and receipt names with
`capture_compiled_profile` and `compiled_profile`. The worker copies the
compiler result before applying the same object; successful application and
normal completion remain prerequisites for publishing its bytes. Capture
availability never substitutes for separate application or access evidence.

Use request schema 5, response schema 22 and nested capture schema 2; leave
controller envelope 7. Captured receipts require `producer: "worker"` and
`capture_stage: "before_apply"`. Unavailable receipts must not assert either
context field. Keep the nonce, byte bounds, identity checks and publication
gates. Reject the retired request spelling without an alias.

Update request admission, Swift types/encoding/decoding, independent response
readers, fixtures and diagnostics together. Add controls for new context,
retired spelling/version rejection, and preserved unavailable cases. Migrate
current request specimens, regenerate owned contracts, limits, architecture
and worker identity, and review the encoder-produced shape golden. Preserve
historical captures; refresh current live consumer fixtures from actual runs.

Build a signed app and run capture/request/reader/native controls, then the
default battery. Retain the applicable evidence, record any failures and
replacement results, and commit the implementation. Retire this plan when the
owning documentation and passing evidence establish the completed change.

Acceptance exposed a repeated log-collection race in unchanged code: an idle
nonblocking read after observed exit was treated as a terminal open pipe. A
deterministic delayed-read control reproduces the failure. Repair this required
verification blocker by retaining collection until EOF or its original deadline,
preserving bounded cleanup and process ownership, then rebuild and rerun the
battery. Keep the failed and interrupted acceptance evidence.
