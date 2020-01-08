import logging
from NodeList import NodeList
from NodeDescriptor import NodeDescriptor
from GameDescriptor import GameDescriptor
from Loader import *
import traceback

class NodeManager():
	nodes = None
	_autoboot = False

	def __init__(self, autoboot=False):
		self._autoboot = autoboot
		self.__logger = logging.getLogger("NodeManager")
		self.nodes = NodeList()
		self._loaders = LoaderList()
		MBus.add_handler(Node_LoaderUploadPctMessage, self.handle_LoaderUploadPctMessage)

	def setgame(self, n: str, gd : GameDescriptor):
		node = self.nodes[n]
		if not self.validateGameDescriptor(node, gd):
			self.__logger.debug("Won't boot " + self.nodes[n].game.filename + " on " + self.nodes[n].node_id)
			return

		self.nodes[n].game = gd

		tloader = Loader(self.nodes[n].node_id, self.nodes[n].game.filepath, self.nodes[n].ip, self.nodes[n].port)
		self._loaders.append(tloader)

	def launchgame(self, node_id : str) -> bool:
		#DO EET NOW
		if self._loaders[node_id]:
			return self._loaders[node_id].bootGame()

		return False

	def getLoaderState(self, node_id : str):
		if len(self._loaders) > 0:
			return self._loaders[node_id].state

		return ""

	def tickLoaders(self):
		if len(self._loaders) > 0:
			for l in self._loaders:
				l.tick()

	def validateGameDescriptor(self, nd : NodeDescriptor, gd : GameDescriptor, strict = True):
		bootable = True
		try:
			# If the systems don't match up,
			# OR if the system is a NAOMI2:
			#   If the system id of the game isn't NAOMI, NAOMI2, or Atomiswave, and the game isn't a NAOMI2 conversion.....
			#
			# Side note: Hard coding ID's like this is bad practice. It's all 20 year old hardware though so fuck it.
			# If anyone's going to be messing with this they're gonna be gutting it anyways.
			if (nd.system[0] != gd.getSystem[0]) and not ((nd.system[0] == 2 and int(gd.getSystem[0]) in {1,2,3}) or (nd.system[0] == 2 and gd.isNaomi2CV)) :
				# You dun goofed.
				self.__logger.debug("Wrong system. Game wants " + gd.getSystem[1] + " but this node is a " + nd.system[1])
				bootable = False
			#else:
				#nd.__logger.debug("system ok")

			if nd.monitor[0] != gd.getMonitor[0]:
			#    nd.__logger.debug('Wrong monitor type. Game wants ' + gd.getMonitor()[1] + " but node has " + nd.monitor[1])
				if strict: bootable = False
			#else:
			#    nd.__logger.debug("monitor ok")

			#1if nd.controls[0] != gd.getControls()[0]:
				#FIXME: do in-depth logic of control schemes
				#nd.__logger.debug('Wrong control scheme, game wants ' + gd.getControls()[1] + " but this node has " + nd.controls[1])
				#if strict: bootable = False
			#else:
			#    nd.__logger.debug("controls ok")

			if nd.dimm_ram[1].strip('MB') < gd.getDIMMRAMReq[1].strip('MB'):
				#nd.__logger.debug('Not enough RAM in NetDIMM node to load game, ' + gd.getDIMMRAMReq()[1] + "required")
				bootable = False
			#else:
				#self.__logger.debug("DIMM RAM ok")
		except Exception as ex:
			traceback.print_exc()
			print(repr(ex))
			print(vars(gd))

		return bootable


	def loadNodesFromDisk(self, nodes_dir: str):
		self.nodes.loadNodes(nodes_dir)

		for n in self.nodes:
			tloader = Loader(n.node_id, n.game.filepath, n.ip, n.port)
			if self._autoboot:
				tloader.state = LoaderState.WAITING
	
			self._loaders.append(tloader)


	def saveNodesToDisk(self, nodes_dir: str):
		self.nodes.exportNodes(nodes_dir)

	def handle_LoaderUploadPctMessage(self, message: Node_LoaderUploadPctMessage):
		if message.payload[0] == self.node_id:
			self.loader_uploadpct = message.payload[1] #I don't know why this isn't setting on my python but it's blocking me and I'm going to look at it with fresh eyes later