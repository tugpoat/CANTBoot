import socket
import json
import yaml
import io
import glob

import GameDescriptor
from Loader import LoadWorker
'''
Organizational container for DIMM endpoints.
Attached to a Loader object.
'''
class NodeDescriptor(yaml.YAMLObject):
	nickname = ""
	hostname = ""
	ip = ""
	port = 0
	system = None
	monitor = None
	controls = None
	dimm_ram = None
	game = None
	_extension = None #TODO: for card reader emulators, VMU emulators, etc. will use multiprocessing. each node *should* only ever need one of these.
	_loader = None

	def __init__(self, hostname, port):
		self.hostname = hostname
		#TODO: Error check DNS resolution
		self.ip = self._resolve_hostname(hostname) #automatically resolve hostnames if we can
		self.port = port

	# Copy constructor
	def __init__(self, other_obj):
		if not type(other_obj) is NodeDescriptor:
			return

		self.nickname = other_obj.nickname
		self.hostname = other_obj.hostname
		self.ip = other_obj.ip
		self.port = other_obj.port
		self.system = other_obj.system
		self.monitor = other_obj.monitor
		self.controls = other_obj.controls
		self.dimm_ram = other_obj.dimm_ram
		self.game = other_obj.game

	#If we have an active loader
	def is_active(self):
		return type(loader) is LoadWorker and loader.is_active()

	def _resolve_hostname(self, hostname):
		return socket.gethostbyname(hostname)

	def serialize(self):
		return json.dumps({"hostname": self.hostname, "ip": self.ip, "port": self.port, "system": self.system, "monitor": self.monitor})

	def Load(self, mq, gd):
		#if not type(gd) is GameDescriptor:
		#	raise Exception('load failed, tried to load object of wrong type or invalid game descriptor object')

		#Validate game for node

		print("Validating " + gd.filename + " for node " + self.nickname + " (" + self.hostname + ")")

		# If the systems don't match up,
		# OR if the system is a NAOMI2:
		#	If the system id of the game isn't NAOMI, NAOMI2, or Atomiswave, and the game isn't a NAOMI2 conversion.....
		if (self.system[0] != gd.getSystem()[0]) and not ((self.system[0] == 2 and int(gd.getSystem()[0]) in {1,2,3}) or (self.system[0] == 2 and gd.isNaomi2CV())) :
			# You dun goofed.
			print("Wrong system. Game wants " + gd.getSystem()[1] + " but this node is a " + self.system[1])
		else:
			print("system ok")

		if self.monitor[0] != gd.getMonitor()[0]:
			print('Wrong monitor type. Game wants ' + gd.getMonitor()[1] + " but node has " + self.monitor[1])
		else:
			print("monitor ok")
		if self.controls[0] != gd.getControls()[0]:
			print('Wrong control scheme, game wants ' + gd.getControls()[1] + " but this node has " + self.controls[1])
		else:
			print("controls ok")

		if self.dimm_ram[1].strip('MB') < gd.getDIMMRAMReq()[1].strip('MB'):
			print('Not enough RAM in NetDIMM node to load game, ' + gd.getDIMMRAMReq()[1] + "required")
		else:
			print("DIMM RAM ok")

		self.game = gd

		self._loader = LoadWorker(mq, gd.filepath, self.ip, self.port)
		self._loader.start()


class NodeList():

	_nodes = []

	def __len__(self):
		return len(self._nodes)

	def __iter__(self):
		for elem in self._nodes:
			yield elem
			
	def __getitem__(self, key):
		return self._nodes[key]

	def append(self, node):
		self._nodes.append(node)

	def len(self):
		return len(self._nodes)

	def loadNodes(self):
		nodedir = 'nodes/'
		nodefiles = glob.glob(nodedir+'*.yml')
		for file in nodefiles:
			try:
				with open(file) as ifs:
					node = yaml.load(ifs)

				self._nodes.append(node)
			except:
				print("couldn't load nodes for some reason")

	def saveNodes(self):
		nodedir = 'nodes/'
		for elem in self._nodes:
			try:
				# We have to do it this way because there's a loader object in there that spawns its own process.
				# Can't cross our pickles, that'd be weird.
				tmp = NodeDescriptor(elem)
				
				with open(nodedir+tmp.nickname+'.yml', 'w') as ofs:
					yaml.dump(tmp, ofs)
			except Exception as ex:
				print(ex)