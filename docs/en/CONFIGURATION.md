# Configuration

Use **Import node link** to paste one AnyTLS, Hysteria2/Hy2, TUIC, VLESS, or VMess share link. Parsing happens locally in the browser and is not sent to an external service. Review the imported server, port, SNI, TLS, and protocol-specific fields before testing. Manual entry remains available. AnyTLS/Hysteria2 use a password; TUIC uses UUID and password; VLESS Reality uses UUID, flow, SNI, public key, short ID and fingerprint; VMess WS uses UUID, Host and path. TLS public-key pins must be Base64 SHA-256 values. The Proxy nodes grid displays alive state, measured latency, and a quality band; this is reachability evidence rather than a full proxy handshake.

Reserve each client IPv4 with DHCP. **Independent tunnel** routes through the selected plugin node. **Follow gateway** is not intercepted and uses the router's default routing. One IP cannot belong to two independent policies. The plugin intercepts IPv4 only.

LuCI provides separate **Settings**, **Wi-Fi Calling Status**, and **Activity Log** pages. The status page shows registration evidence, ePDG, UDP 500/4500, ASSURED, packet totals, and last activity. The activity page refreshes automatically, displays the record count, and can clear the plugin activity file after confirmation.

The states progress from `no_session` to `negotiating` (UDP 500), `nat_t_seen` (UDP 4500), `likely_registered` (bidirectional ASSURED UDP 4500), and `active_traffic` (higher packet count). They are network observations, not carrier activation results.

The monitor records handshake success/failure transitions once. Encrypted traffic must persist for a few seconds (≥3 s threshold, about 5 s with 5 s polling) before it is treated as sustained communication, then packet deltas are aggregated into a configurable time window (60 seconds by default). Each device independently retains a configurable number of newest records (20 by default), and the activity log can be turned off in Settings. Calls and SMS are encrypted inside IPsec, so the router cannot identify numbers or content and cannot reliably distinguish a call from a text message. Clearing this history does not modify system logs, nodes, or device policies.

## Wi-Fi Calling tips

The following are device-side observations, **not plugin features**.

### Protocol choice

The ePDG/IPsec tunnel is highly sensitive to packet loss and jitter. In practice **AnyTLS** works best: it encapsulates UDP (ePDG 500/4500) inside a TCP/TLS stream, providing reliable, ordered delivery so both IPsec keepalives and voice media (RTP) are transmitted without loss. UDP/QUIC-based protocols (Hysteria2, TUIC) can establish the ePDG tunnel and display the Wi-Fi Calling indicator, but **placing a call causes an immediate disconnect** -- UDP-in-UDP jitter and loss on the public network cannot sustain the RTP voice stream.

### Device location

The carrier verifies the device-reported location (wloc) for its service area (for emergency calls). This plugin only provides a UK IP and does not control device location. The device must use a virtual location tool to set its position to the UK, otherwise Wi-Fi Calling will not trigger.

Steps:

1. On the iPhone, use [ios-location-spoofer](https://github.com/smthdagg/ios-location-spoofer) with Shadowrocket to spoof the location to the UK. This is a separate project.
2. Confirm the location is set (map shows UK).
3. **Turn off Shadowrocket.** If left on, its VPN tunnel conflicts with the router plugin's TPROXY, causing a double-proxy issue that prevents the ePDG handshake from completing.
4. Wait a few minutes; the router activity log will show an ePDG handshake (handshake_success) and Wi-Fi Calling activates.
