import Foundation
func save(_ p: String) throws { try Data().write(to: URL(fileURLWithPath: p)) }
func add(_ a: Int, _ b: Int) -> Int { return a + b }
