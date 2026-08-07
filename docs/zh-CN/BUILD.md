# 编译说明

## OpenWrt SDK / Buildroot

把项目目录放入 `package/luci-app-wificalling-gateway`，更新 feeds 后运行：

```sh
make menuconfig
make package/luci-app-wificalling-gateway/compile V=s
```

在 LuCI 分类中选择插件。SDK 会根据 `Makefile` 解析依赖并生成适合目标固件的软件包。

## 架构无关 IPK

macOS/Linux 可运行：

```sh
./scripts/build-ipk.sh 1.0.0-1
shasum -a 256 dist/luci-app-wificalling-gateway_1.0.0-1_all.ipk
```

该包只包含 Shell/LuCI 资源，但依赖包仍必须与目标固件匹配。安装后务必执行 `sing-box check` 和实际路由验证。

## 测试

```sh
python3 -m unittest discover -s tests -v
for f in root/etc/init.d/wificalling-gateway root/usr/libexec/wificalling-gateway/*.sh scripts/*.sh; do sh -n "$f"; done
node --check htdocs/luci-static/resources/view/wificalling-gateway/overview.js
```
