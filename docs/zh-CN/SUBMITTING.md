# 贡献与上游说明

本文件说明如何把 `luci-app-wificalling-gateway` 推进到 OpenWrt / ImmortalWrt 官方软件源，以及作为保底的自建 opkg 源用法。作者信息与仓库地址已在 `Makefile` 中声明：

```make
PKG_MAINTAINER:=Smth Dagg <smthdagg@gmail.com>
LUCI_URL:=https://github.com/smthdagg/luci-app-wificalling-gateway
```

`PKG_MAINTAINER` 只接受 `名字 <邮箱>`；GitHub 项目地址放在 `LUCI_URL`，不要写进 maintainer 字段。提交时每个 commit 必须带 `Signed-off-by: Smth Dagg <smthdagg@gmail.com>`（真实邮箱，**不接受 GitHub noreply 邮箱**）。

## 兼容性结论

已核对 ImmortalWrt 24.10 与 25.12 两个发行线的源码：

- ucode dispatcher（`modules/luci-base/ucode/dispatcher.uc`）都用 `load_catalog(lang, '/usr/lib/lua/luci/i18n')` 加载 `*.zh-cn.lmo`，并经 `_: (...args) => translate(...args) ?? args[0]` 暴露给 JS。
- `luci.mk` 都有 `LUCI_LC_ALIAS.zh_Hans=zh-cn`，即 `po/zh_Hans/` 自动产出 `*.zh-cn.lmo`。
- `sing-box`（`immortalwrt/packages` 的 `net/sing-box`）、`firewall4`（核心）、`kmod-nft-tproxy`/`kmod-nft-socket`（内核模块）两条线都具备。

因此本插件在 24.10 与 25.12 上运行机制一致；自建包同时写入 `/usr/lib/lua/luci/i18n/` 与 `/usr/share/luci/i18n/`，覆盖新旧两种 LuCI 变体。

## 路径 A：ImmortalWrt 官方 luci 源（首选）

依赖栈 `sing-box + firewall4 + kmod-nft-tproxy` 与官方 `luci-app-homeproxy` 完全一致，是现成的获批先例。

1. Fork `https://github.com/immortalwrt/luci`。
2. 新增 `applications/luci-app-wificalling-gateway/`，结构照搬 `luci-app-homeproxy` 与官方 `luci-app-example`：
   ```
   applications/luci-app-wificalling-gateway/
   ├── Makefile                      # include ../../luci.mk
   ├── README.md
   ├── htdocs/luci-static/resources/view/wificalling-gateway/*.js
   ├── root/usr/share/luci/menu.d/luci-app-wificalling-gateway.json
   ├── root/usr/share/rpcd/acl.d/luci-app-wificalling-gateway.json
   └── po/
       ├── templates/wificalling-gateway.pot
       └── zh_Hans/wificalling-gateway.po
   ```
3. `Makefile` 字段齐全：`LUCI_TITLE`、`LUCI_DEPENDS`、`LUCI_URL`、`PKG_LICENSE`、`PKG_MAINTAINER`，`include ../../luci.mk`。**不要提交 `.lmo`**，官方构建用 `po2lmo` 现场编译。
4. 在 feature 分支提交，commit 标题如 `luci-app-wificalling-gateway: add package`，带 `Signed-off-by`。
5. 向 `immortalwrt/luci` 开 PR；可到 Telegram `@ctcgfw_openwrt_discuss` 或 Matrix `#immortalwrt` 寻求 review。

合并后，下次官方构建即进入 ImmortalWrt 的 luci 源，用户 `opkg update && opkg install luci-app-wificalling-gateway` 即可。

## 路径 B：OpenWrt 官方 luci 源（可选，成功率较低）

`sing-box` 与 `v2raya` 也在官方 OpenWrt，但 OpenWrt 历来不收 passwall/openclash 这类聚合代理前端。本插件以「Wi-Fi Calling 网关」这一明确用途包装有机会被接受；以通用代理前端包装则大概率被拒。流程同上但 PR 到 `openwrt/luci`，翻译只提交 `po/templates/*.pot`，译文走 Weblate（不在仓库放 `po/zh_Hans/`）。

## 路径 C：自建 opkg 源（保底，立即可用）

不受官方审批影响，发布即用。

**维护者侧**：把 `.ipk` 放到一个目录，用 OpenWrt 的 `scripts/ipkg-make-index.sh` 生成索引：

```sh
ipkg-make-index.sh . > Packages
gzip -kf Packages   # 生成 Packages.gz
# 用 GitHub Pages 或任意 HTTPS 静态服务器托管该目录（含 Packages、Packages.gz、*.ipk）
```

**用户侧**：在路由器 `/etc/opkg/customfeeds.conf` 加一行，再安装：

```sh
echo 'src/gz wificalling https://你的域名/feed' >> /etc/opkg/customfeeds.conf
opkg update
opkg install luci-app-wificalling-gateway
```
