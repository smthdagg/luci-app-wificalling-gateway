# Changelog

## 1.5.0 - 2026-08-10

- Fixed the local `build-ipk.sh` to produce a standard `ar`-format IPK (Debian binary format 2.0) instead of a gzip tar, which some opkg builds (e.g. iStoreOS) reject with a misleading "No such file or directory" during install.
- Added an iStoreOS-specific package variant: `scripts/build-ipk.sh <version> istoreos` emits `luci-app-wificalling-gateway_<version>_istoreos_all.ipk` with an unversioned sing-box dependency so iStoreOS feeds with an older sing-box still satisfy it; install docs recommend copying the package to `/tmp` first.
- Added `scripts/build-apk.sh` to build the OpenWrt 25.12 `.apk` (apk-tools v3 via Docker Alpine) in the same way the Release artifact is produced.
- Dropped the hard `tcping` dependency (not present in official feeds); node-health probes now use `tcping` only when installed and otherwise fall back to ICMP.
- Fixed VLESS Reality / VMess TLS generation in `compiler.sh` (TLS block emitted for `security=tls` and Reality, `server_name` omitted when SNI is empty, `alter_id` coerced to a number) and the matching security field in the LuCI node form.
- Cleared stale `status.json` / `monitor.state` on service start so the Wi-Fi Calling status page no longer shows old data after device edits.
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
