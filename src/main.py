import threading
import time
import typing as t
import configparser
import copy
import logging
import os
import argparse
import signal
import sys

from GameDescriptor import GameDescriptor
from GameList import *
from NodeManager import *
from Database import ACNTBootDatabase

from mbus import *
from main_events import *
from sysctl import *
from Loader import *

from ui_web import UIWeb_Bottle

on_raspi=False
if "arm" in os.uname().machine:
	on_raspi=True

'''
######################################################################################################
## Basic Configuration and setup
######################################################################################################
'''
# create parser
parser = argparse.ArgumentParser()
 
# add arguments to the parser
parser.add_argument("--cfgdir", default='/mnt/cfg')
parser.add_argument("--romsdir", default='/mnt/roms')

# parse the arguments
args = parser.parse_args()

logger = logging.getLogger("main")
logger.debug("init logger")
logger.info("cfg_dir=" + args.cfgdir)
logger.info("roms_dir=" + args.romsdir)

if not os.path.isfile(args.cfgdir+'/settings.cfg'):
	logger.fatal('no config found. todo: copy default config or create config in ' + args.cfgdir)

PREFS_FILE=args.cfgdir+"/settings.cfg"
prefs = configparser.ConfigParser()
prefs_file = open(PREFS_FILE, 'r')
prefs.read_file(prefs_file)
prefs_file.close()

prefs['Directories']['cfg_dir'] = args.cfgdir
prefs['Directories']['roms_dir'] = args.romsdir

prefs['System']['ftpd_enable'] = 'False'

cfg_debug = bool(prefs['Main']['debug'])
cfg_use_parts = bool(prefs['Main']['use_parts'])

#We're not on a raspi and likely also not using our image. Don't try to mount and unmount the partitions that don't exist.
if not on_raspi and cfg_use_parts:
	cfg_use_parts = False
	prefs['Main']['use_parts'] = 'False'

cfg_api_mode = str(prefs['Main']['api_mode'])

db = None

'''
######################################################################################################
## Event Handlers
######################################################################################################
'''

def handle_Node_SetGameCommandMessage(message: Node_SetGameCommandMessage):
	logger.debug("handling SetGameCommandMessage %s %s", message.payload[0], message.payload[1])
	if message.payload[0] == '0' and message.payload[1] == '0':
		#api ui magic
		nodeid = nodeman.nodes[0].node_id
		nodeman.setgame(nodeid, GameDescriptor('/tmp/game.bin'))
		#we can probably do this in a more complicated way that reduces network transmission overhead but meh.
	elif message.payload[0] == '0':
		#adafruit ui magic for launching on the first node in the list
		nodeid = nodeman.nodes[0].node_id
		nodeman.setgame(nodeid, games_list[message.payload[1]])
	else:
		nodeman.setgame(message.payload[0], games_list[message.payload[1]])

def handle_Node_LaunchGameCommandMessage(message: Node_LaunchGameCommandMessage):
	logger.info("running configured game on %s", message.payload)
	if message.payload == '0':
		#magic for adafruit ui
		nodeid = nodeman.nodes[0].node_id
		nodeman.launchgame(nodeid)
	else:
		nodeman.launchgame(message.payload)

def handle_FTPDEnableMessage(message: FTPDEnableMessage):
	if len(message.payload) < 3:
		disable_ftpd()
	else:
		enable_ftpd(message.payload)

def handle_SaveConfigToDisk(message: SaveConfigToDisk):
	saveconftodisk()

#Remember to save config to disk before calling this!
def handle_ApplySysConfig(message: ApplySysConfig):
	saveconftodisk()
	applysysconfig()

def saveconftodisk():
	logger.info("Saving configuration to disk...")
	if cfg_use_parts: remount_rw(prefs['Partitions']['cfg_part'])
	logger.debug(prefs['Partitions']['cfg_part'])

	logger.debug("Saving nodes...")
	nodeman.saveNodesToDisk(prefs['Directories']['cfg_dir'] + '/nodes')

	logger.debug("Saving rom list...")
	games_list.exportList()

	logger.debug("Saving config...")
	with open(prefs['Directories']['cfg_dir'] + '/settings.cfg', 'w') as prefs_file:
		prefs.write(prefs_file)

	if cfg_use_parts: remount_ro(prefs['Partitions']['cfg_part'])
	logger.info("Done saving configuration to disk")

def applysysconfig():
	logger.info("Applying System configuration...")

	logger.debug("Writing interface config")
	write_ifconfig(prefs)

	logger.debug("writing wlan config")
	write_iwconfig(prefs)

	if (prefs.get('Network', 'wlan0_ip') == 'dhcp' or prefs.get('Network', 'wlan0_netmask') == 'dhcp') and prefs.get('Network', 'wlan0_mode') == 'client':
		#wifi client
		logger.debug("wifi client. disabling dnsmasq and hostapd.")
		disable_dnsmasq()
		disable_hostapd()
	else:
		#wifi ap
		logger.debug("wifi ap. enabling dnsmasq and hostapd.")
		enable_dnsmasq()
		enable_hostapd()
		
	logger.info("Done. rebooting system.")
	reboot_system()
	
'''
######################################################################################################
## MAIN SHITZ
######################################################################################################
'''

#we need cfg rw while we load up
if cfg_use_parts: remount_rw(prefs['Partitions']['cfg_part'])

# set up node list
nodeman = NodeManager(bool(prefs['Main']['autoboot']))
nodeman.loadNodesFromDisk(prefs['Directories']['cfg_dir'] + '/nodes')

ui_threads = []

if cfg_api_mode != 'slave':

	# set up database
	db = ACNTBootDatabase('db.sqlite')

	# set up game list
	games_list = GameList(prefs['Directories']['cfg_dir'], prefs['Directories']['roms_dir'])

	# Set up adafruit ui if detected and enabled
	if prefs['Main']['adafruit_ui'] == 'True' and on_raspi == True:
		from ui_adafruit import UI_Adafruit
		try:
			adafapp = UI_Adafruit(prefs, nodeman, games_list)
			t = threading.Thread(target=adafapp.runui).start()
			ui_threads.append(t)
		except Exception as ex:
			logger.error("Error spawning Adafruit UI: " + repr(ex))

	#TODO: Launch other UIs here

	# Launch web UI if enabled
	if prefs['Main']['web_ui'] == 'True':
		wapp = UIWeb_Bottle('Web UI', games_list, nodeman, prefs)
		t = threading.Thread(target=wapp.start).start()
		ui_threads.append(t)

	#FIXME: Having this after UI loading without notifying the user what's going on is bad.
	games_list.scanForNewGames(db)

else:
	#All we need if we're running as an API Slave node is the NodeManager and the API Receiver
	from ui_api import UIAPI
	wapp = UIAPI()
	t = threading.Thread(target=wapp.start).start()
	ui_threads.append(t)

#ok done loading. remount ro to reduce likelihood of data loss
if cfg_use_parts: remount_ro(prefs['Partitions']['cfg_part'])

# Set up event handlers
MBus.add_handler(Node_SetGameCommandMessage, handle_Node_SetGameCommandMessage)
MBus.add_handler(Node_LaunchGameCommandMessage, handle_Node_LaunchGameCommandMessage)
MBus.add_handler(SaveConfigToDisk, handle_SaveConfigToDisk)

# Let's not even bother trying to touch the system if we're not running on a raspi.
if on_raspi:
	MBus.add_handler(FTPDEnableMessage, handle_FTPDEnableMessage)
	MBus.add_handler(ApplySysConfig, handle_ApplySysConfig)


#TODO: Handle signals properly instead of what I'm doing now

def signal_int_handler(signal, frame):
	logger.info('got SIGINT')
	saveconftodisk()

def signal_kill_handler(signal, frame):
	logger.info('got SIGKILL')
	MBus.handle(FOAD())

	for t in ui_threads:
		t.join()

	sys.exit(0)

def signal_term_handler(signal, frame):
	logger.info('got SIGTERM')
	saveconftodisk()
	MBus.handle(FOAD())

	for t in ui_threads:
		t.join()

	sys.exit(0)

signal.signal(signal.SIGINT, signal_int_handler)
signal.signal(signal.SIGKILL, signal_int_handler)
signal.signal(signal.SIGTERM, signal_term_handler)

while 1:
	nodeman.tickLoaders()
	time.sleep(0.01)