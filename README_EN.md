# Wi-Fi Calling Gateway

[中文](README.md) · [Install](docs/en/INSTALL.md) · [Configure](docs/en/CONFIGURATION.md) · [Build](docs/en/BUILD.md) · [Troubleshoot](docs/en/TROUBLESHOOTING.md)

A standalone LuCI package for OpenWrt and ImmortalWrt. It transparently routes selected LAN clients through selected sing-box outbounds while leaving other clients on the normal gateway or PassWall policy. It also reports observable ePDG/IPsec UDP 500/4500 evidence commonly associated with Wi-Fi Calling.

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

## v1.2 features

- AnyTLS, Hysteria2, TUIC, VLESS Reality and VMess WebSocket outbounds.
- Paste-import for AnyTLS, Hysteria2/Hy2, TUIC, VLESS, and VMess share links with local browser-side parsing.
- One selected node per device policy; multiple fixed private IPv4 addresses per policy.
- **Independent tunnel** bypasses PassWall and uses the plugin node; **Follow gateway** is not intercepted.
- One sing-box process, nftables TPROXY, transparent TCP and UDP routing.
- ICMP/TCP reachability and latency observations.
- Separate LuCI pages for settings, live Wi-Fi Calling status, and encrypted IMS activity.
- UDP 500/4500 evidence with registration state, ePDG, ASSURED, packet totals, and last activity.
- Logs only state changes and time-windowed sustained traffic; each device independently keeps 20 records by default, configurable in Settings.
- `sing-box check` before startup and mode `0600` for credential-bearing files.

## Compatibility

| Component | v1.2 support |
|---|---|
| Firmware | OpenWrt / ImmortalWrt with firewall4 and nftables |
| Hardware tested | ImmortalWrt 24.10.6, Redmi AX6S, aarch64_cortex-a53 |
| sing-box | 1.13.0 or newer recommended |
| LuCI | Modern JavaScript views |
| Network | IPv4 LAN policies; static DHCP leases required |
| Package arch | `all`; runtime support still depends on the target sing-box package |

Dependencies: `luci-base`, `sing-box`, `firewall4`, `kmod-nft-tproxy`, `kmod-nft-socket`, `ip-full`, and `tcping`.

## Quick install

Download the latest stable IPK from [Releases](../../releases) (currently 1.3.0), upload it to the router, then run:

```sh
opkg update
opkg install ./luci-app-wificalling-gateway_1.3.0-1_all.ipk
/etc/init.d/rpcd restart
```

Open **Services → Wi-Fi Calling Gateway**. Save a node first, then create a device policy. See the [installation](docs/en/INSTALL.md) and [configuration](docs/en/CONFIGURATION.md) guides.

## Important boundary

This package provides routing and observable network evidence only. It does not change device location, carrier accounts, IMS provisioning, or emergency addresses. `likely_registered` only means a bidirectional `ASSURED` UDP 4500 flow was observed. An icon, UDP 500/4500 traffic, or high packet counts do not prove carrier activation or call completion. Follow carrier terms and local law, and validate with a real call.

## Documentation

- [Install and upgrade](docs/en/INSTALL.md)
- [Nodes, devices and PassWall](docs/en/CONFIGURATION.md)
- [SDK and source builds](docs/en/BUILD.md)
- [Troubleshooting](docs/en/TROUBLESHOOTING.md)
- [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

## License

[MIT](LICENSE). Not affiliated with Apple, any carrier, OpenWrt, ImmortalWrt, sing-box, or PassWall.
