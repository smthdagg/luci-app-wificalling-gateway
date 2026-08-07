'use strict';
'require view';
'require form';
'require fs';
'require poll';
'require uci';
'require dom';

return view.extend({
	load: function() {
		return Promise.all([
			L.resolveDefault(fs.read('/var/run/wificalling-gateway/status.json'), '{}'),
			L.resolveDefault(fs.read('/var/run/wificalling-gateway/node-status.json'), '{}'),
			L.resolveDefault(fs.read('/var/run/wificalling-gateway/events.log'), ''),
			uci.load('wificalling-gateway')
		]);
	},
	render: function(data) {
		var parsed, nodeParsed;
		try { parsed = JSON.parse(data[0]); } catch (e) { parsed = { devices: [] }; }
		try { nodeParsed = JSON.parse(data[1]); } catch (e) { nodeParsed = { nodes: [] }; }

		function nodeById(id, source) {
			var nodes = (source || nodeParsed).nodes || [];
			for (var i = 0; i < nodes.length; i++) if (nodes[i].id === id) return nodes[i];
			return null;
		}
		function quality(n) {
			if (!n) return '-';
			if (n.state === 'unreachable') return _('Offline');
			if (n.ping_ms == null) return _('Unknown');
			if (n.ping_ms <= 100) return _('Excellent');
			if (n.ping_ms <= 200) return _('Good');
			if (n.ping_ms <= 300) return _('Fair');
			return _('Poor');
		}
		function nodeState(n) {
			if (!n) return '-';
			if (n.state === 'reachable' || n.state === 'tcp_reachable') return _('Alive');
			if (n.state === 'unreachable') return _('Offline');
			return _('Unknown');
		}
		function latency(n) {
			return n && n.ping_ms != null ? n.ping_ms + ' ms (' + n.measurement + ')' : '-';
		}
		function when(epoch) {
			return epoch ? new Date(epoch * 1000).toLocaleString() : '-';
		}
		function statusRows(source) {
			return (source.devices || []).map(function(d) {
				var ports = (d.ike_seen ? '500' : '-') + ' / ' + (d.nat_t_seen ? '4500' : '-');
				var packets = d.sent_packets + ' ↑ / ' + d.reply_packets + ' ↓';
				return E('tr', { class: 'tr' }, [d.label, d.ip, d.wificalling || d.state,
					d.epdg_ip || '-', ports, d.assured ? _('Yes') : _('No'), packets,
					when(d.last_activity), d.activity_evidence || 'none'].map(function(x) {
					return E('td', { class: 'td' }, String(x));
				}));
			});
		}
		function eventRows(raw) {
			var rows = raw.trim() ? raw.trim().split('\n').slice(-30).reverse() : [];
			return rows.map(function(line) {
				var f = line.split('|');
				return E('tr', { class: 'tr' }, [when(Number(f[0])), f[1], f[2], f[7] || '-',
					f[3], (f[4] || '0') + ' ↑ / ' + (f[5] || '0') + ' ↓', _('Calls/SMS unknown')].map(function(x) {
					return E('td', { class: 'td' }, String(x));
				}));
			});
		}

		var m = new form.Map('wificalling-gateway', _('Wi-Fi Calling Gateway'),
			_('Routes selected LAN devices through sing-box. Monitoring shows network evidence, not message or call content.'));
		var s = m.section(form.NamedSection, 'main', 'global', _('General'));
		s.option(form.Flag, 'enabled', _('Enable'));
		var logLevel = s.option(form.ListValue, 'log_level', _('Log level'));
		logLevel.value('warn'); logLevel.value('info'); logLevel.value('debug');

		s = m.section(form.GridSection, 'node', _('Proxy nodes'));
		s.addremove = true; s.nodescriptions = true; s.anonymous = true;
		s.addbtntitle = _('Add proxy node');
		s.sectiontitle = function(id) { return uci.get('wificalling-gateway', id, 'label') || id; };
		s.option(form.Flag, 'enabled', _('Enable')).default = '1';
		var nodeLabel = s.option(form.Value, 'label', _('Node display name'));
		nodeLabel.rmempty = false; nodeLabel.placeholder = _('Example: UK AnyTLS');
		nodeLabel.description = _('This name is shown in the device node selector.');
		var p = s.option(form.ListValue, 'protocol', _('Protocol'));
		['anytls','hysteria2','tuic','vless','vmess'].forEach(function(x) { p.value(x); });
		s.option(form.Value, 'server', _('Server')).datatype = 'host';
		s.option(form.Value, 'port', _('Port')).datatype = 'port';
		var nodeStatus = s.option(form.DummyValue, '_node_status', _('Node status'));
		nodeStatus.textvalue = function(id) { return E('span', { id: 'wfc-node-state-' + id }, nodeState(nodeById(id))); };
		var nodePing = s.option(form.DummyValue, '_node_ping', _('Ping / latency'));
		nodePing.textvalue = function(id) { return E('span', { id: 'wfc-node-ping-' + id }, latency(nodeById(id))); };
		var nodeQuality = s.option(form.DummyValue, '_node_quality', _('Quality'));
		nodeQuality.textvalue = function(id) { return E('span', { id: 'wfc-node-quality-' + id }, quality(nodeById(id))); };
		var secret = s.option(form.Value, 'password', _('Password'));
		secret.password = true; secret.textvalue = function(id) { return this.cfgvalue(id) ? _('Set') : _('Not set'); };
		s.option(form.Value, 'uuid', _('UUID'));
		s.option(form.Value, 'sni', _('TLS server name'));
		s.option(form.Flag, 'insecure', _('Allow insecure certificate'));
		s.option(form.Value, 'alpn', _('ALPN'));
		s.option(form.Value, 'pin_sha256', _('TLS public-key SHA-256 (base64)'));
		s.option(form.Value, 'flow', _('VLESS flow'));
		s.option(form.Value, 'public_key', _('Reality public key'));
		s.option(form.Value, 'short_id', _('Reality short ID'));
		s.option(form.Value, 'fingerprint', _('Reality fingerprint'));
		var udpMode = s.option(form.ListValue, 'udp_mode', _('TUIC UDP mode'));
		udpMode.value('native'); udpMode.value('quic');
		var transport = s.option(form.ListValue, 'transport', _('Transport'));
		transport.value(''); transport.value('ws');
		s.option(form.Value, 'path', _('WebSocket path'));
		s.option(form.Value, 'host', _('WebSocket Host'));

		s = m.section(form.GridSection, 'device', _('Device policies'));
		s.addremove = true; s.nodescriptions = true; s.anonymous = true;
		s.addbtntitle = _('Add LAN device');
		s.sectiontitle = function(id) { return uci.get('wificalling-gateway', id, 'label') || id; };
		s.option(form.Flag, 'enabled', _('Enable')).default = '1';
		var deviceLabel = s.option(form.Value, 'label', _('Device display name'));
		deviceLabel.rmempty = false; deviceLabel.placeholder = _('Example: iPhone 12');
		var routeMode = s.option(form.ListValue, 'route_mode', _('Routing mode'));
		routeMode.value('independent', _('Independent tunnel'));
		routeMode.value('follow_gateway', _('Follow gateway'));
		routeMode.default = 'independent';
		routeMode.description = _('Independent tunnel bypasses PassWall. Follow gateway is not intercepted.');
		var selectedNode = s.option(form.ListValue, 'node', _('Node'));
		selectedNode.rmempty = false; selectedNode.depends('route_mode', 'independent');
		selectedNode.description = _('Save the node first, then reload this page to select it for a device.');
		uci.sections('wificalling-gateway', 'node').forEach(function(node) { selectedNode.value(node['.name'], node.label || node['.name']); });
		var ips = s.option(form.DynamicList, 'source_ip', _('LAN IPv4 addresses'));
		ips.datatype = 'ip4addr'; ips.rmempty = false; ips.placeholder = '192.168.31.189';
		ips.description = _('Enter one fixed LAN IPv4 address per item. Reserve it in DHCP first.');

		var body = E('tbody', { id: 'wfc-status-body' }, statusRows(parsed));
		var eventBody = E('tbody', { id: 'wfc-event-body' }, eventRows(data[2]));
		var status = E('div', { class: 'cbi-section' }, [
			E('h3', {}, _('Wi-Fi Calling device monitoring')),
			E('p', {}, _('Registered means an ASSURED bidirectional UDP 4500 tunnel was observed. UDP 500/4500 and packet counts are network evidence.')),
			E('table', { class: 'table' }, [
				E('tr', { class: 'tr table-titles' }, [_('Device'), _('IP'), _('Wi-Fi Calling status'), _('ePDG IP'), _('UDP 500/4500'), _('ASSURED'), _('Packets'), _('Last activity'), _('Evidence')].map(function(x) { return E('th', { class: 'th' }, x); })), body
			])
		]);
		var events = E('div', { class: 'cbi-section' }, [
			E('h3', {}, _('Encrypted IMS activity log')),
			E('p', {}, _('Calls and SMS cannot be distinguished because IMS traffic is encrypted inside IPsec. This log records only state and packet changes.')),
			E('table', { class: 'table' }, [
				E('tr', { class: 'tr table-titles' }, [_('Time'), _('Device'), _('IP'), _('Wi-Fi Calling'), _('Activity'), _('Packet delta'), _('Content')].map(function(x) { return E('th', { class: 'th' }, x); })), eventBody
			])
		]);

		poll.add(function() {
			return Promise.all([
				L.resolveDefault(fs.read('/var/run/wificalling-gateway/status.json'), '{}'),
				L.resolveDefault(fs.read('/var/run/wificalling-gateway/node-status.json'), '{}'),
				L.resolveDefault(fs.read('/var/run/wificalling-gateway/events.log'), '')
			]).then(function(raw) {
				var current, currentNodes;
				try { current = JSON.parse(raw[0]); } catch (e) { current = { devices: [] }; }
				try { currentNodes = JSON.parse(raw[1]); } catch (e) { currentNodes = { nodes: [] }; }
				dom.content(body, statusRows(current));
				dom.content(eventBody, eventRows(raw[2]));
				(currentNodes.nodes || []).forEach(function(n) {
					var stateEl = document.getElementById('wfc-node-state-' + n.id);
					var pingEl = document.getElementById('wfc-node-ping-' + n.id);
					var qualityEl = document.getElementById('wfc-node-quality-' + n.id);
					if (stateEl) dom.content(stateEl, nodeState(n));
					if (pingEl) dom.content(pingEl, latency(n));
					if (qualityEl) dom.content(qualityEl, quality(n));
				});
			});
		}, 5);
		return m.render().then(function(formNode) { return E([], [formNode, status, events]); });
	}
});
