			<div class="form-group">
				<label class="col-sm-2 control-label">Skip checksum on startup for installed games</label>
				<div class="col-sm-1">
					<input type="checkbox" class="form-control" name="skip_checksum" {{skip_checksum}} />
				</div>
			</div>

			<div class="form-group">
				<label class="col-sm-2 control-label">Automatically netboot all nodes on software startup if previously configured</label>
				<div class="col-sm-1">
					<input type="checkbox" class="form-control" name="autoboot" {{autoboot}} />
				</div>
			</div>
			<div class="form-group">
				<label class="col-sm-2 control-label">Enable GPIO Reset</label>
				<div class="col-sm-1">
					<input type="checkbox" class="form-control" name="gpio_reset" {{gpio_reset}} />
				</div>
			</div>
			<div class="form-group">
				<label class="col-sm-2 control-label">Temporarily Enable FTP Server</label>
				<div class="col-sm-1">
					<input type="checkbox" class="form-control" name="ftpd_enable" {{ftpd_enable}} />
				</div>
				<label class="col-sm-2 control-label">user: naomiftp, pw: </label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="ftpd_user_pw" value="" />
				</div>
			</div>