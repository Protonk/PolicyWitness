import Foundation

// Small, deliberately closed wire vocabulary. No Codable, reflection or JSON
// interpretation is involved in the converted response path.
enum PWPorcelainError: Error { case invalid(String) }
let pwPorcelainByteLimit = 128 * 1024 * 1024

protocol PWPorcelainValue { func porcelainWrite() throws -> Data }
protocol PWPorcelainWritable: PWPorcelainValue {
    static var porcelainRecordID: UInt16 { get }
}

func pwPorcelainLE<T: FixedWidthInteger>(_ value: T) -> Data {
    var little = value.littleEndian
    return withUnsafeBytes(of: &little) { Data($0) }
}

func pwPorcelainValue(_ kind: UInt8, _ payload: Data) throws -> Data {
    guard payload.count <= pwPorcelainByteLimit else {
        throw PWPorcelainError.invalid("value exceeds byte limit")
    }
    var bytes = Data([kind])
    bytes.append(pwPorcelainLE(UInt32(payload.count)))
    bytes.append(payload)
    return bytes
}

func pwPorcelainFrame(_ record: Data) -> Data {
    var bytes = Data([0x50, 0x57, 0x50, 0x31])
    bytes.append(contentsOf: PWPorcelainSchema.fingerprint)
    bytes.append(record)
    return bytes
}

func pwPorcelainEncode<T: PWPorcelainWritable>(_ value: T) throws -> Data {
    pwPorcelainFrame(try value.porcelainWrite())
}

struct PWPorcelainRecordWriter {
    private var payload: Data
    private var last: UInt16 = 0
    init(_ id: UInt16) { payload = pwPorcelainLE(id) }
    mutating func field<T: PWPorcelainValue>(_ tag: UInt16, _ value: T) throws {
        guard tag > last else { throw PWPorcelainError.invalid("field order") }
        let bytes = try value.porcelainWrite()
        guard bytes.count <= pwPorcelainByteLimit - payload.count - 2 else {
            throw PWPorcelainError.invalid("record exceeds byte limit")
        }
        payload.append(pwPorcelainLE(tag)); payload.append(bytes); last = tag
    }
    mutating func field<T: PWPorcelainValue>(_ tag: UInt16, _ value: T?) throws {
        if let value { try field(tag, value) }
    }
    func finish() throws -> Data { try pwPorcelainValue(6, payload) }
}

extension Bool: PWPorcelainValue {
    func porcelainWrite() throws -> Data { try pwPorcelainValue(1, Data([self ? 1 : 0])) }
}
extension String: PWPorcelainValue {
    func porcelainWrite() throws -> Data { try pwPorcelainValue(4, Data(utf8)) }
}
extension Data: PWPorcelainValue {
    func porcelainWrite() throws -> Data { try pwPorcelainValue(5, self) }
}
extension Int: PWPorcelainValue {
    func porcelainWrite() throws -> Data { try pwPorcelainValue(2, pwPorcelainLE(Int64(self))) }
}
extension Int32: PWPorcelainValue {
    func porcelainWrite() throws -> Data { try pwPorcelainValue(2, pwPorcelainLE(Int64(self))) }
}
extension Int64: PWPorcelainValue {
    func porcelainWrite() throws -> Data { try pwPorcelainValue(2, pwPorcelainLE(self)) }
}
extension UInt32: PWPorcelainValue {
    func porcelainWrite() throws -> Data { try pwPorcelainValue(3, pwPorcelainLE(UInt64(self))) }
}
extension UInt64: PWPorcelainValue {
    func porcelainWrite() throws -> Data { try pwPorcelainValue(3, pwPorcelainLE(self)) }
}

extension Array: PWPorcelainValue where Element: PWPorcelainValue {
    func porcelainWrite() throws -> Data {
        guard count <= pwPorcelainByteLimit / 5 else { throw PWPorcelainError.invalid("list count") }
        var bytes = pwPorcelainLE(UInt32(count))
        for item in self {
            let value = try item.porcelainWrite()
            guard value.count <= pwPorcelainByteLimit - bytes.count else {
                throw PWPorcelainError.invalid("list exceeds byte limit")
            }
            bytes.append(value)
        }
        return try pwPorcelainValue(7, bytes)
    }
}

extension Dictionary: PWPorcelainValue where Key == String, Value: PWPorcelainValue {
    func porcelainWrite() throws -> Data {
        guard count <= pwPorcelainByteLimit / 10 else { throw PWPorcelainError.invalid("map count") }
        var bytes = pwPorcelainLE(UInt32(count))
        for key in keys.sorted(by: { $0.utf8.lexicographicallyPrecedes($1.utf8) }) {
            let k = try key.porcelainWrite(), v = try self[key]!.porcelainWrite()
            guard k.count + v.count <= pwPorcelainByteLimit - bytes.count else {
                throw PWPorcelainError.invalid("map exceeds byte limit")
            }
            bytes.append(k); bytes.append(v)
        }
        return try pwPorcelainValue(8, bytes)
    }
}

extension PWDispositionValue: PWPorcelainValue {
    func porcelainWrite() throws -> Data {
        var bytes: Data
        switch self {
        case .integer(let value):
            bytes = pwPorcelainLE(UInt16(1)); bytes.append(try value.porcelainWrite())
        case .request(let value):
            bytes = pwPorcelainLE(UInt16(2)); bytes.append(try value.porcelainWrite())
        }
        return try pwPorcelainValue(9, bytes)
    }
}
