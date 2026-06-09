package ex.cart; import ex.pricing.Pricing; public class Cart { public static long total(long c){ return Pricing.quote(c); } }
