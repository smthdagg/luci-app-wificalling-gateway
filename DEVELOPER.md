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
# Tests (54 as of 1.7.3)
python3 -m unittest discover -s tests

# Syntax checks
for f in root/etc/init.d/wificalling-gateway root/usr/libexec/wificalling-gateway/*.sh scripts/*.sh; do sh -n "$f"; done
for f in htdocs/luci-static/resources/view/wificalling-gateway/*.js htdocs/luci-static/resources/wificalling-gateway/*.js; do node --check "$f"; done

# i18n (after touching strings): update po/templates + po/zh_Hans in sync, then
python3 scripts/po2lmo.py po/zh_Hans/wificalling-gateway.po /tmp/test.lmo

# Build (version is the single source of truth in Makefile + build scripts)
./scripts/build-ipk.sh 1.7.3-1
./scripts/build-ipk.sh 1.7.3-1 1806   # 18.06/Lede variant: deps luci-base/nftables/ip-full only, no menu.d
./scripts/build-apk.sh 1.7.3-r1        # requires Docker (alpine:edge apk mkpkg)

# Package sanity
git diff --check    # whitespace; also run the PackageTests suite
```

## Versioning & release

- Version lives in `Makefile` (`PKG_VERSION`), `scripts/build-ipk.sh` (`version=${1:-...}`) and `scripts/build-apk.sh`. The PR forks' `Makefile` intentionally has **no** `PKG_VERSION` (upstream LuCI style).
- Bump in `CHANGELOG.md` with dated entry. Update README install commands on every release.
- Release artifacts: `.ipk` (gzip tar of `debian-binary`/`data.tar.gz`/`control.tar.gz` — the official ipkg-build format, **not** ar) and `.apk` (noarch, apk-tools v3 via Docker).
- **18.06/Lede**: build a dedicated variant with `./scripts/build-ipk.sh <ver> 1806` — deps are only what the official 18.06 feeds ship (`luci-base`, `nftables`, `ip-full`) and `menu.d` is excluded (the legacy Lua dispatcher cannot serve JS views). Before every release, verify the variant installs on the official 18.06.9 rootfs (`docker import` the rootfs, `opkg install`) — the generic package cannot install there and must never be pointed at 18.06 users.

## Upstream PR workflow (important)

**Only one upstream channel is correct: `openwrt/luci#8921`** (fork `smthdagg/luci-1`, branch `luci-app-wificalling-gateway`). The package lives under `applications/luci-app-wificalling-gateway/` (19 files, no README_EN/SECURITY/docs - only what the feed wants).

> **Do not open an independent PR against `immortalwrt/luci`.** ImmortalWrt's luci repo is a mirror of OpenWrt's; its `CONTRIBUTING.md` explicitly says "open a pull request against the openwrt/luci repository". ImmortalWrt only accepts its own apps that are not in OpenWrt upstream (e.g. `luci-app-passwall`). A normal luci app PR was opened there once (#694) and was **closed without comment by the maintainer (Tianling Shen)** because it should go through OpenWrt upstream. After `openwrt/luci#8921` is merged, ImmortalWrt picks the app up via its regular upstream sync - no separate action needed. (The old `smthdagg/luci` fork #694 can be left closed.)

- **Reviewer is an automated AI bot (`openwrt-ai`) plus FormalityCheck CI.** Rules that have bitten us:
  - Commit subject ≤ 80 chars, `luci-app-wificalling-gateway: ` prefix, `Signed-off-by:` line, author/committer = real full name (`Smth Dagg <smthdagg@gmail.com>` - the local git identity is `Ethan.Y`, always override with `-c user.name=... -c user.email=...`).
  - `git diff --check` clean; Makefile SPDX header stays; tabs not spaces in shell.
  - When updating the PR: copy changed files from the release repo into the fork checkout, run the full local verification, commit with the proper identity, push, then wait for FormalityCheck (three jobs) to pass. Force-push only when amending your own unpushed commit.
  - `gh pr edit` is broken by the Projects-classic GraphQL deprecation; update the PR body via `gh api repos/openwrt/luci/pulls/8921 -X PATCH --input <json>` instead.

## Release workflow (small-version release, 固化流程)

Every small version (1.8.x) follows the same fixed flow. Run `scripts/release.sh <version>` — it bumps the version everywhere, runs the full local verification, builds all three platforms and runs the docker install tests on the official rootfs of each. What it does **not** do: write the CHANGELOG entry, commit, push, or publish the Release — those stay manual (below).

```sh
# 1) Write the CHANGELOG.md entry for the new version FIRST (dated, same
#    style as previous entries). Then:
./scripts/release.sh 1.8.4
#    The script: bumps Makefile/build-ipk.sh/build-apk.sh/tests/README(zh+en)
#    -> unit tests + sh -n + node --check + git diff --check
#    -> builds generic ipk, 18.06 variant ipk, noarch apk
#    -> docker install tests on official rootfs:
#       OpenWrt 24.10.8 (generic ipk via opkg),
#       OpenWrt 18.06.9 (18.06 variant via opkg, distfeeds configured),
#       OpenWrt 25.12.3 (noarch apk via apk --allow-untrusted)
#       (rootfs tarballs cached under dist/rootfs/; docker images cached)
#    -> writes dist/sha256sums-<ver>.txt and prints the manual next steps

# 2) Commit (Smth Dagg identity, Signed-off-by, subject <= 80):
git add -A && git -c user.name="Smth Dagg" -c user.email="smthdagg@gmail.com" commit -s -m "..."
git push origin main

# 3) Sync the PR fork (only the in-scope files) and push:
cp -R htdocs/. /tmp/luci-fork1/applications/luci-app-wificalling-gateway/htdocs/
cp -R root/.  /tmp/luci-fork1/applications/luci-app-wificalling-gateway/root/
cp -R po/.    /tmp/luci-fork1/applications/luci-app-wificalling-gateway/po/
cp Makefile README.md /tmp/luci-fork1/applications/luci-app-wificalling-gateway/
cd /tmp/luci-fork1
git add applications/luci-app-wificalling-gateway/
git -c user.name="Smth Dagg" -c user.email="smthdagg@gmail.com" commit -s -m "luci-app-wificalling-gateway: <lowercase verb> ..."
git push origin luci-app-wificalling-gateway
#    PR commit rules: subject <= 80, prefix + lowercase word, Signed-off-by.

# 4) Check the PR and wait for FormalityCheck (three jobs) to pass:
gh pr checks 8921 --repo openwrt/luci

# 5) Publish the Release (Latest) with the three artifacts + checksums:
cd dist
gh release create v1.8.4 --title "Wi-Fi Calling Gateway 1.8.4" \
  luci-app-wificalling-gateway_1.8.4-1_all.ipk \
  luci-app-wificalling-gateway_1.8.4-1_18.06_all.ipk \
  luci-app-wificalling-gateway_1.8.4-r1_noarch.apk \
  sha256sums-1.8.4.txt
```

Known release pitfalls (all hit in the field):

- **README version drift**: every version bump must update the README install references (current-version line + package filenames in the commands, zh + en). The script does this mechanically — the CHANGELOG entry is the only manual doc edit.
- **18.06 test needs the variant**: the 18.06 docker test must install the `_18.06_all.ipk` (feed-only deps), never the generic ipk — the script swaps the package between the 24.10 and 18.06 runs.
- **Docker mounts**: test packages must live under the repo tree (`dist/rootfs/wfc-pkgs`); macOS Docker Desktop does not share `/tmp`, so `/tmp` mounts come up empty.
- **25.12 rootfs is double-gzipped** (`-generic-targz-rootfs.img.gz` = gzip of tar.gz); the script pipes it through `gzip -dc` twice for `docker import`.
- Release only after FormalityCheck is green on the PR head; the Release and the PR head should always describe the same version.

## Pre-submission checklist (run before every push)

- [ ] **Verify the target repo's contribution rules first** (read its CONTRIBUTING / README) - do not assume the submission channel from memory. This was not done for ImmortalWrt and the PR was closed.
- [ ] `python3 -m unittest discover -s tests` green; `sh -n` / `node --check` / `git diff --check` clean.
- [ ] Version bumped in `Makefile` + `scripts/build-ipk.sh` + `scripts/build-apk.sh` + README install commands + `tests/test_gateway.py` (`test_release_metadata_and_runtime_dependencies`).
- [ ] `.pot` and `.po` in sync, ASCII-sorted, compile with `po2lmo.py`.
- [ ] Commit author/committer = `Smth Dagg <smthdagg@gmail.com>` (override local `Ethan.Y`), `Signed-off-by:` present, subject ≤ 80 chars with `luci-app-wificalling-gateway:` prefix.
- [ ] On the router: install the built IPK, restart rpcd + service, confirm `running`, `clients`, nft `clients4`, `wfc_` DHCP hosts, and the LuCI pages render.

## Known pitfalls (field-learned, keep these in mind)

0. **Assume vs verify** - the meta-pitfall. Several regressions in this project came from confidently asserting something that was never checked: "two parallel PRs, either merges" (ImmortalWrt's CONTRIBUTING says otherwise), "Test Formalities failure is just an upstream workflow issue" (the PR was actually closed for being on the wrong repo), "label with `|` is fine" (the delimiter guard rejected 4 subscription nodes silently), "Hysteria2 node is alive" (ICMP reachable but proxy path dead -> device lost internet), "Map.save() persists" (it never commits the session changeset), "18.06 cannot install, so documenting why is enough" (a dedicated variant whose deps are exactly what the 18.06 feeds ship **does** install — verified on the official 18.06.9 rootfs; the generic package's hard `firewall4` dep was the actual blocker). **Before stating a fact that gates work, verify it against the source** (repo rules, real binaries, actual uci state). If unsure, say so and check first.
1. **LuCI 24.10 "Save" button**: `Map.save()` alone never commits the session-scoped UCI changeset (only `ui.changes.apply()` does), and the default footer Save handler resolves the Map via a DOM instance lookup that silently fails under out-of-tree themes. `overview.js` overrides the supported `view.handleSave` hook: `m.save().then(() => ui.changes.apply(true))`, guarded by `if (ui.changes)` so older LuCI (where save applies directly) is unaffected. Do NOT patch footer buttons via DOM listeners — a co-registered listener double-saves and `stopPropagation` cannot suppress it (openwrt-ai review round 5); do NOT simplify back to a plain `map.save()`.
2. **DummyValue in grid edit modals** renders its (always null) `cfgvalue`; the DHCP binding column overrides `renderWidget` and sets `rmempty = true` (without it the save parse rejects "must not be empty"). Grid rows use `textvalue`.
3. **Delimiter guard vs labels**: `normalized.conf` is pipe-delimited; the guard covers every field that enters it. `label` must be **excluded** (subscription labels routinely contain `|`, e.g. `HK01|BGP|CMCU`) and sanitized in the `nodes`/`clients` files (`tr '|' ' '`).
4. **Lease file format**: dnsmasq `/tmp/dhcp.leases` lines are `expiry MAC IP hostname clientid` - IP is field 3, MAC is field 2 (both `dhcp-sync.sh` and `overview.js` parse this). The lease file path is a UCI option (`dhcp.@dnsmasq[0].leasefile`), not always `/tmp/dhcp.leases`.
5. **Exit nodes**: only TCP-based protocols (anytls/vless/vmess/trojan) are reliable gateway exits. Hysteria2/TUIC "alive" only proves ICMP; a dead UDP proxy path left a routed device with no internet. WireGuard needs sing-box ≥ 1.11 (endpoint form; legacy outbound removed in 1.13).
6. **iOS private Wi-Fi MACs rotate** — this silently breaks manual DHCP bindings; `dhcp-sync.sh` heals them at service start, and the device just needs to reconnect Wi-Fi.
7. **i18n discipline**: every new UI string must appear in both `po/templates/*.pot` and `po/zh_Hans/*.po` (msgid must match exactly; keep alphabetical order); the zh catalog must compile with `po2lmo.py`.

## Verifying on the reference router

> **The plugin was uninstalled from the reference router (192.168.31.1) on 2026-08-13** — the user switched to another solution (`luci-app-wificalling-location-gateway`, which is still running and even depended on this plugin). Do **not** reinstall or redeploy this plugin to that router or suggest it. From now on verify via rootfs simulation (docker import of official OpenWrt 24.10.8 / 25.12.3 / 18.06.9 rootfs + opkg/apk install) and the local unit tests instead of a real device.

Historical verification flow (kept for reference): the reference device was an ImmortalWrt 24.10.6 Redmi AX6S (sing-box 1.13.16) with several real subscription nodes and an iPhone policy. Standard verification after deploying:

- `opkg install --force-reinstall` the new IPK, restart `rpcd` and the service.
- Check `status.json`, `sing-box.json` (compile output), `clients`, nftables `clients4`, `wfc_` DHCP hosts, `node-status.json`.
- Browser: settings page renders the DHCP binding column and the Save button persists edits; add/remove a device policy and confirm the `wfc_` lease appears/disappears.
- Confirm routing: the policy device's egress IP matches the node country (e.g. via ip.sb).

Credentials and exact router access are documented in the private handoff file (not in this repository).
