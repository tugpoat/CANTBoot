from multiprocessing import Manager, Process
from asyncio import *
import time
import configparser

from Database import ACNTBootDatabase
from NodeDescriptor import NodeDescriptor, NodeList
from GameDescriptor import GameDescriptor
from GameList import *
from Loader import Loader, LoadWorker
from ui_web import UIWeb
from sysctl import *
from gpio_reboot import *
from queues import *
from mbus import *

#Message handlers

def cb_gpio_reset():
	print("got message")
	GPIO_Reboot();

# load settings
PREFS_FILE = "settings.cfg"
prefs = configparser.ConfigParser()
prefs_file = open(PREFS_FILE, 'r')
prefs.read_file(prefs_file)
prefs_file.close()

# set up database
db = ACNTBootDatabase('db.sqlite')

games_list = []

# set up messaging
# TODO: At this point maybe I should just use a messagebus
# TODO: These need to be able to operate asynchronously
#MBus.subscribe("gpio.reset", MBus.self, cb_gpio_reset)

# TODO: build node list from config or saved profiles or something
nodes = NodeList()
defnode = NodeDescriptor(prefs['Network']['dimm_ip'], 10703)
defnode.nickname = 'default'
defnode.system = (1, 'NAOMI')
defnode.monitor = (14, 'Horizontal')
defnode.controls = (25, '2L12B')
nodes.append(defnode)

nodes.saveNodes()

print("yay")

# loader list
loaders = []

# Launch web UI
app = UIWeb('Web UI', games_list, prefs)
t = Process(target=app.start)
t.start()

# TODO: set up adafruit ui if detected and enabled

# scan games. We do this after loading the UIs. This way, we can signal progress (TODO) so the user isn't left in the dark.
games_list = build_games_list(db, prefs)
app._games = games_list
app.list_loaded = True

# Main loop
# Handles messaging between loaders, etc. and the main thread/UI instances


while 1:
	try:

		#FIXME: Kinda works. finish implementation of messaging. needs to be more asynchronous in its fetches.
		if not ui_webq.empty():
			witem = ui_webq.get(False)
			print(witem)
			if witem[0] == 'LOAD':
				#FIXME: Check to see if we're already running something on whatever node has been specified and then kill it if yes
				newgame = None

				#make sure that the requested node is valid
				if int(witem[1]) < len(nodes) and int(witem[1]) > -1:
					for g in games_list:
						if g.file_checksum == witem[2]:
							newgame = g
							break
					#set up loader
					print(newgame.title)

					tloader = Loader()
					tloader.game = newgame
					#loader.node = nodes[int(witem[1])]
					tloader.system_name = newgame.system_name

					nodes[int(witem[1])].loader = tloader
					nodes[int(witem[1])].loader.pworker = LoadWorker(loaderq, nodes[int(witem[1])], newgame)
					nodes[int(witem[1])].loader.pworker.start()

					nodes.saveNodes()

					ui_webq.task_done()
				else:
					print('requested node out of range')

			#system control functions	
			elif witem[0] == 'gpio':
				if witem[1] == 'reset':
					GPIO_Reboot()
			elif witem[0] == 'sysctl':
				# Ideally we would do some kind of mapping in here so we don't need a giant if structure 
				# but I'm going to be lazy for now and clean it up later
				if witem[1] == 'reboot':
					reboot_system()
				elif witem[1] == 'shutdown':
					shutdown_system()
				elif witem[1] == 'writeappconfig':
					exit()
					#remount configs/roms partition rw
					#write config
					#remount configs/roms partition ro
				elif witem[1] == 'writesysconfig':
					remount_root_rw()
					#TODO: Write config
					remount_root_ro()
				elif witem[1] == 'sshd_en':
					enable_sshd()
				elif witem[1] == 'sshd_dis':
					disable_sshd()

		if not loaderq.empty():
			loader_item = loaderq.get(False)
			print(loader_item)

	except Exception as e:
		print(str(e))
		pass
