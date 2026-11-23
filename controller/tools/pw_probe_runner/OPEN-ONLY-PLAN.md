# What should a successful open establish?

**Release target.** Conclude during the 0.3.8 guide work. Choose the release for any product change with the result.

**Decision goes to.** A new section of [experiments to preserve](../../../records/guide/EXPERIMENTS-TO-PRESERVE.md), and an entry in the [product-change ledger](../../../records/guide/PRODUCT-CHANGES.md), whether or not the behavior changes.

**Draft 0 decision, 2026-11-23.** Keep both current open actions. The regular-file and FIFO controls show why an eventual plain open would need a distinct action.

`open_read` reads and discards one byte. `open_write` opens with `O_TRUNC`, tries to write `x`, and discards the write result. Both report success once the open succeeds. Can someone ask whether an existing document opens for writing and safely reuse its contents afterward? [Worker operations](pw_probe_runner.c) · [Observed file effects](../../../tests/suites/run_effects/README.md)

1. On separate copies of one nonempty regular file, compare plain `O_WRONLY`, the current `open_write`, and `write_fresh`. Record the open flags, each subsequent call and its result, and independent before/after samples of bytes, size and inode. Include a refused open. Truncation during `open` and a later `ftruncate` are distinct operations. [Operation definitions](../../../docs/contract/12-probes.surface.md)
2. For `open_read`, keep a caller-owned FIFO reader and writer open throughout each trial. Queue one known byte, run the probe, then try a nonblocking read on the caller's descriptor. Compare the remaining byte after an open followed by close with what remains after the current probe. On a regular file both operations leave the contents intact.
3. Find specimens that rely on truncation at open, the one-byte transfer, or the worker's descriptor-derived path. Which would change meaning under plain read-only and write-only opens?

Return a call-and-effect table and one concrete compatibility example for each behavior worth preserving. Use them to weigh changing the existing actions, offering an explicit open, or keeping today's actions.
