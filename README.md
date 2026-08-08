# Wi-Fi Calling Gateway

[English](README_EN.md) · [安装](docs/zh-CN/INSTALL.md) · [配置](docs/zh-CN/CONFIGURATION.md) · [编译](docs/zh-CN/BUILD.md) · [排错](docs/zh-CN/TROUBLESHOOTING.md)

面向 OpenWrt / ImmortalWrt 的独立 LuCI 插件。它把指定局域网设备通过指定的 sing-box 节点转发，同时让其他设备继续遵循原网关或 PassWall 策略，并观察 Wi‑Fi Calling 常用的 ePDG/IPsec UDP 500、4500 会话证据。

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

- 支持 AnyTLS、Hysteria2、TUIC、VLESS Reality、VMess WebSocket。
- 支持直接粘贴 AnyTLS、Hysteria2/Hy2、TUIC、VLESS、VMess 分享链接并自动解析导入。
- 每台设备可绑定一个节点；一个策略可包含多个固定私网 IPv4 地址。
- `独立通道`：绕过 PassWall，使用插件节点；`跟随网关`：插件不拦截。
- 单个 sing-box 进程、nftables TPROXY、TCP 与 UDP 透明转发。
- 节点 ICMP/TCP 可达性与延迟检测。
- 内置简体中文界面（语言包随 IPK 安装）；中文说明与状态，协议名与技术字段（TLS、UDP、UUID、SNI、ALPN、Reality、WebSocket 等）保留英文。
- 设置、Wi‑Fi Calling 状态、加密 IMS 活动日志分为三个独立管理页面。
- 观察 UDP 500/4500，显示注册状态、ePDG、ASSURED、包计数及最后活动时间。
- 只记录握手成功/失败与持续加密通讯（响铃或通话，持续数秒以上）；每台设备默认独立保留最近 20 条，可在设置中调整或关闭活动日志。
- 启动前执行 `sing-box check`；配置和运行时凭据权限设为 `0600`。

## 支持环境

| 项目 | 支持范围 |
|---|---|
| 固件 | OpenWrt / ImmortalWrt，firewall4 + nftables |
| 已实机验证 | ImmortalWrt 24.10.6，Redmi AX6S，aarch64_cortex-a53 |
| 源码兼容 | ImmortalWrt 24.10 与 25.12（ucode dispatcher 的 i18n 加载路径、`luci.mk` 的 `LUCI_LC_ALIAS.zh_Hans=zh-cn`、`sing-box`/`firewall4`/`kmod-nft-tproxy` 依赖均一致） |
| sing-box | 建议 1.13.0 或更高版本 |
| LuCI | JavaScript 视图（现代 LuCI） |
| 网络 | IPv4 LAN 策略；设备必须使用 DHCP 静态租约 |
| 包架构 | `all`（Shell 与 LuCI 资源）；运行能力取决于目标 sing-box 包 |

依赖：`luci-base`、`sing-box`、`firewall4`、`kmod-nft-tproxy`、`kmod-nft-socket`、`ip-full`、`tcping`。

## 快速安装

从 [Releases](../../releases) 下载最新稳定版，上传到路由器后执行（当前为 1.4.0）：

```sh
opkg update
opkg install ./luci-app-wificalling-gateway_1.4.0-1_all.ipk
/etc/init.d/rpcd restart
```

然后进入 **服务 → Wi‑Fi Calling Gateway**。先添加并保存节点，再添加设备策略。详细步骤见[安装说明](docs/zh-CN/INSTALL.md)和[配置说明](docs/zh-CN/CONFIGURATION.md)。

## 重要边界

本插件只提供网络转发和可观察证据，不修改手机定位、运营商账户、IMS 配置或紧急呼叫地址。`likely_registered` 仅表示观察到双向 `ASSURED` UDP 4500；Wi‑Fi Calling 图标、UDP 500/4500 或高流量均不能单独证明号码已激活或电话一定能接通。请遵守运营商条款和所在地法律，并在真实设备上完成通话验证。

## 项目文档

- [安装与升级](docs/zh-CN/INSTALL.md)
- [节点、设备和 PassWall 配置](docs/zh-CN/CONFIGURATION.md)
- [常见问题与排错](docs/zh-CN/TROUBLESHOOTING.md)
- [安全策略](SECURITY.md) · [更新记录](CHANGELOG.md)

## 许可证

[MIT](LICENSE)。本项目与 Apple、任何移动运营商、OpenWrt、ImmortalWrt、sing-box 或 PassWall 均无隶属关系。
