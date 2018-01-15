function jumpToHall37WebPage(uri) {
	var loc = window.location;
	var params = {
		"action" : "html_redirect",
		"url" : "${http_game}" + uri,
		"refhost" : '' + loc.protocol + '//' + loc.hostname + ':' + loc.port
	};
	SS.setData(SS.url.model.debug_action, params, function(da) {
		if (da != undefined && da.result != undefined
				&& da.result.text != undefined) {
			document.location = da.result.text;
		} else {
			alert(JSON.stringify(da));
		}
	});
}
