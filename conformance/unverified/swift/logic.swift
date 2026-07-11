enum domain {
    static func price(_ fetch: () -> Int) -> Int { return fetch() + 1 }
}
