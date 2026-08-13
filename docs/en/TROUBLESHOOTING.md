# Troubleshooting

- **Install fails with `wfopen: ... No such file or directory` (common on iStoreOS)**: opkg cannot open the file — usually a file-location problem, not a package-format problem. Confirm the file actually exists (`ls -la <path>`), or upload via LuCI System → Software → Upload (the dialog shows MD5/SHA256 when the file is present), then install by absolute path: `opkg install /root/luci-app-wificalling-gateway_1.7.3-1_all.ipk`. Avoid `./` relative paths; mind tmpfs mounts when uploading to `/tmp`.
- **iStoreOS reports `incompatible with the architectures configured`**: the iStoreOS custom opkg (koolcenter build) applies its own architecture check to local-file installs (`all` and concrete arches may both be rejected); the package itself parses fine (verified). Use the extract install instead (verified on 24.10.7 full firmware):
  ```sh
  cd /tmp && tar xzf luci-app-wificalling-gateway_1.7.3-1_all.ipk && tar xzf data.tar.gz -C /
  /etc/init.d/wificalling-gateway enable && /etc/init.d/wificalling-gateway start
  ```
- **25.12 install fails with `uninstallable, arch: all`**: the 25.12 apk rejects `arch: all` packages. Use the **noarch** build: `apk add --allow-untrusted ./luci-app-wificalling-gateway_1.7.3-r1_noarch.apk` (one package covers x86_64 / aarch64 / armv7 / mipsel).
- **18.06/Lede install fails with `cannot find dependency firewall4`**: use the **18.06 variant** — `luci-app-wificalling-gateway_1.7.3-1_18.06_all.ipk` depends only on what the official 18.06 feeds ship (`luci-base`, `nftables`, `ip-full`); verified installing on the official 18.06.9 rootfs (nftables 0.9.0 auto-resolved):
  ```sh
  opkg update
  opkg install ./luci-app-wificalling-gateway_1.7.3-1_18.06_all.ipk
  /etc/init.d/wificalling-gateway enable
  ```
  Background: firewall4 is a 22.03+ era nftables firewall and does not exist in 18.06 feeds; the hard dependency in 1.7.1 and earlier made opkg reject the whole package (the `incompatible with the architectures configured` line is the cascading dependency error, **not** an architecture mismatch). The generic package dropped it in 1.7.2, but the 18.06 official feeds still lack sing-box and the TPROXY kernel modules, hence the dedicated variant. 18.06 limitations handled by the variant: the LuCI pages need the 19.07+ JS view architecture (the legacy 18.06 Lua dispatcher cannot serve them), so no menu is registered — configure over UCI from the command line; sing-box and the TPROXY kmods (kernel ≥ 4.11) must come from your feed, otherwise the service start preflight fails with a clear reason in `logread -e wificalling-gateway`.
- **Install fails with `cannot find dependency sing-box`**: 24.10-line feeds (including iStoreOS) may not ship sing-box; install a matching sing-box for your firmware/CPU and retry. The 25.12 official feed ships sing-box and resolves it automatically. Never mix packages from different firmware branches.
- Missing LuCI page or ACL error: restart `rpcd` and `uhttpd`, log out, and start a fresh LuCI session.
- Service failure: inspect `logread -e wificalling-gateway` and run `sing-box check -c /var/run/wificalling-gateway/sing-box.json` locally. Never post that JSON publicly.
- Reachable node but no Internet: reachability is not a proxy handshake. Check protocol fields, SNI, credentials, server UDP support, DNS, time, MTU, and the selected static IP.
- Wi-Fi Calling icon but calls fail: UDP 4500 evidence does not validate carrier account, IMS provisioning, emergency address, or call routing. Verify with a known-good comparison and a completed real call.
- Recovery: stop the service and confirm the `wificalling_gateway` nftables table and policy rule table 166 are gone. The plugin never removes unrelated firewall rules.
