import json
import os
import subprocess
import tempfile
import unittest
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "root/usr/libexec/wificalling-gateway/compiler.sh"
MONITOR = ROOT / "root/usr/libexec/wificalling-gateway/monitor.sh"
FIREWALL = ROOT / "root/usr/libexec/wificalling-gateway/firewall.sh"
NODE_HEALTH = ROOT / "root/usr/libexec/wificalling-gateway/node-health.sh"
PASSWALL_BYPASS = ROOT / "root/usr/libexec/wificalling-gateway/passwall-bypass.sh"


def run_script(script, *args):
    return subprocess.run(
        [str(script), *map(str, args)], text=True, capture_output=True, check=False
    )


class CompilerTests(unittest.TestCase):
    def compile(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "normalized.conf"
            output = Path(tmp) / "sing-box.json"
            source.write_text(content, encoding="utf-8")
            result = run_script(COMPILER, source, output)
            payload = json.loads(output.read_text()) if output.exists() else None
            return result, payload

    def test_compiles_all_supported_protocols_and_multi_ip_rules(self):
        cfg = """\
global|log_level|warn
node|uk_any|anytls|vpn.example|443|secret-a|sni.example|0||||||||
node|uk_hy2|hysteria2|hy.example|8443|secret-b|hy.example|0|h3|||||||
node|uk_tuic|tuic|tuic.example|10443|secret-c|tuic.example|0|h3|uuid-1|bbr|native||||
node|uk_vless|vless|vl.example|443|uuid-2|apple.com|0||xtls-rprx-vision|||public-key|short-id|chrome|reality
node|uk_vmess|vmess|vm.example|8080|uuid-3|www.example|0|||0|||||ws|/ws|www.example
device|phones|uk_any|192.168.31.189,192.168.31.190
"""
        result, payload = self.compile(cfg)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            {x["type"] for x in payload["outbounds"]},
            {"anytls", "hysteria2", "tuic", "vless", "vmess", "direct"},
        )
        source_rules = [r for r in payload["route"]["rules"] if "source_ip_cidr" in r]
        self.assertEqual(source_rules[0]["source_ip_cidr"], ["192.168.31.189/32", "192.168.31.190/32"])
        self.assertEqual(source_rules[0]["outbound"], "node-uk_any")
        self.assertEqual(source_rules[0]["action"], "route")
        self.assertNotIn("secret-a", json.dumps(payload["log"]))
        self.assertEqual(
            [item["listen_port"] for item in payload["inbounds"]],
            [11441, 11442],
        )

    def test_rejects_duplicate_client_assignment(self):
        cfg = """\
node|a|hysteria2|a.example|443|one|a.example|0|h3|||||||
node|b|tuic|b.example|443|two|b.example|0|h3|uuid|bbr|native||||
device|first|a|192.168.1.20
device|second|b|192.168.1.20
"""
        result, payload = self.compile(cfg)
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(payload)
        self.assertIn("duplicate client IP", result.stderr)

    def test_rejects_unsupported_protocol_and_non_lan_ip(self):
        unsupported, _ = self.compile(
            "node|bad|socks|x.example|443|secret|x.example|0||||||||\n"
        )
        self.assertNotEqual(unsupported.returncode, 0)
        non_lan, _ = self.compile(
            "node|a|hysteria2|x.example|443|secret|x.example|0|h3|||||||\n"
            "device|phone|a|8.8.8.8\n"
        )
        self.assertNotEqual(non_lan.returncode, 0)
        self.assertIn("private IPv4", non_lan.stderr)

    def test_node_only_configuration_is_valid_json(self):
        result, payload = self.compile(
            "node|a|anytls|x.example|443|secret|x.example|0||||||||\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["route"]["rules"][0]["outbound"], "direct")

    def test_hysteria2_emits_base64_tls_public_key_pin(self):
        pin = "NjnZ/n+TKv/anU0iRGShxHKvs1qfVMcEwjc/oLYSJVM="
        fields = [
            "node", "hy", "hysteria2", "hy.example", "443", "secret",
            "hy.example", "0", "h3", "", "", "", "", "", "", "",
            "", "", "", pin,
        ]
        result, payload = self.compile("|".join(fields) + "\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        tls = payload["outbounds"][0]["tls"]
        self.assertEqual(tls["certificate_public_key_sha256"], [pin])


class MonitorTests(unittest.TestCase):
    def monitor(self, conntrack):
        with tempfile.TemporaryDirectory() as tmp:
            clients = Path(tmp) / "clients"
            table = Path(tmp) / "nf_conntrack"
            output = Path(tmp) / "status.json"
            clients.write_text("phone|192.168.31.189|node-uk\n", encoding="utf-8")
            table.write_text(conntrack, encoding="utf-8")
            result = run_script(MONITOR, clients, table, output)
            payload = json.loads(output.read_text()) if output.exists() else None
            return result, payload

    def test_reports_no_session(self):
        result, payload = self.monitor("")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["devices"][0]["state"], "no_session")

    def test_reports_negotiating_for_udp_500(self):
        line = "ipv4 2 udp 17 25 src=192.168.31.189 dst=203.0.113.8 sport=51000 dport=500 packets=2 bytes=320 src=203.0.113.8 dst=192.168.31.189 sport=500 dport=51000 packets=1 bytes=160\n"
        _, payload = self.monitor(line)
        self.assertEqual(payload["devices"][0]["state"], "negotiating")
        self.assertEqual(payload["devices"][0]["epdg_ip"], "203.0.113.8")

    def test_reports_likely_registered_for_assured_udp_4500(self):
        line = "ipv4 2 udp 17 170 src=192.168.31.189 dst=203.0.113.9 sport=4500 dport=4500 packets=12 bytes=4300 src=203.0.113.9 dst=192.168.31.189 sport=4500 dport=4500 packets=14 bytes=5200 [ASSURED] mark=0 use=1\n"
        _, payload = self.monitor(line)
        item = payload["devices"][0]
        self.assertEqual(item["state"], "likely_registered")
        self.assertTrue(item["assured"])
        self.assertEqual(item["reply_packets"], 14)

    def test_ignores_other_devices(self):
        line = "ipv4 2 udp 17 20 src=192.168.31.77 dst=203.0.113.9 sport=4500 dport=4500 packets=8 bytes=1 src=203.0.113.9 dst=192.168.31.77 sport=4500 dport=4500 packets=8 bytes=1 [ASSURED]\n"
        _, payload = self.monitor(line)
        self.assertEqual(payload["devices"][0]["state"], "no_session")

    def test_reports_active_traffic_for_high_packet_assured_flow(self):
        line = "ipv4 2 udp 17 170 src=192.168.31.189 dst=203.0.113.9 sport=4500 dport=4500 packets=70 bytes=4300 src=203.0.113.9 dst=192.168.31.189 sport=4500 dport=4500 packets=60 bytes=5200 [ASSURED]\n"
        _, payload = self.monitor(line)
        self.assertEqual(payload["devices"][0]["state"], "active_traffic")

    def test_persists_last_activity_and_writes_encrypted_ims_event(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            clients = tmp / "clients"
            table = tmp / "nf_conntrack"
            output = tmp / "status.json"
            state = tmp / "monitor.state"
            events = tmp / "events.log"
            clients.write_text("phone|192.168.31.189|node-uk\n", encoding="utf-8")
            table.write_text(
                "ipv4 2 udp 17 170 src=192.168.31.189 dst=203.0.113.9 "
                "sport=4500 dport=4500 packets=70 bytes=4300 "
                "src=203.0.113.9 dst=192.168.31.189 sport=4500 dport=4500 "
                "packets=60 bytes=5200 [ASSURED]\n",
                encoding="utf-8",
            )
            result = run_script(MONITOR, clients, table, output, state, events)
            self.assertEqual(result.returncode, 0, result.stderr)
            item = json.loads(output.read_text(encoding="utf-8"))["devices"][0]
            self.assertEqual(item["wificalling"], "registered")
            self.assertGreater(item["last_activity"], 0)
            self.assertEqual(item["activity_evidence"], "encrypted_ims_traffic")
            log = events.read_text(encoding="utf-8")
            self.assertIn("encrypted_ims_traffic", log)
            self.assertIn("call_or_sms_unknown", log)
            self.assertEqual(output.stat().st_mode & 0o777, 0o644)
            self.assertEqual(events.stat().st_mode & 0o777, 0o644)
            self.assertEqual(state.stat().st_mode & 0o777, 0o600)


class NodeHealthTests(unittest.TestCase):
    def test_reports_ping_latency_and_unreachable_nodes(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            nodes = tmp / "nodes"
            output = tmp / "node-status.json"
            nodes.write_text(
                "node-a|London AnyTLS|anytls|198.51.100.10|443\n"
                "node-b|London TUIC|tuic|198.51.100.11|443\n"
                "node-c|London VLESS|vless|198.51.100.12|8443\n",
                encoding="utf-8",
            )
            ping = tmp / "ping"
            ping.write_text(
                "#!/bin/sh\n"
                "case \"$*\" in\n"
                "  *198.51.100.10*) echo '64 bytes: time=23.4 ms'; exit 0;;\n"
                "  *) exit 1;;\n"
                "esac\n",
                encoding="utf-8",
            )
            ping.chmod(0o755)
            tcping = tmp / "tcping"
            tcping.write_text(
                "#!/bin/sh\n"
                "case \"$*\" in\n"
                "  *198.51.100.12*) echo 'response seq=0 time=41.7 ms'; exit 0;;\n"
                "  *) exit 1;;\n"
                "esac\n",
                encoding="utf-8",
            )
            tcping.chmod(0o755)
            env = dict(os.environ, PATH=f"{tmp}:{os.environ['PATH']}")
            result = subprocess.run(
                [str(NODE_HEALTH), str(nodes), str(output)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["nodes"][0]["state"], "reachable")
            self.assertEqual(payload["nodes"][0]["ping_ms"], 23.4)
            self.assertEqual(payload["nodes"][0]["measurement"], "icmp")
            self.assertEqual(payload["nodes"][1]["state"], "no_icmp_reply")
            self.assertIsNone(payload["nodes"][1]["ping_ms"])
            self.assertEqual(payload["nodes"][2]["state"], "tcp_reachable")
            self.assertEqual(payload["nodes"][2]["ping_ms"], 41.7)
            self.assertEqual(payload["nodes"][2]["measurement"], "tcp")
            self.assertEqual(output.stat().st_mode & 0o777, 0o644)


class PackageTests(unittest.TestCase):
    def test_release_metadata_and_runtime_dependencies(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        builder = (ROOT / "scripts/build-ipk.sh").read_text(encoding="utf-8")
        self.assertIn("PKG_VERSION:=1.1.1", makefile)
        self.assertIn("+tcping", makefile)
        self.assertIn("version=${1:-1.1.1-1}", builder)
        self.assertIn("tcping", builder)

    def test_public_project_documentation_exists(self):
        expected = [
            "README.md", "README_EN.md", "CHANGELOG.md", "SECURITY.md",
            "CONTRIBUTING.md", "docs/zh-CN/INSTALL.md", "docs/zh-CN/CONFIGURATION.md",
            "docs/zh-CN/BUILD.md", "docs/zh-CN/TROUBLESHOOTING.md",
            "docs/en/INSTALL.md", "docs/en/CONFIGURATION.md", "docs/en/BUILD.md",
            "docs/en/TROUBLESHOOTING.md", ".github/workflows/ci.yml",
        ]
        for name in expected:
            self.assertTrue((ROOT / name).exists(), name)

    def test_openwrt_package_surface_exists(self):
        expected = [
            "Makefile",
            "root/etc/config/wificalling-gateway",
            "root/etc/init.d/wificalling-gateway",
            "root/usr/share/luci/menu.d/luci-app-wificalling-gateway.json",
            "root/usr/share/rpcd/acl.d/luci-app-wificalling-gateway.json",
            "htdocs/luci-static/resources/view/wificalling-gateway/overview.js",
        ]
        for name in expected:
            self.assertTrue((ROOT / name).exists(), name)

    def test_luci_list_values_are_not_chained(self):
        source = (
            ROOT / "htdocs/luci-static/resources/view/wificalling-gateway/overview.js"
        ).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"\.value\([^\n;]*\)\.value\(")

    def test_luci_masks_password_in_grid_summary(self):
        source = (
            ROOT / "htdocs/luci-static/resources/view/wificalling-gateway/overview.js"
        ).read_text(encoding="utf-8")
        self.assertIn("secret.password = true", source)
        self.assertIn("secret.textvalue = function", source)

    def test_luci_acl_allows_ubus_file_reads_for_runtime_status(self):
        acl = json.loads(
            (ROOT / "root/usr/share/rpcd/acl.d/luci-app-wificalling-gateway.json")
            .read_text(encoding="utf-8")
        )["luci-app-wificalling-gateway"]["read"]
        self.assertEqual(acl["ubus"]["file"], ["read"])
        self.assertIn("/var/run/wificalling-gateway/status.json", acl["file"])
        self.assertIn("/var/run/wificalling-gateway/events.log", acl["file"])

    def test_luci_integrates_node_quality_and_removes_duplicate_reachability_panel(self):
        source = (
            ROOT / "htdocs/luci-static/resources/view/wificalling-gateway/overview.js"
        ).read_text(encoding="utf-8")
        self.assertIn("s.anonymous = true", source)
        self.assertIn("192.168.31.189", source)
        self.assertIn("Save the node first", source)
        self.assertNotIn("Observed node reachability", source)
        self.assertIn("Node status", source)
        self.assertIn("Ping / latency", source)
        self.assertIn("Quality", source)

    def test_luci_shows_wificalling_evidence_and_encrypted_activity_log(self):
        source = (
            ROOT / "htdocs/luci-static/resources/view/wificalling-gateway/overview.js"
        ).read_text(encoding="utf-8")
        self.assertIn("Wi-Fi Calling status", source)
        self.assertIn("UDP 500/4500", source)
        self.assertIn("Last activity", source)
        self.assertIn("Encrypted IMS activity log", source)
        self.assertIn("Calls and SMS cannot be distinguished", source)

    def test_luci_offers_independent_and_gateway_device_modes(self):
        source = (
            ROOT / "htdocs/luci-static/resources/view/wificalling-gateway/overview.js"
        ).read_text(encoding="utf-8")
        self.assertIn("route_mode", source)
        self.assertIn("independent", source)
        self.assertIn("follow_gateway", source)

    def test_passwall_bypass_targets_only_independent_client_file(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            clients = tmp / "clients"
            clients.write_text(
                "phone-a|192.168.31.189|node-a\nphone-b|192.168.31.190|node-b\n",
                encoding="utf-8",
            )
            log = tmp / "nft.log"
            nft = tmp / "nft"
            nft.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$*\" >> \"$WFC_TEST_LOG\"\n"
                "case \"$*\" in\n"
                "  'list table inet passwall') exit 0;;\n"
                "  'list chain inet passwall PSW_MANGLE'|'list chain inet passwall PSW_NAT') exit 0;;\n"
                "esac\n",
                encoding="utf-8",
            )
            nft.chmod(0o755)
            env = dict(os.environ, PATH=f"{tmp}:{os.environ['PATH']}", WFC_TEST_LOG=str(log))
            result = subprocess.run(
                [str(PASSWALL_BYPASS), "ensure", str(clients)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = log.read_text(encoding="utf-8")
            self.assertIn("192.168.31.189, 192.168.31.190", calls)
            self.assertIn("insert rule inet passwall PSW_MANGLE", calls)
            self.assertIn("insert rule inet passwall PSW_NAT", calls)
            self.assertIn("WFC_GATEWAY_BYPASS", calls)

    def test_ipk_builder_emits_standard_package_members(self):
        builder = ROOT / "scripts/build-ipk.sh"
        result = run_script(builder, "0.1.0-test")
        self.assertEqual(result.returncode, 0, result.stderr)
        package = Path(result.stdout.strip())
        with tarfile.open(package, "r:gz") as archive:
            self.assertEqual(
                archive.getnames(),
                ["debian-binary", "data.tar.gz", "control.tar.gz"],
            )
            data_member = archive.extractfile("data.tar.gz")
            self.assertIsNotNone(data_member)
            with tempfile.NamedTemporaryFile() as nested:
                nested.write(data_member.read())
                nested.flush()
                with tarfile.open(nested.name, "r:gz") as data_archive:
                    installed = data_archive.getmember("./etc/init.d/wificalling-gateway")
                    self.assertEqual((installed.uid, installed.gid), (0, 0))
        self.assertEqual(package.read_bytes()[:2], b"\x1f\x8b")

    def test_firewall_targets_only_listed_clients_and_both_transports(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            clients = tmp / "clients"
            clients.write_text(
                "phone-a|192.168.31.189|node-a\nphone-b|192.168.31.190|node-a\n",
                encoding="utf-8",
            )
            log = tmp / "calls"
            for command in ("nft", "ip"):
                stub = tmp / command
                stub.write_text(
                    "#!/bin/sh\nprintf '%s' \"$0 $*\" >> \"$WFC_TEST_LOG\"\n"
                    "[ \"$(basename \"$0\")\" = nft ] && cat >> \"$WFC_TEST_LOG\"\n"
                    "printf '\\n' >> \"$WFC_TEST_LOG\"\n",
                    encoding="utf-8",
                )
                stub.chmod(0o755)
            env = dict(os.environ, PATH=f"{tmp}:{os.environ['PATH']}", WFC_TEST_LOG=str(log))
            result = subprocess.run(
                [str(FIREWALL), "start", str(clients)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rules = log.read_text(encoding="utf-8")
            self.assertIn("192.168.31.189, 192.168.31.190", rules)
            self.assertIn("meta l4proto tcp", rules)
            self.assertIn("meta l4proto udp", rules)
            self.assertIn("meta l4proto tcp counter", rules)
            self.assertIn("meta l4proto udp counter", rules)
            self.assertIn("tproxy to :11441", rules)
            self.assertIn("tproxy to :11442", rules)
            self.assertNotIn("192.168.31.77", rules)


if __name__ == "__main__":
    unittest.main()
