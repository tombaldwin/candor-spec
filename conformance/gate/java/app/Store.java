package app;
import java.nio.file.*;
public class Store {
    // Statically performs Fs — violates `deny Fs app` (AS-EFF-006). The pure method must NOT appear.
    public void save(String p, byte[] b) throws Exception { Files.write(Paths.get(p), b); }

    // SOUNDNESS R411 — THE DEFECT ARM. `save` above is a second CONTROL: its path is built inline by
    // `Paths.get(p)`, which every engine's path-construction branch marks incomplete, so every engine
    // passes and the row discriminates nothing. Here the path arrives ALREADY CONSTRUCTED, as a `Path`
    // parameter, and never enters that branch — beside a benign ALLOWED literal, which is what turns a
    // missing mask into a certified caller-controlled write.
    public void masked(Path p, byte[] b) throws Exception {
        Files.write(Paths.get("/var/data"), b);   // the ALLOWED literal
        Files.write(p, b);                        // caller-controlled — invisible unless the surface is marked
    }
    public int add(int a, int b) { return a + b; }
}
