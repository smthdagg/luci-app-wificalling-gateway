# 安装与升级

## 前提

- OpenWrt / ImmortalWrt / iStoreOS，使用 firewall4/nftables。
- 软件源能提供 `sing-box`、`ip-full` 和 TPROXY 内核模块（`tcping` 为可选，未安装时 TCP 型节点探测自动降级为 ICMP）。建议 sing-box ≥ 1.13.0；IPK 不锁版本，兼容各源较旧版本；OpenWrt 25.12 官方源自带 sing-box。
- 设备有足够空间运行 sing-box；建议至少预留 20 MB 闪存和 64 MB 可用内存。
- 为目标手机设置 DHCP 静态租约。

## 安装包与支持范围

| 包 | 覆盖 | 实测 |
|---|---|---|
| `luci-app-wificalling-gateway_1.5.0-1_all.ipk` | OpenWrt / ImmortalWrt / iStoreOS **24.10 全系** | 真实路由器（ImmortalWrt 24.10.6）、官方 24.10.8 rootfs、iStoreOS 24.10 |
| `luci-app-wificalling-gateway_1.5.0-r1_noarch.apk` | OpenWrt / ImmortalWrt **25.12 全芯片** | x86_64 / aarch64 / armv7 / mipsel（官方 25.12.3 rootfs） |

> 说明：OpenWrt 25.12 的 apk 包体系不接受 `arch: all`（官方包按目标架构分发），因此 25.12 使用 `noarch` 架构的 APK——一个包覆盖所有芯片。

## 安装 Release IPK（24.10 系）

```sh
opkg update
opkg install ./luci-app-wificalling-gateway_1.5.0-1_all.ipk
/etc/init.d/rpcd restart
```

**iStoreOS 提示**：部分 opkg 对 `./` 相对路径或上传位置会报误导性的 `wfopen: ... No such file or directory`。请确认文件**真实上传成功**（可通过 LuCI「系统 → 软件包 → 上传软件包」上传，上传时会显示 MD5/SHA256 校验），再用绝对路径安装：

```sh
opkg install /root/luci-app-wificalling-gateway_1.5.0-1_all.ipk
```

若依赖在当前软件源不存在（例如 sing-box），请先为当前固件版本和 CPU 架构安装匹配依赖，禁止混装不同固件分支的内核模块。

## 安装 Release APK（25.12 系）

```sh
apk update
apk add --allow-untrusted ./luci-app-wificalling-gateway_1.5.0-r1_noarch.apk
/etc/init.d/rpcd restart
```

依赖（luci-base、sing-box、firewall4、kmod-nft-tproxy、kmod-nft-socket、ip-full）由官方源自动解析。

## 首次启用

进入 **服务 → Wi-Fi Calling Gateway**，添加节点并保存，再添加设备策略。确认配置后启用服务并“保存并应用”。服务启动前会检查生成的 sing-box 配置；检查失败时不会安装转发规则。

## 升级与卸载

升级前自行备份 `/etc/config/wificalling-gateway`，不要公开备份。安装新版：

```sh
opkg install ./luci-app-wificalling-gateway_NEW_all.ipk   # 24.10 系
apk add --allow-untrusted ./luci-app-wificalling-gateway_NEW_noarch.apk  # 25.12 系
/etc/init.d/wificalling-gateway restart
```

卸载会停止服务并清理插件 nftables/策略路由规则：

```sh
/etc/init.d/wificalling-gateway stop
opkg remove luci-app-wificalling-gateway    # 24.10 系
apk del luci-app-wificalling-gateway        # 25.12 系
```
