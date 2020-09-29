% include('header.tpl', title='NetDIMM Loader')
<link href="/static/nodes.css" rel="stylesheet" type="text/css" />
<div class="container">
	% include('navbar.tpl', activePage='nodes')

	% if defined('nodes'):
	<h4>DIMM Nodes</h4>
	% for node in nodes:
		<div class="label label-default node" id="{{node.node_id}}">
			<progress max="100" value="692"></progress>
			<div class="row">
				<div class="col0">
					<img class="system-logo" src="/static/images/systems/{{node.system[0]}}.png" alt="{{node.system[1]}}" />
					
					<div class="node-details">
						<span class="node-nickname row">{{node.nickname}}</span>
						<span class="node-ip-port row">{{node.ip}}:{{node.port}}</span> 
						%if node.hostname:
						(<span class="node-hostname">{{node.hostname}}</span>)
						%end
						<span class="node-status row"></span>
					</div>
					<div class="game-details">
						% if node.game:
						<span class="row game-title"><em>{{node.game.title}}</em></span>
						<span class="filename"><em>{{node.game.filename}}</em></span> <span class="label label-default fileinfo">{{round(node.game.file_size/float(1024*1024), 1)}} MB</span>
						%else:
						no game set
						%end
					</div>
				</div>
				<div class="col1">
					% if node.game:
					<img class="game-logo" src="/static/images/games/{{node.game.game_id}}.jpg" alt="game image" />
					%else:
					<img class="game-logo" src="/static/images/games/0.jpg" alt="game image" />
					%end
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
	<a class="add-link" href="/nodes/add"><span class="glyphicon glyphicon-plus"></span>Add Node</a>

	% if not defined('nodes'):
	<div class="alert alert-danger"><span class="glyphicon glyphicon-warning-sign"></span> No nodes were found! You'll need to add one.</div>
	% end

</div>

% include('footer.tpl')
