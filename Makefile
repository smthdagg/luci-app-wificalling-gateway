include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-wificalling-gateway
PKG_VERSION:=1.7.0
PKG_RELEASE:=1
PKG_LICENSE:=MIT
PKG_LICENSE_FILES:=LICENSE
PKG_MAINTAINER:=Smth Dagg <smthdagg@gmail.com>

LUCI_TITLE:=LuCI support for per-device Wi-Fi Calling gateway
LUCI_URL:=https://github.com/smthdagg/luci-app-wificalling-gateway
LUCI_DEPENDS:=+luci-base +sing-box +firewall4 +kmod-nft-tproxy +kmod-nft-socket +ip-full
LUCI_PKGARCH:=all

include $(TOPDIR)/feeds/luci/luci.mk
