#ADAFRUIT LCD UI
import os, collections, signal, sys, subprocess, socket
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from threading import Thread
from time import sleep

from GameDescriptor import GameDescriptor
from GameList import GameList, GameList_ScanEventMessage
from Loader import Node_SetGameCommandMessage, Node_LaunchGameCommandMessage
from mbus import *

#TODO: break each menu out into its own class and just set an instance of the parent

##TODO: My brain isn't working well enough right now to implement this. I may or may not be on the right track.`
class TwoLineLcdMenu():
	_line1 = 'C==============3'
	_line2 = '8==============D'
	_parent_menu = None
	_sub_menu = None

	_lcd = None

	_list = None
	_index = 0

	def __init__(self, lcd, parent = None):
		self._lcd = lcd

		if parent != None:
			self._parent_menu = parent

	def render():
		self._lcd.clear()
		self._lcd.message(self._line1 + "\n" + self._line2)

	def btn_press_up():
		pass

	def btn_press_dn():
		pass

	def btn_press_left():
		pass

	def btn_press_right():
		pass

	def btn_press_sel():
		pass

	def run_menu():
		# Should include a while loop here to run the menu in each inherited definition, as these menus are all executed synchronously 
		# So we can have a bunch of nested loops and not give a fuck
		# Also because we're guaranteed to be working with more than enough memory/cpu resources on any platform we will be running this code on
		# Since python treats all objects as references, we can just pass all the LCD and MessageBus objects around and it's fine
		# Therefore, code readability > efficiency for this module.
		pass

class NodeMenu(TwoLineLcdMenu):
	pass 

class GamesMenu(TwoLineLcdMenu):
	pass


##TODO: Throw most of this out in favor of the above model
class UI_Adafruit(Thread):
	_db = None
	_pi_rev = None
	_lcd = None

	_scandone = False

	_pressedButtons = []

	_index = 0

	# Currently selected menu/mode. Maybe supercede this with something better
	_mode = None

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
		self._lcd.message("ACNTBoot Loading\n    Hold up.")

		self._mode ="games" #set for games list by default

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

	def cb_menu_nodes_up(self):
		#select prev node
		return

	def cb_menu_nodes_dn(self):
		#select next node
		return

	def cb_menu_nodes_left(self):
		#idk, rescan or something?
		return

	def cb_menu_nodes_right(self):
		#node options... universal patches maybe?
		return

	def cb_menu_nodes_sel(self):
		#goto games menu for node
		return

	# Input callbacks for games menu
	def cb_menu_games_up(self):
		if self._lcd.UP not in self._pressedButtons:
			self.__logger.debug(self._games.len())
			self._pressedButtons.append(self._lcd.UP)

			self._index += 1
			if self._index >= self._games.len(): self._index = 0

			self._lcd.clear()
			self._lcd.message(self._games[self._index].title)
		elif self._lcd.UP in self._pressedButtons:
			self._pressedButtons.remove(self._lcd.UP)
		return

	def cb_menu_games_dn(self):
		if self._lcd.DOWN not in self._pressedButtons:
			self._pressedButtons.append(self._lcd.DOWN)

			self._index -= 1
			if self._index < 0: self._index = self._games.len() - 1

			self._lcd.clear()
			self._lcd.message(self._games[self._index].title)
		elif self._lcd.DOWN in self._pressedButtons:
			self._pressedButtons.remove(self._lcd.DOWN)
		return

	def cb_menu_games_left(self):
		#back?
		return

	def cb_menu_games_right(self):
		#goto game options menu (patch select?)
		return

	def cb_menu_games_sel(self):

		#Yell at main thread to set game
		MBus.handle(Node_SetGameCommandMessage(payload=['0', self._games[self._index].file_checksum]))
		#Yell at main to run the game on the node
		MBus.handle(Node_LaunchGameCommandMessage(payload='0'))
		return

	# THE MEAT(tm)
	def runui(self):
		#TODO: display thingy while games list is loading/scanning

		#if scanning complete but no games found or if configuration is invalid, alert user
		self._lcd.clear()

		self.__logger.debug(self._games.len())
			#main loop
		while 1:
			if self._scandone:
				# Handle button presses

				# Handle UP
				if self._lcd.buttonPressed(self._lcd.UP):
					if self._mode == "games":
						self.cb_menu_games_up()
					elif self._mode == "nodes":
						pass
						
				# Handle DOWN
				if self._lcd.buttonPressed(self._lcd.DOWN):
					if self._mode == "games":
						self.cb_menu_games_dn()
	
				if self._lcd.buttonPressed(self._lcd.SELECT):
					if self._mode == "games":
						self.cb_menu_games_sel();

				sleep(0.1)

		return
