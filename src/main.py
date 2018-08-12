from multiprocessing import Manager, Process
from asyncio import Queue
from Database import NATCBootDatabase
from GameDescriptor import GameDescriptor
from Loader import Loader, LoadWorker


#load settings
PREFS_FILE = "settings.cfg"
prefs = configparser.ConfigParser()

#set up database
db = NATCBootDatabase('db.sqlite')

#scan games
games_list = build_games_list(db, prefs)

#set up messaging
# TODO: At this point maybe I should just use a messagebus
loaderq = Queue()
sysq	= Queue()
ui_webq = Queue()
ui_lcdq = Queue()
#set up web ui if enabled
#set up adafruit ui if detected and enabled
#enter main loop (manages messaging between the loaders and ui modules)