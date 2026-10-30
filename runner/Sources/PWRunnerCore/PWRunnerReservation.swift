import Foundation

/// A host owns one slot across every authenticated connection. No expired,
/// abandoned or executed slot becomes free again. Returned actions are invoked
/// by the service after releasing this lock.
final class PWRunnerAdmission {
    /// One token per exported connection. Its lifetime flag is accessed only
    /// under this admission owner's lock; retired tokens need no host-wide set.
    final class Connection {
        fileprivate var closed = false
    }
    struct Reservation {
        var owner: Connection
        var token: String
        var expiry: UInt64
        var leaseMs: Int
    }
    enum Slot { case free, reserved(Reservation), executing(Connection, String), retiring(String) }
    struct Decision {
        var accepted: Bool = false
        var reason: String?
        var reservation: Reservation?
        var retire: Bool = false
    }
    let instance = UUID().uuidString
    private let lock = NSLock()
    private var slot: Slot = .free
    private let clock: () -> UInt64
    init(clock: @escaping () -> UInt64 = PWContinuousClock.now) { self.clock = clock }

    func reserve(owner: Connection, leaseMs: Int) -> Decision {
        lock.lock(); defer { lock.unlock() }
        guard !owner.closed else { return Decision(reason: "occupied") }
        guard leaseMs > 0 else { return Decision(reason: "invalid_request") }
        let now = clock()
        guard now != UInt64.max else { return Decision(reason: "clock_error") }
        if case .reserved(let held) = slot, now >= held.expiry {
            slot = .retiring("expired")
            return Decision(reason: "occupied", retire: true)
        }
        guard case .free = slot else { return Decision(reason: "occupied") }
        let lease = min(leaseMs, PWRunnerTransportLimits.reservationLeaseMs)
        let held = Reservation(owner: owner, token: UUID().uuidString,
            expiry: PWContinuousClock.adding(milliseconds: UInt64(lease), to: now), leaseMs: lease)
        slot = .reserved(held)
        return Decision(accepted: true, reservation: held)
    }

    func submit(owner: Connection, token: String) -> Decision {
        lock.lock(); defer { lock.unlock() }
        switch slot {
        case .free: return Decision(reason: "absent")
        case .executing: return Decision(reason: "consumed")
        case .retiring(let reason): return Decision(reason: ["expired", "clock_error"].contains(reason) ? reason : "consumed")
        case .reserved(let held):
            let now = clock()
            if now == UInt64.max || now >= held.expiry {
                let reason = now == UInt64.max ? "clock_error" : "expired"
                slot = .retiring(reason)
                return Decision(reason: reason, retire: true)
            }
            guard !owner.closed, held.owner === owner, held.token == token else { return Decision(reason: "wrong") }
            slot = .executing(owner, token)
            return Decision(accepted: true)
        }
    }

    func expire(owner: Connection, token: String) -> Bool {
        lock.lock(); defer { lock.unlock() }
        guard case .reserved(let held) = slot, held.owner === owner, held.token == token else { return false }
        let now = clock()
        guard now == UInt64.max || now >= held.expiry else { return false }
        slot = .retiring(now == UInt64.max ? "clock_error" : "expired")
        return true
    }

    func expiryDelay(owner: Connection, token: String) -> Int? {
        lock.lock(); defer { lock.unlock() }
        guard case .reserved(let held) = slot, held.owner === owner, held.token == token else { return nil }
        let now = clock()
        guard now != UInt64.max, now < held.expiry else { return 0 }
        let ns = held.expiry - now
        return Int(min(100, ns / 1_000_000 + (ns % 1_000_000 == 0 ? 0 : 1)))
    }

    func disconnected(owner: Connection) -> Bool {
        lock.lock(); defer { lock.unlock() }
        owner.closed = true
        guard case .reserved(let held) = slot, held.owner === owner else { return false }
        slot = .retiring("abandoned")
        return true
    }

    func complete(owner: Connection, token: String) -> Bool {
        lock.lock(); defer { lock.unlock() }
        guard case .executing(let current, let consumed) = slot, current === owner, consumed == token else { return false }
        slot = .retiring("consumed")
        return true
    }
}
