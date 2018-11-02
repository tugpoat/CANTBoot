from multiprocessing import Manager, Process
from asyncio import *
import time
import configparser

from Database import ACNTBootDatabase
from NodeDescriptor import NodeDescriptor
from GameDescriptor import GameDescriptor
from GameList import *
from Loader import Loader, LoadWorker
from queues import *
from ui_web import UIWeb


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

# TODO: build node list from config or saved profiles or something
nodes = []
nodes.append(NodeDescriptor(prefs['Network']['dimm_ip'], 10703))

# loader list
loaders = []

# Launch web UI
app = UIWeb('Web UI', games_list, prefs)
t = Process(target=app.start)
t.start()

# TODO: set up adafruit ui if detected and enabled

# scan games. We do this after loading the UIs. This way, we can signal progress (TODO) so the user isn't left in the dark.
games_list = build_games_list(db, prefs)

# Main loop
# Handles messaging between loaders, etc. and the main thread/UI instances
print('entering main loop')

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

					loader = Loader()
					loader.game = newgame
					loader.node = nodes[int(witem[1])]
					loader.system_name = newgame.system_name
					loader.pworker = LoadWorker(loaderq, nodes[int(witem[1])], newgame)
					loader.pworker.start()

					ui_webq.task_done()
				else:
					print('requested node out of range')


		if not loaderq.empty():
			loader_item = loaderq.get(False)
			print(loader_item)

	except Exception as e:
		print(str(e))
		pass