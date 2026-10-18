# Host setup controls

The `runner_unit/host_setup_controls` case copies the production Swift package,
renames selected native call sites in `CWorker.swift` and `ExtensionIssuer.swift`,
and adds `SetupControls.swift` only to that copy. Exact substitution counts and
source/instrumented hashes are retained. Production control flow is unchanged;
the signed app is never modified. `shim.c` exposes a fixed-argument shared-memory
lookup because Swift cannot call the variadic native declaration.

Each scenario runs in a fresh process. The adapters return a selected setup error
without performing that operation, or pass through to Darwin. Baselines reserve
low descriptors. The collision case closes stdin and low unused descriptors;
the checker requires the actual source/destination overlap and the child's wrong
evidence endpoint, not merely a low-descriptor label. The issuer's high duplicate
is exercised in the same low-descriptor arrangement.

`observer.c` is a separate native executable with no PW protocol headers. It
records its PID, argc and `fstat` results for protocol descriptor numbers before
opening its receipt file. Its receipt path is compiled into this per-run helper,
so reporting adds no inherited endpoint or argument. Descriptor metadata can
distinguish the pipe, null device and token-source file in these cases; matching
shared-memory metadata is not a general shared-object identity proof. The
optional-token control supplies the observer executable's descriptor, distinct
from the baseline's null devices; it tests descriptor delivery, not token validity.
The observer never applies a sandbox or publishes a worker/issuer result.

A failed handle initialization leaves nil. Subsequent adapter calls record the
invalid use and return EINVAL instead of passing nil into libc; an attempted
spawn with such a handle is likewise contained. Those observations establish
continued host control flow, not libc's behavior on an invalid handle. Issuer
no-spawn results after failed initialization depend on that fixture containment.
Action-add and argument-copy failures otherwise reach real native spawn when the
host permits it; the receipt establishes whether a child ran and what it received.

Cleanup is observed before independent fixture cleanup: descriptor closure,
successful unmapping/destruction, released copied strings, name lookup and child
reaping. The injected unlink cases leave names; the fixture removes them and
checks absence. A failed observation retains the name and cleanup receipt in the
case artifacts. Each child is either already reaped by the host or independently
terminated/reaped by the fixture, with host-reap evidence kept separate.

These are characterization controls. A passing case does not assert that every
setup failure is refused safely. The checker also rejects independently altered
receipts with missing injections, wrong children, missing reaping, unexpected
spawn, unconfirmed cleanup, unestablished collisions and missing child effects.
Real allocation exhaustion, private-library behavior and production XPC launch
conditions are outside these substituted-boundary observations.
