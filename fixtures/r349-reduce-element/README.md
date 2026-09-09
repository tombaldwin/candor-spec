# R349 — `reduce`'s second closure parameter is the element, and was never typed

Run: `candor-swift . --json` and read `functions[]`.

`H.base` (`v.forEach { _ = $0.run() }`) charges `Fs` — it is the CONTROL, and it is what makes the
rest a measurement rather than an assertion that the scan found nothing.

ABSENT today, each a purity claim over a body that writes a file:

    H.x_reduce      v.reduce(0) { a, x in a + x.run() }
    H.x_reduceSh    v.reduce(0) { $0 + $1.run() }
    H.x_reduceIn    v.reduce(into: 0) { a, x in a += x.run() }
    H.x_enumEach    v.enumerated().forEach { _ = $0.1.run() }
    H.x_zip         for (g, _) in zip(v, [1]) { _ = g.run() }

`H.x_enum` (`for (_, g) in v.enumerated()`) CHARGES. That is the discriminator: `enumerated` is
understood; a tuple-yielding adapter reaching a CLOSURE parameter is not.

`H.ctl_reduce` is the over-charge control — the same `reduce` shape over a `[Calm]` whose `run()` is
pure. It is uninformative today (everything is absent) and becomes the load-bearing assertion the
moment anything here is fixed. Write it into the test before the fix, not after.
