package c.svc;
// base: svc does Net only — Fs is fully contained in repo.
public class Svc {
  public static void net() throws Exception { new java.net.Socket("h", 80).getInputStream(); }
}
