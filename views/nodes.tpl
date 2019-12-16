% include('header.tpl', title='NetDIMM Loader')

<div class="container">
	% include('navbar.tpl', activePage='nodes')

	% if defined('nodes'):
	<h4>DIMM Nodes</h4>
	% for node in nodes:
	<a class="edit-link" href="edit/{{node.game.file_checksum}}"><span class="glyphicon glyphicon-edit"></span></a>
		<div class="label label-default game {{node.game.checksum_status}}">
			<div class="col0">
				<img src="/static/images/systems/{{node.system[0]}}.png" alt="{{node.system[1]}}" />
			</div>
			<div class="col1">
				<img src="/static/images/{{node.game.game_id}}.jpg" alt="game image" />
				
				<span class="node-nickname">{{node.nickname}}</span>

			</div>
		</div>
		
	% end
	% end



	% if not defined('nodes'):
	<div class="alert alert-danger"><span class="glyphicon glyphicon-warning-sign"></span> No nodes were found! You'll need to add one.</div>
	% end

</div>

% include('footer.tpl')
