import Darwin
import Foundation

// The authority-bearing mapping is separate from the worker's evidence mapping.
// Only this owner passes its descriptor; neither the reply nor diagnostics read
// the token bytes. Issuer exit/reaping precedes delivery to a worker.
final class ExtensionSession {
    static let tokenBytes = 16384
    static let pathBytes = 1024
    static let channelBytes = 17472
    static let issuerWaitMs = 5000
    static let tokenOffset = 1088
    private(set) var descriptor: Int32 = -1
    private var mapping: UnsafeMutableRawPointer?
    var record: PWRunnerExtensionRecord
    var capabilityUnavailable = false

    init(declaration: PWRunnerExtensionDeclaration, executable: String,
         processCalls: ChildProcessCalls = ChildProcessCalls()) {
        record = PWRunnerExtensionRecord(token_ref: declaration.token_ref, submitted_target: declaration.target)
        guard FileManager.default.isExecutableFile(atPath: executable) else {
            capabilityUnavailable = true; record.issuance_status = "issuer_unavailable"; return
        }
        var resolved = [CChar](repeating: 0, count: Self.pathBytes)
        let pathResult = declaration.target.withCString { realpath($0, &resolved) }
        let pathErrno = errno
        guard pathResult != nil else {
            record.preparation_status = "resolution_failed"; record.preparation_errno = pathErrno; return
        }
        let target = String(cString: resolved)
        record.resolved_target = target
        var metadata = stat()
        let statRC = target.withCString { fstatat(AT_FDCWD, $0, &metadata, 0) }
        let statErrno = errno
        guard statRC == 0 else {
            record.preparation_status = "metadata_failed"; record.preparation_errno = statErrno; return
        }
        record.identity = PWFileIdentity(device: UInt64(UInt32(bitPattern: metadata.st_dev)),
            inode: UInt64(metadata.st_ino), mode: UInt32(metadata.st_mode), uid: metadata.st_uid, gid: metadata.st_gid)
        record.preparation_status = "prepared"
        let name = "/pwx_" + UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(24)
        let fd = name.withCString { pw_cworker_shm_open_create($0, 0o600) }
        guard fd >= 0 else { record.issuance_status = "channel_setup_failed"; return }
        _ = name.withCString { shm_unlink($0) }
        descriptor = fd
        guard fcntl(fd, F_SETFD, FD_CLOEXEC) == 0, ftruncate(fd, off_t(Self.channelBytes)) == 0,
              let base = mmap(nil, Self.channelBytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0), base != MAP_FAILED else {
            record.issuance_status = "channel_setup_failed"; return
        }
        mapping = base
        memset(base, 0, Self.channelBytes)
        let bytes = base.assumingMemoryBound(to: UInt8.self)
        writeU32(bytes, offset: 0, 0x50574558)
        _ = resolved.withUnsafeBytes { memcpy(bytes.advanced(by: 64), $0.baseAddress!, Self.pathBytes) }
        // dup2(fd, fd) preserves FD_CLOEXEC; always use a distinct source.
        let spawnFD = fcntl(fd, F_DUPFD_CLOEXEC, 64)
        guard spawnFD >= 0 else { record.issuance_status = "channel_setup_failed"; return }
        defer { close(spawnFD) }
        var actions: posix_spawn_file_actions_t?
        posix_spawn_file_actions_init(&actions)
        defer { posix_spawn_file_actions_destroy(&actions) }
        // CLOEXEC_DEFAULT closes every descriptor except these explicit actions.
        // The dup precedes stdio opens in case the mapping occupied a low FD.
        var setup = posix_spawn_file_actions_adddup2(&actions, spawnFD, 3)
        for number: Int32 in [0, 1, 2] {
            let rc = posix_spawn_file_actions_addopen(&actions, number, "/dev/null", O_RDWR, 0)
            if setup == 0 { setup = rc }
        }
        var attributes: posix_spawnattr_t?
        posix_spawnattr_init(&attributes)
        defer { posix_spawnattr_destroy(&attributes) }
        let flagRC = posix_spawnattr_setflags(&attributes, Int16(POSIX_SPAWN_CLOEXEC_DEFAULT))
        if setup == 0 { setup = flagRC }
        var pid: pid_t = 0
        let rc: Int32 = setup != 0 ? setup : withCStringArrayCopy(["pw-extension-issuer"]) { argv in
            posix_spawn(&pid, executable, &actions, &attributes, argv, nil)
        }
        var issuer = PWRunnerIssuer(executable_path: executable)
        guard rc == 0 else {
            issuer.spawn_failure = PWRunnerSpawnFailure(executable_path: executable, return_code: rc,
                diagnostic: "issuer launch failed")
            record.issuer = issuer; record.issuance_status = "spawn_failed"; return
        }
        issuer.pid = pid
        var child = ChildProcessState(pid: pid, calls: processCalls)
        let deadline = MonotonicDeadline(milliseconds: Self.issuerWaitMs)
        var stop = "deadline"
        while let sample = deadline.sample(), sample.remaining > 0 {
            switch child.wait(options: WNOHANG, stage: "issuer_wait") {
            case .reaped: stop = "reaped"
            case .failed: stop = "wait_error"
            case .pending: usleep(1000); continue
            }
            break
        }
        if child.status == nil { child.terminate() }
        issuer.reaped = child.status != nil
        issuer.wait_errors = child.waitErrors
        issuer.termination_request = child.terminationRequest
        if let status = child.status {
            if (status & 0x7f) == 0 { issuer.exit_code = (status >> 8) & 0xff }
            else { issuer.term_signal = status & 0x7f }
        }
        issuer.call_boundary_observed = loadAcquire(bytes, offset: 4) == 1
        let published = loadAcquire(bytes, offset: 8) == 1
        issuer.result_published = published
        record.issuance_status = stop == "deadline" ? "issuer_timeout" : stop == "wait_error" ? "issuer_wait_error" : "issuer_result_missing"
        if published {
            let state = UInt32(bitPattern: readI32(bytes, offset: 12))
            issuer.uid = UInt32(bitPattern: readI32(bytes, offset: 28))
            issuer.euid = UInt32(bitPattern: readI32(bytes, offset: 32))
            issuer.gid = UInt32(bitPattern: readI32(bytes, offset: 36))
            issuer.egid = UInt32(bitPattern: readI32(bytes, offset: 40))
            if [1, 2, 3].contains(state) {
                issuer.native_nonnull = state != 2
                issuer.errno = readI32(bytes, offset: 16)
            }
            let length = UInt32(bitPattern: readI32(bytes, offset: 20))
            if state == 1 { issuer.token_length = length }
            if state == 4 { capabilityUnavailable = true; record.issuance_status = "native_api_unavailable" }
            else if state == 2 { record.issuance_status = "native_refusal" }
            else if state == 3 { record.issuance_status = "token_oversized" }
            else if state != 1 || !issuer.call_boundary_observed || readI32(bytes, offset: 24) != pid
                        || length == 0 || length >= Self.tokenBytes {
                record.issuance_status = "invalid_transport"
            } else if child.status != nil && issuer.exit_code == 0 && stop == "reaped" {
                record.issuance_status = "issued"
            }
        }
        record.issuer = issuer
        // No delivery after unconfirmed cleanup, abnormal exit, malformed or
        // incomplete publication. Clearing the publication prevents consumption.
        if record.issuance_status != "issued" { pw_cworker_store_release_u32(bytes.advanced(by: 8).withMemoryRebound(to: UInt32.self, capacity: 1) { $0 }, 0) }
    }

    var deliveryDescriptor: Int32? { record.issuance_status == "issued" ? descriptor : nil }
    func erase() {
        if let mapping { pw_extension_clear(mapping, Self.channelBytes); record.host_buffer_erased = true }
    }
    deinit {
        erase()
        if let mapping { munmap(mapping, Self.channelBytes) }
        if descriptor >= 0 { close(descriptor) }
    }
}

@_silgen_name("pw_extension_clear")
private func pw_extension_clear(_ bytes: UnsafeMutableRawPointer, _ length: Int)
