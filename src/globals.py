import configparser
import logging

from Database import ACNTBootDatabase

from NodeDescriptor import NodeDescriptor
from NodeList import *
from NodeManager import NodeManager

from GameDescriptor import GameDescriptor
from GameList import *

logger = logging.getLogger("main")

# load settings
PREFS_FILE = "settings.cfg"
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
nodeman = NodeManager()