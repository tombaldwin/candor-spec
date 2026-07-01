package app;
import java.nio.file.*;
public class Store {
    // Statically performs Fs — violates `deny Fs app` (AS-EFF-006). The pure method must NOT appear.
    public void save(String p, byte[] b) throws Exception { Files.write(Paths.get(p), b); }
    public int add(int a, int b) { return a + b; }
}
