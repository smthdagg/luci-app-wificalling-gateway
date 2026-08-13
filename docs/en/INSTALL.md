# Installation and upgrade

## Requirements

- OpenWrt / ImmortalWrt / iStoreOS on the **22.03+ / 23.05+ line** (nftables + TPROXY kernel; the plugin configures nftables directly and does not use the firewall4 daemon).
- **18.06/Lede builds are not supported**: their feeds lack `firewall4` (the hard dependency in 1.7.1 and earlier was exactly what caused `cannot find dependency firewall4` install failures on 18.06; removed in 1.7.2) and usually also the nftables TPROXY kernel modules and sing-box — see [Troubleshooting](TROUBLESHOOTING.md).
- A feed providing `sing-box`, `ip-full`, and the TPROXY kernel modules (`tcping` is optional; TCP-type node probes fall back to ICMP when it is absent). sing-box 1.13.0 or newer is recommended; the IPK leaves it unversioned to stay compatible with older sing-box in some feeds; the OpenWrt 25.12 official feed ships sing-box.
- Enough space for sing-box: at least ~20 MB flash and ~64 MB RAM recommended.
- A static DHCP lease for every selected client.

## Packages and supported scope

| Package | Covers | Verified |
|---|---|---|
| `luci-app-wificalling-gateway_1.7.2-1_all.ipk` | OpenWrt / ImmortalWrt / iStoreOS **24.10 line** | Real router (ImmortalWrt 24.10.6), official 24.10.8 rootfs, iStoreOS 24.10 |
| `luci-app-wificalling-gateway_1.7.2-r1_noarch.apk` | OpenWrt / ImmortalWrt **25.12 line, all chips** | x86_64 / aarch64 / armv7 / mipsel (official 25.12.3 rootfs) |

> Note: the OpenWrt 25.12 apk-based package system rejects `arch: all` packages (official 25.12 packages are built per target), so the 25.12 APK uses the **`noarch`** architecture — one package covers every target.

## Install the Release IPK (24.10 line)

```sh
opkg update
opkg install ./luci-app-wificalling-gateway_1.7.2-1_all.ipk
/etc/init.d/rpcd restart
```

**iStoreOS note**: some opkg builds report a misleading `wfopen: ... No such file or directory` for `./` relative paths or upload locations. Make sure the file was actually uploaded (LuCI's System → Software → upload dialog shows MD5/SHA256 when the file is present), then install by absolute path:

```sh
opkg install /root/luci-app-wificalling-gateway_1.7.2-1_all.ipk
```

If the iStoreOS custom opkg rejects local files with `incompatible with the architectures configured` (confirmed on the 24.10.7 full firmware), install by extracting instead (also verified):

```sh
cd /tmp && tar xzf luci-app-wificalling-gateway_1.7.2-1_all.ipk && tar xzf data.tar.gz -C /
/etc/init.d/wificalling-gateway enable && /etc/init.d/wificalling-gateway start
```

> Note: extracting does not write the opkg database; to uninstall, remove the plugin files manually (`/usr/libexec/wificalling-gateway`, `/www/luci-static/resources/*/wificalling-gateway`, `/etc/config/wificalling-gateway`, `/etc/init.d/wificalling-gateway`, the language packs and menu/ACL JSON).

If a dependency is missing from the current feed (e.g. sing-box), install a matching build for your firmware version and CPU architecture first. Never mix kernel packages from different firmware branches.

## Install the Release APK (25.12 line)

```sh
apk update
apk add --allow-untrusted ./luci-app-wificalling-gateway_1.7.2-r1_noarch.apk
/etc/init.d/rpcd restart
```

Dependencies (luci-base, sing-box, nftables, kmod-nft-tproxy, kmod-nft-socket, ip-full) are resolved automatically from the official feed.

## First run

Open **Services → Wi-Fi Calling Gateway**, save a node, then add a device policy and enable the service. Startup validates the generated sing-box configuration before installing routing rules.

## Upgrade and uninstall

Back up `/etc/config/wificalling-gateway` privately before upgrading. Install the new version:

```sh
opkg install ./luci-app-wificalling-gateway_NEW_all.ipk      # 24.10 line
apk add --allow-untrusted ./luci-app-wificalling-gateway_NEW_noarch.apk  # 25.12 line
/etc/init.d/wificalling-gateway restart
```

Uninstall stops the service and removes the plugin's nftables / policy-routing rules:

```sh
/etc/init.d/wificalling-gateway stop
opkg remove luci-app-wificalling-gateway    # 24.10 line
apk del luci-app-wificalling-gateway        # 25.12 line
```
