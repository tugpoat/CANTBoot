#ADAFRUIT LCD UI
import os, collections, signal, sys, subprocess, socket
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from time import sleep

from GameDescriptor import GameDescriptor
from GameList import GameList, GameList_ScanEventMessage
from mbus import *

class UI_Adafruit(Thread):
	_db = None
	_pi_rev = None
	_lcd = None

	_scandone = False

	_pressedButtons = []

	# Currently selected menu/mode. Maybe supercede this with something better
	_mode = None

	def __init__(self, prefs, games):
		super(UI_Adafruit, self).__init__()

		# We need to know the hw revision apparently.
		# piforcetools did this so I'll do it too
		self._pi_rev = self.get_hw_rev();

		if self._pi_rev.startswith('a'):
			self._lcd = Adafruit_CharLCDPlate(busnum = 1)
		else:
			self._lcd = Adafruit_CharLCDPlate()

		MBus.add_handler(GameList_ScanEventMessage, handle_GameList_ScanEventMessage)

		# Let the user know that we're doing things
		self._lcd.begin(16, 2)
		self._lcd.message("ACNTBoot Loading\n    Hold up.")

		if prefs['Main']['multinode'] == 'True':
			self._lcd.clear()
			#TODO: Maybe display Node information in the future when running as API slave?
			self._lcd.message("WARN: LCD only\nboots first node")
			return

		self._mode ="games" #set for games list by default

		self._games = games

	def handle_GameList_ScanEventMessage(self, message: GameList_ScanEventMessage):
		self.lcd.clear()
		if message.payload = "donelol":
			self._scandone = True
		else:
			self._lcd.message("Scanning...\n" + message.payload[16:])

	def get_hw_rev(self):
		cpuinfo = open("/proc/cpuinfo", "r")
		for line in cpuinfo:
			item = line.split(':', 1)
			if item[0].strip() == "Revision":
				revision = item[1].strip()
		return revision

	# Input callbacks for games menu
	def cb_menu_games_up(self):
		if lcd.DOWN not in pressedButtons:
			self._pressedButtons.append(lcd.UP)
			iterator = iter(self._games)
			needle = iterator.next()
			selection = previous
			previous = needle
			while selection != needle and selection != previous:
				previous = needle
				try:
					needle = iterator.next()
				except StopIteration:
					break
			lcd.clear()
			lcd.message(selection.title)
		elif lcd.UP in pressedButtons:
			pressedButtons.remove(lcd.UP)
		return

	def cb_menu_games_dn(self):
		if lcd.DOWN not in pressedButtons:
			pressedButtons.append(lcd.DOWN)
			previous = selection
			try:
				selection = iterator.next()
			except StopIteration:
					iterator = iter(games)

				selection = iterator.next()
			lcd.clear()
			lcd.message(selection.title)
		elif lcd.DOWN in pressedButtons:
			pressedButtons.remove(lcd.DOWN)
		return

	def cb_menu_games_left(self):
		return

	def cb_menu_games_right(self):
		return

	def cb_menu_games_select(self):
		#Yell at main thread to set game
		MBus.handle(Node_SetGameCommandMessage(payload=['0', selection.file_checksum]))
		#Yell at main to run the game on the node
		MBus.handle(Node_LaunchGameCommandMessage(payload='0'))
		return

	# THE MEAT(tm)
	def run(self):
		#TODO: display thingy while games list is loading/scanning

		#if scanning complete but no games found or if configuration is invalid, alert user
		self._lcd.clear()

		#TODO: if scan error
		self._lcd.message("E:No games found\nCopy games to SD")
		#self._lcd.message("E:Config Invalid\nSetup with WebUI")

		#main loop
		while 1:
			if self._scandone:
				# Handle button presses

				# Handle UP
				if lcd.buttonPressed(lcd.UP):
					if self._mode == "games":
						self.cb_menu_games_up()
				# Handle DOWN
				if lcd.buttonPressed(lcd.DOWN):
					if self._mode == "games":
						self.cb_menu_games_dn()

				if lcd.buttonPressed(lcd.SELECT):
					if self._mode == "games":
						self.cb_menu_games_select();

			sleep(0.1)

		return
