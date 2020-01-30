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
	loader_uploadpct=0

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

		self.node_id =  hashlib.md5((self.hostname+self.ip+str(self.port)).encode()).hexdigest()

		pass


	def setup(self):
		#self.ip = self._resolve_hostname(hostname) #automatically resolve hostnames if we can
		self.node_id = hashlib.md5((self.hostname+self.ip+str(self.port)).encode()).hexdigest()

	#If we have an active loader
	def is_active(self):
		return type(loader) is Loader and loader.is_active()

	def _resolve_hostname(self, hostname):
		return socket.gethostbyname(hostname)
