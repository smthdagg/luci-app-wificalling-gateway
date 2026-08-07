# 安装与升级

## 前提

- OpenWrt 或 ImmortalWrt 使用 firewall4/nftables。
- 软件源能提供 `sing-box >= 1.13.0`、`tcping`、`ip-full` 和 TPROXY 内核模块。
- 设备有足够空间运行 sing-box；建议至少预留 20 MB 闪存和 64 MB 可用内存。
- 为目标手机设置 DHCP 静态租约。

## 安装 Release IPK

```sh
opkg update
opkg install ./luci-app-wificalling-gateway_1.3.0-2_all.ipk
/etc/init.d/rpcd restart
```

若依赖在当前软件源不存在，请先为当前固件版本和 CPU 架构安装匹配依赖，禁止混装不同固件分支的内核模块。

## 首次启用

进入 **服务 → Wi-Fi Calling Gateway**，添加节点并保存，再添加设备策略。确认配置后启用服务并“保存并应用”。服务启动前会检查生成的 sing-box 配置；检查失败时不会安装转发规则。

## 升级与卸载

升级前自行备份 `/etc/config/wificalling-gateway`，不要公开备份。安装新版：

```sh
opkg install ./luci-app-wificalling-gateway_NEW_all.ipk
/etc/init.d/wificalling-gateway restart
```

卸载会停止服务并清理插件 nftables/策略路由规则：

```sh
/etc/init.d/wificalling-gateway stop
opkg remove luci-app-wificalling-gateway
```
