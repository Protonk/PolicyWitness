# Experiments to preserve

When considering a simpler way to run or report a specimen, try the paired cases below. Can a user still choose which question to ask and tell from the observations which case occurred?

## Can I query the same path on either side of a filesystem change in one worker?

### Teaching finding 2

**A PW phase lets you place a prediction on one side of a real event.** Suppose a phase contains an unlink followed by an open of the same path. PW holds the worker while a separate validator collects eligible predictions against its live PID. Then it releases the worker to perform both actions. The prediction associated with the open belongs to the time before the unlink, even though the open itself happens after. Put the open in a second phase and PW can attempt a fresh query after removal, with the same worker and policy still in place. The path may then be unavailable for prediction, while the open can still go ahead and report `ENOENT`.

**How can a query come first for an action the worker never reached?** One phase scheduled two opens of `/etc/hosts`, with a create between them. Both opens had an `allow` prediction and `comparison.order: query_first`. The validator had answered both questions before the worker was released. The worker completed the first open and died before it could publish the create's result. The last open kept its prediction. The two values of `attempt.lifecycle.summary` tell you which open happened. The first said `completed` and the last said `not_reached`. Run `20261121T201959Z_113ddef9` in the gitignored `tests/out/runs/guide-retry-20261121/` retains the envelope in this checkout. [Ordering statement](../../docs/contract/31-steps.surface.md) · [Publication control](../../tests/suites/witness_contract/check_killed_before_publication.py)

### Trust finding 6

**Ask about a path an earlier action created, without a second run.** PW plans each phase's queries when that phase arrives. If the path is absent then, a create followed by a read in that phase gets no path prediction for the read. If the path already exists, the same two steps can get a read prediction even when the exclusive create fails with `EEXIST`. Both second runs in teaching finding 1 did (`GUIDE-STUDIES.md`). To ask about the newly created file, put the read in a later phase. Six steps on an initially absent path (create, read, unlink, read, create, read) got no predictions as one plan. Run as six phases of one worker, each read after a create was predicted `deny` with `query_first`, and the read after the unlink had no prediction and returned `ENOENT`. The user chooses where to divide the phases. PW collects the eligible queries there without making the user stop and start another worker.

The retained single-plan and six-phase runs use the same sequence of filesystem operations. Compare the prediction for the read after creation with the prediction for the read after removal. [Single-plan envelope](work/evidence/phases/result_single.json) · [Six-phase envelope](work/evidence/phases/result_phases.json)

## Can I change which reader receives an extension and keep a second reader as a control?

### Teaching finding 3

**A PW specimen can contain its own control subject.** Alice and Bob run separate copies of the same signed worker with the same profile. Both try to read a file containing a recognizable word. A third actor gives Alice a read extension. She consumes it, then both readers try again. In a second run, Bob receives and consumes the extension instead. If only Alice reads the word in the first run and only Bob reads it in the second, the successful read has followed the recipient. The other reader shows what another copy of the same program could do with the same file without receiving the extension. PW lets the user make that comparison without writing either reader.

### Trust finding 5

**Deliver an extension token from one sandboxed process to another without opening a channel in their policies.** To test whether a token issued in one process grants access in another, the user would otherwise write an issuer and a consumer. They would need a channel the consumer's policy still permits, keep the token's bytes out of logs, and check that the consumer got the bytes that were issued. In an actor specimen, the user can leave delivery to PW. The host takes the token, places it in the recipient's slot and compares the two copies. A transfer marked `delivered` with `equality: equal` arrived intact, and the reply carries the token's length but never its bytes. Delivery doesn't show that consuming the token gave the recipient access. The recipient's fresh reads before and after consumption answer that.

In both saved runs the transfer was delivered. Only the recipient read the file after consumption. Giving the extension to the other reader reversed which read succeeded. [Alice received the extension](work/evidence/extension-delivery/res_Alice.json) · [Bob received the extension](work/evidence/extension-delivery/res_Bob.json)

## Can I try opening an existing document and keep its contents?

**Decision for 0.3.8.** Keep the existing action meanings. A future open-without-I/O action would be a distinct operation. In a direct trial on macOS 25G241, each write began with a separate 12-byte regular file containing `old contents`. The caller sampled bytes, size and inode before and after each trial. The simple native open/close was a caller-side control. The other three rows used signed build 1666.

| Operation | What happens after a successful open | What the caller observed |
| --- | --- | --- |
| Plain `O_WRONLY` | Close immediately | Same inode and all 12 bytes |
| `open_write` | Open with `O_TRUNC`, obtain any descriptor path, try writing `x`, close. The reported success covers the open. | Same inode, one byte `78` |
| `write_fresh` | Open without truncation, stat, truncate, stat, write, stat, close. Each reached call has a result. | Same inode, sizes 12, 0 and 1 in the reply; one byte `78` on disk |
| `open_write` with writes denied | Open failed with `EPERM` | Same inode and original 12 bytes |

On a FIFO held open by the caller, plain `O_RDONLY` followed by close left the queued byte `z`. After putting it back and running PW's `open_read`, the caller's nonblocking read got `EAGAIN`. An existing specimen can depend on the read or on truncation at open. A reader asking only about opening for write cannot reuse an original document after today's probe. Use a disposable copy, or use the application's own plain open if the exact flags are the question. The worker's unchecked one-byte call cannot establish that the byte was transferred; the independent samples did that in these fixtures. [Worker actions](../../controller/tools/pw_probe_runner/pw_probe_runner.c) · [File-effect controls](../../tests/suites/run_effects/check_file_actions.py)
