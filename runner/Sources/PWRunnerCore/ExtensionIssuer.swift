import Darwin
import Foundation

// Checked against compiled C sizeof/offsetof by runner_abi_layout.
enum PWExtensionLayout {
    static let magic: UInt32 = 0x50574558
    static let tokenBytes: Int = 16384
    static let pathBytes: Int = 1024
    static let channelBytes: Int = 17472
    static let issuerWaitMs: Int = 5000
    static let magicOffset: Int = 0
    static let callBoundaryOffset: Int = 4
    static let completedOffset: Int = 8
    static let statusOffset: Int = 12
    static let errnoOffset: Int = 16
    static let tokenLengthOffset: Int = 20
    static let pidOffset: Int = 24
    static let uidOffset: Int = 28
    static let euidOffset: Int = 32
    static let gidOffset: Int = 36
    static let egidOffset: Int = 40
    static let authorityOffset: Int = 44
    static let targetOffset: Int = 64
    static let tokenOffset: Int = 1088
}

// The authority-bearing mapping is separate from the worker's evidence mapping.
// Only this owner passes its descriptor; neither the reply nor diagnostics read
// the token bytes. Issuer exit/reaping precedes delivery to a worker.
final class ExtensionSession {
    static let tokenBytes = PWExtensionLayout.tokenBytes
    static let pathBytes = PWExtensionLayout.pathBytes
    static let channelBytes = PWExtensionLayout.channelBytes
    static let issuerWaitMs = PWExtensionLayout.issuerWaitMs
    static let tokenOffset = PWExtensionLayout.tokenOffset
    private(set) var descriptor: Int32 = -1
    private var mapping: UnsafeMutableRawPointer?
    var record: PWRunnerExtensionRecord
    var capabilityUnavailable = false

    init(declaration: PWRunnerExtensionDeclaration, executable: String,
         processCalls: ChildProcessCalls = ChildProcessCalls()) {
        record = PWRunnerExtensionRecord(token_ref: declaration.token_ref, submitted_target: declaration.target)
        record.extension_class = declaration.nativeClass
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
        writeU32(bytes, offset: PWExtensionLayout.magicOffset, PWExtensionLayout.magic)
        let authority: UInt32 = declaration.effectiveAuthority == "read_write" ? 1 : 0
        writeU32(bytes, offset: PWExtensionLayout.authorityOffset, authority)
        _ = resolved.withUnsafeBytes { memcpy(bytes.advanced(by: PWExtensionLayout.targetOffset), $0.baseAddress!, Self.pathBytes) }
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
        issuer.call_boundary_observed = loadAcquire(bytes, offset: PWExtensionLayout.callBoundaryOffset) == 1
        let published = loadAcquire(bytes, offset: PWExtensionLayout.completedOffset) == 1
        issuer.result_published = published
        record.issuance_status = stop == "deadline" ? "issuer_timeout" : stop == "wait_error" ? "issuer_wait_error" : "issuer_result_missing"
        if published {
            let state = UInt32(bitPattern: readI32(bytes, offset: PWExtensionLayout.statusOffset))
            let validHeader = UInt32(bitPattern: readI32(bytes, offset: PWExtensionLayout.magicOffset)) == PWExtensionLayout.magic
                && UInt32(bitPattern: readI32(bytes, offset: PWExtensionLayout.authorityOffset)) == authority
                && readI32(bytes, offset: PWExtensionLayout.pidOffset) == pid && [1, 2, 3, 4].contains(state)
                && (state == 4 ? !issuer.call_boundary_observed : issuer.call_boundary_observed)
            if !validHeader {
                record.issuance_status = "invalid_transport"
            } else {
            issuer.uid = UInt32(bitPattern: readI32(bytes, offset: PWExtensionLayout.uidOffset))
            issuer.euid = UInt32(bitPattern: readI32(bytes, offset: PWExtensionLayout.euidOffset))
            issuer.gid = UInt32(bitPattern: readI32(bytes, offset: PWExtensionLayout.gidOffset))
            issuer.egid = UInt32(bitPattern: readI32(bytes, offset: PWExtensionLayout.egidOffset))
            if [1, 2, 3].contains(state) {
                issuer.native_nonnull = state != 2
                issuer.errno = readI32(bytes, offset: PWExtensionLayout.errnoOffset)
            }
            let length = UInt32(bitPattern: readI32(bytes, offset: PWExtensionLayout.tokenLengthOffset))
            if state == 1 { issuer.token_length = length }
            if state == 4 { capabilityUnavailable = true; record.issuance_status = "native_api_unavailable" }
            else if state == 2 { record.issuance_status = "native_refusal" }
            else if state == 3 { record.issuance_status = "token_oversized" }
            else if length == 0 || length >= Self.tokenBytes {
                record.issuance_status = "invalid_transport"
            } else if child.status != nil && issuer.exit_code == 0 && stop == "reaped" {
                record.issuance_status = "issued"
            } else if child.status != nil && stop == "reaped" {
                record.issuance_status = "issuer_abnormal_exit"
            }
            }
        }
        record.issuer = issuer
        // No delivery after unconfirmed cleanup, abnormal exit, malformed or
        // incomplete publication. Clearing the publication prevents consumption.
        if record.issuance_status != "issued" { pw_cworker_store_release_u32(bytes.advanced(by: PWExtensionLayout.completedOffset).withMemoryRebound(to: UInt32.self, capacity: 1) { $0 }, 0) }
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
