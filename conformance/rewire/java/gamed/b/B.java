package b; public class B { public static void work(){ try { java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/x")); } catch(Exception e){} } }
