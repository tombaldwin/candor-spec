// orderflow, Swift: api.get -> domain.bulk -> domain.price -> infra.fetch (the Net source).
// Enum namespaces give the same module.function shape as the other engines' fixtures (leaf names
// fetch/price/bulk/get, scope segment `domain`), so `deny Net domain` yields the same remedy.
import Foundation
enum infra {
    static func fetch() { _ = URLSession.shared.dataTask(with: URL(string: "http://h/")!) }
}
enum domain {
    static func price() { infra.fetch() }
    static func bulk() { price() }
}
enum api {
    static func get() { domain.bulk() }
}
enum app {
    static func run() { api.get() }
}
