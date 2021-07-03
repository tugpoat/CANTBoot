$('.game').click(function(event)
{
	event.preventDefault();
	
	$.ajax
	({
		url: $(this).find('.game-link').attr('href'),
		type: 'get',
		success: function(result)
		{
			window.location = '/';
			//var json = $.parseJSON(result)
			//$('#status').html(json.message);
		}
	});
});

$('.launch-link').click(function(event)
{
	event.preventDefault();

	$.ajax
	({
		url: $(this).attr('href'),
		type: 'get',
		success: function(result)
		{
			//window.location = '/';
			//var json = $.parseJSON(result)
			//$('#status').html(json.message);
		}
	});
});

$('#btn-apply').click(function() {
	event.preventDefault();
	
	$.ajax
	({
		url: "/config/apply",
		type: 'get',
		success: function(result)
		{
			alert("applying conf and reboobing fuck u");
		}
	});
})

$('#gpio_reboot').click(function() {
	event.preventDefault();
	
	$.ajax
	({
		url: "/gpio_reboot",
		type: 'get',
		success: function(result)
		{
			alert("reboobed");
		}
	});
})


$('#rescan-games').click(function(event) {
	event.preventDefault();

	$.ajax
	({
		url: "/rescan",
		type: 'get',
		success: function(result)
		{
			$(this).attr('disabled','disabled');
			//location.reload();
		}
	});
});

//Status bar

var source = new EventSource("/nodes/status");
source.onmessage = function(event) {
	var obj = JSON.parse(event.data);
	nodes = obj.nodes;
	for (i = 0; i < nodes.length; i++) {
	
	    var status = '';
		if (nodes[i].node_state != '') {
			status += nodes[i].node_state + "\n";
		}
		if (nodes[i].uploadpct > 0) {
			$("#node_"+nodes[i].node_id+" > progress").val(nodes[i].uploadpct);
			if (nodes[i].node_state == 'LoaderState.TRANSFERRING') status += " " + nodes[i].uploadpct + "%";
		}
		//console.log(status);

		$("#node_"+nodes[i].node_id+" .node-status").html(status);
	}
};

/*
//Node Status
var node_status_evs = Array()

function node_addEventSource(node_id, url) {
	source = new EventSource(url);
	source.onmessage = function(event) {
		var json = $.parseJSON(event.data);
		console.log(json);
		status = '';
		if (json.loaderstate != '') {
			status += json.node_state + "\n";
		}
		if (json.uploadpct != 0) {
			status += ' uploading: ' + json.uploadpct + "%\n" ;
		}

		$("#"+node_id+"> .node-status").html(status);
	};
	node_status_evs.push(source);
};*/