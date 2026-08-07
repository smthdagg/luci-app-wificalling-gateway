# Changelog

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
