# Changelog

## 1.7.2 - 2026-08-13

- **18.06/Lede install failure fixed (issue #1)**: the hard `firewall4` dependency is gone (the plugin configures nftables itself and never talks to the firewall4 daemon; on 18.06-style feeds the unresolvable dependency made opkg reject the whole package with `cannot find dependency firewall4` / `incompatible with the architectures configured`). The Makefile and the IPK builder now depend on the actual runtime needs (`nftables`, `kmod-nft-tproxy`, `kmod-nft-socket`); `init.d` preflights `nft`/`sing-box` and fails with a readable log message on firmwares that cannot run the gateway. Requirements and a dedicated troubleshooting entry (README zh/en, INSTALL, TROUBLESHOOTING zh/en) document the 18.06 situation.
- Review fixes (openwrt-ai round 5): the Save button now goes through the supported `handleSave` view hook only — the DOM-patching workaround was removed (it co-registered a second click listener with LuCI's own, double-saving and applying without being asked; `stopPropagation` cannot suppress it), and `handleSave` commits the 24.10 session-scoped changeset via `ui.changes.apply(true)` with a guard for older LuCI; the DHCP binding column reads the dnsmasq lease file from `dhcp.@dnsmasq[0].leasefile` like `dhcp-sync.sh` (ACL now also covers `/etc/dhcp.leases`); `compiler.sh` rejects WireGuard `reserved` values with empty elements (`1,,2`, `,1`, `1,`); imports restore `+` in `pinSHA256` (and standard-base64 `pbk`/`sid`); `dhcp-sync.sh` allowlists hostnames to `[A-Za-z0-9_-]` (≤63 chars; backslash, `.`-leading and control characters included) and logs a failed dnsmasq restart instead of hiding it; the dead `$auxiliary` guard field was removed from `init.d`; `.pot`/`.po` entry gap fixed. 53/53 tests pass.

## 1.7.1 - 2026-08-11

- Activity log now marks sustained encrypted communication as **"Call in progress (inferred from sustained encrypted traffic)"** (`likely_call`): sustained bidirectional traffic after registration is the RTP signature of ringing/an in-call voice stream. The IPsec tunnel stays fully encrypted, so SMS cannot be reliably distinguished (short bursts look like keepalives/pushes) and is not logged; numbers, content and call direction remain invisible. Docs (README / CONFIGURATION, zh + en) now explain the DHCP static-binding rationale and the monitoring capability boundary.
- Review fixes (openwrt-ai): `dhcp-sync.sh` scrubs dnsmasq `dhcp-host` names (spaces/commas/quotes/semicolons would make dnsmasq reject the host line, breaking LAN DNS/DHCP) and reads the lease file from `dhcp.@dnsmasq[0].leasefile`; `compiler.sh` fails early with node-specific messages for missing wireguard keys/address or non-numeric `reserved`/`mtu`; `wg://` import restores `+` in base64 keys; `local` declarations in init.d; `.pot`/`.po` re-sorted to ASCII order. 49/49 tests pass.

## 1.7.0 - 2026-08-11

- **DHCP static leases are now auto-managed from device policies**: the nftables policy rules match a fixed client IPv4, but hand-made DHCP bindings silently broke when a device's MAC changed (iOS rotates its private Wi-Fi address) or when a policy was edited. A new `dhcp-sync.sh` runs on every service start: it creates/updates `wfc_`-prefixed DHCP host bindings from the live lease table (so a policy IP in use by a device always pins the device's current MAC), drops bindings whose policy was removed, and only touches plugin-created hosts (user-managed ones are left alone). `dnsmasq` is restarted only when something changed.
- LuCI device policies gained a **DHCP binding** status column (Bound / MAC changed, rebind on reconnect / Not bound yet / Device offline / Following gateway), backed by new read ACLs for `dhcp` and `/tmp/dhcp.leases`.
- Version bumped to 1.7.0; docs updated (README, README_EN).

## 1.6.0 - 2026-08-11

- Added **Trojan** and **WireGuard** proxy node protocols: Trojan emits a sing-box `trojan` outbound (`password` + TLS with SNI/ALPN/insecure/pin); WireGuard works with every sing-box generation — `init.d` detects the installed version and emits the **wireguard endpoint** form (route rules target the endpoint tag) for sing-box ≥ 1.11, or the legacy wireguard **outbound** for 1.10.x and older. The legacy outbound was deprecated in 1.11.0 (gated behind `ENABLE_DEPRECATED_WIREGUARD_OUTBOUND`) and removed in 1.13.0, so this was verified with `sing-box check` against 1.10.0 / 1.11.7 / 1.12.0 / 1.13.18 real binaries.
- Share-link import now accepts `trojan://` and `wg://` (WireGuard, Clash Meta / sing-box style: `wg://<peer-public-key>@<server>:<port>?private_key=…&local_address=…&reserved=…&mtu=…`); imported nodes map into UCI and never leave the browser.
- Node health probe falls back to `tcping` for Trojan (TCP-based) when ICMP is blocked; WireGuard stays ICMP-only (UDP).
- LuCI node form gained the WireGuard fields (private key, local address, reserved, MTU); protocol list and import panel text updated, with new Simplified Chinese translations.
- Version bumped to 1.6.0; docs updated (README, README_EN, CONFIGURATION zh/en).

## 1.5.0 - 2026-08-10

- Aligned IPK packaging with the official OpenWrt `scripts/ipkg-build` format (gzip tar of `debian-binary`, `data.tar.gz`, `control.tar.gz`); verified compatible with the real opkg in an official OpenWrt 24.10.8 rootfs and by an upgrade install on an ImmortalWrt 24.10.6 router (service running).
- Unified to a single universal `.ipk` for OpenWrt / ImmortalWrt / iStoreOS (24.10 based): the `sing-box` dependency is left unversioned so feeds shipping an older sing-box (e.g. iStoreOS) still satisfy it. Verified by a forced reinstall on an ImmortalWrt 24.10.6 router (service running) and parsing on iStoreOS / OpenWrt 24.10.8; install docs recommend using an absolute path (some opkg builds report a misleading "No such file or directory" for `./` relative paths). iStoreOS was further verified on the **24.10.7 full firmware under QEMU** (same version as the reported issue): install + service active + LuCI Settings/Status/Activity Log pages all working in Simplified Chinese; where the iStoreOS custom opkg rejects local files with `incompatible with the architectures configured`, an extract install (`tar xzf data.tar.gz -C /`) is documented and verified.
- Fixed the OpenWrt 25.12 `.apk` architecture: 25.12 apk-based repos ship every package with a concrete target arch and reject `arch: all` with "uninstallable". The build now defaults to **`noarch`** (accepted by the 25.12 apk and architecture-independent), verified with the exact user command (`apk add --allow-untrusted`) on official 25.12.3 rootfs for **x86_64, aarch64, armv7 and mipsel** — one APK covers every target.
- Added `scripts/build-apk.sh` to build the OpenWrt 25.12 `.apk` (apk-tools v3 via Docker Alpine, `ARCH` overridable, defaults to `noarch`).
- Dropped the hard `tcping` dependency (not present in official feeds); node-health probes now use `tcping` only when installed and otherwise fall back to ICMP.
- Fixed VLESS Reality / VMess TLS generation in `compiler.sh` (TLS block emitted for `security=tls` and Reality, `server_name` omitted when SNI is empty, `alter_id` coerced to a number) and the matching security field in the LuCI node form.
- Cleared stale `status.json` on service start and stop so the Wi-Fi Calling status page no longer shows old data after device edits or when the gateway is disabled; `monitor.state` is deliberately kept as the monitor's per-device baseline to avoid fabricated handshake events on restart.
- Hardened `init.d` (firewall.sh exit-status check with cleanup, delimiter guards on node/device names, vmess auxiliary/flow handling) and made `firewall.sh` exit cleanly when no clients are configured.
- Removed the unused `monitor_interval` config option.

## 1.4.0 - 2026-08-08

- Added a complete Simplified Chinese (zh-cn) LuCI translation catalog compiled into a real `.lmo` language pack and packaged into the IPK, so Chinese renders on the router instead of only in source.
- Chinese interface now shows unified Chinese descriptions, status, and error messages; protocol names and technical fields (TLS, UDP, UUID, SNI, ALPN, Reality, WebSocket, ePDG, IMS, ASSURED, QUIC, etc.) stay in English.
- Wrapped `node-import.js` error messages and the status/activity machine values (registered, connecting, sustained traffic, etc.) with `_()` so they translate in the UI instead of leaking raw English strings.
- Ships the language pack to both `/usr/lib/lua/luci/i18n/` and `/usr/share/luci/i18n/` for legacy Lua and modern ucode LuCI compatibility.
- Added a portable `scripts/po2lmo.py` (byte-compatible with luci-base `po2lmo`) so translations rebuild from `po/` on every package build.
- Refined the encrypted IMS activity log to record only handshake success/failure and sustained encrypted communication (ringing or calls lasting a few seconds); brief traffic bursts are no longer logged.
- Added an "Activity log" on/off toggle (default enabled) so observation logging can be disabled entirely from the Settings page; the activity log page then reports that recording is off.
- Restructured for official feed inclusion: `PKG_MAINTAINER`/`LUCI_URL` set, `po/` uses the gettext code `zh_Hans` with a `po/templates/` template, and `build-ipk.sh` aliases `zh_Hans`->`zh-cn` mirroring `luci.mk`'s `LUCI_LC_ALIAS`.
- Verified ImmortalWrt 25.12 compatibility (ucode dispatcher i18n path, `LUCI_LC_ALIAS`, and `sing-box`/`firewall4`/`kmod-nft-tproxy` deps match 24.10). Documented distribution via Releases, self-hosted opkg feed, and the ImmortalWrt official feed path.

## 1.3.0 - 2026-08-07

- Added local paste-import for AnyTLS, Hysteria2/Hy2, TUIC, VLESS, and VMess share links.
- Maps labels, credentials, TLS/SNI, Reality, WebSocket, UDP, and transport-specific fields into UCI nodes.
- Keeps imported links inside the LuCI browser session and never logs the raw URI.
- Package release 2 fixes the parser module factory for LuCI's `baseclass` loader.

## 1.2.1 - 2026-08-07

- Replaced per-poll event spam with one-time registration transitions and time-windowed sustained-traffic summaries.
- Requires traffic in three consecutive samples before writing a sustained activity event.
- Added configurable aggregation interval and per-device retention limit (defaults: 60 seconds and 20 records).

## 1.2.0 - 2026-08-07

- Split configuration, live Wi-Fi Calling status, and encrypted IMS activity into separate LuCI pages.
- Added automatic activity refresh, record count, and confirmation-protected log clearing.
- Restricted log write access to this plugin's activity file only.

## 1.1.1 - 2026-08-07

- Fixed LuCI runtime file access on OpenWrt systems where `/var/run` resolves to `/tmp/run`.
- Kept credential-bearing configuration private while exposing only non-secret monitoring data.

## 1.1.0 - 2026-08-07

- Integrated node alive state, measured latency, and quality bands directly into the Proxy nodes grid.
- Removed the duplicate Observed node reachability panel.
- Expanded device monitoring with Wi-Fi Calling registration, ePDG, UDP 500/4500, ASSURED, packet totals, deltas, and last activity.
- Added a capped encrypted IMS activity log while explicitly avoiding unsupported call/SMS identification claims.

## 1.0.1 - 2026-08-07

- Fixed empty LuCI monitoring tables by granting the required read-only `ubus.file.read` permission for the two runtime status files.
- Added a regression test for runtime status ACL access.

## 1.0.0 - 2026-08-07

- First stable release.
- Added AnyTLS, Hysteria2, TUIC, VLESS Reality, and VMess WebSocket nodes.
- Added per-device independent/follow-gateway routing and PassWall coexistence.
- Added node reachability and ePDG/IPsec UDP 500/4500 evidence views.
- Added startup validation, restrictive credential permissions, tests, CI, and bilingual documentation.
