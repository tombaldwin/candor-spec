import Foundation
final class Guard { func run() -> Int { try? "x".write(toFile: "/tmp/swr", atomically: true, encoding: .utf8); return 1 } }
final class Calm  { func run() -> Int { 7 } }

final class H {
    var v: [Guard] = []
    var c: [Calm]  = []

    func base()      { v.forEach { _ = $0.run() } }                       // control: Fs
    func x_reduce()  { _ = v.reduce(0) { a, x in a + x.run() } }          // 2nd param IS the element
    func x_reduceSh(){ _ = v.reduce(0) { $0 + $1.run() } }                // shorthand $1
    func x_reduceIn(){ _ = v.reduce(into: 0) { a, x in a += x.run() } }   // (inout Acc, Element)
    func x_enum()    { for (_, g) in v.enumerated() { _ = g.run() } }
    func x_enumEach(){ v.enumerated().forEach { _ = $0.1.run() } }
    func x_zip()     { for (g, _) in zip(v, [1]) { _ = g.run() } }

    func ctl_reduce(){ _ = c.reduce(0) { a, x in a + x.run() } }          // over-charge control
}
