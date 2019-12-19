from multiprocessing import Manager, Process
from asyncio import *
import time
import typing as t
import configparser
import copy

from Database import ACNTBootDatabase
from NodeDescriptor import NodeDescriptor
from NodeList import *
from GameDescriptor import GameDescriptor
from GameList import *

from mbus import *
from main_events import *
from Loader import Node_LoaderStatusMessage, Node_LoaderUploadPctMessage, Node_UploadCommandMessage

from ui_web import UIWeb

# load settings
PREFS_FILE = "settings.cfg"
prefs = configparser.ConfigParser()
prefs_file = open(PREFS_FILE, 'r')
prefs.read_file(prefs_file)
prefs_file.close()

debug = bool(prefs['Main']['debug'])

#TODO: if config file/directory does not exist, copy a default from the read-only partition to the SD card.

# set up database
db = ACNTBootDatabase('db.sqlite')

# set up game list
games_list = GameList(prefs['Directories']['cfg_dir'], prefs['Directories']['games_dir'])
games_list.scanForNewGames(db)

# set up node list
nodes = NodeList(prefs['Directories']['nodes_dir'])
nodes.loadNodes()
if prefs['Main']['multinode'] == 'False':
	n = copy.deepcopy(nodes[0])
	nodes.clear()
	nodes.append(n)

# Set up event handlers
#FIXME: probably should break these out into their own module(s))

def handle_Node_UploadCommandMessage(message: Node_UploadCommandMessage):
	print(message.payload[0])
	print(message.payload[1])
	nodes[message.payload[0]].load(games_list[message.payload[1]])

def handle_SaveConfigToDisk(message: SaveConfigToDisk):
	if not debug: remount_rw(prefs['Directories']['cfg_part'])
	nodes.exportNodes()
	games_list.exportList()
	if not debug: remount_ro(prefs['Directories']['cfg_part'])

MBus.add_handler(Node_UploadCommandMessage, handle_Node_UploadCommandMessage)
MBus.add_handler(SaveConfigToDisk, handle_SaveConfigToDisk)


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
