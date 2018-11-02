#ADAFRUIT LCD UI
import os, collections, signal, sys, subprocess, socket
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from time import sleep

class UI_Adafruit(Process):
	_db = None
	_pi_rev = None
	_lcd = None
	_games = None

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

        # Let the user know that we're doing things
        self._lcd.begin(16, 2)
        self._lcd.message("CANTBoot Loading\n    Hold up.")

        self._mode ="games" #set for games list by default

        self._games = games

    def get_hw_rev(self):
    	cpuinfo = open("/proc/cpuinfo", "r")
		for line in cpuinfo:
		    item = line.split(':', 1)
		    if item[0].strip() == "Revision":
		        revision = item[1].strip()
		return revision

	# Input callbacks for games menu
	def cb_menu_games_up(self):
		return

	def cb_menu_games_dn(self):
		return

	def cb_menu_games_left(self):
		return

	def cb_menu_games_right(self):
		return

	def cb_menu_games_select(self):
		return

	# THE MEAT(tm)
    def run(self):
    	#TODO: display thingy while games list is loading/scanning

    	#if scanning complete but no games found or if configuration is invalid, alert user
    	self._lcd.clear()

    	self._lcd.message("E:No games found\nCopy games to SD")
    	self._lcd.message("E:Config Invalid\nSetup with WebUI")

    	#main loop
    	while 1:
    		#yolo

    	return