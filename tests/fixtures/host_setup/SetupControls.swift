// Compiled only into a disposable copy of PWRunnerCore. Native boundaries are
// renamed there; source control flow is unchanged. No request enables this.
import Darwin
import Foundation

@_silgen_name("pw_setup_shm_open_existing")
func setupOpenExisting(_ name: UnsafePointer<CChar>) -> Int32

var setupCase = ""
var setupEvents: [[String: Any]] = []
var setupFDs: [Int32] = []
var setupNames: [String] = []
var setupMaps: Set<UInt> = []
var setupStrings: Set<UInt> = []
var setupHandles = 0
var setupStringIndex = 0
var setupPID: pid_t = 0

func setupEvent(_ call: String, _ fields: [String: Any] = [:]) {
    var event = fields; event["call"] = call; setupEvents.append(event)
}
func setupFault(_ point: String) -> Bool {
    if setupCase == point { setupEvent("injected", ["point": point]); return true }
    return false
}
func setupIdentity(_ fd: Int32) -> [String: Any] {
    var s = stat(); let rc = fstat(fd, &s)
    var value: [String: Any] = ["fd": fd, "rc": rc]
    if rc == 0 { value["device"] = UInt32(bitPattern: s.st_dev); value["inode"] = s.st_ino; value["mode"] = s.st_mode }
    return value
}
func setup_shm(_ name: UnsafePointer<CChar>, _ mode: mode_t) -> Int32 {
    let fd = pw_cworker_shm_open_create(name, mode)
    if fd >= 0 { setupFDs.append(fd); setupNames.append(String(cString: name)) }
    setupEvent("shm", ["fd": fd]); return fd
}
func setup_unlink(_ name: UnsafePointer<CChar>) -> Int32 {
    if setupFault("unlink") { errno = EACCES; return -1 }
    return Darwin.shm_unlink(name)
}
func setup_pipe(_ fds: UnsafeMutablePointer<Int32>) -> Int32 {
    let rc = Darwin.pipe(fds)
    if rc == 0 { setupFDs += [fds[0], fds[1]] }
    return rc
}
func setup_fcntl(_ fd: Int32, _ command: Int32, _ value: Int32) -> Int32 {
    if command == F_SETFD && value == 0 && setupFault("clear_cloexec") { errno = EIO; return -1 }
    if command == F_SETNOSIGPIPE && setupFault("nosigpipe") { errno = EIO; return -1 }
    let rc = Darwin.fcntl(fd, command, value)
    if command == F_DUPFD_CLOEXEC && rc >= 0 { setupFDs.append(rc) }
    return rc
}
func setup_mmap(_ address: UnsafeMutableRawPointer?, _ length: Int, _ protection: Int32,
                _ flags: Int32, _ fd: Int32, _ offset: off_t) -> UnsafeMutableRawPointer? {
    let result = Darwin.mmap(address, length, protection, flags, fd, offset)
    if let result, result != MAP_FAILED { setupMaps.insert(UInt(bitPattern: result)) }
    return result
}
func setup_munmap(_ address: UnsafeMutableRawPointer, _ length: Int) -> Int32 {
    let rc = Darwin.munmap(address, length)
    if rc == 0 { setupMaps.remove(UInt(bitPattern: address)) }
    setupEvent("munmap", ["rc": rc]); return rc
}
func setup_actions_init(_ actions: UnsafeMutablePointer<posix_spawn_file_actions_t?>) -> Int32 {
    if setupFault("actions_init") { actions.pointee = nil; return ENOMEM }
    let rc = posix_spawn_file_actions_init(actions)
    if rc == 0 { setupHandles += 1 }
    return rc
}
func setup_actions_destroy(_ actions: UnsafeMutablePointer<posix_spawn_file_actions_t?>) -> Int32 {
    guard actions.pointee != nil else { setupEvent("nil_actions_destroy"); return EINVAL }
    let rc = posix_spawn_file_actions_destroy(actions)
    if rc == 0 { setupHandles -= 1 }
    return rc
}
func setup_dup2(_ actions: UnsafeMutablePointer<posix_spawn_file_actions_t?>, _ source: Int32, _ destination: Int32) -> Int32 {
    setupEvent("dup2", ["source": source, "destination": destination, "identity": setupIdentity(source)])
    guard actions.pointee != nil else { setupEvent("nil_actions_use"); return EINVAL }
    if setupFault("dup2.\(destination)") { return ENOMEM }
    return posix_spawn_file_actions_adddup2(actions, source, destination)
}
func setup_open(_ actions: UnsafeMutablePointer<posix_spawn_file_actions_t?>, _ fd: Int32,
                _ path: UnsafePointer<CChar>, _ flags: Int32, _ mode: mode_t) -> Int32 {
    guard actions.pointee != nil else { setupEvent("nil_actions_use"); return EINVAL }
    if setupFault("open.\(fd)") { return ENOMEM }
    return posix_spawn_file_actions_addopen(actions, fd, path, flags, mode)
}
func setup_attrs_init(_ attrs: UnsafeMutablePointer<posix_spawnattr_t?>) -> Int32 {
    if setupFault("attrs_init") { attrs.pointee = nil; return ENOMEM }
    let rc = posix_spawnattr_init(attrs)
    if rc == 0 { setupHandles += 1 }
    return rc
}
func setup_attrs_destroy(_ attrs: UnsafeMutablePointer<posix_spawnattr_t?>) -> Int32 {
    guard attrs.pointee != nil else { setupEvent("nil_attrs_destroy"); return EINVAL }
    let rc = posix_spawnattr_destroy(attrs)
    if rc == 0 { setupHandles -= 1 }
    return rc
}
func setup_flags(_ attrs: UnsafeMutablePointer<posix_spawnattr_t?>, _ flags: Int16) -> Int32 {
    guard attrs.pointee != nil else { setupEvent("nil_attrs_use"); return EINVAL }
    if setupFault("flags") { return ENOMEM }
    return posix_spawnattr_setflags(attrs, flags)
}
func setup_strdup(_ value: String) -> UnsafeMutablePointer<CChar>? {
    let index = setupStringIndex; setupStringIndex += 1
    if setupFault("strdup.\(index)") { errno = ENOMEM; return nil }
    let p = Darwin.strdup(value)
    if let p { setupStrings.insert(UInt(bitPattern: p)) }
    return p
}
func setup_free(_ p: UnsafeMutablePointer<CChar>) {
    setupStrings.remove(UInt(bitPattern: p)); Darwin.free(p)
}
func setup_spawn(_ pid: UnsafeMutablePointer<pid_t>, _ path: UnsafePointer<CChar>,
                 _ actions: UnsafePointer<posix_spawn_file_actions_t?>?,
                 _ attrs: UnsafePointer<posix_spawnattr_t?>?,
                 _ argv: UnsafePointer<UnsafeMutablePointer<CChar>?>,
                 _ env: UnsafePointer<UnsafeMutablePointer<CChar>?>?) -> Int32 {
    var argc = 0
    while argv[argc] != nil { argc += 1 }
    setupEvent("spawn_reached", ["argc": argc])
    // A failed native initialization leaves no handle. Do not pass that state
    // to libc in the fixture: record attempted use and bound the experiment.
    // This refusal is test equipment, not a claimed production guard.
    if (actions != nil && actions!.pointee == nil) || (attrs != nil && attrs!.pointee == nil) {
        setupEvent("fixture_refused_invalid_handle"); return EINVAL
    }
    let rc = posix_spawn(pid, path, actions, attrs, argv, env)
    if rc == 0 { setupPID = pid.pointee }
    setupEvent("native_spawn", ["rc": rc, "pid": pid.pointee]); return rc
}

func runSetupControl(_ owner: String, _ fault: String, _ child: String, _ output: String) throws {
    setupCase = fault
    // Each invocation has its own process. Occupy low descriptors for the
    // baseline; the collision case closes stdin so evidence is allocated at 0.
    let savedOut = fcntl(STDOUT_FILENO, F_DUPFD_CLOEXEC, 128)
    let savedErr = fcntl(STDERR_FILENO, F_DUPFD_CLOEXEC, 128)
    for fd: Int32 in 3..<64 { close(fd) }
    if fault == "collision" { close(0) }
    else {
        while true {
            let fd = open("/dev/null", O_RDWR)
            guard fd >= 0 else { throw NSError(domain: "setup fixture", code: 1) }
            if fd >= 16 { close(fd); break }
        }
    }
    var token: Int32 = -1
    if owner == "worker_token" { token = open(child, O_RDONLY) }
    var outcome = ""
    if owner.hasPrefix("worker") {
        var input = CWorkerInput(workerExecutablePath: child, policy: "(version 1) (allow default)",
            slots: [], readyByteTimeoutMs: 100, sentinelTimeoutMs: 200, exitGraceMs: 200)
        if token >= 0 { input.extensionFD = token }
        let result = runCWorker(input, postApplied: nil)
        switch result {
        case .failure(let failure, _): outcome = String(describing: failure)
        case .success(let value): outcome = "worker observation pid=\(value.workerPid)"
        }
    } else {
        var session: ExtensionSession? = ExtensionSession(
            declaration: PWRunnerExtensionDeclaration(token_ref: "setup", target: child), executable: child)
        outcome = session!.record.issuance_status
        session = nil // observe owner teardown, not fixture cleanup
    }
    if token >= 0 { close(token) }
    let fdsClosed = setupFDs.allSatisfy { fcntl($0, F_GETFD) == -1 && errno == EBADF }
    var namesPresent: [String] = []
    for name in setupNames {
        let fd = name.withCString { setupOpenExisting($0) }
        if fd >= 0 { namesPresent.append(name); close(fd) }
    }
    var reaped = false
    if setupPID > 0 {
        var status: Int32 = 0
        let rc = waitpid(setupPID, &status, WNOHANG)
        reaped = rc == -1 && errno == ECHILD
        if !reaped { if rc == 0 { kill(setupPID, SIGKILL); _ = waitpid(setupPID, &status, 0) } }
    }
    // Independent cleanup owns names deliberately left by the unlink fault.
    var namesRemoved = true
    for name in namesPresent { if name.withCString({ Darwin.shm_unlink($0) }) != 0 { namesRemoved = false } }
    for name in setupNames {
        let fd = name.withCString { setupOpenExisting($0) }
        if fd >= 0 { namesRemoved = false; close(fd) }
        else if errno != ENOENT { namesRemoved = false }
    }
    dup2(savedOut, STDOUT_FILENO); dup2(savedErr, STDERR_FILENO)
    close(savedOut); close(savedErr)
    let receipt: [String: Any] = ["owner": owner, "fault": fault, "events": setupEvents,
        "outcome": outcome, "fds_closed": fdsClosed, "maps_remaining": setupMaps.count,
        "strings_remaining": setupStrings.count, "handles_remaining": setupHandles,
        "names_present_before_fixture_cleanup": namesPresent, "fixture_names_removed": namesRemoved,
        "spawn_pid": setupPID, "host_reaped": reaped]
    let data = try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
    try data.write(to: URL(fileURLWithPath: output))
}
