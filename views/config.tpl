% include('header.tpl', title='Configure')
		<div class="container">
			% include('navbar.tpl', activePage='config')

			% if defined('did_config'):
			<div class="alert alert-success"><span class="glyphicon glyphicon-ok"></span> Saved configuration!</div>

			%end
			<form class="form-horizontal" action="config" method="POST" role="form">
				<div id="config-tabs">
					<ul>
						<li><a href="#config-tabs-main">Main</a></li>
						<li><a href="#config-tabs-wifi">WiFi</a></li>
						<li><a href="#config-tabs-wired">Ethernet</a></li>
					</ul>
					<div id="config-tabs-main">
% include('config_main.tpl')
					</div>
					<div id="config-tabs-wifi">
% include('config_wlan0.tpl')
					</div>
					<div id="config-tabs-wired">
% include('config_eth0.tpl')
					</div>
				</div>
				<div class="row container">
					<div class="col-md-2">
						<button type="submit" class="btn btn-default">Save Settings</button>
					</div>
		            <div class="col-md-2">
						<button class="btn btn-default btn-apply" id="btn-apply">Apply Network Settings and Reboot</button>
					</div>
				</div>
			</form>
		</div>
% include('footer.tpl')