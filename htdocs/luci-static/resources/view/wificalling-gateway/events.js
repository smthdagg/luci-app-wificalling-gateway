'use strict';
'require view';
'require fs';
'require poll';
'require dom';
'require ui';

return view.extend({
	load: function() { return L.resolveDefault(fs.read('/var/run/wificalling-gateway/events.log'), ''); },
	render: function(raw) {
		function when(epoch) { return epoch ? new Date(epoch * 1000).toLocaleString() : '-'; }
		function lines(value) { return value.trim() ? value.trim().split('\n').reverse() : []; }
		function rows(value) {
			return lines(value).map(function(line) {
				var f = line.split('|');
				return E('tr', { class: 'tr' }, [when(Number(f[0])), f[1], f[2], f[7] || '-', f[3], (f[4] || '0') + ' ↑ / ' + (f[5] || '0') + ' ↓', _('Encrypted activity; call/SMS unknown')].map(function(x) { return E('td', { class: 'td' }, String(x)); }));
			});
		}
		var body = E('tbody', {}, rows(raw));
		var count = E('span', {}, String(lines(raw).length));
		function update(value) { dom.content(body, rows(value)); dom.content(count, String(lines(value).length)); }
		var clear = E('button', { class: 'btn cbi-button-negative', click: function() {
			ui.showModal(_('Clear activity log?'), [E('p', {}, _('This permanently removes only the Wi-Fi Calling activity history. Settings and system logs are not affected.')),
				E('div', { class: 'right' }, [E('button', { class: 'btn', click: ui.hideModal }, _('Cancel')),
				E('button', { class: 'btn cbi-button-negative', click: function() { fs.write('/var/run/wificalling-gateway/events.log', '').then(function() { update(''); ui.hideModal(); ui.addNotification(null, E('p', {}, _('Activity log cleared.')), 'info'); }).catch(function(err) { ui.addNotification(null, E('p', {}, _('Unable to clear log: ') + err.message), 'error'); }); } }, _('Clear log'))])]);
		} }, _('Clear log'));
		poll.add(function() { return L.resolveDefault(fs.read('/var/run/wificalling-gateway/events.log'), '').then(update); }, 5);
		return E([], [E('h2', {}, _('Encrypted IMS activity log')), E('p', {}, _('Records encrypted tunnel activity only. Phone numbers, message content, and whether an event is a call or SMS are not visible.')),
			E('div', { class: 'cbi-section' }, [E('p', {}, [_('Records: '), count, ' ', clear]), E('table', { class: 'table' }, [E('tr', { class: 'tr table-titles' }, [_('Time'), _('Device'), _('IP'), _('Wi-Fi Calling'), _('Activity'), _('Packet delta'), _('Meaning')].map(function(x) { return E('th', { class: 'th' }, x); })), body])])]);
	}
});
