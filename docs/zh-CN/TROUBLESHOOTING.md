# 排错

## 安装报 `wfopen: ... No such file or directory`（iStoreOS 常见）

opkg 打不开文件，通常**不是包格式问题**，而是文件没真正到位：

- 用 `ls -la <路径>` 确认文件真实存在，或通过 LuCI「系统 → 软件包 → 上传软件包」上传（上传对话框会显示 MD5/SHA256，能显示即文件已到位）。
- 避免 `./` 相对路径（当前目录可能不是文件所在目录），用绝对路径安装：`opkg install /root/luci-app-wificalling-gateway_1.5.0-1_all.ipk`。
- 上传到 `/tmp` 时注意 tmpfs 挂载与上传工具的写入目标是否一致。

## iStoreOS 报 `incompatible with the architectures configured`

iStoreOS 的定制 opkg（koolcenter 版）对**本地文件安装**有架构检查限制（`all` 与具体架构都可能被拒），不影响包本身（格式已实测解析正常）。已实测可用的**解包安装**：

```sh
cd /tmp && tar xzf luci-app-wificalling-gateway_1.5.0-1_all.ipk && tar xzf data.tar.gz -C /
/etc/init.d/wificalling-gateway enable && /etc/init.d/wificalling-gateway start
```

## 25.12 安装报 `uninstallable, arch: all`

OpenWrt 25.12 的 apk 不接受 `arch: all` 的包。请使用 **noarch** 版：

```sh
apk add --allow-untrusted ./luci-app-wificalling-gateway_1.5.0-r1_noarch.apk
```

一个 noarch 包覆盖 x86_64 / aarch64 / armv7 / mipsel 全芯片。

## 安装报 `cannot find dependency sing-box`

24.10 系的源（含 iStoreOS）可能不提供 sing-box，需要自行安装与固件架构匹配的 sing-box 后重试。25.12 官方源自带 sing-box（自动解析）。禁止混装不同固件分支的包。

## LuCI 页面不出现或报权限错误

重启 rpcd 和 uhttpd，并退出 LuCI 后重新登录，旧会话可能缓存 ACL：

```sh
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

## 服务不能启动

```sh
/etc/init.d/wificalling-gateway restart
logread -e wificalling-gateway
sing-box check -c /var/run/wificalling-gateway/sing-box.json
```

检查节点字段、DNS、时间、证书、sing-box 版本和依赖。不要把运行时 JSON 发到公开 issue。

## 节点可达但不能上网

Ping/TCP 端口成功不等于代理握手成功。检查节点协议、SNI、TLS 指纹、UUID/密码、服务端 UDP 能力和 MTU。确认设备使用的 IP 与策略一致。

## 有 Wi-Fi Calling 图标但电话失败

UDP 4500 `ASSURED` 只证明双向 NAT-T 会话；运营商号码、IMS、激活资格、紧急地址和呼叫路由仍可能失败。用另一已知可用设备/节点做对照，并以运营商确认或真实通话为准。

## 停止后恢复网络

```sh
/etc/init.d/wificalling-gateway stop
nft list tables | grep wificalling_gateway
ip rule show | grep 'lookup 166'
```

正常情况下后两项无输出。若手工改过其他插件规则，应按其自身备份恢复，插件不会删除无关规则。
