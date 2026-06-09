import java.nio.file.*;

// Cross-impl conformance fixtures (Java). Each method mirrors a fn in ../rust/src/lib.rs with the SAME
// intended effect; the harness asserts candor-java and candor-scan infer the same set. JDK-only.
public class Cases {
  // --- direct vocabulary ---
  public static void fs_read() throws Exception { Files.readAllBytes(Path.of("/tmp/x")); }
  public static void net_connect() throws Exception { new java.net.Socket("example.com", 80); }
  public static void exec_spawn() throws Exception { new ProcessBuilder("ls").start(); }
  public static void env_read() { System.getenv("PATH"); }
  public static void clock_now() { long t = System.currentTimeMillis(); }
  public static int pure_fn() { return 1 + 2; }

  // --- the trust contract: an unanalysable call is Unknown ---
  public static void unknown_dyn(String cls) throws Exception { Class.forName(cls); }

  // --- composition: union + transitive propagation ---
  public static void combined() throws Exception { Files.readAllBytes(Path.of("/tmp/x")); new java.net.Socket("h", 1); }
  public static void transitive_leaf() throws Exception { Files.readAllBytes(Path.of("/tmp/x")); }
  public static void transitive_caller() throws Exception { transitive_leaf(); }

  // --- effect inside a locally-invoked lambda flows to the enclosing method ---
  public static void closure_effect() {
    Runnable r = () -> { try { Files.readAllBytes(Path.of("/tmp/x")); } catch (Exception e) {} };
    r.run();
  }

  // --- Unknown propagates across a call like any other effect ---
  public static void unknown_propagates(String s) throws Exception { unknown_dyn(s); }

  // --- a method with BOTH an opaque call and a concrete effect ---
  public static void mixed_unknown(String s) throws Exception { Class.forName(s); Files.readAllBytes(Path.of("/tmp/x")); }

  // --- a 3-hop chain a -> b -> c(Net) ---
  public static void hop_c() throws Exception { new java.net.Socket("h", 1); }
  public static void hop_b() throws Exception { hop_c(); }
  public static void hop_a() throws Exception { hop_b(); }

  // --- a caller unions the effects of two distinct callees ---
  public static void union_b() throws Exception { Files.readAllBytes(Path.of("/tmp/x")); }
  public static void union_c() throws Exception { new java.net.Socket("h", 1); }
  public static void union_a() throws Exception { union_b(); union_c(); }

  // --- recursion: the fixpoint must terminate AND keep the effect ---
  public static void recurse(int n) { if (n > 0) { System.getenv("X"); recurse(n - 1); } }

  // --- an effect in one branch only is still inferred (over-approximation) ---
  public static void conditional(boolean b) throws Exception { if (b) new ProcessBuilder("x").start(); }

  // --- transitive purity: a -> b -> c, all pure, stays pure (negative) ---
  public static int pure_c() { return 3; }
  public static int pure_b() { return pure_c(); }
  public static int pure_a() { return pure_b(); }
}
