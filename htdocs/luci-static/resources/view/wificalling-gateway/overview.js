'use strict';
'require view';
'require form';
'require fs';
'require poll';
'require ui';
'require uci';
'require dom';

return view.extend({
	load: function() {
		return Promise.all([
			L.resolveDefault(fs.read('/var/run/wificalling-gateway/status.json'), '{}'),
			L.resolveDefault(fs.read('/var/run/wificalling-gateway/node-status.json'), '{}'),
			uci.load('wificalling-gateway')
		]);
	},
	render: function(data) {
		function statusRows(parsed) {
			return (parsed.devices || []).map(function(d) {
				return E('tr', { class: 'tr' }, [d.label, d.ip, d.node, d.state, d.epdg_ip || '-', d.assured ? _('Yes') : _('No')].map(function(x) {
					return E('td', { class: 'td' }, String(x));
				}));
			});
		}
		function nodeRows(parsed) {
			return (parsed.nodes || []).map(function(n) {
				return E('tr', { class: 'tr' }, [n.label, n.protocol, n.server + ':' + n.port, n.state, n.measurement || '-', n.ping_ms == null ? '-' : n.ping_ms + ' ms'].map(function(x) {
					return E('td', { class: 'td' }, String(x));
				}));
			});
		}
		var m = new form.Map('wificalling-gateway', _('Wi-Fi Calling Gateway'),
			_('Routes only selected LAN devices through one sing-box process. Status is network evidence, not carrier activation confirmation.'));
		var s = m.section(form.NamedSection, 'main', 'global', _('General'));
		s.option(form.Flag, 'enabled', _('Enable'));
		var logLevel = s.option(form.ListValue, 'log_level', _('Log level'));
		logLevel.value('warn');
		logLevel.value('info');
		logLevel.value('debug');

		s = m.section(form.GridSection, 'node', _('Proxy nodes'));
		s.addremove = true; s.nodescriptions = true; s.anonymous = true;
		s.addbtntitle = _('Add proxy node');
		s.sectiontitle = function(sectionId) { return uci.get('wificalling-gateway', sectionId, 'label') || sectionId; };
		s.option(form.Flag, 'enabled', _('Enable')).default = '1';
		var nodeLabel = s.option(form.Value, 'label', _('Node display name'));
		nodeLabel.rmempty = false;
		nodeLabel.placeholder = _('Example: UK AnyTLS');
		nodeLabel.description = _('This is the name shown in the device node selector. The internal ID is generated automatically.');
		var p = s.option(form.ListValue, 'protocol', _('Protocol'));
		['anytls','hysteria2','tuic','vless','vmess'].forEach(function(x) { p.value(x); });
		s.option(form.Value, 'server', _('Server')).datatype = 'host';
		s.option(form.Value, 'port', _('Port')).datatype = 'port';
		var secret = s.option(form.Value, 'password', _('Password'));
		secret.password = true;
		secret.textvalue = function(sectionId) {
			return this.cfgvalue(sectionId) ? _('Set') : _('Not set');
		};
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
		udpMode.value('native');
		udpMode.value('quic');
		var transport = s.option(form.ListValue, 'transport', _('Transport'));
		transport.value('');
		transport.value('ws');
		s.option(form.Value, 'path', _('WebSocket path'));
		s.option(form.Value, 'host', _('WebSocket Host'));

		s = m.section(form.GridSection, 'device', _('Device policies'));
		s.addremove = true; s.nodescriptions = true; s.anonymous = true;
		s.addbtntitle = _('Add LAN device');
		s.sectiontitle = function(sectionId) { return uci.get('wificalling-gateway', sectionId, 'label') || sectionId; };
		s.option(form.Flag, 'enabled', _('Enable')).default = '1';
		var deviceLabel = s.option(form.Value, 'label', _('Device display name'));
		deviceLabel.rmempty = false;
		deviceLabel.placeholder = _('Example: iPhone 12');
		var routeMode = s.option(form.ListValue, 'route_mode', _('Routing mode'));
		routeMode.value('independent', _('Independent tunnel'));
		routeMode.value('follow_gateway', _('Follow gateway'));
		routeMode.default = 'independent';
		routeMode.description = _('Independent tunnel bypasses PassWall for this device and uses the selected plugin node. Follow gateway is not intercepted by this plugin.');
		var selectedNode = s.option(form.ListValue, 'node', _('Node'));
		selectedNode.rmempty = false;
		selectedNode.depends('route_mode', 'independent');
		selectedNode.description = _('Save the node first, then reload this page to select it for a device.');
		uci.sections('wificalling-gateway', 'node').forEach(function(node) {
			selectedNode.value(node['.name'], node.label || node['.name']);
		});
		var ips = s.option(form.DynamicList, 'source_ip', _('LAN IPv4 addresses'));
		ips.datatype = 'ip4addr';
		ips.rmempty = false;
		ips.placeholder = '192.168.31.189';
		ips.description = _('Enter one fixed LAN IPv4 address per item, for example 192.168.31.189. Reserve it in DHCP first. Multiple addresses may use the same policy.');

		var parsed;
		try { parsed = JSON.parse(data[0]); } catch (e) { parsed = { devices: [] }; }
		var body = E('tbody', { id: 'wfc-status-body' }, statusRows(parsed));
		var nodeParsed;
		try { nodeParsed = JSON.parse(data[1]); } catch (e) { nodeParsed = { nodes: [] }; }
		var nodeBody = E('tbody', { id: 'wfc-node-status-body' }, nodeRows(nodeParsed));
		var nodeStatus = E('div', { class: 'cbi-section' }, [
			E('h3', {}, _('Observed node reachability')),
			E('p', {}, _('Ping is ICMP reachability only. It does not prove that the proxy protocol or Wi-Fi Calling works.')),
			E('table', { class: 'table' }, [
				E('tr', { class: 'tr table-titles' }, [_('Node'), _('Protocol'), _('Server'), _('State'), _('Method'), _('Latency')].map(function(x) { return E('th', { class: 'th' }, x); })),
				nodeBody
			])
		]);
		var status = E('div', { class: 'cbi-section' }, [
			E('h3', {}, _('Observed IPsec/ePDG status')),
			E('p', {}, _('likely_registered means bidirectional ASSURED UDP 4500 was observed. It does not prove that the carrier account is activated or that a call will complete.')),
			E('table', { class: 'table' }, [
				E('tr', { class: 'tr table-titles' }, [_('Device'), _('IP'), _('Node'), _('State'), _('ePDG IP'), _('ASSURED')].map(function(x) { return E('th', { class: 'th' }, x); }))
				, body
			])
		]);
		poll.add(function() {
			return Promise.all([
				L.resolveDefault(fs.read('/var/run/wificalling-gateway/status.json'), '{}'),
				L.resolveDefault(fs.read('/var/run/wificalling-gateway/node-status.json'), '{}')
			]).then(function(raw) {
				var current, currentNodes;
				try { current = JSON.parse(raw[0]); } catch (e) { current = { devices: [] }; }
				try { currentNodes = JSON.parse(raw[1]); } catch (e) { currentNodes = { nodes: [] }; }
				dom.content(body, statusRows(current));
				dom.content(nodeBody, nodeRows(currentNodes));
			});
		}, 5);
		return m.render().then(function(formNode) {
			return E([], [formNode, nodeStatus, status]);
		});
	}
});
