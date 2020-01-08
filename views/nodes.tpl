% include('header.tpl', title='NetDIMM Loader')
<link href="/static/nodes.css" rel="stylesheet" type="text/css" />
<div class="container">
	% include('navbar.tpl', activePage='nodes')

	% if defined('nodes'):
	<h4>DIMM Nodes</h4>
	% for node in nodes:
		<div class="label label-default node {{node.game.checksum_status}}" id="{{node.node_id}}">
			<div class="row">
				<div class="col0">
					<img class="system-logo" src="/static/images/systems/{{node.system[0]}}.png" alt="{{node.system[1]}}" />
					
					<div class="node-details">
						<span class="node-nickname row">{{node.nickname}}</span>
						<span class="node-ip-port row">{{node.ip}}:{{node.port}}</span> (<span class="node-hostname">{{node.hostname}}</span>)
						<span class="node-status row"></span>
					</div>
					<div class="game-details">
						<span class="row game-title"><em>{{node.game.title}}</em></span>
						<span class="filename"><em>{{node.game.filename}}</em></span> <span class="label label-default fileinfo">{{round(node.game.file_size/float(1024*1024), 1)}} MB</span>
					</div>
				</div>
				<div class="col1">
					<img class="game-logo" src="/static/images/games/{{node.game.game_id}}.jpg" alt="game image" />
				</div>
			</div>
			<div class="node-control">
				<a class="edit-link" href="/nodes/edit/{{node.node_id}}"><span class="glyphicon glyphicon-edit"></span></a>
				<a class="select-game-link" href="/games/{{node.node_id}}"><span class="glyphicon glyphicon glyphicon-list-alt"></span></a>
				<a class="launch-link" href="/launch/{{node.node_id}}"><span class="glyphicon glyphicon-play-circle"></span></a>
			</div>
		</div>
		
	% end
	% end

	% if not defined('nodes'):
	<div class="alert alert-danger"><span class="glyphicon glyphicon-warning-sign"></span> No nodes were found! You'll need to add one.</div>
	% end

</div>

% include('footer.tpl')
