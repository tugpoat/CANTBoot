from multiprocessing import Manager, Process
from asyncio import *
import configparser
from Database import ACNTBootDatabase
from NodeDescriptor import NodeDescriptor
from GameDescriptor import GameDescriptor
from GameList import *
from Loader import Loader, LoadWorker


# load settings
PREFS_FILE = "settings.cfg"
prefs = configparser.ConfigParser()
prefs_file = open(PREFS_FILE, 'r')
prefs.read_file(prefs_file)
prefs_file.close()

# set up database
db = ACNTBootDatabase('db.sqlite')

# scan games
print(prefs['Games'])
games_list = build_games_list(db, prefs)

# set up messaging
# TODO: At this point maybe I should just use a messagebus
# TODO: These need to be able to operate asynchronously
loaderq = Manager().Queue()
sysq	= Queue()
ui_webq = Queue()
ui_lcdq = Queue()
# set up web ui if enabled
# set up adafruit ui if detected and enabled

# Functionality test
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
# End functionality test

# Main loop
# Handles messaging between loaders, etc. and the main thread/UI instances
while 1:
	try:
		item = loaderq.get()
		print(item)
	except QueueEmpty as ex:
		v = 1
		#do nothing

