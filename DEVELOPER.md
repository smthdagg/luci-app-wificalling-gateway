# Development & Maintenance Guide

This document is the handoff reference for contributors and automated agents taking over this project. It covers architecture, build/test flows, release process, upstream PR workflow, and known pitfalls learned in the field.

## Repository layout

```
Makefile                     OpenWrt/LuCI package definition (feed include)
README.md / README_EN.md     User documentation (bilingual)
CHANGELOG.md / SECURITY.md
DEVELOPER.md                 This file
root/
  etc/config/wificalling-gateway        UCI defaults (secrets never stored)
  etc/init.d/wificalling-gateway        procd service: config -> compiler -> firewall -> monitor
  usr/libexec/wificalling-gateway/
    compiler.sh        pipe-delimited normalized.conf -> sing-box.json (awk)
    firewall.sh        nftables TPROXY rules for listed clients
    monitor.sh         per-device ePDG/IPsec evidence + activity events
    monitor-loop.sh    periodic monitor driver
    node-health.sh     ICMP/tcping reachability + latency JSON
    dhcp-sync.sh       auto-manage DHCP static leases (wfc_ hosts) from device policies
    passwall-bypass.sh optional: exempt gateway clients from passwall interception
  usr/share/luci/menu.d/  rpcd/acl.d/
htdocs/luci-static/resources/
  view/wificalling-gateway/{overview,status,events}.js   LuCI views
  wificalling-gateway/node-import.js                      share-link parser (browser-side)
po/templates + po/zh_Hans        i18n (.pot template + zh-cn catalog)
scripts/  tests/  docs/testing/  outputs/    Developer-only (gitignored, not published)
dist/                            Built artifacts (gitignored)
```

## Core data flow

1. **init.d `start_service`**: reads UCI → writes `normalized.conf` (pipe-delimited) + `clients` (label|ip|node) + `nodes` (health list) into `/var/run/wificalling-gateway/`.
2. **dhcp-sync.sh**: reconciles `wfc_`-prefixed DHCP host bindings (MAC→IP) with the device policies, from the live lease table. Runs on every service start; restarts dnsmasq only when something changed.
3. **compiler.sh**: `normalized.conf` → `sing-box.json` (single tproxy process, 11441/11442). WireGuard is emitted as a sing-box **endpoint** (route rules target the endpoint tag) when `global|wireguard_style|endpoint`, else the legacy outbound — selected by init.d from the installed sing-box version.
4. **firewall.sh**: nftables `table inet wificalling_gateway` — prerouting rules matching `clients4` set → tproxy to sing-box.
5. **monitor.sh**: parses `nf_conntrack` for UDP 500/4500 flows per client; writes `status.json` + activity events (`handshake_success` / `handshake_failed` / `sustained_traffic`).

## Local development loop

```sh
# Tests (45 as of 1.7.0)
python3 -m unittest discover -s tests

# Syntax checks
for f in root/etc/init.d/wificalling-gateway root/usr/libexec/wificalling-gateway/*.sh scripts/*.sh; do sh -n "$f"; done
for f in htdocs/luci-static/resources/view/wificalling-gateway/*.js htdocs/luci-static/resources/wificalling-gateway/*.js; do node --check "$f"; done

# i18n (after touching strings): update po/templates + po/zh_Hans in sync, then
python3 scripts/po2lmo.py po/zh_Hans/wificalling-gateway.po /tmp/test.lmo

# Build (version is the single source of truth in Makefile + build scripts)
./scripts/build-ipk.sh 1.7.0-1
./scripts/build-apk.sh 1.7.0-r1        # requires Docker (alpine:edge apk mkpkg)

# Package sanity
git diff --check    # whitespace; also run the PackageTests suite
```

## Versioning & release

- Version lives in `Makefile` (`PKG_VERSION`), `scripts/build-ipk.sh` (`version=${1:-...}`) and `scripts/build-apk.sh`. The PR forks' `Makefile` intentionally has **no** `PKG_VERSION` (upstream LuCI style).
- Bump in `CHANGELOG.md` with dated entry. Update README install commands on every release.
- Release artifacts: `.ipk` (gzip tar of `debian-binary`/`data.tar.gz`/`control.tar.gz` — the official ipkg-build format, **not** ar) and `.apk` (noarch, apk-tools v3 via Docker).

## Upstream PR workflow (important)

Two parallel PRs exist, from **two different forks**:

| Target | Fork | PR |
|---|---|---|
| `immortalwrt/luci` | `smthdagg/luci` | #694 |
| `openwrt/luci` | `smthdagg/luci-1` | #8921 |

- Both use branch `luci-app-wificalling-gateway`; the package lives under `applications/luci-app-wificalling-gateway/` (19 files, no README_EN/SECURITY/docs — only what the feed wants).
- **Reviewer is an automated AI bot (`openwrt-ai`) plus FormalityCheck CI.** Rules that have bitten us:
  - Commit subject ≤ 80 chars, `luci-app-wificalling-gateway: ` prefix, `Signed-off-by:` line, author/committer = real full name (`Smth Dagg <smthdagg@gmail.com>` — the local git identity is `Ethan.Y`, always override with `-c user.name=... -c user.email=...`).
  - `git diff --check` clean; Makefile SPDX header stays; tabs not spaces in shell.
  - When updating the PRs: copy changed files from the release repo into both fork checkouts, run the full local verification, commit with the proper identity, push, then wait for FormalityCheck (three jobs) to pass. Force-push only when amending your own unpushed commit.
- The immortalwrt PR's `Test Formalities` failure is an upstream workflow issue (`pull_request_target` + checkout without `allow-unsafe-pr-checkout`), affecting all fork PRs — not a submission defect; it is documented in the PR thread.

## Known pitfalls (field-learned, keep these in mind)

1. **LuCI 24.10 "Save" button**: `Map.save()` alone never commits the session-scoped UCI changeset (only `apply` does), and the default footer Save handler resolves the Map via a DOM instance lookup that silently fails on this firmware. `overview.js` binds the footer Save button directly to `m.save().then(() => ui.changes.apply(true))`. Do not "simplify" this back to a plain `map.save()`.
2. **DummyValue in grid edit modals** renders its (always null) `cfgvalue`; the DHCP binding column overrides `renderWidget` and sets `rmempty = true` (without it the save parse rejects "must not be empty"). Grid rows use `textvalue`.
3. **Delimiter guard vs labels**: `normalized.conf` is pipe-delimited; the guard covers every field that enters it. `label` must be **excluded** (subscription labels routinely contain `|`, e.g. `HK01|BGP|CMCU`) and sanitized in the `nodes`/`clients` files (`tr '|' ' '`).
4. **Lease file format**: dnsmasq `/tmp/dhcp.leases` lines are `expiry MAC IP hostname clientid` — IP is field 3, MAC is field 2 (both `dhcp-sync.sh` and `overview.js` parse this).
5. **Exit nodes**: only TCP-based protocols (anytls/vless/vmess/trojan) are reliable gateway exits. Hysteria2/TUIC "alive" only proves ICMP; a dead UDP proxy path left a routed device with no internet. WireGuard needs sing-box ≥ 1.11 (endpoint form; legacy outbound removed in 1.13).
6. **iOS private Wi-Fi MACs rotate** — this silently breaks manual DHCP bindings; `dhcp-sync.sh` heals them at service start, and the device just needs to reconnect Wi-Fi.
7. **i18n discipline**: every new UI string must appear in both `po/templates/*.pot` and `po/zh_Hans/*.po` (msgid must match exactly; keep alphabetical order); the zh catalog must compile with `po2lmo.py`.

## Verifying on the reference router

The reference device is an ImmortalWrt 24.10.6 Redmi AX6S (sing-box 1.13.16) with several real subscription nodes and an iPhone policy. Standard verification after deploying:

- `opkg install --force-reinstall` the new IPK, restart `rpcd` and the service.
- Check `status.json`, `sing-box.json` (compile output), `clients`, nftables `clients4`, `wfc_` DHCP hosts, `node-status.json`.
- Browser: settings page renders the DHCP binding column and the Save button persists edits; add/remove a device policy and confirm the `wfc_` lease appears/disappears.
- Confirm routing: the policy device's egress IP matches the node country (e.g. via ip.sb).

Credentials and exact router access are documented in the private handoff file (not in this repository).
