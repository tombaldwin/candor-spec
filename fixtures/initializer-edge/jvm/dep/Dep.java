package dep;
public class Dep {
    // The dependency's STATIC INITIALIZER performs an effect (the graceful-fs shape).
    public static final String DBG = System.getenv("NODE_DEBUG");
    public static int go() { return 1; }
}
