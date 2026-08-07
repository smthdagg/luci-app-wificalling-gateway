# 排错

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

Ping/TCP 端口成功不等于代理握手成功。检查节点协议、SNI、TLS 指纹、UUID/密码、服务端 UDP 能力和 MTU。确认设备使用的 IP 与策略一致，且没有重复的 PassWall ACL。

## 有 Wi-Fi Calling 图标但电话失败

UDP 4500 `ASSURED` 只证明双向 NAT-T 会话；运营商号码、IMS、激活资格、紧急地址和呼叫路由仍可能失败。用另一已知可用设备/节点做对照，并以运营商确认或真实通话为准。

## 停止后恢复网络

```sh
/etc/init.d/wificalling-gateway stop
nft list tables | grep wificalling_gateway
ip rule show | grep 'lookup 166'
```

正常情况下后两项无输出。若手工改过其他插件规则，应按其自身备份恢复，插件不会删除无关规则。
