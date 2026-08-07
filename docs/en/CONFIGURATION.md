# Configuration

Create and save a node before creating device policies. AnyTLS/Hysteria2 use a password; TUIC uses UUID and password; VLESS Reality uses UUID, flow, SNI, public key, short ID and fingerprint; VMess WS uses UUID, Host and path. TLS public-key pins must be Base64 SHA-256 values. The Proxy nodes grid displays alive state, measured latency, and a quality band; this is reachability evidence rather than a full proxy handshake.

Reserve each client IPv4 with DHCP. **Independent tunnel** bypasses PassWall and uses the selected node. **Follow gateway** is not intercepted and continues through the normal gateway/PassWall policy. One IP cannot belong to two independent policies. v1.0 intercepts IPv4 only.

The states progress from `no_session` to `negotiating` (UDP 500), `nat_t_seen` (UDP 4500), `likely_registered` (bidirectional ASSURED UDP 4500), and `active_traffic` (higher packet count). They are network observations, not carrier activation results.

The monitor retains the latest 100 encrypted IMS activity events with timestamps, state changes, and packet deltas. Calls and SMS are encrypted inside IPsec, so the router cannot identify numbers or content and cannot reliably distinguish a call from a text message.

Independent clients receive temporary `WFC_GATEWAY_BYPASS` return rules in PassWall. The monitor restores them after a PassWall reload and removes them when the plugin stops.
