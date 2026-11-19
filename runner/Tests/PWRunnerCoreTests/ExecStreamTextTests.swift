import Foundation
@testable import PWRunnerCore

// Constructed stored bytes and received counts given to the host's stream
// composition. No worker or child runs here; the expected texts are authored
// from the byte patterns, not derived through the decoder under test.
private let marker = "\n... [truncated]"

/// `prefix` then `unit` repeated, cut at `count` bytes as a full stream buffer cuts it.
private func stream(_ prefix: String, _ unit: [UInt8], count: Int = 1023) -> [UInt8] {
    var bytes = Array(prefix.utf8)
    while bytes.count < count { bytes += unit }
    return Array(bytes.prefix(count))
}

func runExecStreamTextTests(_ tk: TestKit) {
    tk.group("exec stream text composition") {
        tk.run("every kept byte is decoded and the counts state what the text represents") {
            let eAcute: [UInt8] = [0xC3, 0xA9], euro: [UInt8] = [0xE2, 0x82, 0xAC], face: [UInt8] = [0xF0, 0x9F, 0x98, 0x80]
            func repeated(_ text: String, _ count: Int) -> String { String(repeating: text, count: count) }
            let rows: [(name: String, stored: [UInt8], received: UInt64, text: String?, retained: UInt32, truncated: Bool, exact: Bool)] = [
                ("nothing read", [], 0, nil, 0, false, true),
                ("embedded NUL", Array("HEAD\u{0}TAIL".utf8), 9, "HEAD\u{0}TAIL", 9, false, true),
                ("leading NUL", [0, 0x41], 2, "\u{0}A", 2, false, true),
                ("exactly the allowance", stream("", [0x41]), 1023, repeated("A", 1023), 1023, false, true),
                ("one byte over the allowance", stream("", [0x41]), 1024, repeated("A", 1007) + marker, 1007, true, true),
                ("NUL before overflow", stream("HEAD\u{0}", [0x30]), 2053, "HEAD\u{0}" + repeated("0", 1002) + marker, 1007, true, true),
                ("cut inside a two-byte character", stream("xx", eAcute), 4002, "xx" + repeated("\u{E9}", 502) + marker, 1006, true, true),
                ("cut between two-byte characters", stream("x", eAcute), 4001, "x" + repeated("\u{E9}", 503) + marker, 1007, true, true),
                ("cut after two bytes of three", stream("", euro), 3000, repeated("\u{20AC}", 335) + marker, 1005, true, true),
                ("cut after one byte of three", stream("a", euro), 3001, "a" + repeated("\u{20AC}", 335) + marker, 1006, true, true),
                ("cut between three-byte characters", stream("aa", euro), 3002, "aa" + repeated("\u{20AC}", 335) + marker, 1007, true, true),
                ("cut after three bytes of four", stream("", face), 4000, repeated("\u{1F600}", 251) + marker, 1004, true, true),
                ("cut after two bytes of four", stream("a", face), 4001, "a" + repeated("\u{1F600}", 251) + marker, 1005, true, true),
                ("cut after one byte of four", stream("aa", face), 4002, "aa" + repeated("\u{1F600}", 251) + marker, 1006, true, true),
                ("invalid bytes without overflow", [UInt8](repeating: 0xFF, count: 17), 17, repeated("\u{FFFD}", 17), 17, false, false),
                ("invalid bytes with overflow", [UInt8](repeating: 0xFF, count: 1023), 2000, repeated("\u{FFFD}", 1007) + marker, 1007, true, false),
                ("a stray continuation byte at the cut is kept", stream(repeated("A", 1006), [0x80]), 1500,
                 repeated("A", 1006) + "\u{FFFD}" + marker, 1007, true, false),
                ("a byte that begins no sequence at the cut is kept", stream(repeated("A", 1006), [0xC0]), 1500,
                 repeated("A", 1006) + "\u{FFFD}" + marker, 1007, true, false),
                ("malformed lead before the cut is replaced", stream(repeated("A", 1006), [0xE2, 0x41]), 1500,
                 repeated("A", 1006) + "\u{FFFD}" + marker, 1007, true, false),
                ("invalid scalar straddling the cut is replaced", stream(repeated("A", 1005), [0xED, 0xA0, 0x80]), 1500,
                 repeated("A", 1005) + "\u{FFFD}\u{FFFD}" + marker, 1007, true, false),
                ("the child's own U+FFFD is exact", [0x41, 0xEF, 0xBF, 0xBD], 4, "A\u{FFFD}", 4, false, true),
                ("the child's own marker characters are not truncation", Array(("done" + marker).utf8), 20, "done" + marker, 20, false, true),
                ("an incomplete sequence ending an untruncated stream is replaced", [0x41, 0xC3], 2, "A\u{FFFD}", 2, false, false),
            ]
            for row in rows {
                let composed = composeExecStream(stored: row.stored, received: row.received)
                try expectEqual(composed.text, row.text, row.name)
                try expectEqual(composed.retained, row.retained, row.name)
                try expectEqual(composed.truncated, row.truncated, row.name)
                try expectEqual(composed.exact, row.exact, row.name)
                // An exact text is its retained bytes, plus the marker when truncated.
                if row.exact {
                    try expectEqual((composed.text ?? "").utf8.count, Int(row.retained) + (row.truncated ? marker.utf8.count : 0), row.name)
                    try expectTrue((composed.text ?? "").utf8.count <= 1023, row.name)
                }
            }
        }
    }
}
