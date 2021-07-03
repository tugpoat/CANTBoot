import os
import sys
import configparser
import signal
import string
import json
import copy
from ast import literal_eval as make_tuple

from bottle import Bottle, template, static_file, error, request, response, view
import beaker.middleware
from Database import ACNTBootDatabase
from GameList import *

from mbus import *
from main_events import SaveConfigToDisk, ApplySysConfig, FOAD, FTPDEnableMessage
from Loader import *


session_opts = {
	'session.type': 'file',
	'session.cookie_expires': 300,
	'session.data_dir': './data',
	'session.auto': True
}

class UIWeb():
	_bottle = None
	def __init__(self, name, db, gameslist, nodeman, prefs):
		self._bottle = UIWeb_Bottle(name, gameslist, nodeman, prefs)

	def start(self):
		self._bottle.start()

#FIXME: The way this operates does not gracefully exit on receiving SIGINT/SIGKILL/SIGTERM
class UIWeb_Bottle(Bottle):
	#FIXME: The Web UI opening its own DB connection is not ideal.
	_db = None
	_games = None
	_nodeman = None
	_prefs = None
	_bottle = None
	_beaker = None
	list_loaded = False

	def __init__(self):
		super(UIWeb_Bottle, self).__init__()
		self._beaker = beaker.middleware.SessionMiddleware(self, session_opts)

		#set up routes
		self.route('/', method="GET", callback=self.index)
		self.route('/static/<filepath:path>', method="GET", callback=self.serve_static)
		self.route('/config', method="GET", callback=self.appconfig)
		self.route('/config', method="POST", callback=self.do_appconfig)
		self.route('/edit/<fhash>', method="GET", callback=self.edit)
		self.route('/edit/<fhash>', method="POST", callback=self.do_edit)
		self.route('/load/<node>/<fhash>', method="GET", callback=self.load)

		self.route('/gpio_reset', method="GET", callback=self.do_gpio_reset)

		MBus.add_handler(FOAD, self.die)

	def __init__(self, name, gameslist, nodeman, prefs):
		super(UIWeb_Bottle, self).__init__()
		self._beaker = beaker.middleware.SessionMiddleware(self, session_opts)
		self.name = name
		self._games = gameslist
		self._nodeman = nodeman
		self._prefs = prefs

		#set up routes
		self.route('/', method="GET", callback=self.index)

		self.route('/api/setmode/slave', method="GET")
		
		self.route('/static/<filepath:path>', method="GET", callback=self.serve_static)
		self.route('/config', method="GET", callback=self.appconfig)
		self.route('/config', method="POST", callback=self.do_appconfig)
		self.route('/config/apply', method="GET", callback=self.apply_appconfig)

		self.route('/load/<node_id>/<fhash>', method="GET", callback=self.load)
		self.route('/launch/<node_id>', method="GET", callback=self.launch)

		self.route('/games/<node_id>', method="GET", callback=self.games)
		self.route('/games/edit/<fhash>', method="GET", callback=self.game_edit)
		self.route('/games/edit/<fhash>', method="POST", callback=self.game_do_edit)

		self.route('/nodes', method="GET", callback=self.nodes)
		self.route('/nodes/add', method="GET", callback=self.node_add)
		self.route('/nodes/add', method="POST", callback=self.do_node_add)
		self.route('/nodes/edit/<node_id>', method="GET", callback=self.node_edit)
		self.route('/nodes/edit/<node_id>', method="POST", callback=self.do_node_edit)
		self.route('/nodes/status', method="GET", callback=self.node_status)

		self.route('/gpio_reset', method="GET", callback=self.do_gpio_reset)

		MBus.add_handler(FOAD, self.die)

	def start(self):
		self._db = ACNTBootDatabase('db.sqlite')
		self.run(host='0.0.0.0', port=8000, debug=False, quiet=True)

	def die(self, data):
		#TODO: ensure clean exit
		print("ohfuck")
		sys.stderr.close()
		self = None

	def serve_static(self, filepath):
		if 'images/games' in filepath and not os.path.isfile('static/'+filepath):
			return static_file('images/games/0.jpg', 'static')
		elif 'images/systems' in filepath and not os.path.isfile('static/'+filepath):
			return static_file('images/systems/0.jpg', 'static')

		return static_file(filepath, 'static')

	def index(self):
			return self.nodes()

	def games(self, node_id : str):
		node = self._nodeman.nodes[node_id]
		tmplist = []

		for g in self._games:
			if not self._nodeman.validateGameDescriptor(node, g):
				continue
			tmplist.append(copy.deepcopy(g))

		return template('games', node=node, games=tmplist)

	def game_edit(self, fhash : str):
		outgames = self._db.getGameList()
		cur_game = self._games[fhash]

		return template('game_edit', hashid=fhash, filename=cur_game.filename, game_title=cur_game.title, games_list=outgames)

	def game_do_edit(self, fhash : str):

		new_id = request.forms.get('games')
		identity = self._db.getGameInformationById(new_id)
		self._games[fhash].game_id = identity[0]
		self._games[fhash].title = identity[1]

		self._games[fhash].setSystem(self._db.getGameSystem(identity[0]))
		self._games[fhash].setAttributes(self._db.getGameAttributes(identity[0]))

		return self.game_edit(fhash)
		#TODO: Session variables so we can kick back to the game list for this node without passing things everywhere

	def do_gpio_reset(self):
		return "todo"
#        MBus.bus.publish("gpio.reset", "1")
		#ui_webq.put(["gpio", "reset"])

	def auth(self):
		return

	def appconfig(self):
		if self._prefs['Main']['skip_checksum'] == 'True':
			skip_checksum = 'checked'
		else:
			skip_checksum =  ''

		if self._prefs['Main']['gpio_reset'] == 'True':
			gpio_reset = 'checked'
		else:
			gpio_reset =  ''

		if self._prefs['Main']['autoboot'] == 'True':
			autoboot = 'checked'
		else:
			autoboot =  ''

		if self._prefs['Main']['fastboot_enable'] == 'True':
			fastboot_enable = 'checked'
		else:
			fastboot_enable = ''

		if self._prefs['System']['ftpd_enable'] == 'True':
			ftpd_enable = 'checked'
		else:
			ftpd_enable = ''

		#TODO: default settings are stupid, make them go away. maybe load them from the system if not present in settings.cfg
		eth0_ip         =   self._prefs['Network']['eth0_ip']       or '192.168.0.1'
		eth0_netmask    =   self._prefs['Network']['eth0_netmask']  or '255.255.255.0'

		wlan0_mode      =   self._prefs['Network']['wlan0_mode']    or 'AP'
		wlan0_ip        =   self._prefs['Network']['wlan0_ip']      or '10.0.0.1'
		wlan0_netmask   =   self._prefs['Network']['wlan0_netmask'] or '255.255.255.0'
		wlan0_ssid      =   self._prefs['Network']['wlan0_ssid']    or 'NAOMI'
		wlan0_psk       =   self._prefs['Network']['wlan0_psk']     or 'segarocks'

		wlan0_dhcp_low = self._prefs['Network']['wlan0_dhcp_low']  or '10.0.0.100'
		wlan0_dhcp_high = self._prefs['Network']['wlan0_dhcp_high']  or '10.0.0.200'

		#render
		return template('config',
			skip_checksum=skip_checksum,
			autoboot=autoboot,
			gpio_reset=gpio_reset,
			fastboot_enable=fastboot_enable,
			ftpd_enable=ftpd_enable,
			eth0_ip=eth0_ip,
			eth0_netmask=eth0_netmask,
			wlan0_mode=wlan0_mode,
			wlan0_ip=wlan0_ip,
			wlan0_ssid=wlan0_ssid,
			wlan0_psk=wlan0_psk,
			wlan0_netmask=wlan0_netmask,
			wlan0_dhcp_low=wlan0_dhcp_low,
			wlan0_dhcp_high=wlan0_dhcp_high)

	def do_appconfig(self):
		skip_checksum   = request.forms.get('skip_checksum')
		autoboot        = request.forms.get('autoboot')
		gpio_reset      = request.forms.get('gpio_reset')
		fastboot_enable = request.forms.get('fastboot_enable')

		ftpd_enable		= request.forms.get('ftpd_enable')

		ftpd_user_pw	= request.forms.get('ftpd_user_pw')

		if skip_checksum == 'on':
			skip_checksum = 'True'
		else:
			skip_checksum = 'False'

		if autoboot == 'on':
			autoboot = 'True'
		else:
			autoboot = 'False'

		if gpio_reset == 'on':
			gpio_reset = 'True'
		else:
			gpio_reset = 'False'

		if fastboot_enable == 'on':
			fastboot_enable = 'True'
		else:
			fastboot_enable = 'False'

		if ftpd_enable == 'on':
			ftpd_enable = 'True'
		else:
			ftpd_enable = 'False'

		self._prefs['Main']['skip_checksum']	= skip_checksum
		self._prefs['Main']['autoboot']			= autoboot
		self._prefs['Main']['gpio_reset']		= gpio_reset
		self._prefs['Main']['fastboot_enable']	= fastboot_enable

		self._prefs['System']['ftpd_enable']	= ftpd_enable

		if ftpd_enable == 'True' and len(ftpd_user_pw) > 3:
			MBus.handle(FTPDEnableMessage(payload=ftpd_user_pw))
		else:
			MBus.handle(FTPDEnableMessage(payload=''))

		#TODO: sanity checking on string values

		self._prefs['Network']['eth0_ip']         =     eth0_ip         =   request.forms.get('eth0_ip')
		self._prefs['Network']['eth0_netmask']    =     eth0_netmask    =   request.forms.get('eth0_netmask')

		wlan0_mode = request.forms.get('wlan0_mode') 
		if wlan0_mode == 'wlan0_mode_client':
			wlan0_mode = 'Client'
		else:
			wlan0_mode = 'AP'

		#TODO: sanity checking on string values

		self._prefs['Network']['wlan0_mode']      =     wlan0_mode.lower()
		self._prefs['Network']['wlan0_ip']        =     wlan0_ip        =   request.forms.get('wlan0_ip').lower()
		self._prefs['Network']['wlan0_netmask']   =     wlan0_netmask   =   request.forms.get('wlan0_netmask')
		self._prefs['Network']['wlan0_ssid']      =     wlan0_ssid      =   request.forms.get('wlan0_ssid')
		self._prefs['Network']['wlan0_psk']       =     wlan0_psk       =   request.forms.get('wlan0_psk')

		self._prefs['Network']['wlan0_dhcp_low']       =     wlan0_dhcp_low       =   request.forms.get('wlan0_dhcp_low')
		self._prefs['Network']['wlan0_dhcp_high']      =     wlan0_dhcp_high      =   request.forms.get('wlan0_dhcp_high')

		#Save config to disk
		MBus.handle(SaveConfigToDisk())


		if skip_checksum == 'True':
			skip_checksum = 'checked'
		else:
			skip_checksum = ''

		if autoboot == 'True':
			autoboot = 'checked'
		else:
			autoboot = ''

		if gpio_reset == 'True':
			gpio_reset = 'checked'
		else:
			gpio_reset = ''

		if fastboot_enable == 'True':
			fastboot_enable = 'checked'
		else:
			fastboot_enable = ''

		if ftpd_enable == 'True':
			ftpd_enable = 'checked'
		else:
			ftpd_enable = ''

		return template('config',
			did_config=True,
			skip_checksum=skip_checksum,
			autoboot=autoboot,
			gpio_reset=gpio_reset,
			fastboot_enable=fastboot_enable,
			ftpd_enable=ftpd_enable,
			eth0_ip=eth0_ip,
			eth0_netmask=eth0_netmask,
			wlan0_mode=wlan0_mode,
			wlan0_ip=wlan0_ip,
			wlan0_ssid=wlan0_ssid,
			wlan0_psk=wlan0_psk,
			wlan0_netmask=wlan0_netmask,
			wlan0_dhcp_low=wlan0_dhcp_low,
			wlan0_dhcp_high=wlan0_dhcp_high)

	def apply_appconfig(self):
		#yell at the main thread to reconfigure the network and reboob
		MBus.handle(ApplySysConfig())
		return

	def nodes(self):
		return template('nodes', nodes=self._nodeman.nodes)

	def node_add(self):
		node = NodeDescriptor('localhost', 10703)

		systems = self._db.getSystems()
		controls = self._db.getControlTypes()
		players = self._db.getPlayers()
		monitors = self._db.getMonitorTypes()
		dimm_ram = self._db.getDIMMRAMValues()

		node.system = systems[0]
		node.controls = controls[0]
		node.players = players[0]
		node.monitor = monitors[0]
		node.dimm_ram = dimm_ram[0]
		return template('node_edit', did_edit=False, node=node, systems=systems, controls=controls, players=players, monitors=monitors, dimm_ram=dimm_ram)

	def do_node_add(self):
		#Node doesn't exist, add it
		tnode = NodeDescriptor(str(request.forms.get('node_ip')), str(request.forms.get('node_port')))
		tnode.nickname = str(request.forms.get('nickname'))
		tnode.system = make_tuple(request.forms.get('system'))
		tnode.controls = make_tuple(request.forms.get('control-type'))
		tnode.monitor = make_tuple(request.forms.get('monitor-type'))
		tnode.dimm_ram = make_tuple(request.forms.get('dimm-ram'))

		self._nodeman.nodes.append(tnode)

		MBus.handle(SaveConfigToDisk())

		return template('nodes', nodes=self._nodeman.nodes)

	def node_edit(self,node_id, did_edit=False):
		node = self._nodeman.nodes[node_id]
		systems = self._db.getSystems()
		controls = self._db.getControlTypes()
		players = self._db.getPlayers()
		monitors = self._db.getMonitorTypes()
		dimm_ram = self._db.getDIMMRAMValues()
		return template('node_edit', did_edit=did_edit, node=node, systems=systems, controls=controls, players=players, monitors=monitors, dimm_ram=dimm_ram)

	def do_node_edit(self, node_id):
		#Node exists, edit it
		if self._nodeman.nodes[node_id]:
			if request.forms.get('delete_node') == 'on':
				self._nodeman.nodes.pop(node_id)
			else:
				# if self._nodeman.nodes[node_id].nickname != str(request.forms.get('nickname')): #TODO: remove old file

				self._nodeman.nodes[node_id].nickname = str(request.forms.get('nickname'))
				self._nodeman.nodes[node_id].system = make_tuple(request.forms.get('system'))
				self._nodeman.nodes[node_id].controls = make_tuple(request.forms.get('control-type'))
				self._nodeman.nodes[node_id].monitor = make_tuple(request.forms.get('monitor-type'))
				self._nodeman.nodes[node_id].dimm_ram = make_tuple(request.forms.get('dimm-ram'))

				MBus.handle(SaveConfigToDisk())
				
				return self.node_edit(node_id, True)

		#kick em back to the index
		return self.nodes()


	def load(self, node_id, fhash):
		#Yell at main to tell the node to load the game
		MBus.handle(Node_SetGameCommandMessage(payload=[node_id, fhash]))

	def launch(self, node_id):
		#Yell at main to run the game on the node
		MBus.handle(Node_LaunchGameCommandMessage(payload=node_id))

	#FIXME
	def node_status(self):
		response.content_type = "text/event-stream"
		response.cache_control = "no-cache"
		
		sobj = []
		for n in self._nodeman.nodes:
			n_state = str(self._nodeman.getLoaderState(n.node_id))
			
			nsob = {'node_id': n.node_id, 'node_state': n_state, 'uploadpct': round(float(n.loader_uploadpct))}

			sobj.append(nsob)

		ret = 'data: ' + json.dumps({'nodes': sobj}) + "\n\n"
		return ret

	#TODO: other routes