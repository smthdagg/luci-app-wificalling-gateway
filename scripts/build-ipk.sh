#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
version=${1:-1.0.0-1}
out="$root/dist/luci-app-wificalling-gateway_${version}_all.ipk"
stage=$(mktemp -d "${TMPDIR:-/tmp}/wfc-ipk.XXXXXX")
trap 'rm -rf "$stage"' EXIT HUP INT TERM

mkdir -p "$stage/control" "$stage/data" "$root/dist"
cp -R "$root/root/." "$stage/data/"
cp -R "$root/htdocs" "$stage/data/www/"

printf '%s\n' \
  'Package: luci-app-wificalling-gateway' \
  "Version: $version" \
  'Architecture: all' \
  'Maintainer: Wi-Fi Calling Gateway contributors' \
  'Depends: luci-base, sing-box (>= 1.13.0), firewall4, kmod-nft-tproxy, kmod-nft-socket, ip-full, tcping' \
  'Section: luci' \
  'Priority: optional' \
  'License: MIT' \
  'Description: Per-device transparent Wi-Fi Calling gateway and ePDG/IPsec evidence monitor.' \
  > "$stage/control/control"
printf '/etc/config/wificalling-gateway\n' > "$stage/control/conffiles"
printf '2.0\n' > "$stage/debian-binary"

(cd "$stage/control" && COPYFILE_DISABLE=1 tar --format gnutar --uid 0 --gid 0 --uname root --gname root -czf "$stage/control.tar.gz" .)
(cd "$stage/data" && COPYFILE_DISABLE=1 tar --format gnutar --uid 0 --gid 0 --uname root --gname root -czf "$stage/data.tar.gz" .)
rm -f "$out"
(cd "$stage" && COPYFILE_DISABLE=1 tar --format gnutar --uid 0 --gid 0 --uname root --gname root -czf "$out" debian-binary data.tar.gz control.tar.gz)
echo "$out"
