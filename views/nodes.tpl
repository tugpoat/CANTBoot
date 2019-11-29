% include('header.tpl', title='NetDIMM Loader')

<div class="container">
	% include('navbar.tpl', activePage='nodes')

	% if defined('games'):
	<h4>DIMM Nodes</h4>
	% for node in nodes:
	<a class="edit-link" href="edit/{{game.file_checksum}}"><span class="glyphicon glyphicon-edit"></span></a>
		<div class="label label-default game {{game.checksum_status}}">
			<div class="col0">
				<img src="/static/images/systems/{{node.system[0]}}.png" alt="{{node.system[1]}}" />
			</div>
			<div class="col1">
				<img src="/static/images/{{game.game_id}}.jpg" alt="game image" />
				
				<span class="node-nickname">{{node.nickname}}</span>

			</div>
		</div>
		
	% end
	% end



	% if not defined('games'):
	<div class="alert alert-danger"><span class="glyphicon glyphicon-warning-sign"></span> No games were found! Verify that the directory set on the configuration screen exists and contains valid NAOMI games.</div>
	% end

</div>

% include('footer.tpl')
