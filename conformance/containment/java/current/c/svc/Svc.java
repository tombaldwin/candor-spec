package c.svc;
// current: svc does Net (its own effect) AND has started touching Fs — the drift the ratchet catches.
public class Svc {
  public static void net()  throws Exception { new java.net.Socket("h", 80).getInputStream(); }
  public static void leak() throws Exception { new java.io.FileInputStream("c").read(); }
}
