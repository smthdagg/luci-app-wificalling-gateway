# Build

Place this project at `package/luci-app-wificalling-gateway` in an OpenWrt SDK or buildroot, then select it in `make menuconfig` and run:

```sh
make package/luci-app-wificalling-gateway/compile V=s
```

For the portable Shell/LuCI package envelope:

```sh
./scripts/build-ipk.sh 1.4.0-1
shasum -a 256 dist/luci-app-wificalling-gateway_1.4.0-1_all.ipk
```

Runtime dependencies must still match the target firmware. Test with:

```sh
python3 -m unittest discover -s tests -v
for f in root/etc/init.d/wificalling-gateway root/usr/libexec/wificalling-gateway/*.sh scripts/*.sh; do sh -n "$f"; done
node --check htdocs/luci-static/resources/view/wificalling-gateway/overview.js
```
