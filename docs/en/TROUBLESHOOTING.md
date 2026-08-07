# Troubleshooting

- Missing LuCI page or ACL error: restart `rpcd` and `uhttpd`, log out, and start a fresh LuCI session.
- Service failure: inspect `logread -e wificalling-gateway` and run `sing-box check -c /var/run/wificalling-gateway/sing-box.json` locally. Never post that JSON publicly.
- Reachable node but no Internet: reachability is not a proxy handshake. Check protocol fields, SNI, credentials, server UDP support, DNS, time, MTU, the selected static IP, and duplicate PassWall ACLs.
- Wi-Fi Calling icon but calls fail: UDP 4500 evidence does not validate carrier account, IMS provisioning, emergency address, or call routing. Verify with a known-good comparison and a completed real call.
- Recovery: stop the service and confirm the `wificalling_gateway` nftables table and policy rule table 166 are gone. The plugin never removes unrelated firewall rules.
