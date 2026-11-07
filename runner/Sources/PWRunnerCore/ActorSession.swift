import Darwin
import Foundation

/*
 * ActorSession — one owned worker process: its evidence region, pipes,
 * launch, policy transfer, readiness, polling primitives, cleanup and the
 * decoded publications. The single-worker adapter (`runCWorker` in
 * CWorker.swift) and the actor scheduler both drive sessions; the session
 * never decides what a phase means or classifies anything.
 *
 * Setup runs in the initializer, in the order the legacy driver used:
 *   1. shm_open, unlink, ftruncate and mmap an evidence region. Only the
 *      explicit dup2 destination is inherited by an actor.
 *   2. Zero the header, write identity, counts, actor fields, slots, params,
 *      phase partitions (with each visit's global phase), touch pages.
 *   3. Release-store `prepared = 1`.
 *   4. Create ready + policy pipes; parent ends FD_CLOEXEC.
 *   5. posix_spawn the worker with FDs dup'd to 0/3/4 (and 5 for a token channel).
 *   6. Deliver the policy under its deadline; read the pre-apply ready byte.
 * A refusal before spawn leaves `spawned` false with `failure` set; a transfer
 * failure after spawn leaves the child running for the caller's cleanup.
 */
final class ActorSession {
    let input: CWorkerInput
    let calls: ChildProcessCalls
    private(set) var failure: CWorkerRunError?
    private(set) var spawned = false
    private(set) var pid: pid_t = 0
    var process: ChildProcessState
    private var base: UnsafeMutableRawPointer?
    private(set) var rawBase: UnsafeMutablePointer<UInt8>
    private var shmFD: Int32 = -1
    private var ownsShmFD = false
    private var tokenFD: Int32 = -1
    private var fileActions: posix_spawn_file_actions_t? = nil
    private var actionsInitialized = false
    private var spawnAttributes: posix_spawnattr_t? = nil
    private var attributesInitialized = false
    private var tornDown = false
    let policyBytes: [UInt8]
    private(set) var transferTimeout: PWWorkerPolicyTransferTimeout?
    private(set) var transferError: PWWorkerPolicyTransferError?
    private(set) var transferFailure: CWorkerRunError?
    private(set) var readyByteReceived = false
    private(set) var readyWait: PWHostWait?
    var phaseOutputs: [CWorkerPhaseOutput]
    var ownershipUnbroken = true
    var pollStopReason: String
    var sentinelWait: PWHostWait?
    private(set) var graceEnd = "not_entered"
    private(set) var graceWait: PWHostWait?
    private(set) var exitRequested = false

    private static let placeholder = UnsafeMutablePointer<UInt8>.allocate(capacity: 1)

    init(_ input: CWorkerInput, processCalls: ChildProcessCalls = ChildProcessCalls(),
         transferCalls: PolicyTransferCalls = PolicyTransferCalls(), setupRemainingMs: (() -> Int)? = nil) {
        self.input = input
        self.calls = processCalls
        self.policyBytes = Array(input.policy.utf8)
        self.phaseOutputs = input.phases.map { _ in CWorkerPhaseOutput() }
        self.process = ChildProcessState(pid: 0, calls: processCalls)
        self.rawBase = ActorSession.placeholder
        self.pollStopReason = "sentinel_deadline"
        if input.captureCompiledProfile && captureNonceBytes(input.captureNonce) == nil {
            failure = .captureNonceInvalid; return
        }
        // All capacity refusals use the same host-owned record, before shm/spawn.
        if let refused = workerAdmissionFailure(input) { failure = .admissionFailed(refused); return }
        var endSlot = 0
        guard !input.phases.isEmpty, input.phases.allSatisfy({ phase in
            defer { endSlot = phase.endSlot }
            return phase.firstSlot == endSlot && phase.endSlot >= endSlot && phase.endSlot <= input.slots.count
        }), endSlot == input.slots.count else { failure = .shmSetupFailed("invalid phase partition"); return }
        for slot in input.slots where slot.attemptKind == .execSpawn && !slot.target.hasPrefix("/") {
            failure = .execTargetNotAbsolute(stepId: slot.stepId, target: slot.target); return
        }

        // ---- shm region.
        let shmName: String = {
            // shm_open names cap at 32 chars on macOS including the leading '/'.
            let base = "/pw_cw_\(getpid())_\(input.actorIndex)"
            return String(base.prefix(31))
        }()
        shmFD = shmName.withCString { cName -> Int32 in
            return pw_cworker_shm_open_create(cName, 0o600)
        }
        if shmFD < 0 {
            failure = .shmSetupFailed("shm_open: \(String(cString: strerror(errno)))"); return
        }
        // Unlink immediately; the FD survives and the region is anonymous-ish.
        guard shmName.withCString({ Darwin.shm_unlink($0) }) == 0 else {
            let error = errno
            close(shmFD); shmFD = -1
            failure = .shmSetupFailed("shm_unlink \(shmName): \(String(cString: strerror(error)))"); return
        }
        guard fcntl(shmFD, F_SETFD, input.actorMode == 0 ? 0 : FD_CLOEXEC) == 0 else {
            let error = errno
            close(shmFD); shmFD = -1
            failure = .shmSetupFailed("evidence descriptor flags: \(String(cString: strerror(error)))"); return
        }

        if ftruncate(shmFD, off_t(PWShmLayout.regionBytes)) != 0 {
            let why = String(cString: strerror(errno))
            close(shmFD); shmFD = -1
            failure = .shmSetupFailed("ftruncate: \(why)"); return
        }
        guard let base = mmap(nil, PWShmLayout.regionBytes,
                              PROT_READ | PROT_WRITE,
                              MAP_SHARED, shmFD, 0) else {
            let why = String(cString: strerror(errno))
            close(shmFD); shmFD = -1
            failure = .shmSetupFailed("mmap: \(why)"); return
        }
        if base == MAP_FAILED {
            let why = String(cString: strerror(errno))
            close(shmFD); shmFD = -1
            failure = .shmSetupFailed("mmap: \(why)"); return
        }
        self.base = base
        ownsShmFD = true

        // Zero the region. The worker checks ABI identity + prepared so a
        // leftover non-zero from a recycled mapping wouldn't be confusing,
        // but zeroing is cheap and removes a class of "did I clear it?"
        // questions.
        memset(base, 0, PWShmLayout.regionBytes)

        // ---- Populate header.
        rawBase = base.assumingMemoryBound(to: UInt8.self)
        writeU32(rawBase, offset: PWShmLayout.abiMagicOffset, PWShmLayout.abiMagic)
        PWShmLayout.abiIdentity.withUnsafeBytes { identity in
            rawBase.advanced(by: PWShmLayout.abiIdentityOffset).update(from: identity.bindMemory(to: UInt8.self).baseAddress!,
                                                                     count: PWShmLayout.abiIdentityBytes)
        }
        writeU32(rawBase, offset: PWShmLayout.authoritySetupOffset + 12, input.authorityRequired ? 1 : 0)
        writeU32(rawBase, offset: PWShmLayout.authoritySetupOffset + 16, input.actorIndex)
        writeU32(rawBase, offset: PWShmLayout.stepCountOffset, UInt32(input.slots.count))
        writeU32(rawBase, offset: PWShmLayout.paramCountOffset, UInt32(input.params.count))
        // The submission's byte array is built once. Its count is the header's
        // expected policy length and every transfer record's bytes_expected, and
        // the same bytes are what writePolicy delivers after spawn. The worker
        // compares the count it reads at EOF against this input; admission bounds
        // it below the source capacity.
        writeU32(rawBase, offset: PWShmLayout.policyBytesExpectedOffset, UInt32(policyBytes.count))
        writeU32(rawBase, offset: PWShmLayout.captureRequestedOffset, input.captureCompiledProfile ? 1 : 0)
        if input.captureCompiledProfile, let nonce = captureNonceBytes(input.captureNonce) {
            nonce.copyBytes(to: rawBase.advanced(by: PWShmLayout.captureNonceOffset), count: nonce.count)
        }
        // Actor-form inputs: mode, index, the shared lifetime cutoff. Zero in
        // the legacy form.
        writeU32(rawBase, offset: PWShmLayout.actorModeOffset, input.actorMode)
        writeU32(rawBase, offset: PWShmLayout.actorIndexOffset, input.actorIndex)
        writeU64(rawBase, offset: PWShmLayout.lifetimeCutoffTicksOffset, input.lifetimeCutoffTicks)

        writeU32(rawBase, offset: PWShmLayout.phaseCountOffset, UInt32(input.phases.count))
        for (index, phase) in input.phases.enumerated() {
            let base = rawBase.advanced(by: PWShmLayout.phaseRecordsOffset + index * PWShmLayout.phaseBytes)
            writeU32(base, offset: PWShmLayout.phaseFirstSlotOffset, UInt32(phase.firstSlot))
            writeU32(base, offset: PWShmLayout.phaseEndSlotOffset, UInt32(phase.endSlot))
            writeU32(base, offset: PWShmLayout.phaseGlobalPhaseOffset, UInt32(phase.globalPhase ?? (index + 1)))
        }

        // ---- Populate slots.
        for (i, slot) in input.slots.enumerated() {
            let slotBase = rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes)
            writeString(slotBase, offset: PWShmLayout.slotStepIdOffset,
                        value: slot.stepId, max: PWShmLayout.stepIdMax)
            writeU32(slotBase, offset: PWShmLayout.slotAttemptKindOffset,
                     slot.attemptKind.rawValue)
            writeString(slotBase, offset: PWShmLayout.slotTargetOffset,
                        value: slot.target, max: PWShmLayout.targetMax)
            // Exec slots: argv[0] is target; args occupy argv[1..argv_count-1].
            // Other slots leave argv_count = 0 (host memset already zeroed
            // the table) so the worker's EXEC_SPAWN case sees a clean
            // argv_count == 0 → 1 fallback for kinds that aren't dispatched
            // here.
            if let operands = slot.extensionOperands {
                writeU32(slotBase, offset: PWShmLayout.slotExtFamilyOffset, operands.family)
                writeU32(slotBase, offset: PWShmLayout.slotExtAuthorityOffset, operands.authority)
                writeU32(slotBase, offset: PWShmLayout.slotExtTokenIndexOffset, operands.tokenIndex)
                writeU32(slotBase, offset: PWShmLayout.slotExtDeliveryIndexOffset, operands.deliveryIndex)
                writeU32(slotBase, offset: PWShmLayout.slotExtHandleIndexOffset, operands.handleIndex)
                writeU32(slotBase, offset: PWShmLayout.slotExtRecipientIndexOffset, operands.recipientIndex)
                writeU32(slotBase, offset: PWShmLayout.slotExtLastUseOffset, operands.lastUse ? 1 : 0)
                writeString(slotBase, offset: PWShmLayout.slotExtTargetOffset, value: operands.target, max: PWShmLayout.extTargetBytes)
            }
            if slot.attemptKind == .execSpawn {
                let argvCount = 1 + slot.args.count
                writeU32(slotBase, offset: PWShmLayout.slotArgvCountOffset, UInt32(argvCount))
                // Write argv[0] = target.
                let argvBase = slotBase.advanced(by: PWShmLayout.slotArgvOffset)
                writeString(argvBase, offset: 0,
                            value: slot.target, max: PWShmLayout.argvBytes)
                // Write argv[1..N] = args.
                for (j, arg) in slot.args.enumerated() {
                    writeString(argvBase,
                                offset: (j + 1) * PWShmLayout.argvBytes,
                                value: arg, max: PWShmLayout.argvBytes)
                }
            }
        }

        // ---- Populate params.
        for (i, p) in input.params.enumerated() {
            let paramBase = rawBase.advanced(by: PWShmLayout.paramsOffset + i * PWShmLayout.paramBytes)
            writeString(paramBase, offset: PWShmLayout.paramKeyOffset,
                        value: p.key, max: PWShmLayout.paramKeyMax)
            writeString(paramBase, offset: PWShmLayout.paramValueOffset,
                        value: p.value, max: PWShmLayout.paramValueMax)
        }

        // ---- Touch pages in the host mapping. The worker maps independently;
        // host touching does not prove its page residency or absence of faults.
        let pageSize: Int = {
            let v = sysconf(_SC_PAGESIZE)
            return v > 0 ? Int(v) : 4096
        }()
        var off = 0
        while off < PWShmLayout.regionBytes {
            let p = rawBase.advanced(by: off)
            p.pointee = p.pointee
            off += pageSize
        }
        let last = rawBase.advanced(by: PWShmLayout.regionBytes - 1)
        last.pointee = last.pointee

        // ---- Release-store prepared sentinel.
        storeRelease(rawBase, offset: PWShmLayout.preparedOffset, 1)

        // ---- Pipes.
        var readyPipe = [Int32](repeating: -1, count: 2)
        var policyPipe = [Int32](repeating: -1, count: 2)
        if pipe(&readyPipe) != 0 {
            failure = .pipeFailed("ready pipe: \(String(cString: strerror(errno)))"); return
        }
        if pipe(&policyPipe) != 0 {
            close(readyPipe[0]); close(readyPipe[1])
            failure = .pipeFailed("policy pipe: \(String(cString: strerror(errno)))"); return
        }
        // FD-scoped SIGPIPE suppression leaves process-wide signal handling intact.
        guard fcntl(policyPipe[1], F_SETNOSIGPIPE, 1) == 0 else {
            let error = errno
            close(readyPipe[0]); close(readyPipe[1]); close(policyPipe[0]); close(policyPipe[1])
            failure = .pipeFailed("F_SETNOSIGPIPE: \(String(cString: strerror(error)))"); return
        }
        let policyFlags = fcntl(policyPipe[1], F_GETFL, 0)
        guard policyFlags >= 0, fcntl(policyPipe[1], F_SETFL, policyFlags | O_NONBLOCK) == 0 else {
            let error = errno
            for fd in readyPipe + policyPipe { close(fd) }
            failure = .pipeFailed("policy O_NONBLOCK: \(String(cString: strerror(error)))"); return
        }
        // Original pipe descriptors close on exec; only the explicit dup2 targets
        // survive. An extra policy read end would keep a closed stdin pipe alive.
        for fd in readyPipe + policyPipe {
            guard fcntl(fd, F_SETFD, FD_CLOEXEC) == 0 else {
                let error = errno
                for opened in readyPipe + policyPipe { close(opened) }
                failure = .pipeFailed("FD_CLOEXEC: \(String(cString: strerror(error)))"); return
            }
        }

        // A high CLOEXEC duplicate avoids collisions with the evidence/ready dup2
        // destinations even when the session's original channel occupied FD 3/4/5.
        if let source = input.authorityFD {
            tokenFD = fcntl(source, F_DUPFD_CLOEXEC, 64)
            let duplicateErrno = errno
            input.authorityRecorder?.integer(6, "authority_duplicate", tokenFD, duplicateErrno)
            if tokenFD < 0 {
                for fd in readyPipe + policyPipe { close(fd) }
                failure = .shmSetupFailed("authority descriptor duplication failed"); return
            }
        }
        // Relocate all actor sources away from 0/3/4/5. Besides avoiding
        // collisions, this ensures every adddup2 is an actual duplication:
        // an already-CLOEXEC source at its destination must not disappear.
        var launchSources = [policyPipe[0], shmFD, readyPipe[1]]
        var relocated: [Int32] = []
        defer { for fd in relocated { close(fd) } }
        if input.actorMode != 0 {
            for source in launchSources {
                let fd = fcntl(source, F_DUPFD_CLOEXEC, 64)
                guard fd >= 0 else {
                    let error = errno
                    for opened in readyPipe + policyPipe { close(opened) }
                    failure = .spawnFailed("launch descriptor relocation: \(String(cString: strerror(error)))"); return
                }
                relocated.append(fd)
            }
            launchSources = relocated
        }
        // ---- posix_spawn.
        func spawnSetup(_ rc: Int32, _ operation: String) -> Bool {
            guard rc == 0 else {
                for fd in readyPipe + policyPipe { close(fd) }
                failure = .spawnFailed("\(operation): \(String(cString: strerror(rc)))")
                return false
            }
            return true
        }
        guard spawnSetup(posix_spawn_file_actions_init(&fileActions), "file actions init") else { return }
        actionsInitialized = true
        guard spawnSetup(posix_spawn_file_actions_adddup2(&fileActions, launchSources[0], 0), "policy dup2"),
              spawnSetup(posix_spawn_file_actions_adddup2(&fileActions, launchSources[1], 3), "evidence dup2"),
              spawnSetup(posix_spawn_file_actions_adddup2(&fileActions, launchSources[2], 4), "ready dup2") else { return }
        if tokenFD >= 0 {
            let dupRC = posix_spawn_file_actions_adddup2(&fileActions, tokenFD, 5)
            input.authorityRecorder?.record(7, "authority_spawn_dup2", dupRC == 0 ? "succeeded":"failed", kind:"error_code", rc:Int64(dupRC))
            guard spawnSetup(dupRC, "authority dup2") else { return }
        }
        // Actor form: defined standard streams and an empty environment. The
        // legacy form keeps its inherited streams and environment unchanged.
        guard spawnSetup(posix_spawnattr_init(&spawnAttributes), "attributes init") else { return }
        attributesInitialized = true
        if input.actorMode != 0 {
            guard spawnSetup(posix_spawn_file_actions_addopen(&fileActions, 1, "/dev/null", O_WRONLY, 0), "stdout open"),
                  spawnSetup(posix_spawn_file_actions_addopen(&fileActions, 2, "/dev/null", O_WRONLY, 0), "stderr open") else { return }
            guard spawnSetup(posix_spawnattr_setflags(&spawnAttributes, Int16(POSIX_SPAWN_CLOEXEC_DEFAULT)), "close-on-exec default") else { return }
        }

        let stepCountStr = String(input.slots.count)
        var argv: [String] = [
            "pw-probe-runner",
            "--shm-fd", "3",
            "--ready-fd", "4",
            "--step-count", stepCountStr,
        ]
        if tokenFD >= 0 { argv += ["--authority-fd", "5"] }
        if let hangMs = input.postApplyHangMs, hangMs > 0 {
            argv.append("--post-apply-hang-ms")
            argv.append(String(hangMs))
        }
        if let killSig = input.postApplyKillSignal, killSig > 0 {
            argv.append("--post-apply-kill-signal")
            argv.append(String(killSig))
        }
        if let preReadyMs = input.preReadyHangMs, preReadyMs > 0 {
            argv.append("--pre-ready-hang-ms")
            argv.append(String(preReadyMs))
        }
        if let slot = input.killBeforePublishSlot, slot >= 0 {
            argv.append("--kill-before-publish-slot")
            argv.append(String(slot))
        }
        if let deadlineMs = input.execChildDeadlineMs, deadlineMs > 0 {
            argv.append("--exec-child-deadline-ms")
            argv.append(String(deadlineMs))
        }
        if let waitMs = input.proceedWaitMs {
            argv += ["--proceed-wait-ms", String(waitMs)]
        }
        if let budgetMs = input.execAttemptBudgetMs {
            argv.append("--exec-attempt-budget-ms")
            argv.append(String(budgetMs))
        }
        var child: pid_t = 0
        let spawnRC = withCStringArrayCopy(argv) { argvPtr in
            withCStringArrayCopy([]) { emptyEnvironment in
                posix_spawn(&child, input.workerExecutablePath, &fileActions, &spawnAttributes, argvPtr,
                            input.actorMode != 0 ? emptyEnvironment : nil)
            }
        }
        for fd in relocated { close(fd) }
        relocated.removeAll()
        if spawnRC != 0 {
            close(policyPipe[0]); close(policyPipe[1])
            close(readyPipe[0]); close(readyPipe[1])
            failure = .spawnFailed("\(String(cString: strerror(spawnRC)))"); return
        }
        pid = child
        closeAuthorityDuplicate()
        spawned = true
        // The transfer calls (clock, write, poll) are one injection point: the
        // deadline and the writer share the supplied clock, and production keeps
        // the Darwin defaults.
        let transferBudgetMs = min(input.policyTransferTimeoutMs, setupRemainingMs?() ?? input.policyTransferTimeoutMs)
        let transferDeadline = MonotonicDeadline(milliseconds: transferBudgetMs, clock: transferCalls.clock)
        // The child now owns its evidence endpoint. Retain only our mapping, so
        // later validators cannot inherit the host's writable descriptor. Retire
        // close ownership first: a reused number must never reach deferred close.
        ownsShmFD = false
        close(shmFD)
        // Close parent-side ends that the child now owns.
        close(policyPipe[0])
        close(readyPipe[1])
        process = ChildProcessState(pid: pid, calls: processCalls)

        // ---- Deliver under one deadline established immediately after spawn. The
        // bytes are the array whose count the header already carries.
        let transfer = writePolicy(policyBytes, fd: policyPipe[1], deadline: transferDeadline, calls: transferCalls)
        close(policyPipe[1])
        switch transfer.stop {
        case .complete: break
        case .timeout(let elapsed):
            transferTimeout = PWWorkerPolicyTransferTimeout(budget_ms: transferBudgetMs,
                elapsed_ms: elapsed, bytes_written: transfer.written, bytes_expected: policyBytes.count)
            transferFailure = .policyTransferTimedOut("exceeded \(transferBudgetMs) ms; wrote \(transfer.written) of \(policyBytes.count) bytes")
        case .writeError(let error):
            transferError = PWWorkerPolicyTransferError(errno: error, bytes_written: transfer.written,
                bytes_expected: policyBytes.count)
            transferFailure = .policyWriteFailed("errno=\(error) (\(String(cString: strerror(error)))); wrote \(transfer.written) of \(policyBytes.count) bytes")
        case .failed(let diagnostic):
            transferFailure = .policyWriteFailed(diagnostic + "; wrote \(transfer.written) of \(policyBytes.count) bytes")
        }
        pollStopReason = transferFailure == nil ? "sentinel_deadline" : (transferTimeout == nil ? "policy_write_error" : "policy_transfer_deadline")

        // ---- Read pre-apply ready byte under its elapsed allowance. The wait
        // starts after policy transfer completed. The read end must be
        // nonblocking first: a blocking read would turn the allowance into an
        // unbounded wait, so a failed prerequisite is recorded and no wait runs.
        // Between reads the host waits for the pipe to become readable for at
        // most the smaller of 10 ms and the remaining allowance; readability,
        // hangup, interruption or timeout all lead to the next read.
        var readyByte: UInt8 = 0
        if transferFailure == nil {
            let readyBudgetMs = min(input.readyByteTimeoutMs, setupRemainingMs?() ?? input.readyByteTimeoutMs)
            let flags = fcntl(readyPipe[0], F_GETFL, 0)
            if flags < 0 || fcntl(readyPipe[0], F_SETFL, flags | O_NONBLOCK) < 0 {
                readyWait = PWHostWait(budget_ms: readyBudgetMs, elapsed_ms: 0, stop: "setup_failed",
                                       native_errno: errno, clock_fault: false)
            } else {
                var clock = HostWaitClock(milliseconds: readyBudgetMs, pollNs: 10_000_000, calls: processCalls)
                var stop = "deadline"
                var readErrno: Int32? = nil
                while true {
                    // The read precedes the clock: a byte that lands as the
                    // allowance runs out is received, not timed out.
                    let n = Darwin.read(readyPipe[0], &readyByte, 1)
                    if n == 1 { readyByteReceived = true; stop = "received"; break }
                    if n == 0 { stop = "eof"; break }     // EOF — worker exited without writing
                    if n < 0 && errno != EAGAIN && errno != EINTR { stop = "read_error"; readErrno = errno; break }
                    if clock.expiredAfterWaiting(readable: readyPipe[0]) { break }
                }
                readyWait = clock.record(stop: stop, nativeErrno: readErrno)
            }
        }
        close(readyPipe[0])
    }

    deinit { tearDown() }

    /// Release the host mapping, descriptors and spawn handles once. The
    /// child's own references keep their separate lifetimes.
    func tearDown() {
        if tornDown { return }
        tornDown = true
        if let base { _ = munmap(base, PWShmLayout.regionBytes) }
        base = nil
        if ownsShmFD && shmFD >= 0 { close(shmFD) }
        ownsShmFD = false
        closeAuthorityDuplicate()
        if actionsInitialized { posix_spawn_file_actions_destroy(&fileActions); actionsInitialized = false }
        if attributesInitialized { posix_spawnattr_destroy(&spawnAttributes); attributesInitialized = false }
    }

    private func closeAuthorityDuplicate() {
        if tokenFD >= 0 {
            let fd=tokenFD; tokenFD = -1
            let rc=close(fd), saved=errno
            input.authorityRecorder?.integer(8,"close_launch_duplicate",rc,saved,cleanup:true)
        }
    }

    // MARK: - Publication primitives

    func phaseBase(_ index: Int) -> UnsafeMutablePointer<UInt8> {
        rawBase.advanced(by: PWShmLayout.phaseRecordsOffset + index * PWShmLayout.phaseBytes)
    }
    var appliedObserved: Bool { loadAcquire(rawBase, offset: PWShmLayout.appliedOffset) == 1 }
    var doneObserved: Bool { loadAcquire(rawBase, offset: PWShmLayout.doneOffset) != 0 }
    var applyRCIsZero: Bool { readI32(rawBase, offset: PWShmLayout.applyRcOffset) == 0 }
    var identityMatches: Bool { workerIdentityMatches(rawBase) }
    /// The worker's setup publication: 1 applied, 2 unapplied declared, 0 none.
    var actorSetup: UInt32 { loadAcquire(rawBase, offset: PWShmLayout.actorSetupOffset) }
    var authoritySetupObservation: PWRunnerAuthorityScope { decodeAuthoritySetup(rawBase, actor: Int(input.actorIndex), required: input.authorityRequired) }
    var authorityStatus: UInt32 { authoritySetupObservation.publication == "observed" ? UInt32(bitPattern: readI32(rawBase, offset: PWShmLayout.authorityStatusOffset)) : 0 }
    var authorityDetail: UInt32 { authoritySetupObservation.publication == "observed" ? UInt32(bitPattern: readI32(rawBase, offset: PWShmLayout.authorityDetailOffset)) : 0 }
    var activationObserved: UInt32 { loadAcquire(rawBase, offset: PWShmLayout.activationObservedOffset) }
    /// Slots this worker has published as completed; an acquire sample.
    var completedSlotCount: Int {
        (0..<input.slots.count).filter { i in
            loadAcquire(rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes),
                        offset: PWShmLayout.slotCompletedOffset) == 1
        }.count
    }
    func arrived(_ index: Int) -> Bool { loadAcquire(phaseBase(index), offset: PWShmLayout.phaseArrivedOffset) == 1 }
    func acknowledged(_ index: Int) -> Bool { loadAcquire(phaseBase(index), offset: PWShmLayout.phaseAcknowledgedOffset) == 1 }
    func completed(_ index: Int) -> Bool { loadAcquire(phaseBase(index), offset: PWShmLayout.phaseCompletedOffset) == 1 }

    /// Ownership through acknowledgement: a release this host stored followed
    /// by the worker's acknowledgement while no wait on this child failed.
    func observeAcknowledgement() {
        for index in input.phases.indices {
            let base = phaseBase(index)
            let ack = loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset)
            if ownershipUnbroken && phaseOutputs[index].releaseSet && ack == 1 {
                phaseOutputs[index].ownershipEstablished = true
            }
        }
    }

    func checkPrematurePublication(_ index: Int) {
        let base = phaseBase(index)
        let ordinal = loadAcquire(rawBase, offset: PWShmLayout.proceedObservedOffset)
        let ack = loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset)
        let progress = loadAcquire(rawBase.advanced(by: PWShmLayout.evidenceOffset), offset: PWShmLayout.evidenceProgressOffset)
        let progressIndex = Int(progress & 0xfffff) - 1
        let completed = (input.phases[index].firstSlot..<input.slots.count).contains { i in
            loadAcquire(rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes),
                        offset: PWShmLayout.slotCompletedOffset) == 1
        }
        if ack != 0 || ordinal > UInt32(index) { phaseOutputs[index].violations.append("acknowledgement_before_release") }
        if completed || (progress >> 24 == 9 && progressIndex >= input.phases[index].firstSlot) {
            phaseOutputs[index].violations.append("attempt_before_release")
        }
    }

    /// Release visit `index` with the host's ordinal store. The ordinal seam
    /// is internal test equipment; production releases index + 1.
    func releaseVisit(_ index: Int) {
        let ordinal = input.phaseReleaseOrdinal?(index) ?? UInt32(index + 1)
        storeRelease(rawBase, offset: PWShmLayout.proceedOffset, ordinal)
        phaseOutputs[index].releaseSet = ordinal == UInt32(index + 1)
        if ordinal != UInt32(index + 1) { phaseOutputs[index].violations.append("wrong_release_ordinal") }
    }

    /// Actor form: name the global phase that activates this actor's next visit.
    @discardableResult
    func activate(globalPhase: UInt32) -> PWRunnerActorActivation {
        let ordinal=process.nextCaptureOrdinal()
        storeRelease(rawBase, offset: PWShmLayout.activationOffset, globalPhase)
        return PWRunnerActorActivation(capture_ordinal:ordinal,observed_ns:process.calls.clock())
    }

    /// One nonblocking wait on the child; a failed wait breaks ownership.
    func waitChild(stage: String) -> ChildWaitObservation {
        let observation = process.wait(options: WNOHANG, stage: stage)
        if observation == .failed { ownershipUnbroken = false }
        return observation
    }

    // MARK: - Cleanup

    func requestExit() {
        process.departureRequested = true
        storeRelease(rawBase, offset: PWShmLayout.exitRequestedOffset, 1)
        exitRequested = true
    }

    /// Grace, termination and the post-reap acknowledgement reconciliation.
    /// How the grace wait ended is recorded directly, never inferred later.
    func finishCleanup() {
        if process.status == nil && !process.childUnavailable {
            var clock = HostWaitClock(milliseconds: input.exitGraceMs, pollNs: 10_000_000, calls: calls)
            graceEnd = "exhausted"
            grace: while true {
                observeAcknowledgement()
                switch process.wait(options: WNOHANG, stage: "exit_grace") {
                case .reaped:
                    graceEnd = "reaped_during_grace"
                    break grace
                case .failed:
                    graceEnd = "wait_error"
                    ownershipUnbroken = false
                    break grace
                case .pending:
                    break
                }
                if clock.expiredAfterSleeping() { break }
            }
            graceWait = clock.record(stop: graceEnd)
            observeAcknowledgement()
            let errorsBeforeTermination = process.waitErrors.count
            process.terminate()
            if process.waitErrors.count > errorsBeforeTermination { ownershipUnbroken = false }
        }
        // Acknowledgement may follow the last polling/grace sample and precede
        // reap, including a fatal exit without done. Unbroken ownership through
        // that publication establishes the phase's historical lifetime; the
        // existing predicate cannot repair ownership lost before acknowledgement.
        if process.status != nil { observeAcknowledgement() }
    }

    // MARK: - Output

    /// The final acquire snapshot after cleanup. Publications are immutable, so
    /// this also safely retains results if cleanup failed and the child is still
    /// alive. Never rewrites pollStopReason.
    func collectOutput() -> CWorkerOutput {
        let cleanupTrigger = PWDisposition.triggerForStop[pollStopReason] ?? pollStopReason
        // Collection basis: whether every read below follows a successful reap. A
        // reap observed later cannot upgrade it.
        let collectionBasis = process.status != nil ? "after_confirmed_reap" : "execution_may_continue"
        let sawApplied = loadAcquire(rawBase, offset: PWShmLayout.appliedOffset) == 1
        let sawDone = loadAcquire(rawBase, offset: PWShmLayout.doneOffset) == 1
        for index in input.phases.indices {
            let base = phaseBase(index)
            phaseOutputs[index].arrived = loadAcquire(base, offset: PWShmLayout.phaseArrivedOffset) == 1
            phaseOutputs[index].acknowledged = loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset) == 1
            phaseOutputs[index].completed = loadAcquire(base, offset: PWShmLayout.phaseCompletedOffset) == 1
        }
        let finalProceedObserved = phaseOutputs.allSatisfy { $0.acknowledged }
        let workerEvidence=decodeWorkerEvidence(rawBase)
        let nativeApplyFailure=workerEvidence?.failure_state == "published" && workerEvidence?.failure?.operation == 8
            && workerEvidence?.failure?.code == 1 && workerEvidence?.failure?.native_kind == 1 ? workerEvidence?.failure:nil
        let applyRC = sawApplied ? readI32(rawBase, offset:PWShmLayout.applyRcOffset) : nativeApplyFailure?.native_result ?? 0
        let applyErrno = nativeApplyFailure?.errno ?? 0

        // Slot payloads are immutable after release publication. Read only confirmed slots.
        var slotResults: [CWorkerSlotResult] = []
        slotResults.reserveCapacity(input.slots.count)
        for i in 0..<input.slots.count {
            let slotBase = rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes)
            let completed = loadAcquire(slotBase, offset: PWShmLayout.slotCompletedOffset)
            if completed != 1 {
                slotResults.append(CWorkerSlotResult(callBoundary: loadAcquire(slotBase, offset: PWShmLayout.slotCallBoundaryOffset) == 1, stepId: input.slots[i].stepId,
                    rc: 0, errnoVal: 0, completed: false))
                continue
            }
            let stepId = readString(slotBase, offset: PWShmLayout.slotStepIdOffset,
                                    max: PWShmLayout.stepIdMax)
            let rc = readI32(slotBase, offset: PWShmLayout.slotRcOffset)
            let errnoVal = readI32(slotBase, offset: PWShmLayout.slotErrnoValOffset)
            let observedRaw = readString(slotBase, offset: PWShmLayout.slotObservedPathOffset,
                                         max: PWShmLayout.observedPathMax)
            let errorRaw = readString(slotBase, offset: PWShmLayout.slotErrorOffset,
                                      max: PWShmLayout.errorMax)

            // Exec output fields. Only read when the input slot was exec
            // (we trust input.slots[i].attemptKind here because the host
            // wrote the slot's attempt_kind field with that value;
            // re-reading the shm field would just round-trip the same
            // value). Non-exec slots leave these nil so the orchestrator's
            // `childPid != nil` branch works.
            let isExec = input.slots[i].attemptKind == .execSpawn
            let childPid:        Int32? = isExec ? readI32(slotBase, offset: PWShmLayout.slotChildPidOffset)        : nil
            let childExitCode:   Int32? = isExec ? readI32(slotBase, offset: PWShmLayout.slotChildExitCodeOffset)   : nil
            let childTermSignal: Int32? = isExec ? readI32(slotBase, offset: PWShmLayout.slotChildTermSignalOffset) : nil
            let childStdout: String? = isExec ? readString(slotBase, offset: PWShmLayout.slotChildStdoutOffset,
                                                           max: PWShmLayout.childOutputBytes) : nil
            let childStderr: String? = isExec ? readString(slotBase, offset: PWShmLayout.slotChildStderrOffset,
                                                           max: PWShmLayout.childOutputBytes) : nil

            let execAccount = isExec ? decodeExecObservation(slotBase, childPid: childPid ?? 0) : (nil, nil)
            let extensionKind = [.extensionConsume, .extensionRelease, .extensionIssue, .extensionTransfer].contains(input.slots[i].attemptKind)

            slotResults.append(CWorkerSlotResult(
                callBoundary: loadAcquire(slotBase, offset: PWShmLayout.slotCallBoundaryOffset) == 1,
                nativeResult: readI32(slotBase, offset: PWShmLayout.slotNativeResultValidOffset) == 1 ? readI64(slotBase, offset: PWShmLayout.slotNativeResultOffset) : nil,
                nativeErrno: readI32(slotBase, offset: PWShmLayout.slotNativeResultValidOffset) == 1 ? readI32(slotBase, offset: PWShmLayout.slotNativeErrnoOffset) : nil,
                unavailableCode: extensionKind ? UInt32(bitPattern: readI32(slotBase, offset: PWShmLayout.slotUnavailableCodeOffset)) : nil,
                extensionPublication: input.slots[i].extensionOperands == nil ? nil : CWorkerExtensionPublication(
                    tokenLength: UInt32(bitPattern: readI32(slotBase, offset: PWShmLayout.slotExtTokenLengthOffset)),
                    custodyStatus: UInt32(bitPattern: readI32(slotBase, offset: PWShmLayout.slotExtCustodyStatusOffset)),
                    transferStatus: UInt32(bitPattern: readI32(slotBase, offset: PWShmLayout.slotExtTransferStatusOffset))),
                freshRead: input.slots[i].attemptKind == .fileReadFresh ? decodeFreshRead(slotBase) : nil,
                freshWrite: [.fileWriteFresh, .fileCreateFresh].contains(input.slots[i].attemptKind) ? decodeFreshWrite(slotBase) : nil,
                execObservation: execAccount.0, execObservationProblem: execAccount.1,
                stepId: stepId,
                rc: rc,
                errnoVal: errnoVal,
                observedPath: observedRaw.isEmpty ? nil : observedRaw,
                error: errorRaw.isEmpty ? nil : errorRaw,
                completed: completed != 0,
                childPid: childPid,
                childExitCode: childExitCode,
                childTermSignal: childTermSignal,
                childStdout: (childStdout?.isEmpty ?? true) ? nil : childStdout,
                childStderr: (childStderr?.isEmpty ?? true) ? nil : childStderr
            ))
        }

        let exitCode: Int32?
        let termSignal: Int32?
        if let status = process.status, (status & 0x7f) == 0 {
            exitCode = (status >> 8) & 0xff
            termSignal = nil
        } else if let status = process.status, (((status & 0x7f) + 1) >> 1 > 0) {
            exitCode = nil
            termSignal = status & 0x7f
        } else {
            exitCode = nil
            termSignal = nil
        }

        var policyReceived: String? = nil
        if loadAcquire(rawBase, offset: PWShmLayout.policyHashPublishedOffset) == 1 {
            policyReceived = Data(bytes: rawBase.advanced(by: PWShmLayout.policyReceivedSha256Offset), count: 32)
                .map { String(format: "%02x", $0) }.joined()
        }

        return CWorkerOutput(
            workerPid: pid,
            readyByteReceived: readyByteReceived,
            applied: sawApplied,
            applyRC: applyRC,
            applyErrno: applyErrno,
            done: sawDone,
            exitCode: exitCode,
            termSignal: termSignal,
            slots: slotResults,
            profileCapture: input.captureCompiledProfile ? decodeProfileCapture(
                rawBase.advanced(by: PWShmLayout.captureOffset), workerPid: pid,
                applied: sawApplied, applyRC: applyRC, done: sawDone,
                exitCode: exitCode, termSignal: termSignal, source: input.policy, params: input.params,
                nonce: input.captureNonce) : nil,
            pollStopReason: pollStopReason,
            exitRequested: exitRequested,
            terminationRequest: process.terminationRequest,
            reaped: process.status != nil,
            waitErrors: process.waitErrors,
            workerEvidence: decodeWorkerEvidence(rawBase),
            policyTransferTimeout: transferTimeout,
            policyTransferError: transferError,
            phases: phaseOutputs,
            hookInvoked: phaseOutputs.allSatisfy { $0.collectionClosed },
            proceedSet: phaseOutputs.allSatisfy { $0.releaseSet },
            proceedObserved: finalProceedObserved,
            proceedOwnershipEstablished: phaseOutputs.allSatisfy { $0.ownershipEstablished },
            orderingProtocolViolations: Array(Set(phaseOutputs.flatMap { $0.violations })).sorted(),
            cleanupTrigger: cleanupTrigger,
            graceEnd: graceEnd,
            collectionBasis: collectionBasis,
            readyWait: readyWait,
            sentinelWait: sentinelWait,
            graceWait: graceWait,
            actorSetup: actorSetup,
            activationObserved: activationObserved,
            policyReceivedSha256: policyReceived,
            authorityStatus: authorityStatus,
            authorityDetail: authorityDetail,
            nativeSymbols: authoritySetupObservation.publication == "observed" ? UInt32(bitPattern: readI32(rawBase, offset: PWShmLayout.nativeSymbolsOffset)) : 0,
            authoritySetup: input.actorMode == 0 ? nil : authoritySetupObservation,
            ownedReap: process.ownedReap
        )
    }
}

// MARK: - Layout helpers shared with the legacy driver

func writeU64(_ base: UnsafeMutablePointer<UInt8>, offset: Int, _ value: UInt64) {
    base.advanced(by: offset).withMemoryRebound(to: UInt64.self, capacity: 1) { p in
        p.pointee = value
    }
}

func storeRelease(_ base: UnsafeMutablePointer<UInt8>, offset: Int, _ value: UInt32) {
    base.advanced(by: offset).withMemoryRebound(to: UInt32.self, capacity: 1) { p in
        pw_cworker_store_release_u32(p, value)
    }
}

/// Copies `value` (UTF-8) into `base[offset..offset+max-1]`, NUL-terminating
/// at `offset + n` where `n = min(value.utf8.count, max - 1)`. Validation
/// happens earlier; this is a tight memcpy.
func writeString(_ base: UnsafeMutablePointer<UInt8>, offset: Int,
                 value: String, max: Int) {
    let bytes = Array(value.utf8)
    let n = Swift.min(bytes.count, max - 1)
    let dst = base.advanced(by: offset)
    bytes.withUnsafeBufferPointer { buf in
        if let src = buf.baseAddress, n > 0 {
            memcpy(UnsafeMutableRawPointer(dst), src, n)
        }
    }
    dst.advanced(by: n).pointee = 0
}

/// Reads a NUL-bounded UTF-8 string from `base[offset..offset+max]`.
/// Stops at the first NUL or at `max`, whichever comes first.
func readString(_ base: UnsafePointer<UInt8>, offset: Int, max: Int) -> String {
    let start = base.advanced(by: offset)
    var len = 0
    while len < max && start.advanced(by: len).pointee != 0 {
        len += 1
    }
    let data = Data(bytes: start, count: len)
    return String(data: data, encoding: .utf8) ?? ""
}
