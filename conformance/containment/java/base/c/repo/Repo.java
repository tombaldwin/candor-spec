package c.repo;
// The persistence layer — the proper home of Fs (file I/O).
public class Repo {
  public static void readA() throws Exception { new java.io.FileInputStream("a").read(); }
  public static void readB() throws Exception { new java.io.FileInputStream("b").read(); }
}
