package domain;
public class Domain {
    public static void inner() throws Exception { infra.Infra.fetch(); }
    public static void top() throws Exception { api.Api.mid(); }
}
