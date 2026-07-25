# Fixtures: the initializer edge into an unanalyzed dependency

See [../../SOUNDNESS-VEIN-initializer-edge.md](../../SOUNDNESS-VEIN-initializer-edge.md).

Each fixture has a dependency whose **module top level / static initializer** performs an effect, and an
application unit whose own top level performs none but which imports it. The point of the pair is the
contrast, so run it twice:

**jvm/** — `javac -d classes dep/Dep.java app/App.java`, then

    candor-java classes        # dep INSIDE the scanned set  -> app.App.<clinit> { Env* }, 1 hop via dep.Dep.<clinit>
    candor-java classes/app    # dep OUTSIDE it              -> pure, silently   <-- the vein

**node/** — `node scan.mjs . --allow-js`. `effectful-dep` sits in `node_modules`, so it is always outside
the scanned set: `app.js` reports pure while its `require` runs a `process.env` read.
