% include('header.tpl', title='NetDIMM Loader')
<link href="/static/games.css" rel="stylesheet" type="text/css" />
<div class="container">
	% include('navbar.tpl', activePage='games')

	% if defined('games'):
	<h4>Choose a game to play</h4>
	% for game in games:
	<a class="edit-link" href="/games/edit/{{game.file_checksum}}"><span class="glyphicon glyphicon-edit"></span></a>
		<div class="label label-default game {{game.checksum_status}}">
			<div class="col0">
				<img src="/static/images/games/{{game.game_id}}.jpg" alt="game image">
			</div>
			<div class="col1">
				<div><a class="game-link" href="/load/{{node.node_id}}/{{game.file_checksum}}">{{game.title}}</a></div>
				<div><span class="filename"><em>{{game.filename}}</em></span> <span class="label label-default fileinfo">{{round(game.file_size/float(1024*1024), 1)}} MB</span></div>
			</div>
		</div>
	% end
	% end
</div>
		
% include('footer.tpl')
