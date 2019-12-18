from multiprocessing import Manager, Process
from asyncio import *
import time
import configparser

from Database import ACNTBootDatabase
from NodeDescriptor import NodeDescriptor
from NodeList import *
from GameDescriptor import GameDescriptor
from GameList import *

from mbus import *
from loader_events import *

from ui_web import UIWeb

# load settings
PREFS_FILE = "settings.cfg"
prefs = configparser.ConfigParser()
prefs_file = open(PREFS_FILE, 'r')
prefs.read_file(prefs_file)
prefs_file.close()

#TODO: if config file/directory does not exist, copy a default from the read-only partition to the SD card.

# set up database
db = ACNTBootDatabase('db.sqlite')

# set up game list
games_list = GameList(prefs['Directories']['cfg_dir'], prefs['Directories']['games_dir'])
games_list.scanForNewGames(db)

# set up node list
nodes = NodeList(prefs['Directories']['nodes_dir'])
nodes.loadNodes()

# Set up event handlers
#FIXME: probably should break these out into their own module(s))

def cb_uploadcmd(message: Node_UploadCommandMessage):
	print("got it :)")

	print(message.payload[0])
	print(message.payload[1])
	nodes[message.payload[0]].load(games_list[message.payload[1]])

MBus.add_handler(Node_UploadCommandMessage, cb_uploadcmd)



# Set up adafruit ui if detected and enabled
if prefs['Main']['adafruit_ui'] == 'True':
	print('todo: adafruit ui')

# Launch web UI if enabled
if prefs['Main']['web_ui'] == 'True':
	app = UIWeb('Web UI', db, games_list, nodes, prefs)
	app._games = games_list
	app.list_loaded = True
	t = Process(target=app.start)
	t.start()

# FIXME: THE WHOLE THING IS BROKEN RIGHT NOW
# ALREADY GOT A MESSAGEBUS IN THOUGH, JUST NEED TO DEFINE AND HOOK EVERYTHING UP.
# This project has literally been in a non-working state for over a year so I mean whatever lol
