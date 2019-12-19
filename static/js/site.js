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


//Filters
$('.filter-group').change(function() {
	var val_select = $('select[name=filter-value].filter-value');
	val_select.children().addClass("hidden");
	val_select.children('optgroup#' + $(this).val()).removeClass('hidden');
	
	val_select.val(val_select.children('optgroup:not(.hidden)').children('option:first').val());
});

$('#add-filter').click(function(event) {
	event.preventDefault();
	
	$.ajax
	({
		url: "/filter/add/" + $('#filter-group option:selected').text() + "/" + $('#filter-value option:selected').text(),
		type: 'get',
		success: function(result)
		{
			location.reload();
		}
	});
});

$('.rm-filter').click(function(event) {
	event.preventDefault();

	$.ajax
	({
		url: $(this).attr('href'),
		type: 'get',
		success: function(result)
		{
			location.reload();
		}
	});
});


//remove hidden class from first option group by efault
$('select[name=filter-value].filter-value').children('optgroup#1').removeClass('hidden')

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

var source = new EventSource("/status");
source.onmessage = function(event) {
	var json = $.parseJSON(event.data);

	for(var i = 0; i < json.length; i++) {
	    var obj = json[i];

	    console.log(obj.id);
	    status = '';
		if (obj.loaderstate != '') {
			status += json.loaderstate + "\n";
		}
		if (obj.uploadpct != 0) {
			status += ' uploading: ' + json.uploadpct + "%\n" ;
		}

		$("#"+obj.node_id+"> .node-status").html(status);
	}
};

//Node Status
var node_status_evs = Array()

function node_addEventSource(node_id, url) {
	source = new EventSource(url);
	source.onmessage = function(event) {
		var json = $.parseJSON(event.data);
		status = '';
		if (json.loaderstate != '') {
			status += json.loaderstate + "\n";
		}
		if (json.uploadpct != 0) {
			status += ' uploading: ' + json.uploadpct + "%\n" ;
		}

		$("#"+node_id+"> .node-status").html(status);
	};
	node_status_evs.push(source);
};