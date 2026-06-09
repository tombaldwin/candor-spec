import java.nio.file.*;
public class Cases {
  public static void fs_read() throws Exception { Files.readAllBytes(Path.of("/tmp/x")); }
  public static void net_connect() throws Exception { new java.net.Socket("example.com", 80); }
  public static void exec_spawn() throws Exception { new ProcessBuilder("ls").start(); }
  public static void env_read() { System.getenv("PATH"); }
  public static void clock_now() { long t = System.currentTimeMillis(); }
  public static int pure_fn() { return 1 + 2; }
  public static void unknown_dyn(String cls) throws Exception { Class.forName(cls); }
  public static void combined() throws Exception { Files.readAllBytes(Path.of("/tmp/x")); new java.net.Socket("h", 1); }
  public static void transitive_leaf() throws Exception { Files.readAllBytes(Path.of("/tmp/x")); }
  public static void transitive_caller() throws Exception { transitive_leaf(); }
}
