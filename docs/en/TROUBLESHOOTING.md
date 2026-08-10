# Troubleshooting

- **Install fails with `wfopen: ... No such file or directory` (common on iStoreOS)**: opkg cannot open the file — usually a file-location problem, not a package-format problem. Confirm the file actually exists (`ls -la <path>`), or upload via LuCI System → Software → Upload (the dialog shows MD5/SHA256 when the file is present), then install by absolute path: `opkg install /root/luci-app-wificalling-gateway_1.5.0-1_all.ipk`. Avoid `./` relative paths; mind tmpfs mounts when uploading to `/tmp`.
- **25.12 install fails with `uninstallable, arch: all`**: the 25.12 apk rejects `arch: all` packages. Use the **noarch** build: `apk add --allow-untrusted ./luci-app-wificalling-gateway_1.5.0-r1_noarch.apk` (one package covers x86_64 / aarch64 / armv7 / mipsel).
- **Install fails with `cannot find dependency sing-box`**: 24.10-line feeds (including iStoreOS) may not ship sing-box; install a matching sing-box for your firmware/CPU and retry. The 25.12 official feed ships sing-box and resolves it automatically. Never mix packages from different firmware branches.
- Missing LuCI page or ACL error: restart `rpcd` and `uhttpd`, log out, and start a fresh LuCI session.
- Service failure: inspect `logread -e wificalling-gateway` and run `sing-box check -c /var/run/wificalling-gateway/sing-box.json` locally. Never post that JSON publicly.
- Reachable node but no Internet: reachability is not a proxy handshake. Check protocol fields, SNI, credentials, server UDP support, DNS, time, MTU, and the selected static IP.
- Wi-Fi Calling icon but calls fail: UDP 4500 evidence does not validate carrier account, IMS provisioning, emergency address, or call routing. Verify with a known-good comparison and a completed real call.
- Recovery: stop the service and confirm the `wificalling_gateway` nftables table and policy rule table 166 are gone. The plugin never removes unrelated firewall rules.
