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

			<div class="form-group">
				<label class="col-sm-2 control-label">DHCP Low</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="wlan0_dhcp_low" value="{{wlan0_dhcp_low}}" placeholder="10.0.0.100" />
				</div>
				<label class="col-sm-2 control-label">DHCP High</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="wlan0_dhcp_high" value="{{wlan0_dhcp_high}}" placeholder="10.0.0.200" />
			</div>
		</div>
