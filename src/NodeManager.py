import logging
from NodeList import NodeList
from NodeDescriptor import NodeDescriptor
from Loader import *

class NodeManager():
	_loaders = []
	nodes = None

	def __init__(self):
		self.__logger = logging.getLogger("NodeManager")
		self.nodes = NodeList()
		MBus.add_handler(Node_LoaderStatusMessage, self.handle_LoaderStatusMessage)
		MBus.add_handler(Node_LoaderUploadPctMessage, self.handle_LoaderUploadPctMessage)

	def loadNodesFromDisk(self, nodes_dir: str):
		self.nodes.loadNodes(nodes_dir)

	def saveNodesToDisk(self, nodes_dir: str):
		self.nodes.exportNodes(nodes_dir)

	def handle_LoaderStatusMessage(self, message: Node_LoaderStatusMessage):
		#OK what the heck is going on?
		#It has the old address assigned to the variable, it updates it, it confirms it updates it, and then when we access this in UIWeb_Bottle, it's fucked.
		self.__logger.debug("setting status for %s at %s to %s", message.payload[0], id(self.nodes[message.payload[0]]._loader_state), message.payload[1])
		self.nodes[message.payload[0]].loader_state = message.payload[1]

	def handle_LoaderUploadPctMessage(self, message: Node_LoaderUploadPctMessage):
		if message.payload[0] == self.node_id:
			self.loader_uploadpct = message.payload[1] #I don't know why this isn't setting on my python but it's blocking me and I'm going to look at it with fresh eyes later