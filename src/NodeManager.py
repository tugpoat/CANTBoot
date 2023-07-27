import logging
from NodeList import NodeList
from NodeDescriptor import NodeDescriptor
from GameDescriptor import GameDescriptor
from GameList import GameList_ScanEventMessage
from Loader import *
from main_events import *
import traceback

class NodeManager():
	nodes = None
	_autoboot = False

	def __init__(self, autoboot : bool = False , api_master : bool = False):
		self._autoboot = autoboot
		self.__logger = logging.getLogger("NodeManager " + str(id(self)))
		self.__logger.debug("init logger")
		self.nodes = NodeList()
		self._loaders = LoaderList()

		MBus.add_handler(Node_LoaderUploadPctMessage, self.handle_LoaderUploadPctMessage)
		MBus.add_handler(GameList_ScanEventMessage, self.handle_GameList_ScanEventMessage)

	'''
	Associates a GameDescriptor object with a NodeDescriptor object.
	Then, instantiates or updates the appropriate Loader object for the NodeDescriptor.
	This is an integral part of loading a game.
	'''
	def setgame(self, n: str, gd : GameDescriptor):
		node = self.nodes[n]
		loader_class = Loader

		# Valid for this endpoint?
		if not self.validateGameDescriptor(node, gd, False):
			self.__logger.error("Won't boot " + gd.filename + " on " + self.nodes[n].node_id)
			return
			
		self.nodes[n].game = gd
		self.__logger.debug(self.nodes[n].game.filepath)

		# Sync config to disk
		MBus.handle(message=SaveConfigToDisk())

		self.__logger.debug(self.nodes[n].game.filepath)

		#Determine what our endpoint should be and use the appropriate loader
		if node.node_type == 0:
			loader_class = DIMMLoader
		elif node.node_type == 1:
			loader_class = APILoader

		# If there is already a loader for this node, recreate the existing instance
		if self._loaders[n]:
			self.__logger.debug("updating loader")
			self._loaders[n] = loader_class(self.nodes[n].node_id, self.nodes[n].game.filepath, self.nodes[n].ip, self.nodes[n].port)
		else:
			# Add a new loader instance
			tloader = loader_class(self.nodes[n].node_id, self.nodes[n].game.filepath, self.nodes[n].ip, self.nodes[n].port)
			self._loaders.append(tloader)
	
	def file_get_contents(self, filename):
		with open(filename) as f:
			return f.read()

	def launchgame(self, node_id : str) -> bool:
		#DO EET NOW
		if self._loaders[node_id]:
			self.__logger.debug("Booting game")
			
			return self._loaders[node_id].bootGame()

		return False

	def getLoaderState(self, node_id : str) -> str:
		if len(self._loaders) > 0 and self._loaders[node_id]:
			return self._loaders[node_id].state

		return ""

	def tickLoaders(self):
		if len(self._loaders) > 0:
			for l in self._loaders:
				l.tick()

	'''
	This function sanity-checks a gamedescriptor against a nodedescriptor based on what the user has configured for properties.
	It is also used to filter the games list when selecting a game to boot on the specified node.
	'''
	def validateGameDescriptor(self, nd : NodeDescriptor, gd : GameDescriptor, strict = True) -> bool:
		bootable = True
		try:
			# If the systems don't match up,
			# OR if the system is a NAOMI2:
			#   If the system id of the game isn't NAOMI, NAOMI2, or Atomiswave, and the game isn't a NAOMI2 conversion.....
			#
			# Side note: Hard coding ID's like this is bad practice. It's all 20 year old hardware though so fuck it.
			# If anyone's going to be messing with this they're gonna be gutting it anyways.
			if not gd.getSystem is None:
				if (nd.system[0] != gd.getSystem[0]) and not ((nd.system[0] == 2 and int(gd.getSystem[0]) in {1,2,3}) or (nd.system[0] == 2 and gd.isNaomi2CV)) :
					# You dun goofed.
					self.__logger.debug("Checking game " + gd.filename + " against node " + nd.nickname + " : Wrong system. Game wants " + gd.getSystem[1] + " but this node is a " + nd.system[1])
					bootable = False
				#else:
					#nd.__logger.debug("system ok")

			if not gd.getMonitor is None:
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

			if not gd.getDIMMRAMReq is None:
				if int(nd.dimm_ram[1].strip('MB')) < int(gd.getDIMMRAMReq[1].strip('MB')):
					#nd.__logger.debug('Not enough RAM in NetDIMM node to load game, ' + gd.getDIMMRAMReq()[1] + "required")
					bootable = False
				#else:
					#self.__logger.debug("DIMM RAM ok")
					
		except Exception as ex:
			self.__logger.debug(repr(ex) + traceback.print_exc())

		return bootable


	def loadNodesFromDisk(self, nodes_dir: str):
		self.nodes.loadNodes(nodes_dir)

		for n in self.nodes:
			#if there's no game associated with this node yet then don't attempt to create a loader yet
			if n.game:
				if n.node_type == 0:
					tloader = DIMMLoader(n.node_id, n.game.filepath, n.ip, n.port)
				elif n.node_type == 1:
					tloader = APILoader(n.node_id, n.game.filepath, n.ip, n.port)
				if self._autoboot:
					tloader.state = LoaderState.WAITING

				self._loaders.append(tloader)


	def saveNodesToDisk(self, nodes_dir: str):
		self.nodes.exportNodes(nodes_dir)

	def handle_GameList_ScanEventMessage(self, message: GameList_ScanEventMessage):
		if message.payload == 'donelol' and self._autoboot == True:
			for l in self._loaders:
				l.bootGame()

	def handle_LoaderUploadPctMessage(self, message: Node_LoaderUploadPctMessage):
		self.nodes[message.payload[0]].loader_uploadpct = message.payload[1]
