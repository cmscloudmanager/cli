D("$zone", NewRegistrar("none", "NONE"), DnsProvider(NewDnsProvider("hetzner", "HETZNER")),
    NO_PURGE,
    A("$name", "$ip"),
);
