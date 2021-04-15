$( function() {
    $( "#config-tabs" ).tabs();
  } );

function ap_switcheroo() {
	if ($('#wlan0_mode_select').val() == 'wlan0_mode_client') {
		$('#wlan0-dhcp-server-options').hide();
		$('#wlan0-dhcp-client-options').show();
		$('#wlan0-static-ip-client-options').show();
	} else if ($('#wlan0_mode_select').val() == 'wlan0_mode_ap') {
		$('#wlan0-dhcp-server-options').show();
		$('#wlan0-dhcp-client-options').hide();
		$('#wlan0-static-ip-client-options').hide();
	}
}

function dhcpclient_switcheroo() {
	if ($("#wlan0_dhcp_client").prop('checked') == true) {
		$("#wlan0-static-ip-options").hide();
	} else {
		$("#wlan0-static-ip-options").show();
	}
}

$("#wlan0_mode_select").change(function(){
	ap_switcheroo();
});

$("#wlan0_dhcp_client").change(function(){
	dhcpclient_switcheroo();
});

$(document).ready(function(){
	$("input:text[name='ftpd_user_pw']").attr('value', Math.random().toString(16).substr(2, 14));
	ap_switcheroo();
	dhcpclient_switcheroo();
});
