from multiprocessing import Manager, Process
from asyncio import *
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

# scan games
games_list = build_games_list(db, prefs)

# set up messaging
# TODO: At this point maybe I should just use a messagebus
# TODO: These need to be able to operate asynchronously

# Functionality test
'''
test_node = NodeDescriptor("localhost", 10703)
print(test_node.ip)

test_loader = Loader()
test_game = games_list[0]
print(test_game)
print(test_game.title)
test_loader.game = test_game
test_loader.node = test_node
test_loader.system_name = test_game.system_name

print(test_loader.serialize())

test_loader.pworker = LoadWorker(loaderq, test_node, test_game)
test_loader.pworker.start()
'''
# End functionality test


#Launch web UI
app = UIWeb('Web UI', games_list, prefs)
t = Process(target=app.start)
t.start()

# set up adafruit ui if detected and enabled

# Main loop
# Handles messaging between loaders, etc. and the main thread/UI instances
print('entering main loop')
while 1:
	try:

		#FIXME: Kinda works. finish implementation of messaging. needs to be more asynchronous in its fetches.

		witem = ui_webq.get(False)
		print(witem)
		if witem[0] == 'LOAD':
			#FIXME: Check to see if we're already running something on whatever node has been specified and then kill it if yes
			test_game = None
			

			for g in games_list:
				if g.file_checksum == witem[1]:
					test_game = g
					break

			print(test_game.title)

			test_loader = Loader()
			test_loader.game = test_game

			test_node = NodeDescriptor(prefs['Network']['dimm_ip'], 10703)
			test_loader.node = test_node
			test_loader.system_name = test_game.system_name

			test_loader.pworker = LoadWorker(loaderq, test_node, test_game)
			test_loader.pworker.start()

		loader_item = loaderq.get(False)
		print(loader_item)
		litem = ui_lcdq.get(False)
		print(litem)
	except:
		pass
		#do nothing

