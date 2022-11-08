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

$('#chk-gamesfilter').click(function(event) {
	$('#filtergames').submit()
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


/*
	Upgraded, more resource-efficient status checking courtesy of sammargh
	https://www.arcade-projects.com/members/sammargh.3154/
*/
function isFunction(functionToCheck) {
  return functionToCheck && {}.toString.call(functionToCheck) === '[object Function]';
}

function debounce(func, wait) {
    var timeout;
    var waitFunc;

    return function() {
        if (isFunction(wait)) {
            waitFunc = wait;
        }
        else {
            waitFunc = function() { return wait };
        }

        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            func.apply(context, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, waitFunc());
    };
}

// reconnectFrequencySeconds doubles every retry
var reconnectFrequencySeconds = 15;
var evtSource;

var reconnectFunc = debounce(function() {
    setupEventSource();
    // Double every attempt to avoid overwhelming server
    reconnectFrequencySeconds *= 2;
    // Max out at ~1 minute as a compromise between user experience and server load
    if (reconnectFrequencySeconds >= 64) {
        reconnectFrequencySeconds = 64;
    }
}, function() { return reconnectFrequencySeconds * 1000 });

function setupEventSource() {
    evtSource = new EventSource("/nodes/status");
    evtSource.onmessage = function(e) {
        var json = $.parseJSON(event.data);
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
    evtSource.onopen = function(e) {
      // Reset reconnect frequency upon successful connection
      reconnectFrequencySeconds = 15;
    };
    evtSource.onerror = function(e) {
      evtSource.close();
      reconnectFunc();
    };
}
setupEventSource();