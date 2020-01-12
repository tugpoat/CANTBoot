import threading
import time
import typing as t
import configparser
import copy
import logging

from GameDescriptor import GameDescriptor
from GameList import *
from NodeManager import *
from Database import ACNTBootDatabase

from mbus import *
from main_events import *
from Loader import *

from ui_web import UIWeb_Bottle

logger = logging.getLogger("main")
logger.debug("init logger")

PREFS_FILE="settings.cfg"
prefs = configparser.ConfigParser()
prefs_file = open(PREFS_FILE, 'r')
prefs.read_file(prefs_file)
prefs_file.close()

cfg_debug = bool(prefs['Main']['debug'])

#TODO: if config file/directory does not exist, copy a default from the read-only partition to the SD card.

# set up database
db = ACNTBootDatabase('db.sqlite')

# set up game list
games_list = GameList(prefs['Directories']['cfg_dir'], prefs['Directories']['games_dir'])
games_list.scanForNewGames(db)

# set up node list
nodeman = NodeManager(bool(prefs['Main']['autoboot']))
nodeman.loadNodesFromDisk(prefs['Directories']['nodes_dir'])

# Set up event handlers
#FIXME: probably should break these out into their own module(s))


def handle_Node_SetGameCommandMessage(message: Node_SetGameCommandMessage):
	logger.debug("handling SegGameCommandMessage %s %s", message.payload[0], message.payload[1])
	nodeman.setgame(message.payload[0], games_list[message.payload[1]])

def handle_Node_LaunchGameCommandMessage(message: Node_LaunchGameCommandMessage):
	logger.info("running configured game on %s", message.payload)
	nodeman.launchgame(message.payload)

def handle_SaveConfigToDisk(message: SaveConfigToDisk):
	logger.info("Saving configuration to disk...")
	if not cfg_debug: remount_rw(prefs['Directories']['cfg_part'])
	nodeman.saveNodesToDisk(prefs['Directories']['nodes_dir'])
	games_list.exportList()
	if not cfg_debug: remount_ro(prefs['Directories']['cfg_part'])
	logger.info("Done saving configuration to disk")

#TODO: Raise this when we boot a new game
#def handle_SaveNodesToDisk(message: SaveNodesToDisk):
#	if not cfg_debug: remount_rw(prefs['Directories']['cfg_part'])
#	nodeman.saveNodesToDisk(prefs['Directories']['nodes_dir'])
#	if not cfg_debug: remount_ro(prefs['Directories']['cfg_part'])

MBus.add_handler(Node_SetGameCommandMessage, handle_Node_SetGameCommandMessage)
MBus.add_handler(Node_LaunchGameCommandMessage, handle_Node_LaunchGameCommandMessage)
MBus.add_handler(SaveConfigToDisk, handle_SaveConfigToDisk)


# Set up adafruit ui if detected and enabled
if prefs['Main']['adafruit_ui'] == 'True':
	logger.error('todo: adafruit ui')

# Launch web UI if enabled
if prefs['Main']['web_ui'] == 'True':
	wapp = UIWeb_Bottle('Web UI', games_list, nodeman, prefs)
	t = threading.Thread(target=wapp.start).start()

while 1:
	nodeman.tickLoaders()
	time.sleep(0.01)

# FIXME: THE WHOLE THING IS BROKEN RIGHT NOW
# ALREADY GOT A MESSAGEBUS IN THOUGH, JUST NEED TO DEFINE AND HOOK EVERYTHING UP.
# This project has literally been in a non-working state for over a year so I mean whatever lol
