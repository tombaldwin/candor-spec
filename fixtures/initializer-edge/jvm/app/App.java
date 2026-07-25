package app;
public class App {
    // This class's own <clinit> performs no effect of its own. It reads a field of Dep, which
    // forces Dep's <clinit> — and that reads the environment.
    static final String X = dep.Dep.DBG;
    public static int n() { return 1; }
}
