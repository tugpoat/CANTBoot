import socket
import json
import yaml
import io

'''
Organizational container for DIMM endpoints.
Attached to a Loader object.
'''
class NodeDescriptor(yaml.YAMLObject):
	nickname = ""
	hostname = ""
	ip = ""
	port = 0
	system = dict()
	monitor = dict()
	controls = dict()
	loader = None

	#FIXME: store details about the machine, e.g. control panel setup, monitor orientation etc.
	# we can use this to filter games for this particular node.

	def __init__(self, hostname, port):
		self.hostname = hostname
		#TODO: Error check DNS resolution
		self.ip = self._resolve_hostname(hostname) #automatically resolve hostnames if we can
		self.port = port

	def _resolve_hostname(self, hostname):
		return socket.gethostbyname(hostname)

	def json_serialize(self):
		return json.dumps({"hostname": self.hostname, "ip": self.ip, "port": self.port, "system": self.system, "monitor": self.monitor})

class NodeList:
	_nodes = []

	def append(self, node):
		self._nodes.append(node)

	def loadNodes(self):
		nodedir = 'nodes/'
		nodefiles = glob.glob(nodedir+'*.yml')
		for file in nodefiles:
			try:
				node = yaml.load(file)
			except:
				print("oops")

			self._nodes.append(node)

	def saveNodes(self):
		nodedir = 'nodes/'
		for node in self._nodes:
			of = open(nodedir+node.nickname+'.yml', 'w')
			yaml.dump(node, of)
			print(yaml.dump(node))