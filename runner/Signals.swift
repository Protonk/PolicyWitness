import Darwin

// Sandbox profiles can emit SIGUSR1 on deny (via a deny-signal rule). We count
// these signals to provide evidence alongside sandbox_check and attempt results.
private let PW_RUNNER_DENY_SIGNAL: Int32 = SIGUSR1

private var pwRunnerDenySignalCount: sig_atomic_t = 0

@_cdecl("pw_runner_deny_signal_handler")
private func pw_runner_deny_signal_handler(_ signo: Int32) {
    if signo == PW_RUNNER_DENY_SIGNAL {
        pwRunnerDenySignalCount += 1
    }
}

func installDenySignalHandler() {
    _ = signal(PW_RUNNER_DENY_SIGNAL, pw_runner_deny_signal_handler)
    // XPC/libdispatch can block signals on the current thread. Unblock the deny
    // signal so we can observe profile-emitted SIGUSR1 deterministically.
    var set = sigset_t()
    sigemptyset(&set)
    sigaddset(&set, PW_RUNNER_DENY_SIGNAL)
    _ = pthread_sigmask(SIG_UNBLOCK, &set, nil)
}

func denySignalCount() -> Int {
    Int(pwRunnerDenySignalCount)
}
