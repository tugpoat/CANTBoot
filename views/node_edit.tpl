% include('header.tpl', title='Edit Node')

<div class="container">
	% include('navbar.tpl', activePage='nodes')

	% if defined('did_edit') and did_edit==True:
	<div class="alert alert-success"><span class="glyphicon glyphicon-ok"></span> Saved changes!</div>
	%end

	<form class="form-horizontal" method="POST" role="form">
		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">System</label>
				<select class="form-control" id="system-select" name="system">
				% for elem in systems:
					<option value="{{elem}}" {{"selected" if node.system[0] == elem[0] else ""}}>{{elem[1]}}</option>
				% end
				</select>
			</div>
		</div>

		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">Monitor</label>
				<select class="form-control" id="monitor-type-select" name="monitor-type">
				% for elem in monitors:
					<option value="{{elem}}" {{"selected" if node.monitor[0] == elem[0] else ""}}>{{elem[1]}}</option>
				% end
				</select>
			</div>
		</div>

		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">Controls</label>
				<select class="form-control" id="control-type-select" name="control-type">
				% for elem in controls:
					<option value="{{elem}}" {{"selected" if node.controls[0] == elem[0] else ""}}>{{elem[1]}}</option>
				% end
				</select>
			</div>
		</div>

		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">DIMM RAM</label>
				<select class="form-control filter-group" id="dimm-ram-select" name="dimm-ram">
				% for elem in dimm_ram:
					<option value="{{elem}}" {{"selected" if node.dimm_ram[0] == elem[0] else ""}}>{{elem[1]}}</option>
				% end
				</select>
			</div>
		</div>
		
		<div class="row container">
			<div class="form-group">
				<label class="col-sm-2 control-label">Nickname</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="nickname" value="{{node.nickname}}" placeholder="Clarence" />
				</div>
			</div>
		</div>
		
		<div class="row container">
			<h3>Endpoint (DIMM)</h3>
			<div class="form-group">
				<label class="col-sm-2 control-label">Host:Port</label>
				<div class="col-sm-3">
					<input type="text" class="form-control" name="node_ip" value="{{node.ip}}" placeholder="Host/IP" /> : <input type="text" class="form-control" name="node_port" value="{{node.port}}" placeholder="10703" />
				</div>
			</div>
		</div>
		
		<div class="row container">
			<div class="col-md-2">
				<label class="col-sm-2 control-label">Delete this node</label>
				<input type="checkbox" class="form-control" name="delete_node" />
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
