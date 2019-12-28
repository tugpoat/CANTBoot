import socket
import json
import yaml
import io
import glob
import binascii
import logging
import hashlib

import typing as t

from GameDescriptor import *
from mbus import *
from Loader import *
from loader_events import *

class Node_UploadCommandMessage(t.NamedTuple):
	payload: t.List[str]

'''
Organizational container for DIMM endpoints.
'''
class NodeDescriptor(yaml.YAMLObject):
	yaml_loader = yaml.SafeLoader
	yaml_tag = u'tag:yaml.org,2002:python/object:NodeDescriptor.NodeDescriptor'

	# 0 = DIMM, 1 = API Slave. Future use.
	node_type = 0
	node_id = ""
	nickname = ""
	hostname = ""
	ip = ""
	port = 0
	system = None
	monitor = None
	controls = None
	dimm_ram = None
	game = None

	loader_uploadpct = 0

	#Python doesn't support constructor overloading
	def __init__(self, hostname = None, port = None):
		if type(hostname) is NodeDescriptor:
			self.nickname = hostname.nickname
			self.hostname = hostname.hostname
			self.node_id = hostname.node_id
			self.ip = hostname.ip
			self.port = hostname.port
			self.system = hostname.system
			self.monitor = hostname.monitor
			self.controls = hostname.controls
			self.dimm_ram = hostname.dimm_ram
			self.game = hostname.game
		elif type(hostname) is str and type(port) is int:
			self.hostname = hostname
			#TODO: Error check DNS resolution
			self.ip = self._resolve_hostname(hostname) #automatically resolve hostnames if we can
			self.port = port

		self.node_id = hash((self.hostname, self.ip, self.port)) & 0xffffffff
		self.loader_state = Loader.STATUS_WAITING

		pass


	def setup(self):
		#self.ip = self._resolve_hostname(hostname) #automatically resolve hostnames if we can
		self.node_id = hashlib.md5((self.hostname+self.ip+str(self.port)).encode()).hexdigest()
		self.loader_state = Loader.STATUS_WAITING

	@property
	def loader_state(self):
		return self._loader_state

	@loader_state.setter
	def loader_state(self, value: str):
		self._loader_state = value
		#print("setting ", str(value), " ", id(self._loader_state))

	#If we have an active loader
	def is_active(self):
		return type(loader) is Loader and loader.is_active()

	def _resolve_hostname(self, hostname):
		return socket.gethostbyname(hostname)

	def serialize(self):
		return json.dumps({"hostname": self.hostname, 
			"ip": self.ip,
			"port": self.port,
			"system": self.system,
			"monitor": self.monitor,
			"controls": self.controls,
			"dimm_ram": self.dimm_ram,
			"game": game})

	def validateGameDescriptor(self, gd, strict = True):
		bootable = True
		try:
			# If the systems don't match up,
			# OR if the system is a NAOMI2:
			#   If the system id of the game isn't NAOMI, NAOMI2, or Atomiswave, and the game isn't a NAOMI2 conversion.....
			#
			# Side note: Hard coding ID's like this is bad practice. It's all 20 year old hardware though so fuck it.
			# If anyone's going to be messing with this they're gonna be gutting it anyways.
			if (self.system[0] != gd.getSystem[0]) and not ((self.system[0] == 2 and int(gd.getSystem[0]) in {1,2,3}) or (self.system[0] == 2 and gd.isNaomi2CV)) :
				# You dun goofed.
				#self.__logger.debug("Wrong system. Game wants " + gd.getSystem()[1] + " but this node is a " + self.system[1])
				bootable = False
			#else:
				#self.__logger.debug("system ok")

			if self.monitor[0] != gd.getMonitor[0]:
			#    self.__logger.debug('Wrong monitor type. Game wants ' + gd.getMonitor()[1] + " but node has " + self.monitor[1])
				if strict: bootable = False
			#else:
			#    self.__logger.debug("monitor ok")

			#1if self.controls[0] != gd.getControls()[0]:
				#FIXME: do in-depth logic of control schemes
				#self.__logger.debug('Wrong control scheme, game wants ' + gd.getControls()[1] + " but this node has " + self.controls[1])
				#if strict: bootable = False
			#else:
			#    self.__logger.debug("controls ok")

			if self.dimm_ram[1].strip('MB') < gd.getDIMMRAMReq[1].strip('MB'):
				#self.__logger.debug('Not enough RAM in NetDIMM node to load game, ' + gd.getDIMMRAMReq()[1] + "required")
				bootable = False
			#else:
				#self.__logger.debug("DIMM RAM ok")
		except Exception as ex:
			print(repr(ex))
			print(vars(gd))

		return bootable

	def load(self, gd):
		#if endpoint is DIMM, do this.
		return self.loadToDIMM(gd)
		#TODO: if endpoint is API slave, do something else. 
		#Like send the rom file and any player data/patches over TCP.


	def loadToDIMM(self, gd):
		#if not type(gd) is GameDescriptor:
		#   raise Exception('load failed, tried to load object of wrong type or invalid game descriptor object')

		#Validate game for node

		#self.__logger.debug("Validating " + gd.filename + " for node " + self.nickname + " (" + self.hostname + ")")

		
		if not self.validateGameDescriptor(gd):
			#self.__logger.debug("Won't attempt load.")
			return

		self.game = gd

		# Let's make it do the thing
		self._loader = Loader(gd.filepath, self.ip, self.port)
		# Let's name it so other NodeDescriptors know if it pertains to them when it passes messages up
		#self._loader.name = self.node_id 
		self._loader.start()
		#FIXME: Testing
		MBus.handle(Node_LoaderStatusMessage(payload=[self.node_id, Loader.STATUS_CONNECTING]))