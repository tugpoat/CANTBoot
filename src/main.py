from multiprocessing import Manager, Process
from asyncio import *
import time
import typing as t
import configparser
import copy
import logging

from globals import *

from GameDescriptor import GameDescriptor
from GameList import *

from mbus import *
from main_events import *
from Loader import Node_LoaderStatusMessage, Node_LoaderUploadPctMessage, Node_UploadCommandMessage

from ui_web import UIWeb

nodeman.loadNodesFromDisk(prefs['Directories']['nodes_dir'])

# Set up event handlers
#FIXME: probably should break these out into their own module(s))


def handle_Node_UploadCommandMessage(message: Node_UploadCommandMessage):
	logger.debug("handling uploadcommandmessage %s %s", message.payload[0], message.payload[1])
	nodeman.nodes[message.payload[0]].load(games_list[message.payload[1]])

def handle_SaveConfigToDisk(message: SaveConfigToDisk):
	if not cfg_debug: remount_rw(prefs['Directories']['cfg_part'])
	nodeman.saveNodesToDisk(prefs['Directories']['nodes_dir'])
	games_list.exportList()
	if not cfg_debug: remount_ro(prefs['Directories']['cfg_part'])

MBus.add_handler(Node_UploadCommandMessage, handle_Node_UploadCommandMessage)
MBus.add_handler(SaveConfigToDisk, handle_SaveConfigToDisk)


# Set up adafruit ui if detected and enabled
if prefs['Main']['adafruit_ui'] == 'True':
	print('todo: adafruit ui')

# Launch web UI if enabled
if prefs['Main']['web_ui'] == 'True':
	app = UIWeb('Web UI', db, games_list, nodeman.nodes, prefs)
	app._games = games_list
	app.list_loaded = True
	t = Process(target=app.start)
	t.start()

# FIXME: THE WHOLE THING IS BROKEN RIGHT NOW
# ALREADY GOT A MESSAGEBUS IN THOUGH, JUST NEED TO DEFINE AND HOOK EVERYTHING UP.
# This project has literally been in a non-working state for over a year so I mean whatever lol
