#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
version=${1:-1.4.0-1}
out="$root/dist/luci-app-wificalling-gateway_${version}_all.ipk"
stage=$(mktemp -d "${TMPDIR:-/tmp}/wfc-ipk.XXXXXX")
trap 'rm -rf "$stage"' EXIT HUP INT TERM

tar_format=gnutar
tar_owner_options='--uid 0 --gid 0 --uname root --gname root'
case "$(tar --version 2>/dev/null | head -n 1)" in
	*GNU*) tar_format=gnu; tar_owner_options='--owner=0 --group=0' ;;
esac

mkdir -p "$stage/control" "$stage/data" "$root/dist"
cp -R "$root/root/." "$stage/data/"
cp -R "$root/htdocs" "$stage/data/www/"

# Compile LuCI translations (.po -> .lmo) into both the legacy Lua and the
# modern C i18n directories so the catalog loads on either LuCI variant.
# po/ uses gettext codes (e.g. zh_Hans); map them to the on-disk .lmo language
# code, mirroring luci.mk's LUCI_LC_ALIAS (zh_Hans -> zh-cn, zh_Hant -> zh-tw).
for lang_dir in "$root"/po/*; do
	[ -d "$lang_dir" ] || continue
	lang=$(basename "$lang_dir")
	[ "$lang" = "templates" ] && continue
	case "$lang" in
		zh_Hans) lmo_lang=zh-cn ;;
		zh_Hant) lmo_lang=zh-tw ;;
		*) lmo_lang="$lang" ;;
	esac
	for po in "$lang_dir"/*.po; do
		[ -f "$po" ] || continue
		domain=$(basename "$po" .po)
		for i18n_root in usr/lib/lua/luci/i18n usr/share/luci/i18n; do
			mkdir -p "$stage/data/$i18n_root"
			python3 "$root/scripts/po2lmo.py" "$po" "$stage/data/$i18n_root/$domain.$lmo_lang.lmo"
		done
	done
done

printf '%s\n' \
  'Package: luci-app-wificalling-gateway' \
  "Version: $version" \
  'Architecture: all' \
  'Maintainer: Smth Dagg <smthdagg@gmail.com>' \
  'Depends: luci-base, sing-box (>= 1.13.0), firewall4, kmod-nft-tproxy, kmod-nft-socket, ip-full, tcping' \
  'Section: luci' \
  'Priority: optional' \
  'License: MIT' \
  'Description: Per-device transparent Wi-Fi Calling gateway and ePDG/IPsec evidence monitor.' \
  > "$stage/control/control"
printf '/etc/config/wificalling-gateway\n' > "$stage/control/conffiles"
printf '2.0\n' > "$stage/debian-binary"

(cd "$stage/control" && COPYFILE_DISABLE=1 tar --format "$tar_format" $tar_owner_options -czf "$stage/control.tar.gz" .)
(cd "$stage/data" && COPYFILE_DISABLE=1 tar --format "$tar_format" $tar_owner_options -czf "$stage/data.tar.gz" .)
rm -f "$out"
(cd "$stage" && COPYFILE_DISABLE=1 tar --format "$tar_format" $tar_owner_options -czf "$out" debian-binary data.tar.gz control.tar.gz)
echo "$out"
