// Test instrumentation compiled only into a disposable source copy.
import Darwin
import Foundation
@_silgen_name("pw_descriptor_unmap")
func descriptorUnmap(_ address: UnsafeMutableRawPointer, _ length: Int) -> Int32
@_silgen_name("pw_descriptor_map_word")
func descriptorMapWord(_ index: Int32) -> Int64
@_silgen_name("pw_descriptor_map_acquired")
func descriptorMapAcquired(_ address: UnsafeMutableRawPointer, _ length: Int)
var probeVariant = ""
var probeMode = ""
var originalFD: Int32 = -1
var retainedBase: UnsafeMutableRawPointer?
var decoyFD: Int32 = -1
var decoyBase: UnsafeMutableRawPointer?
var sentinelFD: Int32 = -1
var events: [[String: Any]] = []
var pipeCount = 0
var spawned = false
let challengeOffset = PWShmLayout.headerBytes + (PWShmLayout.maxSteps - 1) * PWShmLayout.slotBytes
func event(_ name: String, _ values: [String: Any] = [:]) { var row = values; row["event"] = name; events.append(row) }
func probeShm(_ name: UnsafePointer<CChar>, _ mode: mode_t) -> Int32 {
    let fd = pw_cworker_shm_open_create(name, mode); originalFD = fd; event("create", ["fd": fd]); return fd
}
func probeClose(_ fd: Int32) -> Int32 {
    let rc = Darwin.close(fd); event("evidence_close", ["fd": fd, "rc": rc, "errno": rc < 0 ? errno : 0]); return rc
}
func probeFault(_ name: String) -> Bool {
    guard probeMode == name else { return false }
    event("injected", ["point": name]); errno = EIO; return true
}
func probeTruncate(_ fd: Int32, _ length: off_t) -> Int32 {
    if probeFault("truncate_failure") { return -1 }
    return Darwin.ftruncate(fd, length)
}
func probeMap(_ address: UnsafeMutableRawPointer?, _ length: Int, _ protection: Int32,
              _ flags: Int32, _ fd: Int32, _ offset: off_t) -> UnsafeMutableRawPointer? {
    if probeFault("mmap_nil") { return nil }
    if probeFault("mmap_failed") { return MAP_FAILED }
    let result = Darwin.mmap(address, length, protection, flags, fd, offset)
    if let result, result != MAP_FAILED { descriptorMapAcquired(result, length) }
    return result
}
func probePipe(_ fds: UnsafeMutablePointer<Int32>) -> Int32 {
    pipeCount += 1
    if probeFault("pipe_\(pipeCount)") { return -1 }
    return Darwin.pipe(fds)
}
func probeFcntl(_ fd: Int32, _ command: Int32, _ value: Int32) -> Int32 {
    if command == F_SETNOSIGPIPE && probeFault("nosigpipe") { return -1 }
    if command == F_DUPFD_CLOEXEC && probeFault("extension_dup") { return -1 }
    if command == F_GETFL && !spawned && probeFault("get_flags") { return -1 }
    if command == F_SETFL && !spawned && probeFault("nonblock") { return -1 }
    if command == F_SETFD && value == FD_CLOEXEC && probeFault("pipe_cloexec") { return -1 }
    return Darwin.fcntl(fd, command, value)
}
func probePrepared(_ base: UnsafeMutableRawPointer) {
    retainedBase = base
    let name = "/pwd_\(getpid())"
    let raw = name.withCString { pw_cworker_shm_open_create($0, 0o600) }
    precondition(raw >= 0)
    _ = name.withCString { shm_unlink($0) }
    decoyFD = fcntl(raw, F_DUPFD, 128); close(raw)
    precondition(decoyFD >= 128 && decoyFD < 256 && fcntl(decoyFD, F_SETFD, 0) == 0)
    precondition(ftruncate(decoyFD, off_t(PWShmLayout.regionBytes)) == 0)
    decoyBase = mmap(nil, PWShmLayout.regionBytes, PROT_READ | PROT_WRITE, MAP_SHARED, decoyFD, 0)
    precondition(decoyBase != nil && decoyBase != MAP_FAILED)
    memcpy(decoyBase!, base, PWShmLayout.regionBytes)
    event("decoy", ["fd": decoyFD])
}
func probeChildSpawned(_ pid: pid_t) {
    spawned = true
    let owner: [String: Any] = ["host_pid": getpid(), "worker_pid": pid, "process_group": getpgrp()]
    try! JSONSerialization.data(withJSONObject: owner, options: [.sortedKeys]).write(to: URL(fileURLWithPath: "child-owner.json"))
}
func probeAfterSpawn(_ ownsFD: Bool) {
    event("after_spawn", ["owns_fd": ownsFD, "original_open": fcntl(originalFD, F_GETFD) >= 0])
    if fcntl(originalFD, F_GETFD) == -1 && errno == EBADF {
        sentinelFD = open("/dev/null", O_RDWR | O_CLOEXEC)
        precondition(sentinelFD == originalFD, "must force reuse of the exact released number")
        event("reused", ["fd": sentinelFD])
    }
}
func runProbe(_ observer: String, _ variant: String, _ mode: String) throws {
    probeVariant = variant; probeMode = mode
    precondition(256 * MemoryLayout<UInt32>.size <= PWShmLayout.slotBytes)
    precondition(challengeOffset + PWShmLayout.slotBytes <= PWShmLayout.paramsOffset)
    // Each invocation is a fresh process. Reserve 3..15 for an alias-bearing
    // launch, or clear unused low descriptors to exercise shmFD == 3.
    for fd: Int32 in 3..<64 { close(fd) }
    if mode != "self" {
        while true { let fd = open("/dev/null", O_RDWR | O_CLOEXEC); precondition(fd >= 0); if fd >= 16 { close(fd); break } }
    }
    var input = CWorkerInput(workerExecutablePath: mode == "spawn_failure" ? "/does/not/exist" : observer,
        policy: "(version 1)(allow default)", slots: [], readyByteTimeoutMs: 1000,
        sentinelTimeoutMs: 5000, exitGraceMs: 500)
    var validator: [String: Any] = [:]
    var readbacks: [[String: Any]] = []
    if mode == "extension_delivery" || mode == "extension_dup" {
        // A real descriptor with distinct file identity exercises the existing
        // high duplication and fd5 delivery. extensionRequested stays false;
        // no native issuance/consumption claim follows from this control.
        let fd = open(observer, O_RDONLY | O_CLOEXEC); precondition(fd >= 0)
        input.extensionFD = fd
    }
    let result = runCWorker(input, processCalls: ChildProcessCalls(), phaseBoundary: { pid, _ in
        precondition(retainedBase != nil && decoyBase != nil)
        // Exact byte-for-byte decoy at validator launch, including live header.
        memcpy(decoyBase!, retainedBase!, PWShmLayout.regionBytes)
        let v = runValidator(ValidatorClientInput(executablePath: observer, targetPid: pid, probes: [], verdictReadTimeoutMs: 2000, exitGraceMs: 500))
        switch v {
        case .success(let o): validator = ["pid": o.validatorPid, "reaped": o.reaped == true, "exit_code": o.exitCode ?? -999]
        case .failure(let e, let p): validator = ["error": String(describing: e), "reaped": p?.reaped == true]
        }
        let report = try! JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: "validator.json"))) as! [String: Any]
        for candidate in report["fds"] as! [[String: Any]] where candidate["mapped"] as! Int == 1 {
            let fd = candidate["fd"] as! Int; let token = (candidate["token"] as! NSNumber).uint32Value
            precondition(fd >= 0 && fd < 256)
            let offset = challengeOffset + 4 * fd
            precondition(offset >= challengeOffset && offset + 4 <= challengeOffset + PWShmLayout.slotBytes)
            let actual = loadAcquire(retainedBase!.assumingMemoryBound(to: UInt8.self), offset: offset)
            let decoy = loadAcquire(decoyBase!.assumingMemoryBound(to: UInt8.self), offset: offset)
            readbacks.append(["fd": fd, "token": token, "host_value": actual, "decoy_value": decoy,
                "same_host_object": token != 0 && actual == token, "same_decoy_object": token != 0 && decoy == token])
        }
    })
    var worker: [String: Any]
    switch result {
    case .success(let o): worker = ["pid": o.workerPid, "reaped": o.reaped == true, "exit_code": o.exitCode ?? -999,
        "done": o.done, "applied": o.applied, "acknowledged": o.proceedObserved, "ownership": o.proceedOwnershipEstablished]
    case .failure(let e, let partial):
        worker = ["error": String(describing: e)]
        if let o = partial {
            worker["pid"] = o.workerPid; worker["reaped"] = o.reaped == true
            worker["exit_code"] = o.exitCode ?? -999; worker["term_signal"] = o.termSignal ?? -999
            worker["applied"] = o.applied; worker["done"] = o.done
        }
    }
    if let pid = worker["pid"] as? pid_t, pid > 0 {
        var status: Int32 = 0
        let rc = waitpid(pid, &status, WNOHANG); let observedErrno = errno
        worker["independent_wait_rc"] = rc; worker["independent_wait_errno"] = rc < 0 ? observedErrno : 0
        worker["independently_confirmed_host_reap"] = rc == -1 && observedErrno == ECHILD
        if rc == 0 {
            let k = kill(pid, SIGKILL); let w = waitpid(pid, &status, 0)
            worker["fixture_kill_rc"] = k; worker["fixture_wait_rc"] = w
        }
    }
    let sentinelOpen = sentinelFD >= 0 && fcntl(sentinelFD, F_GETFD) >= 0
    let originalOpen = originalFD >= 0 && fcntl(originalFD, F_GETFD) >= 0
    let receipt: [String: Any] = ["mode": mode, "variant": variant, "host_pid": getpid(), "events": events, "original_fd": originalFD, "decoy_fd": decoyFD,
        "sentinel_fd": sentinelFD, "sentinel_open_after_return": sentinelOpen,
        "original_open_after_return": originalOpen, "worker": worker, "validator": validator, "readbacks": readbacks,
        "mapping": (0..<11).map { descriptorMapWord(Int32($0)) }]
    if sentinelOpen { close(sentinelFD) }
    if let fd = input.extensionFD { close(fd) }
    if let p = decoyBase { munmap(p, PWShmLayout.regionBytes) }
    if decoyFD >= 0 { close(decoyFD) }
    try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys]).write(to: URL(fileURLWithPath: "receipt.json"))
}
