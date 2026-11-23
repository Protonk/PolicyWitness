# Compare two saved PolicyWitness runs

Examine `compare` during the [CLI and guide transition](../../CLI-TRANSITION-PLAN.md). The first decision is whether the executable can answer a useful question about saved runs. Its release number and command syntax are open.

Record the supported question and limits, or the reason to defer, in this plan. Keep the [worked comparison and original fixture account](../../records/guide/GUIDE-STUDIES.md#what-can-a-saved-run-tell-me-about-a-failed-open) available when judging what a reader can reproduce from the two files alone.

A PAWL caller comparing two policies currently has to interpret PW's evidence on each side. Start with a question a colleague could answer from the same two files. Did the outcome of the worker's open change? A possible invocation is `policy-witness compare before.json after.json --step s0`. The caller chooses the pair and supplies the rationale for treating it as a control. The command reads the saved envelopes offline. Preparing fixtures, changing policies and executing trials stay with the caller.

## First comparison

1. Identify each envelope's build and supported evidence format. Locate the selected step by ID on each side and check the actor, phase and position, attempted operation, and submitted operand. Report differences in what was attempted. Distinguish a missing step, an unreadable or unsupported input, and a step whose worker result went unpublished.
2. Show the recorded outcome on each side and point to its supporting fields. Keep any validator answers attributable to their own operations, operands and collection times. Distinguish the digest of the request file from a digest of selected source, a literal import closure digest or a digest of captured compiled bytes. An absent receipt leaves compiled-byte identity unknown.
3. Try the four saved file-open runs. With the file present, step `s0` changed from `EPERM` to a successful open. With the file absent, both opens returned `ENOENT` and neither received a prediction. The fixture notes establish how the caller prepared the file. Also try a reused step ID with a different target and a published failure paired with an interrupted attempt. Every statement in the output should be traceable to the two envelopes. [Saved runs and fixture account](../../records/guide/GUIDE-STUDIES.md#what-can-a-saved-run-tell-me-about-a-failed-open)

## Decisions on return

Use those pairs to settle the selector, support for older envelopes, a machine-readable result PAWL can consume, and how the exit status distinguishes an observed difference from a comparison that could not be performed. Route the verb through the controller's command table and dispatch, review existing reply admission for reuse, and verify the public entry point with saved files. [Command definitions](interface/commands.rs) · [Dispatch](cli.rs) · [Reply admission](porcelain_admission.rs) · [Interface inventory and checks](../interface/README.md)

If the verb earns a place, have a reader use its help and the saved pair to find the changed observation and its source fields. Move the mechanical field lookup out of the guide once the executable answers it. Keep the choice of control and the limits of causal attribution in the worked lesson. [The command line as an API](../../CONTRIBUTING.md#the-command-line-as-an-api)
