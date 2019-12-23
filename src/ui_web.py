import os
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

from globals import *

from mbus import *
from main_events import SaveConfigToDisk
from loader_events import *
from Loader import Loader


session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': './data',
    'session.auto': True
}

class UIWeb():
    _bottle = None
    def __init__(self, name, db, gameslist, nodeslist, prefs):
        self._bottle = UIWeb_Bottle(name, db, gameslist, nodeslist, prefs)

    def start(self):
        self._bottle.start()

class UIWeb_Bottle(Bottle):
    #FIXME: The Web UI opening its own DB connection is not ideal. correct this, it's un-necessary.
    _db = None
    _games = None
    _nodes = None
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

    def __init__(self, name, db, gameslist, nodelist, prefs):
        super(UIWeb_Bottle, self).__init__()
        self._beaker = beaker.middleware.SessionMiddleware(self, session_opts)
        self.name = name
        self._games = gameslist
        self._nodes = nodelist
        self._prefs = prefs
        self._db = db

        #set up routes
        self.route('/', method="GET", callback=self.index)
        self.route('/static/<filepath:path>', method="GET", callback=self.serve_static)
        self.route('/config', method="GET", callback=self.appconfig)
        self.route('/config', method="POST", callback=self.do_appconfig)
        self.route('/load/<node_id>/<fhash>', method="GET", callback=self.load)

        self.route('/games/<node_id>', method="GET", callback=self.gamechooser)
        self.route('/games/edit/<fhash>', method="GET", callback=self.edit)
        self.route('/games/edit/<fhash>', method="POST", callback=self.do_edit)

        self.route('/nodes', method="GET", callback=self.nodes)
        self.route('/nodes/edit/<node_id>', method="GET", callback=self.node_edit)
        self.route('/nodes/edit/<node_id>', method="POST", callback=self.do_node_edit)
        self.route('/nodes/status', method="GET", callback=self.node_status)

        self.route('/gpio_reset', method="GET", callback=self.do_gpio_reset)

        MBus.add_handler(Node_LoaderStatusMessage, self.handle_LoaderStatusMessage)

    def handle_LoaderStatusMessage(self, message: Node_LoaderStatusMessage):
        #OK what the heck is going on?
        #It has the old address assigned to the variable, it updates it, it confirms it updates it, and then when we access this in UIWeb_Bottle, it's fucked.
        print(id(message.payload[1]))
        print("ui setting status for %s at %s to %s", message.payload[0], id(self._nodes[message.payload[0]]._loader_state), message.payload[1])
        self._nodes[message.payload[0]].loader_state = message.payload[1]

    def start(self):
        self.run(host='0.0.0.0', port=8000, debug=False)

    def serve_static(self, filepath):
        if 'images/games' in filepath and not os.path.isfile('static/'+filepath):
            return static_file('images/games/0.jpg', 'static')
        elif 'images/systems' in filepath and not os.path.isfile('static/'+filepath):
            return static_file('images/systems/0.jpg', 'static')

        return static_file(filepath, 'static')

    def index(self):
            return self.nodes()

    def games(self):
        #FIXME
        filter_groups = self._db.getAttributes()
        filter_values = []
        filters = []
        if len(self._games) > 0:
            return template('index', list_loaded=self.list_loaded, games=self._games, filter_groups=filter_groups, filter_values=filter_values, activefilters=filters)
        else:
            return template('index', list_loaded=self.list_loaded)

    def do_gpio_reset(self):
        return "todo"
#        MBus.bus.publish("gpio.reset", "1")
        #ui_webq.put(["gpio", "reset"])

    def auth(self):
        return

    def appconfig(self):
        if self._prefs['Main']['multinode'] == 'True':
            multinode = 'checked'
        else:
            multinode = ''

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

        #TODO: default settings are stupid, make them go away. maybe load them from the system if not present in settings.cfg
        eth0_ip         =   self._prefs['Network']['eth0_ip']       or '192.168.0.1'
        eth0_netmask    =   self._prefs['Network']['eth0_netmask']  or '255.255.255.0'

        wlan0_mode      =   self._prefs['Network']['wlan0_mode']    or 'AP'
        wlan0_ip        =   self._prefs['Network']['wlan0_ip']      or '10.0.0.1'
        wlan0_netmask   =   self._prefs['Network']['wlan0_netmask'] or '255.255.255.0'
        wlan0_ssid      =   self._prefs['Network']['wlan0_ssid']    or 'NAOMI'
        wlan0_psk       =   self._prefs['Network']['wlan0_psk']     or 'segarocks'

        games_directory =   self._prefs['Games']['directory']       or 'games'

        #render
        return template('config', multinode=multinode, skip_checksum=skip_checksum, autoboot=autoboot, gpio_reset=gpio_reset, eth0_ip=eth0_ip, eth0_netmask=eth0_netmask, wlan0_mode=wlan0_mode, wlan0_ip=wlan0_ip, wlan0_ssid=wlan0_ssid, wlan0_psk=wlan0_psk, wlan0_netmask=wlan0_netmask, games_directory=games_directory)
        
    def do_appconfig(self):
        multinode       = request.forms.get('multinode')
        skip_checksum   = request.forms.get('skip_checksum')
        autoboot        = request.forms.get('autoboot')
        gpio_reset      = request.forms.get('gpio_reset')


        if multinode == 'on':
            multinode= 'True'
        else:
            multinode = 'False'

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

        self._prefs['Main']['multinode']          =     multinode
        self._prefs['Main']['skip_checksum']      =     skip_checksum
        self._prefs['Main']['autoboot']           =     autoboot
        self._prefs['Main']['gpio_reset']         =     gpio_reset

        #TODO: sanity checking on string values

        self._prefs['Network']['eth0_ip']         =     eth0_ip         =   request.forms.get('eth0_ip')
        self._prefs['Network']['eth0_netmask']    =     eth0_netmask    =   request.forms.get('eth0_netmask')

        wlan0_mode = request.forms.get('wlan0_mode') 
        if wlan0_mode == 'wlan0_mode_client':
            wlan0_mode = 'Client'
        else:
            wlan0_mode = 'AP'

        #TODO: sanity checking on string values

        self._prefs['Network']['wlan0_mode']      =     wlan0_mode
        self._prefs['Network']['wlan0_ip']        =     wlan0_ip        =   request.forms.get('wlan0_ip')
        self._prefs['Network']['wlan0_netmask']   =     wlan0_netmask   =   request.forms.get('wlan0_netmask')
        self._prefs['Network']['wlan0_ssid']      =     wlan0_ssid      =   request.forms.get('wlan0_ssid')
        self._prefs['Network']['wlan0_psk']       =     wlan0_psk       =   request.forms.get('wlan0_psk')

        self._prefs['Games']['directory']         =     games_directory =   request.forms.get('games_directory')

        # TODO: Maybe farm this out somewhere else (main thread?)
        with open('settings.cfg', 'w') as prefs_file:
            self._prefs.write(prefs_file)

        #rework this thing for html
        if multinode == 'True':
            multinode = 'checked'
        else:
            multinode = ''

        if skip_checksum == 'True':
            skip_checksum = 'checked'
        else:
            skip_checksum = ''

        if autoboot == 'True':
            autoboot = 'checked'
        else:
            autboot = ''

        if gpio_reset == 'True':
            gpio_reset = 'checked'
        else:
            gpio_reset = ''

        return template('config', did_config=True, multinode=multinode, skip_checksum=skip_checksum, autoboot=autoboot, gpio_reset=gpio_reset, eth0_ip=eth0_ip, eth0_netmask=eth0_netmask, wlan0_mode=wlan0_mode, wlan0_ip=wlan0_ip, wlan0_ssid=wlan0_ssid, wlan0_psk=wlan0_psk, wlan0_netmask=wlan0_netmask, games_directory=games_directory)

    def apply_appconfig(self):
        #TODO: yell at the main thread to reconfigure the network
        return

    def edit(self, fhash):
        return "todo"
        g = None
        #FIXME: REDO THIS
        return template('edit', filename=g.filename, game_title=g.title, hashid=fhash, games_list=gamelist)

    def do_edit(self, fhash):
        return "todo"
        #FIXME: REDO THIS
        return template('edit', filename=g.filename, game_title=g.title, hashid=fhash, games_list=gamelist, did_edit=True)

    def nodes(self):
        return template('nodes', nodes=self._nodes)

    def node_edit(self,node_id):
        node = self._nodes[node_id]
        systems = self._db.getSystems()
        controls = self._db.getControlTypes()
        players = self._db.getPlayers()
        monitors = self._db.getMonitorTypes()
        dimm_ram = self._db.getDIMMRAMValues()
        return template('node_edit', node=node, systems=systems, controls=controls, players=players, monitors=monitors, dimm_ram=dimm_ram)

    def do_node_edit(self, node_id):
        self._nodes[node_id].system = make_tuple(request.forms.get('system'))
        self._nodes[node_id].controls = make_tuple(request.forms.get('control-type'))
        self._nodes[node_id].monitor = make_tuple(request.forms.get('monitor-type'))
        self._nodes[node_id].dimm_ram = make_tuple(request.forms.get('dimm-ram'))
        MBus.handle(SaveConfigToDisk())
        return self.node_edit(node_id)

    def gamechooser(self, node_id):
        node = self._nodes[node_id]
        tmplist = []

        for g in self._games:
            if not node.validateGameDescriptor(g):
                continue
            tmplist.append(copy.deepcopy(g))

        return template('games', node=node, games=tmplist)


    def load(self, node_id, fhash):
        #Yell at main to tell the node to load the game
        MBus.handle(Node_UploadCommandMessage(payload=[node_id, fhash]))

    #FIXME
    def node_status(self):
        status_obj = []
        print('nm', id(nodeman.nodes['e7b7d426547ff42c3d46c7d5f566cde0']._loader_state))
        print('nm', id(nodeman.nodes['8fa801137105de04f7747b06e5bc519e']._loader_state))
        print ('nodeslist', id(self._nodes['e7b7d426547ff42c3d46c7d5f566cde0']._loader_state))
        for n in self._nodes:
            print('n', id(n._loader_state))
            print(vars(n))
            n_status = str(n.loader_state)
            if n.loader_state == Loader.STATUS_UPLOADING: n_status += ("%s%", n.loader_uploadpct)
            status_obj.append([['node_id', n.node_id], ['node_status', n_status]])

        return json.dumps(status_obj)

    #TODO: other routes