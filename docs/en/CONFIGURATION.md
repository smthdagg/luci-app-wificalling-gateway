# Configuration

Use **Import node link** to paste one AnyTLS, Hysteria2/Hy2, TUIC, VLESS, VMess, Trojan (trojan://) or WireGuard (wg://) share link. Parsing happens locally in the browser and is not sent to an external service. Review the imported server, port, SNI, TLS, and protocol-specific fields before testing. Manual entry remains available. AnyTLS/Hysteria2/Trojan use a password; TUIC uses UUID and password; VLESS Reality uses UUID, flow, SNI, public key, short ID and fingerprint; VMess WS uses UUID, Host and path; WireGuard uses a private key, peer public key and local address, with optional reserved bytes and MTU. TLS public-key pins must be Base64 SHA-256 values. The Proxy nodes grid displays alive state, measured latency, and a quality band; this is reachability evidence rather than a full proxy handshake.

**Why the IP must be fixed**: the plugin identifies devices by IP -- the policy `source_ip` is written into the nftables `clients4` set and only matching traffic is TPROXY-forwarded. If the device's actual IP differs from the policy, the rules never match. The DHCP static lease (MAC->IP binding) is maintained automatically since 1.7.0: adding a policy binds the current leaser's MAC, removing a policy cleans the binding, and rotated iOS private MACs are re-bound when the device reconnects (synced at every service start). The policy table's **DHCP binding** column shows the live state (Bound / Not bound yet / MAC changed, rebind on reconnect / Device offline). Device names are sanitized for the dnsmasq host-name field (spaces, commas, quotes, semicolons removed).

**Independent tunnel** routes through the selected plugin node. **Follow gateway** is not intercepted and uses the router's default routing. One IP cannot belong to two independent policies. The plugin intercepts IPv4 only.

LuCI provides separate **Settings**, **Wi-Fi Calling Status**, and **Activity Log** pages. The status page shows registration evidence, ePDG, UDP 500/4500, ASSURED, packet totals, and last activity. The activity page refreshes automatically, displays the record count, and can clear the plugin activity file after confirmation.

The states progress from `no_session` to `negotiating` (UDP 500), `nat_t_seen` (UDP 4500), `likely_registered` (bidirectional ASSURED UDP 4500), and `active_traffic` (higher packet count). They are network observations, not carrier activation results.

The monitor records handshake success/failure transitions once. Encrypted traffic must persist for a few seconds (≥3 s threshold, about 5 s with 5 s polling) before it is treated as sustained communication, then packet deltas are aggregated into a configurable time window (60 seconds by default). Each device independently retains a configurable number of newest records (20 by default), and the activity log can be turned off in Settings.

**Monitoring capability boundary**: the ePDG/IPsec tunnel (inside UDP 4500) is fully encrypted -- the router only sees outer packet counts. Sustained bidirectional traffic after registration (the RTP signature of ringing or an in-call voice stream) is logged as **"Call in progress (inferred from sustained encrypted traffic)"**; SMS cannot be reliably distinguished (short bursts look like keepalives/pushes) and is therefore not logged; phone numbers, message content and call direction are never visible. Clearing this history does not modify system logs, nodes, or device policies.

## 18.06/Lede: command-line configuration (no LuCI pages)

The 18.06 LuCI is the legacy Lua dispatcher and cannot render this plugin's JS pages (19.07+ architecture), so the 18.06 package variant registers no menu. Configure everything over UCI from the command line:

```sh
# 1) Global switch
uci set wificalling-gateway.main.enabled=1

# 2) Add a node (named section so the policy can reference it)
uci set wificalling-gateway.hknode=node
uci set wificalling-gateway.hknode.enabled=1
uci set wificalling-gateway.hknode.label='HK AnyTLS'
uci set wificalling-gateway.hknode.protocol=anytls
uci set wificalling-gateway.hknode.server=example.com
uci set wificalling-gateway.hknode.port=443
uci set wificalling-gateway.hknode.password=…   # set your secret the same way; never paste real secrets into public docs
uci set wificalling-gateway.hknode.sni=cdn.example.com

# 3) Add a device policy (node = the node section name)
uci set wificalling-gateway.iphone12=device
uci set wificalling-gateway.iphone12.enabled=1
uci set wificalling-gateway.iphone12.label='iPhone12'
uci set wificalling-gateway.iphone12.route_mode=independent
uci set wificalling-gateway.iphone12.node=hknode
uci add_list wificalling-gateway.iphone12.source_ip=192.168.31.175

uci commit wificalling-gateway
/etc/init.d/wificalling-gateway enable
/etc/init.d/wificalling-gateway restart
```

Required fields per protocol match the LuCI form: `password` for AnyTLS/Hysteria2/Trojan; `uuid`+`password` for TUIC; `uuid`+`flow`+`public_key`+`short_id`+`fingerprint` for VLESS Reality; `uuid`+`transport=ws`+`path`+`host` for VMess WS; `private_key`+`public_key`+`local_address` for WireGuard (optional `reserved`/`mtu`). `route_mode` is `independent` (tunnel through the node) or `follow_gateway` (default routing). On service start the DHCP static leases are synced automatically and `nft`/`sing-box` are preflighted; failures are logged to `logread -e wificalling-gateway`.

## Wi-Fi Calling tips

The following are device-side observations, **not plugin features**.

### Protocol choice

The ePDG/IPsec tunnel is highly sensitive to packet loss and jitter. In practice **AnyTLS** works best: it encapsulates UDP (ePDG 500/4500) inside a TCP/TLS stream, providing reliable, ordered delivery so both IPsec keepalives and voice media (RTP) are transmitted without loss. UDP/QUIC-based protocols (Hysteria2, TUIC) can establish the ePDG tunnel and display the Wi-Fi Calling indicator, but **placing a call causes an immediate disconnect** -- UDP-in-UDP jitter and loss on the public network cannot sustain the RTP voice stream.

### Device location

The carrier verifies the device-reported location (wloc) for its service area (for emergency calls). This plugin provides an IP in the corresponding country via the proxy node, but does not control device location. The device must use a virtual location tool to set its position to the SIM card's home country, otherwise Wi-Fi Calling will not trigger.

Steps:

1. On the iPhone, use [ios-location-spoofer](https://github.com/smthdagg/ios-location-spoofer) with Shadowrocket to spoof the location to the SIM card's home country. This is a separate project.
2. Confirm the location is set (map shows the home country).
3. **Turn off Shadowrocket.** If left on, its VPN tunnel conflicts with the router plugin's TPROXY, causing a double-proxy issue that prevents the ePDG handshake from completing.
4. Wait a few minutes; the router activity log will show an ePDG handshake (handshake_success) and Wi-Fi Calling activates.
