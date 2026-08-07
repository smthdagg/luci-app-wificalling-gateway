# Installation and upgrade

Requirements: OpenWrt or ImmortalWrt with firewall4/nftables; `sing-box >= 1.13.0`; `tcping`, `ip-full`, and matching TPROXY kernel modules; a static DHCP lease for every selected client. Do not mix kernel packages from different firmware releases.

```sh
opkg update
opkg install ./luci-app-wificalling-gateway_1.2.1-1_all.ipk
/etc/init.d/rpcd restart
```

Open **Services → Wi-Fi Calling Gateway**, save a node, then add a device policy and enable the service. Startup validates the generated sing-box configuration before installing routing rules.

Upgrade with `opkg install ./luci-app-wificalling-gateway_NEW_all.ipk`. Back up `/etc/config/wificalling-gateway` privately first. To uninstall safely:

```sh
/etc/init.d/wificalling-gateway stop
opkg remove luci-app-wificalling-gateway
```
