import os
import configparser
import signal
import string
import json
import copy
from ast import literal_eval as make_tuple

from bottle import Bottle, template, static_file, error, request, response, view
import beaker.middleware

from mbus import *
from main_events import SaveConfigToDisk
from Loader import *


session_opts = {
	'session.type': 'file',
	'session.cookie_expires': 300,
	'session.data_dir': './data',
	'session.auto': True
}

class UIAPI(Bottle):
	_prefs = None
	_bottle = None
	_beaker = None

	def __init__(self):
		super(UIWeb_Bottle, self).__init__()
		self._beaker = beaker.middleware.SessionMiddleware(self, session_opts)

		# TODO: probably some sort of authentication should be implemented so someone can't hop onto the network and mess with everything
		#set up routes
		self.route('/api/gpio_reset', method="GET", callback=self.do_gpio_reset)

		self.route('/api/sys/reboot')

		self.route('/api/rom/get')
		self.route('/api/rom/set', method="POST")
		self.route('/api/rom/upload', method="POST")
		self.route('/api/rom/addpatch', method="POST")
		self.route('/api/rom/clear')
		self.route('/api/bootgame')

		self.route('/api/cfg', method="GET", method=self.getcfg)
		self.route('/api/cfg', method="POST", method=self.setcfg)

	def start(self):
		self.run(host='0.0.0.0', port=8008, debug=False, quiet=True)

	def do_gpio_reset(self):
		pass

	def getcfg(self):
		pass

	def setcfg(self):
		pass

	def getrominfo(self):
		pass

	def setrominfo(self):
		pass

	def handle_upload(self):
		if 'file' in request.files:
			filename = secure_filename(file.filename)
			file.save("/tmp/", filename)

			#TODO: add to loader/set to main
			return "OK"

		return "nope"

	def handle_patch_upload(self):
		pass

	def cleargame(self):
		pass

	def bootgame(self):
		pass