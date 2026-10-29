import Foundation

// Request objects are closed; dictionary keys inside policy.params are data.
// CodingKeys owns both encoding and acceptance, so there is no second schema.
struct RequestKey: CodingKey {
    let stringValue: String
    let intValue: Int? = nil
    init(stringValue: String) { self.stringValue = stringValue }
    init?(intValue: Int) { return nil }
}

func rejectUnknownRequestKeys<K: CodingKey & CaseIterable>(_ type: K.Type, from decoder: Decoder) throws {
    let container = try decoder.container(keyedBy: RequestKey.self)
    let accepted = Set(K.allCases.map { $0.stringValue })
    if let key = container.allKeys.sorted(by: { $0.stringValue < $1.stringValue })
        .first(where: { !accepted.contains($0.stringValue) }) {
        throw RequestContractError.unknownField(decoder.codingPath + [key])
    }
}

func pwRunnerEncodeJSON<T: Encodable>(_ value: T) throws -> Data {
    let enc = JSONEncoder()
    enc.outputFormatting = [.sortedKeys]
    return try enc.encode(value)
}

func pwRunnerDecodeJSON<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
    let dec = JSONDecoder()
    return try dec.decode(type, from: data)
}
