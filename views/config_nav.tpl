	<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
		<ul class="nav navbar-nav">
			<li {{!'class="active"' if activeConfigPage=='main'><a href="/config/main">Main</a></li>
			<li {{!'class="active"' if activeConfigPage=='network' else ''}}><a href="/config/network">Network</a></li>
			<li {{!'class="active"' if activeConfigPage=='system' else ''}}><a href="/config/system">System</a></li>
			<li {{!'class="active"' if activeConfigPage=='log' else ''}}><a href="/config/log">Log</a></li>
		</ul>
	</div>