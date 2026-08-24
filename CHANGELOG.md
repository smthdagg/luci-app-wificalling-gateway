# Changelog

## 1.9.3 - 2026-08-25

- **openwrt-ai round 20 修复**：
  - **设备策略无法保存**：`source_ip` 的 validate 对 DynamicList 容器校验器传来的空值返回错误，导致加了第一个地址后整个策略 `validState=false` 保存不了——空值现在直接通过（"至少一个地址"由 `rmempty` 负责）。
  - **Transport 下拉缺 grpc/httpupgrade**：订阅导入的 grpc/httpupgrade 节点，编辑保存时 `ui.Select` 找不到对应选项而回退 None，传输被静默清空——下拉补上 `gRPC`/`HTTPUpgrade` 选项；`WebSocket path`/`WebSocket Host` 标签泛化为 `Transport path`/`Transport host`（目录同步更新，删孤儿）。
  - **gRPC `service_name` 空值错误兜底**：compiler 与导入器把空 service_name 补成 `"/"`，实际拨号 `///Tun` 必败——现在保持为空字符串（compiler vless/vmess + 导入器 vless/vmess 共 4 处）。
  - **握手防抖吞掉真实掉线**：防抖时钟与 `sustained_traffic` 共用 `old_event`，通话刚结束 15s 内的真实掉线（registered→not_detected）被丢弃——新增独立握手时间戳 `old_hs`（monitor.state 第 12 字段，向后兼容），sustained 不再重置它。
  - nit：`follow_gateway` 设备在空 IP 检查前提前返回（不再误报 "no valid client IP"）；sing-box 内存 profile 注释改为自洽说明（去掉外部项目引用）。
- 82/82 测试通过（新增：空 service_name、sustained 后掉线、round20 内容断言）。

## 1.9.2 - 2026-08-24

- **修复 1.8.17 遗留的 i18n 缺口**（全面审计发现）：`Invalid IPv4 address` 与 `Only private IPv4 addresses (RFC1918) are supported` 两个校验提示此前未进目录，zh-Hans 界面显示英文——现已加入 pot/po（无效的 IPv4 地址 / 仅支持私网 IPv4 地址（RFC1918））。pot/po 现 170 条一致、LC_ALL=C 排序正确、po2lmo 编译通过。
- 79/79 测试通过。

## 1.9.1 - 2026-08-24

- **对齐 wloc gateway 主项目更新（relax lite memory profile）**：
  - **sing-box 低内存 profile**：init.d 为 sing-box 进程设置 `GOMAXPROCS=1` 与 `GOGC=75`（单 worker + 适度 GC），降低受限路由器的常驻内存；不再设置上游已移除的 `GOMEMLIMIT=24MiB` 硬上限（AX6S 突发内存需求证明该上限过紧）。
- 79/79 测试通过（新增：内存 profile 断言）。

## 1.9.0 - 2026-08-24

- **对齐 wloc gateway 1.3 的 wifigateway 增量**（只取新增、不回退）：
  - **grpc/httpupgrade 传输支持**：compiler.sh 现在为 VLESS/VMess 节点生成 grpc（service_name 走 path 槽位）与 httpupgrade 传输块，订阅导入（node-import.js）同步支持 `type=grpc`/`type=httpupgrade` 的 vless:// 与 vmess:// 链接。
  - **xhttp 传输显式拒绝**：xhttp 是 clash/mihomo 的传输，sing-box 无法运行——导入时给出可读报错，编译时 `fail()` 拒绝，避免生成 sing-box 启动即拒绝的配置。
  - **握手事件 15 秒防抖**：registered↔not_detected 抖动（一秒内翻转）此前每次翻转都写一条握手事件刷爆活动日志——现在每个设备最多每 15 秒记一条握手成功/失败事件，与持续通讯事件的节流一致。
- 79/79 测试通过（新增：grpc/httpupgrade 编译、xhttp 拒绝、握手防抖）。

## 1.8.17 - 2026-08-24

- **openwrt-ai round 17 修复**：
  - **唯一 IP 被拒的设备跳过而非拖垮网关**：设备的所有 source_ip 都被校验拒绝时 DEVICE_IPS 为空，compiler 此前会 `fail("device has no client IP")` 使整个网关启动失败——现在 init.d 记录日志并跳过该设备（回落直连路由），与其余设备的 stale-node skip 一致；compiler END 块与 firewall.sh 对空列表已有安全处理。
  - **source_ip 输入收紧为 RFC1918**：LuCI 的 ip4addr datatype 接受任意 IPv4（含公网/CGNAT）——新增 validate 只允许私网地址并在输入时给出可读提示。
  - nit：版本号不再跳号（1.8.16 → 1.8.17）；`wgFailReason` 的 `tcp_failed` arm 为防御性对称（当前不可达），保留。
- 74/74 测试通过。

## 1.8.16 - 2026-08-23

- **openwrt-ai round 15 修复**：
  - **append_ip 完整 IPv4+RFC1918 校验**：此前的字符集 guard 放过了 `1.2`/`10.5`/`10.0.0.300`/`8.8.8.8`，这些值会进入 normalized.conf 并触发 compiler `private4()` 的 fail()——**整个网关编译失败**而非跳过坏 IP。现镜像 private4() 的 quad+range+RFC1918 检查，手写 UCI 的坏值跳过并记录日志。
  - **README 资产链接绝对化**：4 张截图改 raw.githubusercontent、SECURITY.md/CHANGELOG.md 行改 blob 绝对 URL——合并进 openwrt/luci 后不再 404。
  - `wgFailReason` 补 `tcp_failed` → Unreachable（与 wgFailDetail 对称）。
- 版本 bump：PKG_VERSION 1.8.15 → 1.8.16，README 六处安装引用同步更新。
- 74/74 测试通过；三平台 docker 安装测试全部通过。

## 1.8.14 - 2026-08-22

- **主动自查（18 轮 review 检查点全覆盖）发现并修复**：
  - **client IP 无格式验证**：设备策略的 source_ip 原样进入 nftables clients4 集合与生成的配置——LuCI 有 datatype 校验，但手写 UCI 可绕过注入任意字符串。init.d 现在在源头校验（非点分十进制跳过并记录日志），与 compiler/dhcp-sync 的既有验证一致。
  - **文档状态缺失**：DHCP 绑定列新增的「在线（静态 IP）」状态未写入配置文档（中英）——补齐说明。
  - **i18n 全面自查**：以 diffing 方式核对 htdocs 全部 `_()` 字面量与目录——163 个全部覆盖，0 缺失。
- 74/74 测试通过。

## 1.8.13 - 2026-08-22

- **openwrt-ai round 18 修复**：
  - `wgFailReason` 注释补 `tcp_failed`；`unreachable` 分支改传 `r.reason`（不再硬编码字面量绕过映射表）；`wgFailDetail` 增加 `tcp_failed` → Server unreachable（复用已有 msgid）。
  - **PR 内 README 适配上游语境**：导航栏与正文中的相对文档链接（docs/、README_EN.md、DEVELOPER.md）与 `[Releases](../../releases)` 在 openwrt/luci 树内均为死链——全部改为指向独立发布仓库的绝对 URL；快速安装命令**去除硬编码版本号**（改用 `<版本>` 占位符），消除每次 bump 重写 7 行 README 的维护负担。
- 74/74 测试通过。

## 1.8.12 - 2026-08-22

- **openwrt-ai round 17 修复**（3 个 nit）：
  - `wgFailReason` 注释更新（覆盖 node-test 来源的 reason：no_server / no_health_script / no_tcp_probe / busy）。
  - **`tcp_failed` 不再被丢弃**：`unreachable` 分支传入 `wgFailDetail('unreachable')`——AnyTLS/VLESS/VMess/Trojan 节点探测失败显示 "Offline — Server unreachable"（与 WireGuard 一致），复用已有目录字符串。
  - **补齐缺失目录字符串**：`Device offline`（DHCP 绑定列）、`Security`（字段标签）进入 pot/po（中文界面此前残留英文）。
- 74/74 测试通过。

## 1.8.11 - 2026-08-21

- **openwrt-ai round 16 修复**：
  - **未映射失败原因汉化**：`no_health_script` / `no_tcp_probe` 增加 `wgFailReason` 映射（`no_tcp_probe` 在未安装 tcping/nc 的固件上触发，属常见情况）与中文翻译；`no_tcp_probe` 增加 `wgFailDetail`（提示安装 tcping 或 nc）。rpcd 内部错误（`no_node_id` 等）保持原文（内部故障）。
  - **config_missing 语义拆分**：`node-test.sh` 的 server/port 缺失改用独立 `no_server` reason（与 `node-health.sh` 的 WG 密钥缺失语义分开），避免 Trojan/VLESS 无服务器节点被提示"缺少密钥/地址"。
- 74/74 测试通过（node-test config_missing 断言改为 no_server）。

## 1.8.10 - 2026-08-20

- **openwrt-ai round 15 修复**：busy 的 info 提示**仅限 busy**——1.8.9 把整个 `state=failed` 分支改成中性提示，误伤 `config_missing` / `no_health_script` / `no_tcp_probe`（这些是真实失败）；现在仅 `reason=busy` 显示 info，其余保持红色错误横幅 + "Unable to test node:" 前缀。
- 74/74 测试通过。

## 1.8.9 - 2026-08-20

- **openwrt-ai round 14 修复**（确认 round 13 主修复正确后的 3 个清理）：
  - 删除 outbounds 循环中重复的 wireguard+endpoint 跳过（`wg_check` 前重复了一份，后者不可达）。
  - 删除 node 规则中残留的校验说明注释（校验已迁移到 `wg_check`，注释原地残留）。
  - **busy 提示改为 info 而非 error**：`runNodeTest` 的 `state=failed` 分支不再带 "Unable to test node:" 前缀和红色失败样式——busy 场景显示中性提示（"Test in progress — Another test is running right now"）。
- 74/74 测试通过。

## 1.8.8 - 2026-08-19

- **openwrt-ai round 13 修复**：
  - **endpoint 逗号逻辑修正**：1.8.7 的 `first?"":","` 把逗号放在元素前，导致两个被引用 WG 节点编译出非法 JSON（`json.load()` 失败、`sing-box check` 拒绝）——改为**前导逗号**（每个已输出元素后/前正确分隔，跳过节点不影响）。
  - **unused-skip 覆盖节点校验**：WG 必填字段校验从 node 规则（used[] 尚未建立）**延迟到 emit 循环**（`wg_check`）——未被引用且缺键的节点被跳过，不再拖垮整个编译（与 device 侧 warn+skip 一致）；被引用的坏节点仍报错。
  - nit：`runNodeTest` 增加 `state=failed` 分支（busy 等无探测结果场景显示原因而非落入默认分支）。
- 74/74 测试通过（新增：未引用缺键 WG 节点跳过、被引用坏节点仍 fail）。

## 1.8.7 - 2026-08-19

- **全面审计修复（发布后审计发现 2 个 compiler bug）**：
  - **endpoint 分支未跳过未使用 WG 节点**：1.8.6 的 unused-node skip 只覆盖了 outbounds，endpoint 模式的未使用 WireGuard 节点仍生成孤儿 endpoint（无路由规则引用，纯占内存）——补齐跳过。
  - **endpoint 跳过节点后的逗号错误**：跳过一个或多个端点后，`w<nw` 的逗号判断会多输出逗号导致 JSON 解析失败（`Expecting value`）——改用"是否已输出过"标志。
- 73/73 测试通过（新增 endpoint 模式未使用节点跳过断言）。

## 1.8.6 - 2026-08-19

- **openwrt-ai round 12 修复**：
  - **node-test.sh 手动测试的 busy 处理**：`wg_handshake_test` 竞争返回 2 时直接输出 `reason=busy`（不再读空缓存误报 `unreachable`）——"Server unreachable" 从「测试」按钮上也消除。
  - 锁块缩进修正（round 11 重构时丢了一个 tab）。
- **同步 wloc 项目的 compiler 内存优化（unused node skip）**：未被任何设备策略引用的节点不再生成 sing-box outbound——减少配置体积与 sing-box 运行内存；现有测试适配（给被检查节点补充设备引用），新增 `test_compiler_skips_unused_nodes` 断言。
- 73/73 测试通过。

## 1.8.5 - 2026-08-18

- **openwrt-ai round 11 review 修复**（锁状态处理完善）：
  - **dead-pid 锁立即接管**：持有者已死（pid 存在但进程不存在）时不再等 60 秒年龄——`kill -0` 失败且 pid 非空 → 直接接管（round 10 误将 dead-pid 混入 "held" 分支，与 pidless 的正常瞬时状态同等处理）。
  - **busy 不写结果缓存**：竞争返回时不写 60s cache → 解除锁后下一个 tick 可立即重试，不再被"忙"缓存压制整整一分钟。
  - **状态形式区分**：竞争返回 `state=testing`（新状态，前端显示"测试进行中"）而非 `handshake_failed`+reason=busy——Status 和 Quality 列不再对未探测节点显示 "Offline"。
- `release.sh` 版本 bump 的 sed pattern 改为 `PKG_VERSION:=[0-9.]*`（`.*` 会贪婪吞掉引号导致 Python 语法错误）。
- 71/71 测试通过。

## 1.8.4 - 2026-08-18

- **openwrt-ai round 10 review 修复**（锁协议完善 + busy 区分 + nit）：
  - **pidless 锁按"持有中"处理**：无 pid 文件的锁目录是正常瞬时状态（`mkdir`→`echo $$` 之间、每次释放窗口），不再被立即接管——用锁目录**年龄**做废弃判断（超过探测预算 ~60 秒才接管），消除释放方误删新持有者锁、第三个 tick 在同一探测端口起第二个 sing-box 的竞态。
  - **释放单步化**：`release_lock()` 先验证 pid 仍是自己再 `rm -rf`（两步 unlink 会在接管场景删掉新持有者的锁）。
  - **竞争状态区分 busy**：锁被占用且无可用缓存时输出 `reason=busy`（"测试进行中"）而非 `unreachable`——此前 13ms 内对未探测的节点误报"服务器不可达"。
  - nit：`testNotify` 注释归位 + detail 分隔符；`wg_handshake_test` 补 `local result`；版本 bump 与 README 引用在同一版本内（合并时整体 squash 由上游处理）。
- 71/71 测试通过（新增 pidless 年轻锁 held、老锁接管、live holder 无缓存 busy 3 组测试）。

## 1.8.3 - 2026-08-17

- **openwrt-ai round 9 review 修复**（3 项实质 + 5 项 nit 全部处理）：
  - **握手测试锁修正**：`mkdir` 失败且持有者存活时**不再并发执行**（此前会覆盖持有者 pid、在同一探测端口起第二个 sing-box、并把锁从运行中的测试下移除）——改为回退缓存或失败；死锁接管修正 `kill -0 0` 误判（pid 文件缺失时不再接管自己）。
  - **探测子 shell 化**：探测（配置生成 → sing-box → 回显 → kill）整体放入子 shell，EXIT trap 只清理子 shell 自己的临时文件——不再清除调用者的 trap（此前 node-health 的 `$tmp` 清理丢失、node-test.sh 每次手动测试泄漏 `/tmp/wg-test-func.*`）；失败原因判断也移入子 shell（日志在 trap 清理前完成诊断）。
  - **回显驱动改用 curl（硬依赖）**：`/usr/bin/wget` 在官方 OpenWrt 是 uclient-fetch（无 http_proxy 支持）、busybox wget 的 HTTPS 默认关闭——探测改用包硬依赖的 `curl -x`（经 http inbound 的 CONNECT 隧道），wget 仅作降级兜底；`DEPENDS` 增加 `+curl`（含 18.06 专包）。
  - **表格精简补全**：`pre_shared_key` 与 `_device_picker` 补 `modalonly`（此前残留"WireGuard preshared key"凭据列和空选择器列）。
  - nit：nodeTest 按钮改 `_('Test')` 可翻译；`testNotify` 改用 `ui.addNotification`（不再重造横幅）；rpcd `list` 声明 `id` 参数；node-test.sh 注释 40 秒修正。
- 68/68 测试通过（新增 curl 优先、锁竞争 2 组测试）。

## 1.8.2 - 2026-08-17

- **openwrt-ai round 8 review 修复**（10 条 + 3 nit 全部处理）：
  - **compiler 顶层重复 PSK 删除**：endpoint 形式的 `pre_shared_key` 只保留在 peer 内（顶层是 sing-box 不认识的字段，会导致 `sing-box check` 失败、整个服务启动中止）。
  - **握手探测加固**：探测配置以 0600 创建（含 WG 私钥/PSK）并纳入信号 trap 清理；`wg_handshake_test` 全部变量 `local` 声明。
  - **回显服务 HTTPS + 可配置**：握手探测的出口回显改用 HTTPS 并支持 `main.probe_url` 配置（默认 `https://ip-api.com/json/?fields=query`），不再明文披露出口 IP、避免特定主机不可达导致的误报。
  - **node-status 回 `$RUNDIR`**：撤销 /www docroot 导出（未认证 LAN 可读 + 每 30 秒写 flash + 卸载残留）；紧凑输出已消除 /ubus 截断的诱因；overview 改回 `fs.read`（ACL 保护）。
  - **ACL 补 `/proc/net/arp`**：ARP 兜底在线检测与连接设备选择器此前因权限被拒而失效。
  - **服务监控精确匹配**：`singbox_running` 只匹配网关自身实例（`sing-box run -c $RUNDIR/sing-box.json`），握手探测的临时实例不再误报。
  - **设备选择器改用 `getUIElement`**：不再用 DOM id 寻址（GridSection 弹窗中行与弹窗同一 option 实例化两次，`cbid` 歧义）；`source_ip` 统一 `L.toArray` 防手写单值配置导致页面崩溃。
  - nit：status.js 注释改英文。
- 66/66 测试通过。

## 1.8.1 - 2026-08-17

- **再次对齐 wloc 项目 1.2.0**（wloc 1.2 回退了上一轮抽取的部分功能，本次只取其新增，不引入回退）：
  - **节点即时测试（nodeTest）**：节点表格每行新增「nodeTest」按钮，通过新的 rpcd 插件 `luci.wificalling-gateway`（`node_test` 方法，不依赖 wloc 域后端）触发——WireGuard 节点复用 node-health.sh 的握手函数做**绕过 60 秒缓存**的即时握手测试，其他协议做 TCP 可达性探测（tcping，无则 busybox nc）；结果以横幅通知显示（握手出口 IP / 失败原因）。
  - **握手失败原因分类**：`node-health.sh` 缓存与状态输出新增 `reason` 字段（`config_missing` / `timeout` / `unreachable`），状态列悬停显示详细说明；握手测试前校验密钥/地址缺失时快速失败。
  - **握手测试锁串行化**：mkdir 锁 + PID 存活接管，防止 5 秒监控 tick 与进行中的握手测试竞争同一探测端口（互给错误出口 IP）；锁被占用时测试返回 `busy`。
  - **reserved 转发**：握手探测配置转发 WireGuard `reserved`（WARP 风格端点必需，否则握手必失败）；探测端口改为 id 哈希派生。
  - **表单精简**：节点字段全部 `modalonly`（表格只显示名称/协议/服务器/端口/状态/延迟/质量，编辑弹窗可见全部字段），名称列不再重复；设备选择器 DOM id 修正为 `widget.cbid`（1.0.11 选择器在弹窗中失效的 bug）。
- 新增 rpcd 插件 `luci.wificalling-gateway`（exec 插件，`node_test` 方法白名单）+ ACL；10 条新中文翻译；66/66 测试通过。

## 1.8.0 - 2026-08-16

- **对齐 wloc 集成项目（WifiCalling&Wloc Gateway）的 Wi-Fi Calling 部分**（从路由器上运行的 1.0.11 包逐文件比对抽取，仅 wificalling 相关）：
  - **WireGuard 预共享密钥（PSK）**：`pre_shared_key` 字段贯通 init.d → compiler（endpoint 的 per-peer `pre_shared_key` 与 legacy outbound 顶层）→ LuCI 表单 → `[Interface]/[Peer]` 配置块粘贴导入（`parseWireguardConf`）。
  - **compiler 设备容错**：设备策略引用已删除的节点时不再整体编译失败——跳过该设备并警告（其余设备继续代理，失效设备回落到直连）。
  - **WireGuard 真实握手健康检查**：`node-health.sh` 对 WireGuard 节点不再用 ICMP，而是临时起 sing-box endpoint 经 HTTP 代理访问回显服务验证握手（60 秒缓存，输出验证通过的出口 IP；`WFC_SING_BOX` 可覆盖路径）。
  - **紧凑节点状态输出**：`node-status.json` 精简为 `id/state/measurement/ping_ms`，并导出到 `/www/wificalling-node-status.json` 由页面以 GET 读取——规避部分固件上 /ubus 通道截断大响应的问题。
  - **ARP 兜底在线检测**：无 DHCP 租约（静态 IP / 纯 AP 路由器）时用 ARP 缓存判断设备在线，`Device offline` 只在两个来源都不知道设备时报告。
  - **从已连接设备添加**：设备策略编辑弹窗新增「从已连接设备」选择器（DHCP 主机名优先，ARP-only 条目兜底；排除路由器自身与已绑定 IP），自动填写名称和 IP；IP 占位符按 LuCI 访问地址推导子网。
  - **服务健康监控**：新增 `service-health.sh`（每 60 秒由 procd 实例驱动），监控 sing-box/monitor 进程、生成配置有效性、**配置过期检测**（UCI 修改后未重启 → 告警）、nftables 规则数、设备数、节点健康汇总；「Wi-Fi Calling 状态」页顶部新增「服务状态」区渲染并告警。
- 新增中文翻译条目（22 条），61/61 测试通过（新增 PSK 字段对齐、未知节点容错、WG 握手验证、服务健康 4 组测试）。

## 1.7.4 - 2026-08-14

- **VMess/Reality 校验崩溃修复**：节点表单的 `securityOpt.validate` 调用了不存在的 `this.map.getSectionValue()`（60f81a2 引入，LuCI 从未提供该 API），编辑 VLESS 节点时会崩溃。改用 `this.section.formvalue()` 读取弹窗内的实时协议值——`uci.get()` 读的是已保存状态，会让新建的 VMess+Reality 节点漏过校验、已存在的 VMess 节点改成 VLESS 时被误拒；校验失败时返回可读消息而非字面 `false`（openwrt-ai round 6/7 确认）。PR#8921 对应提交同时修正了提交身份与 Signed-off-by（Formality 要求）。

## 1.7.3 - 2026-08-13

- **18.06/Lede 专包**：`luci-app-wificalling-gateway_1.7.3-1_18.06_all.ipk` 只声明 18.06 官方源实际提供的依赖（`luci-base`、`nftables`、`ip-full`），**官方 18.06.9 rootfs 实测安装成功**（nftables 0.9.0 自动解析）；不再注册 LuCI 菜单（18.06 的 Lua dispatcher 无法服务 JS 视图 action，避免坏条目）。服务本身是纯 Shell（init.d + libexec），可在 18.06 上运行；sing-box 与 TPROXY 内核模块由用户自备，缺失时 init.d 预检给出明确日志。LuCI 设置页面依赖 19.07+ 的 JS 视图架构，18.06 上通过命令行 UCI 配置。构建方式：`scripts/build-ipk.sh <版本> 1806`。

## 1.7.2 - 2026-08-13

- **18.06/Lede install failure fixed (issue #1)**: the hard `firewall4` dependency is gone (the plugin configures nftables itself and never talks to the firewall4 daemon; on 18.06-style feeds the unresolvable dependency made opkg reject the whole package with `cannot find dependency firewall4` / `incompatible with the architectures configured`). The Makefile and the IPK builder now depend on the actual runtime needs (`nftables`, `kmod-nft-tproxy`, `kmod-nft-socket`); `init.d` preflights `nft`/`sing-box` and fails with a readable log message on firmwares that cannot run the gateway. Requirements and a dedicated troubleshooting entry (README zh/en, INSTALL, TROUBLESHOOTING zh/en) document the 18.06 situation.
- Review fixes (openwrt-ai round 5): the Save button now goes through the supported `handleSave` view hook only — the DOM-patching workaround was removed (it co-registered a second click listener with LuCI's own, double-saving and applying without being asked; `stopPropagation` cannot suppress it), and `handleSave` commits the 24.10 session-scoped changeset via `ui.changes.apply(true)` with a guard for older LuCI; the DHCP binding column reads the dnsmasq lease file from `dhcp.@dnsmasq[0].leasefile` like `dhcp-sync.sh` (ACL now also covers `/etc/dhcp.leases`); `compiler.sh` rejects WireGuard `reserved` values with empty elements (`1,,2`, `,1`, `1,`); imports restore `+` in `pinSHA256` (and standard-base64 `pbk`/`sid`); `dhcp-sync.sh` allowlists hostnames to `[A-Za-z0-9_-]` (≤63 chars; backslash, `.`-leading and control characters included) and logs a failed dnsmasq restart instead of hiding it; the dead `$auxiliary` guard field was removed from `init.d`; `.pot`/`.po` entry gap fixed. 53/53 tests pass.

## 1.7.1 - 2026-08-11

- Activity log now marks sustained encrypted communication as **"Call in progress (inferred from sustained encrypted traffic)"** (`likely_call`): sustained bidirectional traffic after registration is the RTP signature of ringing/an in-call voice stream. The IPsec tunnel stays fully encrypted, so SMS cannot be reliably distinguished (short bursts look like keepalives/pushes) and is not logged; numbers, content and call direction remain invisible. Docs (README / CONFIGURATION, zh + en) now explain the DHCP static-binding rationale and the monitoring capability boundary.
- Review fixes (openwrt-ai): `dhcp-sync.sh` scrubs dnsmasq `dhcp-host` names (spaces/commas/quotes/semicolons would make dnsmasq reject the host line, breaking LAN DNS/DHCP) and reads the lease file from `dhcp.@dnsmasq[0].leasefile`; `compiler.sh` fails early with node-specific messages for missing wireguard keys/address or non-numeric `reserved`/`mtu`; `wg://` import restores `+` in base64 keys; `local` declarations in init.d; `.pot`/`.po` re-sorted to ASCII order. 49/49 tests pass.

## 1.7.0 - 2026-08-11

- **DHCP static leases are now auto-managed from device policies**: the nftables policy rules match a fixed client IPv4, but hand-made DHCP bindings silently broke when a device's MAC changed (iOS rotates its private Wi-Fi address) or when a policy was edited. A new `dhcp-sync.sh` runs on every service start: it creates/updates `wfc_`-prefixed DHCP host bindings from the live lease table (so a policy IP in use by a device always pins the device's current MAC), drops bindings whose policy was removed, and only touches plugin-created hosts (user-managed ones are left alone). `dnsmasq` is restarted only when something changed.
- LuCI device policies gained a **DHCP binding** status column (Bound / MAC changed, rebind on reconnect / Not bound yet / Device offline / Following gateway), backed by new read ACLs for `dhcp` and `/tmp/dhcp.leases`.
- Version bumped to 1.7.0; docs updated (README, README_EN).

## 1.6.0 - 2026-08-11

- Added **Trojan** and **WireGuard** proxy node protocols: Trojan emits a sing-box `trojan` outbound (`password` + TLS with SNI/ALPN/insecure/pin); WireGuard works with every sing-box generation — `init.d` detects the installed version and emits the **wireguard endpoint** form (route rules target the endpoint tag) for sing-box ≥ 1.11, or the legacy wireguard **outbound** for 1.10.x and older. The legacy outbound was deprecated in 1.11.0 (gated behind `ENABLE_DEPRECATED_WIREGUARD_OUTBOUND`) and removed in 1.13.0, so this was verified with `sing-box check` against 1.10.0 / 1.11.7 / 1.12.0 / 1.13.18 real binaries.
- Share-link import now accepts `trojan://` and `wg://` (WireGuard, Clash Meta / sing-box style: `wg://<peer-public-key>@<server>:<port>?private_key=…&local_address=…&reserved=…&mtu=…`); imported nodes map into UCI and never leave the browser.
- Node health probe falls back to `tcping` for Trojan (TCP-based) when ICMP is blocked; WireGuard stays ICMP-only (UDP).
- LuCI node form gained the WireGuard fields (private key, local address, reserved, MTU); protocol list and import panel text updated, with new Simplified Chinese translations.
- Version bumped to 1.6.0; docs updated (README, README_EN, CONFIGURATION zh/en).

## 1.5.0 - 2026-08-10

- Aligned IPK packaging with the official OpenWrt `scripts/ipkg-build` format (gzip tar of `debian-binary`, `data.tar.gz`, `control.tar.gz`); verified compatible with the real opkg in an official OpenWrt 24.10.8 rootfs and by an upgrade install on an ImmortalWrt 24.10.6 router (service running).
- Unified to a single universal `.ipk` for OpenWrt / ImmortalWrt / iStoreOS (24.10 based): the `sing-box` dependency is left unversioned so feeds shipping an older sing-box (e.g. iStoreOS) still satisfy it. Verified by a forced reinstall on an ImmortalWrt 24.10.6 router (service running) and parsing on iStoreOS / OpenWrt 24.10.8; install docs recommend using an absolute path (some opkg builds report a misleading "No such file or directory" for `./` relative paths). iStoreOS was further verified on the **24.10.7 full firmware under QEMU** (same version as the reported issue): install + service active + LuCI Settings/Status/Activity Log pages all working in Simplified Chinese; where the iStoreOS custom opkg rejects local files with `incompatible with the architectures configured`, an extract install (`tar xzf data.tar.gz -C /`) is documented and verified.
- Fixed the OpenWrt 25.12 `.apk` architecture: 25.12 apk-based repos ship every package with a concrete target arch and reject `arch: all` with "uninstallable". The build now defaults to **`noarch`** (accepted by the 25.12 apk and architecture-independent), verified with the exact user command (`apk add --allow-untrusted`) on official 25.12.3 rootfs for **x86_64, aarch64, armv7 and mipsel** — one APK covers every target.
- Added `scripts/build-apk.sh` to build the OpenWrt 25.12 `.apk` (apk-tools v3 via Docker Alpine, `ARCH` overridable, defaults to `noarch`).
- Dropped the hard `tcping` dependency (not present in official feeds); node-health probes now use `tcping` only when installed and otherwise fall back to ICMP.
- Fixed VLESS Reality / VMess TLS generation in `compiler.sh` (TLS block emitted for `security=tls` and Reality, `server_name` omitted when SNI is empty, `alter_id` coerced to a number) and the matching security field in the LuCI node form.
- Cleared stale `status.json` on service start and stop so the Wi-Fi Calling status page no longer shows old data after device edits or when the gateway is disabled; `monitor.state` is deliberately kept as the monitor's per-device baseline to avoid fabricated handshake events on restart.
- Hardened `init.d` (firewall.sh exit-status check with cleanup, delimiter guards on node/device names, vmess auxiliary/flow handling) and made `firewall.sh` exit cleanly when no clients are configured.
- Removed the unused `monitor_interval` config option.

## 1.4.0 - 2026-08-08

- Added a complete Simplified Chinese (zh-cn) LuCI translation catalog compiled into a real `.lmo` language pack and packaged into the IPK, so Chinese renders on the router instead of only in source.
- Chinese interface now shows unified Chinese descriptions, status, and error messages; protocol names and technical fields (TLS, UDP, UUID, SNI, ALPN, Reality, WebSocket, ePDG, IMS, ASSURED, QUIC, etc.) stay in English.
- Wrapped `node-import.js` error messages and the status/activity machine values (registered, connecting, sustained traffic, etc.) with `_()` so they translate in the UI instead of leaking raw English strings.
- Ships the language pack to both `/usr/lib/lua/luci/i18n/` and `/usr/share/luci/i18n/` for legacy Lua and modern ucode LuCI compatibility.
- Added a portable `scripts/po2lmo.py` (byte-compatible with luci-base `po2lmo`) so translations rebuild from `po/` on every package build.
- Refined the encrypted IMS activity log to record only handshake success/failure and sustained encrypted communication (ringing or calls lasting a few seconds); brief traffic bursts are no longer logged.
- Added an "Activity log" on/off toggle (default enabled) so observation logging can be disabled entirely from the Settings page; the activity log page then reports that recording is off.
- Restructured for official feed inclusion: `PKG_MAINTAINER`/`LUCI_URL` set, `po/` uses the gettext code `zh_Hans` with a `po/templates/` template, and `build-ipk.sh` aliases `zh_Hans`->`zh-cn` mirroring `luci.mk`'s `LUCI_LC_ALIAS`.
- Verified ImmortalWrt 25.12 compatibility (ucode dispatcher i18n path, `LUCI_LC_ALIAS`, and `sing-box`/`firewall4`/`kmod-nft-tproxy` deps match 24.10). Documented distribution via Releases, self-hosted opkg feed, and the ImmortalWrt official feed path.

## 1.3.0 - 2026-08-07

- Added local paste-import for AnyTLS, Hysteria2/Hy2, TUIC, VLESS, and VMess share links.
- Maps labels, credentials, TLS/SNI, Reality, WebSocket, UDP, and transport-specific fields into UCI nodes.
- Keeps imported links inside the LuCI browser session and never logs the raw URI.
- Package release 2 fixes the parser module factory for LuCI's `baseclass` loader.

## 1.2.1 - 2026-08-07

- Replaced per-poll event spam with one-time registration transitions and time-windowed sustained-traffic summaries.
- Requires traffic in three consecutive samples before writing a sustained activity event.
- Added configurable aggregation interval and per-device retention limit (defaults: 60 seconds and 20 records).

## 1.2.0 - 2026-08-07

- Split configuration, live Wi-Fi Calling status, and encrypted IMS activity into separate LuCI pages.
- Added automatic activity refresh, record count, and confirmation-protected log clearing.
- Restricted log write access to this plugin's activity file only.

## 1.1.1 - 2026-08-07

- Fixed LuCI runtime file access on OpenWrt systems where `/var/run` resolves to `/tmp/run`.
- Kept credential-bearing configuration private while exposing only non-secret monitoring data.

## 1.1.0 - 2026-08-07

- Integrated node alive state, measured latency, and quality bands directly into the Proxy nodes grid.
- Removed the duplicate Observed node reachability panel.
- Expanded device monitoring with Wi-Fi Calling registration, ePDG, UDP 500/4500, ASSURED, packet totals, deltas, and last activity.
- Added a capped encrypted IMS activity log while explicitly avoiding unsupported call/SMS identification claims.

## 1.0.1 - 2026-08-07

- Fixed empty LuCI monitoring tables by granting the required read-only `ubus.file.read` permission for the two runtime status files.
- Added a regression test for runtime status ACL access.

## 1.0.0 - 2026-08-07

- First stable release.
- Added AnyTLS, Hysteria2, TUIC, VLESS Reality, and VMess WebSocket nodes.
- Added per-device independent/follow-gateway routing and PassWall coexistence.
- Added node reachability and ePDG/IPsec UDP 500/4500 evidence views.
- Added startup validation, restrictive credential permissions, tests, CI, and bilingual documentation.
