# Wi-Fi Calling Gateway

[English](README_EN.md) · [安装](docs/zh-CN/INSTALL.md) · [配置](docs/zh-CN/CONFIGURATION.md) · [编译](docs/zh-CN/BUILD.md) · [排错](docs/zh-CN/TROUBLESHOOTING.md)

面向 OpenWrt / ImmortalWrt 的独立 LuCI 插件。它把指定局域网设备通过指定的 sing-box 节点转发，同时让其他设备继续走路由器默认路由，并观察 Wi‑Fi Calling 常用的 ePDG/IPsec UDP 500、4500 会话证据。

### 设置

![Wi-Fi Calling Gateway 设置页面](docs/images/overview.png)

### Wi-Fi Calling 状态

![Wi-Fi Calling 状态页面](docs/images/device-status.png)

### 活动日志

![加密 IMS 活动日志页面](docs/images/activity-log.png)

### iPhone 实机观察

下图为实际 iPhone 在飞行模式及 Wi‑Fi 环境中显示 **EE WiFiCall** 的状态：

<p align="center">
  <img src="docs/images/iphone-ee-wificall.jpg" alt="iPhone 实机显示 EE WiFiCall" width="420">
</p>

该截图证明终端已显示 Wi‑Fi Calling 注册状态；是否完成号码激活及呼叫能力，仍应以实际通话或运营商确认结果为准。

## 功能

- 支持 AnyTLS、Hysteria2、TUIC、VLESS Reality、VMess WebSocket、Trojan 与 WireGuard。
- 支持直接粘贴 AnyTLS、Hysteria2/Hy2、TUIC、VLESS、VMess、Trojan (trojan://) 与 WireGuard (wg://) 分享链接并自动解析导入。
- 每台设备可绑定一个节点；一个策略可包含多个固定私网 IPv4 地址。
- `独立通道`：通过插件节点转发；`跟随网关`：插件不拦截，设备走路由器默认路由。
- 单个 sing-box 进程、nftables TPROXY、TCP 与 UDP 透明转发。
- 节点 ICMP/TCP 可达性与延迟检测。
- 内置简体中文界面（语言包随安装包提供）；中文说明与状态，协议名与技术字段（TLS、UDP、UUID、SNI、ALPN、Reality、WebSocket 等）保留英文。
- 设置、Wi‑Fi Calling 状态、加密 IMS 活动日志分为三个独立管理页面。
- 观察 UDP 500/4500，显示注册状态、ePDG、ASSURED、包计数及最后活动时间。
- 只记录握手成功/失败与持续加密通讯（响铃或通话，持续数秒以上）；每台设备默认独立保留最近 20 条，可在设置中调整或关闭活动日志。
- 启动前执行 `sing-box check`；配置和运行时凭据权限设为 `0600`。

## 支持环境

| 项目 | 支持范围 |
|---|---|
| 固件 | OpenWrt / ImmortalWrt / iStoreOS，firewall4 + nftables |
| 24.10 系（opkg/IPK） | OpenWrt 24.10、ImmortalWrt 24.10、iStoreOS 24.10 共用一个 IPK，全部实测 |
| 25.12 系（apk/APK） | OpenWrt / ImmortalWrt 25.12 共用一个 noarch APK，四种芯片全部实测 |
| 25.12 芯片实测 | x86_64 ✅ aarch64 ✅ armv7 ✅ mipsel ✅（官方 25.12.3 rootfs + qemu 用户态模拟） |
| 已实机验证 | ImmortalWrt 24.10.6，Redmi AX6S，aarch64_cortex-a53（真实路由器） |
| iStoreOS 实测 | **24.10.7 完整固件（QEMU 全系统模拟，与用户报错同版本）**：安装 + 服务 active + LuCI 设置/状态/活动日志页面全中文实测通过 |
| 容器/模拟验证 | OpenWrt 24.10.8 / 25.12.3 官方 rootfs；iStoreOS 24.10.5（Docker）、24.10.7（QEMU 完整固件） |
| sing-box | 建议 1.13.0 或更高；IPK 不锁版本（兼容各源较旧版本），25.12 官方源自带（armv7/mipsel 实测自动装 1.12.17）。WireGuard 节点自动适配：sing-box ≥1.11 用 endpoint 形式，1.10.x 及更早用旧版 outbound（均经 1.10.0/1.11.7/1.12.0/1.13.18 实测） |
| LuCI | JavaScript 视图（现代 LuCI） |
| 网络 | IPv4 LAN 策略；设备必须使用 DHCP 静态租约 |
| 包架构 | IPK `all`（Shell 与 LuCI 资源）；APK `noarch`（25.12 apk 不接受 `all`，官方包按目标架构分发） |

依赖：`luci-base`、`sing-box`、`firewall4`、`kmod-nft-tproxy`、`kmod-nft-socket`、`ip-full`。

## 快速安装

从 [Releases](../../releases) 下载最新稳定版（当前为 1.6.0），上传到路由器后安装。**24.10 全系用一个 `.ipk`，25.12 全系用一个 `.apk`（noarch，不分芯片）**。

**OpenWrt / ImmortalWrt / iStoreOS 24.10.x（opkg / IPK）** —— 一个包通用，已实机验证：

```sh
opkg update
opkg install ./luci-app-wificalling-gateway_1.6.0-1_all.ipk
/etc/init.d/rpcd restart
```

> iStoreOS 提示：部分 opkg 对 `./` 相对路径或上传位置会报误导性的 "No such file or directory"。请确认文件**真实上传成功**后再用绝对路径安装：
>
> ```sh
> opkg install /root/luci-app-wificalling-gateway_1.6.0-1_all.ipk
> ```
>
> 若 iStoreOS 的定制 opkg 对本地文件报 `incompatible with the architectures configured`（已实测），可改用**解包安装**（24.10.7 完整固件实测通过）：
>
> ```sh
> cd /tmp && tar xzf luci-app-wificalling-gateway_1.6.0-1_all.ipk && tar xzf data.tar.gz -C /
> /etc/init.d/wificalling-gateway enable && /etc/init.d/wificalling-gateway start
> ```

**OpenWrt / ImmortalWrt 25.12.x（apk / APK）** —— 一个 noarch 包，覆盖 x86_64 / aarch64 / armv7 / mipsel 全芯片，已全部实测：

```sh
apk update
apk add --allow-untrusted ./luci-app-wificalling-gateway_1.6.0-r1_noarch.apk
/etc/init.d/rpcd restart
```

然后进入 **服务 → Wi‑Fi Calling Gateway**。先添加并保存节点，再添加设备策略。详细步骤见[安装说明](docs/zh-CN/INSTALL.md)和[配置说明](docs/zh-CN/CONFIGURATION.md)。

## 重要边界

> **⚠️ 定位要求（Wi-Fi Calling 生效前提）**
>
> 运营商要求设备定位与 SIM 卡归属地一致才能激活 Wi-Fi Calling。本插件通过对应国家的节点提供该国 IP，但**不控制设备自身的定位**（GPS / 基站 / wloc）。设备需要通过虚拟定位将位置设为 SIM 卡归属地，否则 Wi-Fi Calling 无法触发。
>
> **解决方法**：使用 [ios-location-spoofer](https://github.com/smthdagg/ios-location-spoofer) 配合小火箭（Shadowrocket）劫持 iOS 定位到 SIM 卡归属地。这是独立于本插件的项目。

本插件只提供网络转发和可观察证据，不修改手机定位、运营商账户、IMS 配置或紧急呼叫地址。`likely_registered` 仅表示观察到双向 `ASSURED` UDP 4500；Wi‑Fi Calling 图标、UDP 500/4500 或高流量均不能单独证明号码已激活或电话一定能接通。请遵守运营商条款和所在地法律，并在真实设备上完成通话验证。

## 项目文档

- [安装与升级](docs/zh-CN/INSTALL.md)
- [节点和设备配置](docs/zh-CN/CONFIGURATION.md)
- [常见问题与排错](docs/zh-CN/TROUBLESHOOTING.md)
- [安全策略](SECURITY.md) · [更新记录](CHANGELOG.md)

## 许可证

[MIT](LICENSE)。本项目与 Apple、任何移动运营商、OpenWrt、ImmortalWrt、sing-box 或 PassWall 均无隶属关系。
