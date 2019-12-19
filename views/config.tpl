% include('header.tpl', title='Configure')

<div class="container">
	% include('navbar.tpl', activePage='config')

	% if defined('did_config'):
	<div class="alert alert-success"><span class="glyphicon glyphicon-ok"></span> Saved configuration!</div>
	%end

	<form class="form-horizontal" action="config" method="POST" role="form">
		<h2>Main</h2>
		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">Enable MultiNode</label>
				<div class="col-sm-3">
					<input type="checkbox" class="form-control" name="multinode" {{multinode}} />
				</div>
			</div>
		</div>
		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">Skip checksum on startup for installed games</label>
				<div class="col-sm-3">
					<input type="checkbox" class="form-control" name="skip_checksum" {{skip_checksum}} />
				</div>
			</div>
		</div>
		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">Automatically netboot all nodes if previously configured on software startup</label>
				<div class="col-sm-3">
					<input type="checkbox" class="form-control" name="autoboot" {{autoboot}} />
				</div>
			</div>
		</div>
		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">Enable GPIO Reset</label>
				<div class="col-sm-3">
					<input type="checkbox" class="form-control" name="gpio_reset" {{gpio_reset}} />
				</div>
			</div>
		</div>
		
		<h2>Network</h2>
		
		<div class="row container">
			<h3>eth0</h3>
			<div class="form-group">
				<label class="col-sm-2 control-label">IP Address</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="eth0_ip" value="{{eth0_ip}}" placeholder="IP Address" />
				</div>
			</div>

			<div class="form-group">
				<label class="col-sm-2 control-label">Subnet Mask</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="eth0_netmask" value="{{eth0_netmask}}" placeholder="Subnet Mask" />
				</div>
			</div>
		</div>
		<div class="row container">
			<h3>wlan0</h3>
			<div class="form-group">
				<label class="col-sm-2 control-label">Radio Mode</label>
				<div class="col-sm-3">
					<select class="form-control" id="wlan0_mode_select" name="wlan0_mode">
						<option value="wlan0_mode_ap" {{"selected" if wlan0_mode == "AP" else ""}}>AP</option>
						<option value="wlan0_mode_client" {{"selected" if wlan0_mode == "Client" else ""}}>Client</option>
					</select>
				</div>
			</div>

			<div class="form-group">
				<label class="col-sm-2 control-label">SSID</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="wlan0_ssid" value="{{wlan0_ssid}}" placeholder="SSID / Network Name" />
				</div>
			</div>

			<div class="form-group">
				<label class="col-sm-2 control-label">PSK</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="wlan0_psk" value="{{wlan0_psk}}" placeholder="PSK / Network key" />
				</div>
			</div>

			<div class="form-group">
				<label class="col-sm-2 control-label">IP Address</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="wlan0_ip" value="{{wlan0_ip}}" placeholder="IP Address" />
				</div>
			</div>

			<div class="form-group">
				<label class="col-sm-2 control-label">Subnet Mask</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="wlan0_netmask" value="{{wlan0_netmask}}" placeholder="Subnet Mask" />
				</div>
			</div>
		</div>

		<h2>Games</h2>
		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">Directory</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="games_directory" value="{{games_directory}}" placeholder="Directory" />
				</div>
			</div>
		</div>
		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label"></label>
				<div class="col-sm-3">
					<button id="rescan-games" class="btn btn-default">Rescan games</button>
				</div>
			</div>
		</div>
		
		<div class="row container">
			<div class="col-md-2">
				<button type="submit" class="btn btn-default">Save</button>
			</div>
		</div>
	</form>
</div>

% include('footer.tpl')
