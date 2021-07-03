				<h4>WiFi Radio Settings</h4>
				<div class="form-group">
					<label class="col-sm-2 control-label">Radio Mode</label>
					<div class="col-sm-3">
						<select class="form-control" id="wlan0_mode_select" name="wlan0_mode">
							<option value="wlan0_mode_ap" {{"selected" if wlan0_mode == "ap" else ""}}>AP</option>
							<option value="wlan0_mode_client" {{"selected" if wlan0_mode == "client" else ""}}>Client</option>
							<option value="wlan0_mode_disabled" {{"selected" if wlan0_mode == "disabled" else ""}}>Disabled</option>
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
				<h4>IPv4 Settings</h4>
				<div id="wlan0-dhcp-client-options">
					<div class="form-group">
						<label class="col-sm-2 control-label">Use DHCP</label>
						<div class="col-sm-1">
							<input type="checkbox" id="wlan0_dhcp_client" class="form-control" name="wlan0_dhcp_client" {{wlan0_dhcp_client}} />
						</div>
					</div>
				</div>

				<div id="wlan0-static-ip-options">
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
					<div id="wlan0-static-ip-client-options">
						<div class="form-group">
							<label class="col-sm-2 control-label">DNS Server</label>
							<div class="col-sm-3">
								<input type="text" class="form-control" name="wlan0_dns" value="" placeholder="9.9.9.9" />
							</div>
						</div>
					</div>
				</div>
				<div id="wlan0-dhcp-server-options">
					<h4>DHCP Server Settings</h4>
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
				</div>