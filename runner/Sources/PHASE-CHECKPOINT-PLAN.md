# Can a caller observe a file between two phases?

In three runs the caller found the name absent at CLI timeout. One worker later created and kept the file, one lacked the parent directory, and one created then unlinked it. A caller sample between actions distinguished the last two. Getting that sample required a FIFO read inside the policy under study. [Timed observations](../../records/guide/work/evidence/retry/observations.json)

1. Use one worker, a private fixture with a known writer, and two fixed phases. Locate where the host knows the first phase completed and has yet to plan queries for the next. Sketch a bounded pause there. The existing host/worker barrier supplies ordering. How would an independent caller learn which run and phase it can sample, and acknowledge its sample? [Phase driver](PWRunnerCore/CWorker.swift) · [Host lifecycle](../README.md#run-lifecycle)
2. Try a disposable prototype against the three recorded histories and the FIFO control. Compare the caller's `lstat` between phases with its sample after worker exit. Keep the sample and its run/phase identity available to the observer even if the CLI loses the final reply.
3. In separate trials, delay the observer, disconnect it, or stop the worker before it reaches the checkpoint. Record which phase publications exist, what happens at the wait deadline, and whether the added pause itself changes the outcome. Keep later actions fixed. If the prototype changes the worker wait or release store, run the [order-barrier mutation controls](../../tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls).

Return the traces and the cost in timing, policy permissions and coordination. Identify whether an outside observer alone suffices or whether a host checkpoint warrants further work.
