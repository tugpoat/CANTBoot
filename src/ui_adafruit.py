#ADAFRUIT LCD UI
import os, collections, signal, sys, subprocess, socket
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from threading import Thread
from enum import Enum, auto
from time import sleep

from GameDescriptor import GameDescriptor
from GameList import GameList, GameList_ScanEventMessage
from Loader import Node_SetGameCommandMessage, Node_LaunchGameCommandMessage, Node_LoaderStateMessage, Node_LoaderUploadPctMessage, LoaderState, LoaderStateMsgObj
from mbus import *
from main_events import *

'''
Base 16x2 LCD Menu class. Shouldn't be used on its own
'''
class TwoLineLcdMenu():
	_line1 = 'C==============3'
	_line1_outbuf=''
	_line1_rbuf=''
	_line1_scroll_idx = 0
	_line1_scroll_delay = 0

	_line2 = '8==============D'
	_line2_outbuf=''
	_line2_rbuf=''
	_line2_scroll_idx = 0

	_nextmenu = None

	_lcd = None
	_pressed_buttons = []

	_list = None
	_index = 0

	_exitmenu = False

	@property
	def mlist(self) -> list:
		return self._list

	@mlist.setter
	def mlist(self, value : list):
		self._list = value

	@property
	def mindex(self) -> int:
		return self._index

	@mindex.setter
	def mindex(self, value : int):
		self._index = value

	@property
	def line1(self) -> str:
		return self._line1

	@line1.setter
	def line1(self, value : str):
		self._line1 = str(value)
		self._line1_scroll_idx = 0
		self._line1_outbuf = ''
		self._line1_scroll_delay = 0

	@property
	def line2(self) -> str:
		return self._line2

	@line2.setter
	def line2(self, value : str):
		self._line2 = str(value)
		self._line2_scroll_idx = 0
		self._line2_outbuf = ''

	@property
	def exitmenu(self) -> bool:
		return self._exitmenu

	@exitmenu.setter
	def exitmenu(self, value : bool):
		self._exitmenu = value

	@property
	def nextmenu(self):
		return self._nextmenu

	def __init__(self, lcd):
		self._lcd = lcd

		self._logger = logging.getLogger("TwoLineLcdMenu " + str(id(self)))
		self._logger.debug("init logger")

	def render(self):
		#TODO: only render changed characters instead of the whole thing when a line changes
		self._lcd.setCursor(0,0)
		if self._line1_outbuf.ljust(16) != self._line1_rbuf:
			self._line1_rbuf = self._line1_outbuf.ljust(16)

		if self._line2_outbuf.ljust(16) != self._line2_rbuf:
			self._line2_rbuf = self._line2_outbuf.ljust(16)

		self._lcd.message(self._line1_rbuf + "\n" + self._line2_rbuf)

	def btn_press_up(self):
		#One press at a time, please
		if self._lcd.UP in self._pressed_buttons:
			self._pressed_buttons.remove(self._lcd.UP)
		else:
			self._pressed_buttons.append(self._lcd.UP)

	def btn_press_dn(self):
		#One press at a time, please
		if self._lcd.DOWN in self._pressed_buttons: 
			self._pressed_buttons.remove(self._lcd.DOWN)
		else:
			self._pressed_buttons.append(self._lcd.DOWN)

	def btn_press_left(self):
		pass

	def btn_press_right(self):
		pass

	def btn_press_sel(self):
		pass

	def run_menu(self):
		# Should include a while loop here to run the menu in each inherited definition, as these menus are all executed synchronously 
		# So we can have a bunch of nested loops and not give a fuck
		# Also because we're guaranteed to be working with more than enough memory/cpu resources on any platform we will be running this code on
		# Since python treats all objects as references, we can just pass all the LCD and MessageBus objects around and it's fine
		# Therefore, code readability > efficiency for this module.
		while self.exitmenu == False:

			# POLL BUTTONS!
			if self._lcd.buttonPressed(self._lcd.UP):
				self.btn_press_up()
			elif self._lcd.buttonPressed(self._lcd.DOWN):
				self.btn_press_dn()
			elif self._lcd.buttonPressed(self._lcd.LEFT):
				self.btn_press_left()
			elif self._lcd.buttonPressed(self._lcd.RIGHT):
				self.btn_press_right()
			elif self._lcd.buttonPressed(self._lcd.SELECT):
				self.btn_press_sel()


			# Just set this up to a default and because I never know how tf python is scoped
			window_end_idx = 16

			if len(self._line1) > 16 and self._line1_scroll_delay < 5:
				# We don't want to scroll it right away, let's pause for a bit
				self._line1_scroll_delay += 1
			elif len(self._line1) > 16 and self._line1_scroll_delay > 4:
				# OK We have waited a bit and we're going to scroll the line.

				# Get the window end index inside of our string buffer
				window_end_idx = self._line1_scroll_idx+16

				#set this up just in case
				#wrap_idx = 0

				# If the window end is past the end of the string buffer, 
				# then use the end of the string buffer for our window end index

				# aka have we reached the end of our content?
				if window_end_idx > len(self._line1):
					# we've gone beyond the end of our string.
					# get the 0+n index of characters we can wrap by
					#wrap_idx = window_end_idx - len(self._line1) - 2 # Leave room for a whitespace

					#the end of our window is the end of our content string.
					window_end_idx = len(self._line1)

					window = self._line1[self._line1_scroll_idx:window_end_idx]

					'''
					#wrap line
					self._logger.debug("start_idx="+str(self._line1_scroll_idx)+",wrap_idx="+str(wrap_idx)+",window_end_idx="+str(window_end_idx))
					wrap = " " + self._line1[0:wrap_idx]

					self._logger.debug("wrap="+wrap+",window="+window)

					tmpbuf = window+wrap
					'''

					# Reset scroll index and delay counter if we have waited after scrolling
					if self._line1_scroll_delay > 8:
						self._line1_scroll_idx = 0
						self._line1_scroll_delay = 0
					else:
						# wait some more if not
						self._line1_scroll_delay += 1
				else:
					self._line1_scroll_idx += 1 #we will scroll one character every interval until we reach the end of the string.

			#use the end idx we calculated above
			tmpbuf = self._line1[self._line1_scroll_idx:window_end_idx]

			#self._logger.debug(tmpbuf)

			self._line1_outbuf = tmpbuf.ljust(16)
			self._line2_outbuf = self._line2.ljust(16)

			self.render()

			# If I really cared I'd have separate polling intervals for input and output but whatever idgaf this is fine
			sleep(0.2)

		return [self.nextmenu, self.mindex]

'''
Enum for the menus that we plan to use in this application
'''
class UIAdaMenus(Enum):
	main = auto()
	nodes = auto()
	games = auto()
	config = auto()

'''
Main Menu
'''
class UIAdaMainMenu(TwoLineLcdMenu):

	def __init__(self, lcd):
		super().__init__(lcd)

		self.mlist = ['Nodes', 'Config']

		self._logger = logging.getLogger("UIAdaMainMenu " + str(id(self)))
		self._logger.debug("init logger")

		MBus.add_handler(FOAD, self.die)

	def die(self, data):
		self.exitmenu = True

	def btn_press_up(self):
		super().btn_press_up()
		if self._lcd.UP in TwoLineLcdMenu._pressed_buttons: return

		self.mindex += 1
		if self.mindex >= len(self.mlist): self.mindex = 0

		self.line1 = self.mlist[self.mindex]

	def btn_press_dn(self):
		super().btn_press_dn()
		if self._lcd.DOWN in TwoLineLcdMenu._pressed_buttons: return

		self.mindex -= 1
		self._logger.debug(self.mlist[0])
		if self.mindex < 0: self.mindex = len(self.mlist) - 1

		self.line1 = self.mlist[self.mindex]

	def btn_press_sel(self):
		super().btn_press_sel()
		if self._lcd.SELECT in TwoLineLcdMenu._pressed_buttons: return

		if self.mlist[self.mindex] == 'Nodes':
			self.nextmenu = UIAdaMenus.nodes
			self.exitmenu = True
		elif self.mlist[self.mindex] == 'Config':
			self.nextmenu = UIAdaMenus.config
			self.exitmenu = True


'''
Config Menu
'''
class UIAdaConfigMenu(TwoLineLcdMenu):
	def __init__(self, lcd):
		super().__init__(lcd)

		self._logger = logging.getLogger("UIAdaConfigMenu " + str(id(self)))
		self._logger.debug("init logger")

		self.mlist = ['Filter games by monitor', '']

		self.line1 = "N/A"
		self.line2 = "L:Exit U/D:toggle"

		MBus.add_handler(FOAD, self.die)

	def die(self, data):
		self.exitmenu = True

	def btn_press_left(self):
		self.nextmenu = UIAdaMenus.main
		self.exitmenu = True


'''
Node Selection menu
'''
class UIAdaNodesMenu(TwoLineLcdMenu):
	def __init__(self, lcd, nodelist):
		super().__init__(lcd)

		self._logger = logging.getLogger("UIAdaNodeMenu " + str(id(self)))
		self._logger.debug("init logger")

		self.mlist = nodelist
		if len(self.mlist) < 1: 
			self.line2 = "No nodes! :("
		else:
			self.line1 = self.mlist[0].nickname
			self.line2 = self.mlist[0].hostname

		MBus.add_handler(FOAD, self.die)

	def die(self, data):
		self.exitmenu = True

	def btn_press_up(self):
		super().btn_press_up()

		self.mindex += 1
		if self.mindex >= len(self.mlist): self.mindex = 0

		self.line1 = self.mlist[self.mindex].nickname
		self.line2 = self.mlist[self.mindex].hostname


	def btn_press_dn(self):
		super().btn_press_dn()

		self.mindex -= 1
		if self.mindex < 0: self.mindex = len(self.mlist) - 1

		self.line1 = self.mlist[self.mindex].nickname
		self.line2 = self.mlist[self.mindex].hostname

	def btn_press_right(self):
		super.btn_press_right()
		self.line1 = "TODO: PING"
		self.line2 = "Sorry :("

		#TODO: ping node

	def btn_press_sel(self):
		super().btn_press_sel()
		if self._lcd.SELECT in TwoLineLcdMenu._pressed_buttons: return

		self.nextmenu = UIAdaMenus.games
		self.exitmenu = True


'''
Game selection menu. Normally instantiated after a node is selected.
'''
class UIAdaGamesMenu(TwoLineLcdMenu):
	_node_id = '0'
	_is_booting = False
	_nodestate = None

	def __init__(self, lcd, gameslist, sel_node : str):
		super().__init__(lcd)

		self._logger = logging.getLogger("UIAdaNodeMenu " + str(id(self)))
		self._logger.debug("init logger")

		MBus.add_handler(Node_LoaderStateMessage, self.handle_LoaderStateMessage)
		MBus.add_handler(Node_LoaderUploadPctMessage, self.handle_LoaderUploadPctMessage)

		MBus.add_handler(FOAD, self.die)

		#defined in parent
		self.mlist = gameslist

		#non-inherited
		self.node_id = sel_node
		
		if len(self.mlist) < 1: 
			self.line2 = "No games! :("
		else:
			self.line1 = self.mlist[self.mindex].title
			self.line2 = str(round(self.mlist[self.mindex].file_size / 1048576, 2)) + "MiB"

	def handle_LoaderStateMessage(self, message: Node_LoaderStateMessage):
		# Only process if it's related to the node we are working with right now

		# Turn that long enum into something that will fit on a 16x2 character LCD
		if message.payload[0] == self._node_id:
			if  message.payload[1] == LoaderState.WAITING:
				self._nodestate = 'waiting'
			else if message.payload[1] == LoaderState.TRANSFERRING:
				self._nodestate = 'xfering'
			else if message.payload[1] == LoaderState.BOOTING:
				self._nodestate = 'booting'
			else if message.payload[1] == LoaderState.KEEPALIVE:
				self._nodestate = 'done'
				self.line2 = '                '

	def handle_LoaderUploadPctMessage(self, message: Node_LoaderUploadPctMessage):
		# We should only be outputting upload stats for the node we are working with, 
		# and only if that node is actually uploading.
		if self._nodestate == LoaderState.TRANSFERRING and message.payload[0] == self._node_id:
			tmp = "%s%" % (str(round(float(message.payload[1]))))
			tmp = tmp.rjust(16)
			tmp[7:] = self._nodestate
			self.line2 = tmp

	def die(self, data):
		self.exitmenu = True

	def btn_press_up(self):
		super().btn_press_up()

		self.mindex -= 1
		if self.mindex < 0: self.mindex = len(self.mlist) - 1

		self.line1 = self.mlist[self.mindex].title
		self.line2 = str(round(self.mlist[self.mindex].file_size / 1048576, 2)) + "MiB"

	def btn_press_dn(self):
		super().btn_press_dn()
		self.mindex += 1
		if self.mindex >= len(self.mlist): self.mindex = 0

		self.line1 = self.mlist[self.mindex].title
		self.line2 = str(round(self.mlist[self.mindex].file_size / 1048576, 2)) + "MiB"

	def btn_press_sel(self):
		super().btn_press_sel()
		# TODO: This is a simple test. Flesh everything out.
		#Yell at main thread to set game
		MBus.handle(Node_SetGameCommandMessage(payload=[node_id, self.mlist[self.mindex].file_checksum]))
		#Yell at main to run the game on the node
		MBus.handle(Node_LaunchGameCommandMessage(payload=node_id))
		self.line1 = "Booting..."
		self._is_booting = True

'''
######################################################################################################
## The Main UI Object/Thread/Whatever that runs the menus for this application
######################################################################################################
'''
class UI_Adafruit(Thread):
	_db = None
	_pi_rev = None
	_lcd = None

	menu = None
	prevmenu = None
	nextmenu = None

	_scandone = False

	_pressedButtons = []

	_index = 0


	# Simple lookup dict for menu class names
	_menus = {
		UIAdaMenus.main : UIAdaMainMenu,
		UIAdaMenus.nodes : UIAdaNodesMenu,
		UIAdaMenus.games : UIAdaGamesMenu,
		UIAdaMenus.config : UIAdaConfigMenu
	}

	def __init__(self, prefs, nodeman, games):
		super(UI_Adafruit, self).__init__()

		self.__logger = logging.getLogger("UI_Adafruit " + str(id(self)))
		self.__logger.debug("init logger")

		self._lcd = Adafruit_CharLCDPlate()

		MBus.add_handler(GameList_ScanEventMessage, self.handle_GameList_ScanEventMessage)
		MBus.add_handler(FOAD, self.die)

		# Let the user know that we're doing things
		self._lcd.begin(16, 2)
		self._lcd.message("CANTBoot Loading\n    Hold up.")

		self._games = games

		self._nodes = nodeman.nodes

	def die(self, data):
		self.line1="Goodbye George<3"
		self.line2=""
		sleep(2)
		self.line1 = ""
		try:
			menu.exitmenu = True
			sleep(0.5)
		except:
			pass

	def handle_GameList_ScanEventMessage(self, message: GameList_ScanEventMessage):
		self._lcd.clear()
		if message.payload == "donelol":
			self._scandone = True
			self._lcd.message("Init Success")
		else:
			self.line1= message.payload
			self.line2 ='Scanning...'

	# THE MEAT(tm)
	def runui(self):

		sel_idx = 0
		nextmenu = None

		while 1:
			# Don't do anything until we've booted up successfully
			if self._scandone:
				menu = UIAdaNodesMenu(self._lcd, self._nodes)

					if nextmenu:
						prevmenu = nextmenu
						if nextmenu == UIAdaMenus.main:
							menu = UIAdaMainMenu(self._lcd)
						elif nextmenu == UIAdaMenus.nodes:
							menu = UIAdaNodesMenu(self._lcd, self._nodes)
						elif nextmenu == UIAdaMenus.games:
							menu = UIAdaGamesMenu(self._lcd, self._games, self._nodes[sel_idx].node_id)
							#menu = UIAdaGamesMenu(self._lcd, self._games, '0')

					menuret = menu.run_menu()
					nextmenu = menuret[0]
					sel_idx = menuret[1]

					#process return values here and determine if we need to do anything special, e.g. load a game
			else:
				# We're not done booting, hang on a second (literally).
				sleep(1)

		'''
		self.__logger.debug(self._games.len())
		prevmenu = UIAdaMenus.main
		menu = UIAdaMainMenu(self._lcd)
		while 1:
			menuret = menu.run_menu()
			menu = self._menus[menuret[0]]
			selected = menuret[1]
		'''