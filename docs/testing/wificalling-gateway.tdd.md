# Wi-Fi Calling Gateway TDD evidence

This file records the RED/GREEN evidence for the project. It is completed after implementation.

## User journeys

1. An administrator can add AnyTLS, Hysteria2, TUIC, VLESS Reality, and VMess WS nodes without exposing credentials in status output.
2. An administrator can assign one or several private LAN IPv4 addresses to one node; conflicting assignments are rejected.
3. A selected device is transparently routed for TCP and UDP while other LAN devices are untouched.
4. The status monitor distinguishes no session, IKE negotiation, and a bidirectional ASSURED UDP 4500 session.
5. The UI describes observed network evidence and never claims carrier activation solely from an icon or UDP flow.

## Evidence

- RED: `python3 -m unittest discover -s tests -v` executed 8 initial tests; 7 failed because the compiler/monitor did not exist and the package-surface test failed because the package files did not exist.
- GREEN: the v1.1 runner executes 24 tests successfully, covering all five original journeys plus integrated node quality, Wi-Fi Calling evidence, encrypted IMS event logging, invalid protocol, duplicate IP, non-private IP, unrelated-device traffic, PassWall bypass, package format, release metadata, documentation, and LuCI regressions.
- Static checks: every router shell file passes `sh -n`; both LuCI JSON manifests parse; the LuCI JavaScript passes `node --check`; a secret-marker scan found no credentials from earlier diagnostics.
- Acceptance-criterion coverage: 5/5 journeys (100%). A shell line-coverage tool is not installed on the development host, so this report does not invent a numeric source-line percentage.
- Target-router validation: passed on Redmi AX6S, ImmortalWrt 24.10.6 (`aarch64_cortex-a53`) with sing-box 1.13.16. The installed package passed `sing-box check`, kept both procd instances alive, installed scoped nftables TProxy rules, routed only `192.168.31.189`, established the configured AnyTLS tunnel, and observed an ASSURED bidirectional UDP 4500 flow to an ePDG endpoint. Carrier voice activation still requires a completed call or carrier confirmation.

## Target findings folded back into the implementation

- ImmortalWrt 24.10.6 OPKG expects a gzip-compressed tar IPK envelope; the build test now fixes that format.
- Package payload ownership is forced to root/root.
- Dedicated ports 11441/11442 avoid the PassWall 1041 listener.
- UCI and generated credential-bearing configuration are forced to mode 0600.
- TProxy rules include counters for target-side traffic evidence.
- Hysteria2 TLS public-key pins are accepted in sing-box Base64 form and covered by a compiler test; imported hexadecimal pins must be converted before storage.
- LuCI `ListValue` options are populated with separate calls because `.value()` is not chainable on the target LuCI release; a regression test prevents the original `undefined.value` crash. Password summaries are masked in the node grid.
- Node and device sections now use generated internal IDs and required user-facing labels. Device IP fields include a fixed-IPv4 example and the node selector lists all saved display names.
- Node health runs every 30 seconds. It reports ICMP latency when available, falls back to port-specific TCP latency for AnyTLS/VLESS/VMess, and uses the neutral `no_icmp_reply` state for UDP-only Hysteria2/TUIC servers that block ping.
- Each device now selects `independent` or `follow_gateway`. Only independent devices enter the compiler client map, TProxy set, and a runtime PassWall bypass. The bypass is nftables-scoped, removed when the plugin stops, and re-established by the monitor after PassWall reloads. Target validation confirmed automatic restoration after a real PassWall restart.
