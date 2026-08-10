# Wi-Fi Calling Gateway

[中文](README.md) · [Install](docs/en/INSTALL.md) · [Configure](docs/en/CONFIGURATION.md) · [Build](docs/en/BUILD.md) · [Troubleshoot](docs/en/TROUBLESHOOTING.md)

A standalone LuCI package for OpenWrt and ImmortalWrt. It transparently routes selected LAN clients through selected sing-box outbounds while leaving other clients on the normal gateway routing. It also reports observable ePDG/IPsec UDP 500/4500 evidence commonly associated with Wi-Fi Calling.

### Settings

![Wi-Fi Calling Gateway settings page](docs/images/overview.png)

### Wi-Fi Calling status

![Wi-Fi Calling status page](docs/images/device-status.png)

### Activity log

![Encrypted IMS activity log page](docs/images/activity-log.png)

### Observed on a real iPhone

The following screenshot shows **EE WiFiCall** displayed on an actual iPhone while it is using Wi-Fi in airplane mode:

<p align="center">
  <img src="docs/images/iphone-ee-wificall.jpg" alt="EE WiFiCall displayed on a real iPhone" width="420">
</p>

This demonstrates the Wi-Fi Calling registration indicator on the device. Carrier activation and calling capability must still be confirmed by a completed call or by the carrier.

## Features

- AnyTLS, Hysteria2, TUIC, VLESS Reality and VMess WebSocket outbounds.
- Paste-import for AnyTLS, Hysteria2/Hy2, TUIC, VLESS, and VMess share links with local browser-side parsing.
- One selected node per device policy; multiple fixed private IPv4 addresses per policy.
- **Independent tunnel** routes through the plugin node; **Follow gateway** is not intercepted and uses the router default routing.
- One sing-box process, nftables TPROXY, transparent TCP and UDP routing.
- ICMP/TCP reachability and latency observations.
- Built-in Simplified Chinese interface (language pack shipped inside the IPK); Chinese descriptions and status, with protocol names and technical fields (TLS, UDP, UUID, SNI, ALPN, Reality, WebSocket, etc.) kept in English.
- Separate LuCI pages for settings, live Wi-Fi Calling status, and encrypted IMS activity.
- UDP 500/4500 evidence with registration state, ePDG, ASSURED, packet totals, and last activity.
- Logs only handshake success/failure and sustained encrypted communication (ringing or calls lasting a few seconds); each device independently keeps 20 records by default, and the activity log can be turned off in Settings.
- `sing-box check` before startup and mode `0600` for credential-bearing files.

## Compatibility

| Component | Support |
|---|---|
| Firmware | OpenWrt / ImmortalWrt / iStoreOS with firewall4 and nftables |
| 24.10 line (opkg/IPK) | One shared `.ipk` for OpenWrt 24.10, ImmortalWrt 24.10 and iStoreOS 24.10 — all verified |
| 25.12 line (apk/APK) | One shared `noarch` `.apk` for OpenWrt / ImmortalWrt 25.12 — all targets verified |
| 25.12 targets tested | x86_64 ✅ aarch64 ✅ armv7 ✅ mipsel ✅ (official 25.12.3 rootfs via qemu user-mode emulation) |
| Hardware tested | ImmortalWrt 24.10.6, Redmi AX6S, aarch64_cortex-a53 (real router) |
| iStoreOS verified | **24.10.7 full firmware (QEMU full-system emulation, same version as the reported issue)**: install + service active + LuCI Settings/Status/Activity Log pages verified in Simplified Chinese |
| Container/emulation tested | Official OpenWrt 24.10.8 / 25.12.3 rootfs; iStoreOS 24.10.5 (Docker), 24.10.7 (full QEMU firmware) |
| sing-box | 1.13.0 or newer recommended; the IPK leaves it unversioned (compatible with older sing-box in some feeds); the 25.12 official feed ships sing-box (1.12.17 auto-installed on armv7/mipsel in tests) |
| LuCI | Modern JavaScript views |
| Network | IPv4 LAN policies; static DHCP leases required |
| Package arch | IPK `all`; APK `noarch` (the 25.12 apk rejects `arch: all`; official 25.12 packages are built per target) |

Dependencies: `luci-base`, `sing-box`, `firewall4`, `kmod-nft-tproxy`, `kmod-nft-socket`, `ip-full`.

## Quick install

Download the latest stable release (currently 1.5.0) from [Releases](../../releases), upload it to the router, then install. **One `.ipk` for the whole 24.10 line, one `noarch` `.apk` for the whole 25.12 line (any chip).**

**OpenWrt / ImmortalWrt / iStoreOS 24.10.x (opkg / IPK)** — one shared package, verified on real hardware:

```sh
opkg update
opkg install ./luci-app-wificalling-gateway_1.5.0-1_all.ipk
/etc/init.d/rpcd restart
```

**iStoreOS note**: some opkg builds report a misleading "No such file or directory" for `./` relative paths or upload locations — make sure the file was actually uploaded, then install by absolute path:

```sh
opkg install /root/luci-app-wificalling-gateway_1.5.0-1_all.ipk
```

If the iStoreOS custom opkg rejects local files with `incompatible with the architectures configured` (verified), install by extracting instead (verified on 24.10.7 full firmware):

```sh
cd /tmp && tar xzf luci-app-wificalling-gateway_1.5.0-1_all.ipk && tar xzf data.tar.gz -C /
/etc/init.d/wificalling-gateway enable && /etc/init.d/wificalling-gateway start
```

**OpenWrt / ImmortalWrt 25.12.x (apk / APK)** — one `noarch` package covering x86_64 / aarch64 / armv7 / mipsel, all tested:

```sh
apk update
apk add --allow-untrusted ./luci-app-wificalling-gateway_1.5.0-r1_noarch.apk
/etc/init.d/rpcd restart
```

Open **Services → Wi-Fi Calling Gateway**. Save a node first, then create a device policy. See the [installation](docs/en/INSTALL.md) and [configuration](docs/en/CONFIGURATION.md) guides.

## Important boundary

> **⚠️ Location requirement (prerequisite for Wi-Fi Calling)**
>
> The carrier requires the device location to match the SIM card's home country before Wi-Fi Calling can activate. This plugin provides an IP in the corresponding country via the proxy node, but **does not control the device's own location** (GPS / cell tower / wloc). The device must use a virtual location tool to set its position to the SIM card's home country, otherwise Wi-Fi Calling will not trigger.
>
> **Solution**: use [ios-location-spoofer](https://github.com/smthdagg/ios-location-spoofer) with Shadowrocket to spoof iOS location to the SIM card's home country. This is a separate project independent of this plugin.

This package provides routing and observable network evidence only. It does not change device location, carrier accounts, IMS provisioning, or emergency addresses. `likely_registered` only means a bidirectional `ASSURED` UDP 4500 flow was observed. An icon, UDP 500/4500 traffic, or high packet counts do not prove carrier activation or call completion. Follow carrier terms and local law, and validate with a real call.

## Documentation

- [Install and upgrade](docs/en/INSTALL.md)
- [Nodes and devices](docs/en/CONFIGURATION.md)
- [Troubleshooting](docs/en/TROUBLESHOOTING.md)
- [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

## License

[MIT](LICENSE). Not affiliated with Apple, any carrier, OpenWrt, ImmortalWrt, sing-box, or PassWall.
