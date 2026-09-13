import Foundation
func save(_ p: String) throws { try Data().write(to: URL(fileURLWithPath: p)) }
// SOUNDNESS R411 — the DEFECT arm: a benign ALLOWED literal beside a caller-controlled write.
func masked(_ p: String) throws {
    try Data().write(to: URL(fileURLWithPath: "/var/data"))
    try Data().write(to: URL(fileURLWithPath: p))
}
func add(_ a: Int, _ b: Int) -> Int { return a + b }
