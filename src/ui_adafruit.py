#ADAFRUIT LCD UI
import os, collections, signal, sys, subprocess, socket
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from threading import Thread
from time import sleep

from GameDescriptor import GameDescriptor
from GameList import GameList, GameList_ScanEventMessage
from Loader import Node_SetGameCommandMessage, Node_LaunchGameCommandMessage
from mbus import *

nodeman = None
#TODO: break each menu out into its own class and just set an instance of the parent

##TODO: My brain isn't working well enough right now to implement this. I may or may not be on the right track.`
class TwoLineLcdMenu():
	_line1 = 'C==============3'
	_line1_outbuf=''
	_line1_scroll_idx = 0
	_line2 = '8==============D'
	_line2_outbuf=''
	_line2_scroll_idx = 0

	_parent_menu = None
	_sub_menu = None

	_lcd = None
	_prev_button = None
	_pressed_buttons = []

	_list = []
	_index = 0

	_exit = False

	def __init__(self, lcd):
		self._lcd = lcd

		self._logger = logging.getLogger("TwoLineLcdMenu " + str(id(self)))
		self._logger.debug("init logger")

	def render(self):
		self._lcd.clear()
		self._lcd.message(self._line1_outbuf + "\n" + self._line2_outbuf)

	def btn_press_up(self):
		#One press at a time, please
		if self._lcd.UP in self._pressed_buttons:
			self._pressed_buttons.remove(self._lcd.UP)
			return

		self._pressed_buttons.append(self._lcd.UP)

	def btn_press_dn(self):
		#One press at a time, please
		if self._lcd.DOWN in self._pressed_buttons: 
			self._pressed_buttons.remove(self._lcd.DOWN)
			pass

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
		while self._exit == False:
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
			else:
				self._logger.error("unhandled button")

			# FIXME: TEST THIS HORIZONTAL SCROLL WRAPPING STUFF
			# I JUST BLIND-WROTE IT IN LIKE 5 MINUTES AND I HAVENT EATEN YET TODAY SO IT'S PROBABLY CRAP

			#build output buffer for line 1
			if len(self._line1) > 16:

				#get the window end index inside of our string buffer
				window_end_idx = self._line1_scroll_idx+16

				#set this up just in case
				wrap_idx = 0

				# If the window end is past the end of the string buffer, 
				# then use the end of the string buffer for our window end index
				if window_end_idx > len(self._line1)-1:
					# we've gone beyond the end of our string.
					# get the 0+n index of characters we can wrap by
					wrap_idx = window_end_idx - len(self._line1) - 2 # Leave room for a whitespace

					#the end of our window is the end of our content string.
					window_end_idx = len(self._line1) - 1

					self._logger.debug("start_idx="+self._line1_scroll_idx+",wrap_idx="+wrap_idx+",window_end_idx="+window_end_idx)

					window = self._line1[self._line1_scroll_idx:window_end_idx]

					wrap = " " + self._line1[0:wrap_idx]

					self._logger.debug("wrap="+wrap+",window="+window)

					tmpbuf = window+wrap
				else:
					# Otherwise just use the end idx we calculated above
					tmpbuf =self._line1[self._line1_scroll_idx:window_end_idx]

				self._line1_scroll_idx += 1 #we will scroll one character every interval (todo: maybe some kind of refresh counter?)

				# Reset index to 0 when we pass the end of the string
				if self._line1_scroll_idx >= len(self._line1):
					self._line1_scroll_idx = 0
			else:
				tmpbuf = self._line1

			self._logger.debug(tmpbuf)

			self._line1_outbuf = tmpbuf
			self._line2_outbuf = self._line2 # todo: wrap maybe idk

			self.render()

			sleep(0.3)

class UIAdaMainMenu(TwoLineLcdMenu):
	def __init__(self, lcd):
		super().__init__(lcd)

		self._list = ['Nodes', 'Config']

		self._logger = logging.getLogger("UIAdaConfigMenu " + str(id(self)))
		self._logger.debug("init logger")

	def btn_press_up(self):
		super().btn_press_up()
		if self._lcd.UP not in self._pressed_buttons: return

		self._index += 1
		if self._index >= self._list.len(): self._index = 0

		self._line1 = self._list[self._index]

	def btn_press_dn(self):
		super().btn_press_dn()
		if self._lcd.DOWN not in self._pressed_buttons: return

		self._index -= 1
		if self._index < 0: self._index = self._list.len() - 1

		self._line1 = self._list[self._index]

	def btn_press_sel(self):
		super().btn_press_sel()
		if self._lcd.SELECT not in self._pressed_buttons: return

		if self._list[self._index] == 'Nodes':
			submenu = UIAdaNodeListMenu(self._lcd, nodeman.nodes)
			submenu.run_menu()
		elif self._list[self._index] == 'Config':
			submenu = UIAdaConfigMenu(self._lcd)
			submenu.run_menu()

class UIAdaConfigMenu(TwoLineLcdMenu):
	def __init__(self, lcd):
		super().__init__(lcd)

		self._logger = logging.getLogger("UIAdaConfigMenu " + str(id(self)))
		self._logger.debug("init logger")

class UIAdaNodeListMenu(TwoLineLcdMenu):

	def __init__(self, lcd, nodelist):
		super().__init__(lcd)

		self._logger = logging.getLogger("UIAdaNodeMenu " + str(id(self)))
		self._logger.debug("init logger")

		self._list = nodelist

	def btn_press_up(self):
		super().btn_press_up()

		self._index += 1
		if self._index >= len(self._list): self._index = 0

		self._line1 = self._list[self._index].hostname

	def btn_press_dn(self):
		super().btn_press_dn()

		self._index -= 1
		if self._index < 0: self._index = len(self._games) - 1

		self._line1 = self._list[self._index].hostname



class GamesMenu(TwoLineLcdMenu):
	_games = None
	pass


##TODO: Throw most of this out in favor of the above model
class UI_Adafruit(Thread):
	_db = None
	_pi_rev = None
	_lcd = None

	_scandone = False

	_pressedButtons = []

	_index = 0

	def __init__(self, prefs, games):
		super(UI_Adafruit, self).__init__()

		self.__logger = logging.getLogger("UI_Adafruit " + str(id(self)))
		self.__logger.debug("init logger")
		# We need to know the hw revision apparently.
		# piforcetools did this so I'll do it too
		self._pi_rev = self.get_hw_rev();

		if self._pi_rev.startswith('a'):
			self._lcd = Adafruit_CharLCDPlate(busnum = 1)
		else:
			self._lcd = Adafruit_CharLCDPlate()

		MBus.add_handler(GameList_ScanEventMessage, self.handle_GameList_ScanEventMessage)

		# Let the user know that we're doing things
		self._lcd.begin(16, 2)
		self._lcd.message("CANTBoot Loading\n    Hold up.")

		self._games = games

	def handle_GameList_ScanEventMessage(self, message: GameList_ScanEventMessage):
		self._lcd.clear()
		if message.payload == "donelol":
			self._scandone = True

			self._lcd.message(self._games[0].title)
		else:
			self._lcd.message("Scanning...\n" + message.payload[16:])

	def get_hw_rev(self):
		cpuinfo = open("/proc/cpuinfo", "r")
		for line in cpuinfo:
			item = line.split(':', 1)
			if item[0].strip() == "Revision":
				revision = item[1].strip()
		return revision

	# THE MEAT(tm)
	def runui(self):
		#TODO: display thingy while games list is loading/scanning

		#if scanning complete but no games found or if configuration is invalid, alert user
		self._lcd.clear()

		self.__logger.debug(self._games.len())
		
		menu = UIAdaMainMenu(self._lcd)
		menu.run_menu()

		return
