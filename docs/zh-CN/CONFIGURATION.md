# 配置说明

## 节点

点击“导入节点链接”，粘贴一条 AnyTLS、Hysteria2/Hy2、TUIC、VLESS、VMess、Trojan (trojan://) 或 WireGuard (wg://) 分享链接即可自动生成节点。解析在本地浏览器完成，不会发送到外部服务。导入后仍应核对名称、服务器、端口、SNI、TLS 和协议专属字段，再保存并测试节点。

先点“添加代理节点”，填写显示名称、协议、服务器和协议必需字段。AnyTLS/Hysteria2/Trojan 使用密码；TUIC 使用 UUID 和密码；VLESS Reality 使用 UUID、flow、SNI、公钥、short ID 和指纹；VMess WS 使用 UUID、Host 和路径；WireGuard 使用私钥、公钥、本地地址，可选保留位与 MTU。TLS 公钥指纹必须是 Base64 SHA-256，而不是十六进制文本。

Proxy nodes 列表直接显示节点存活状态、Ping/延迟和质量等级。优先检测 ICMP，TCP 型协议失败时会用 `tcping`（已安装时）探测端口。它不执行完整代理握手。UDP 型节点显示未知不能直接判定离线。

## 设备策略

**为什么必须先固定 IP**：插件按 IP 识别设备——策略里的 `source_ip` 写入 nftables `clients4` 集合，只有匹配该 IP 的流量才被 TPROXY 转发。设备 IP 不固定，规则就匹配不到，流量不会经过网关。固定 IP 靠 DHCP 静态租约（MAC→IP 绑定），**1.7.0 起由插件自动维护**：添加策略时自动绑定当前租用该 IP 的设备 MAC；删除策略时自动清理；iOS 私有 MAC 变化时设备重连即自动重绑（服务启动时同步）。设备策略表的「DHCP 绑定」列显示实时状态：已绑定 / 待绑定 / MAC 已变化，重连后自动重绑 / 在线（静态 IP） / 设备未在线。其中「在线（静态 IP）」表示设备不在 DHCP 租约里（静态 IP 或纯 AP 场景），但 ARP 缓存中最近可见。

添加设备步骤：

1. 添加设备，填写易识别的名称（名称会自动用于 DHCP 主机名，含空格/逗号等特殊字符会被自动清理）。
2. 每个输入项填写一个私网 IPv4；一个策略可放多台使用同一节点的设备。
3. 选择路由模式：
   - **独立通道**：该 IP 通过所选插件节点转发。
   - **跟随网关**：插件不拦截该 IP，设备走路由器默认路由。

同一个 IP 不可同时属于两个独立策略。插件不拦截 IPv6；若需要严格单路径测试，应在设备/网络侧正确处理 IPv6，不能把未代理 IPv6 误认为插件已覆盖。

## 独立管理页面

- **设置**：维护节点与设备策略；可调整活动日志间隔、每台设备记录数，并关闭活动日志。
- **Wi-Fi Calling 状态**：显示注册状态、ePDG、UDP 500/4500、ASSURED、包计数和最后活动时间。
- **活动日志**：只记录握手成功/失败与持续加密通讯（响铃或通话），可自动刷新、查看记录数，并在确认后清空；日志关闭时页面会提示「活动日志记录已关闭」。

## 状态含义

| 状态 | 含义 |
|---|---|
| `no_session` | 未观察到相关会话 |
| `negotiating` | 观察到 UDP 500 |
| `nat_t_seen` | 观察到 UDP 4500 |
| `likely_registered` | UDP 4500 为双向 `ASSURED` |
| `active_traffic` | 双向 `ASSURED` 且包量较高 |

这些是路由器侧网络证据，不是运营商激活结论。

握手成功/失败只记录一次状态过渡；加密流量持续数秒（≥3 秒门槛，5 秒轮询精度下约 5 秒）后才判定为持续通讯，并按可配置时间窗口汇总包量（默认 60 秒）；每台设备独立保留可配置的最新记录数（默认 20 条）。活动日志可在设置中关闭。

**监控能力边界**：ePDG/IPsec 隧道（UDP 4500 内）全程加密，插件只能观察外层包量，看不到隧道内内容。因此：
- 持续双向加密流量（响铃/通话的 RTP 特征）→ 日志标记「**通话进行中（根据持续加密流量推断）**」——这是推断，不是解密；
- **短信无法可靠区分**：IMS 短信是短突发流量，与 keepalive、系统推送等无法区分，因此不记录、也不会误报；
- 电话号码、消息内容、呼叫方向永远不可见。

“清空日志”只清理本插件的活动文件，不影响系统日志、节点或设备配置。

## 18.06/Lede：命令行配置（无 LuCI 页面）

18.06 的 LuCI 是旧版 Lua dispatcher，无法渲染本插件的 JS 页面（19.07+ 架构），18.06 专包因此不注册菜单，配置全部通过命令行 UCI 完成：

```sh
# 1) 全局开关
uci set wificalling-gateway.main.enabled=1

# 2) 添加节点（具名段便于后面引用）
uci set wificalling-gateway.hknode=node
uci set wificalling-gateway.hknode.enabled=1
uci set wificalling-gateway.hknode.label='HK AnyTLS'
uci set wificalling-gateway.hknode.protocol=anytls
uci set wificalling-gateway.hknode.server=example.com
uci set wificalling-gateway.hknode.port=443
uci set wificalling-gateway.hknode.password=…   # 密码按同样方式设置，勿写入公开文档
uci set wificalling-gateway.hknode.sni=cdn.example.com

# 3) 添加设备策略（node 填节点段的段名）
uci set wificalling-gateway.iphone12=device
uci set wificalling-gateway.iphone12.enabled=1
uci set wificalling-gateway.iphone12.label='iPhone12'
uci set wificalling-gateway.iphone12.route_mode=independent
uci set wificalling-gateway.iphone12.node=hknode
uci add_list wificalling-gateway.iphone12.source_ip=192.168.31.175

uci commit wificalling-gateway
/etc/init.d/wificalling-gateway enable
/etc/init.d/wificalling-gateway restart
```

各协议的必需字段与 LuCI 页面一致：AnyTLS/Hysteria2/Trojan 用 `password`；TUIC 用 `uuid`+`password`；VLESS Reality 用 `uuid`+`flow`+`public_key`+`short_id`+`fingerprint`；VMess WS 用 `uuid`+`transport=ws`+`path`+`host`；WireGuard 用 `private_key`+`public_key`+`local_address`（可选 `reserved`/`mtu`）。`route_mode` 填 `independent`（独立通道）或 `follow_gateway`（跟随网关）。服务启动时会自动同步 DHCP 静态租约并预检 `nft`/`sing-box`，失败原因查看 `logread -e wificalling-gateway`。

## Wi-Fi Calling 操作要点

以下为设备侧操作经验，**不是插件功能**，仅供配置参考。

### 节点协议选择

ePDG/IPsec 隧道对丢包和抖动高度敏感。实测 **AnyTLS 协议**最适合 Wi-Fi Calling：它将 UDP（ePDG 500/4500）封装在 TCP/TLS 流中，提供可靠有序的传输，IPsec keepalive 不会丢失，语音媒体（RTP）也能稳定传输。基于 UDP/QUIC 的协议（Hysteria2、TUIC）虽然能建立 ePDG 隧道并显示 Wi-Fi Calling 图标，但**拨打电话会立即中断**——UDP-in-UDP 的公网抖动和丢包会导致 RTP 语音流无法维持。建议为 Wi-Fi Calling 设备选择 AnyTLS 节点。

### 设备定位

运营商通过设备上报的定位（wloc）验证服务区（用于紧急呼叫）。本插件通过对应国家的节点提供该国 IP，但不控制设备定位。设备需通过虚拟定位工具将位置设为 SIM 卡归属地，否则 Wi-Fi Calling 无法触发。

操作步骤：

1. 在 iPhone 上使用 [ios-location-spoofer](https://github.com/smthdagg/ios-location-spoofer) 配合小火箭（Shadowrocket）将定位劫持到 SIM 卡归属地。这是独立于本插件的项目。
2. 确认定位成功（地图显示归属地位置）。
3. **关闭小火箭**。如果不关闭，小火箭的 VPN 隧道会与路由器插件的 TPROXY 形成双重代理，导致流量冲突，ePDG 握手无法正常完成。
4. 等待几分钟，路由器活动日志中会出现 ePDG 握手记录（handshake_success），Wi-Fi Calling 激活。
