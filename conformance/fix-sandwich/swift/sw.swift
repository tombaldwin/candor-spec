import Foundation
enum infra { static func fetch() { _ = URLSession.shared.dataTask(with: URL(string: "http://h/")!) } }
enum domain {
    static func inner() { infra.fetch() }
    static func top() { api.mid() }
}
enum api { static func mid() { domain.inner() } }
