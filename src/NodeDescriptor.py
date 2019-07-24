import socket
import json

'''
Organizational container for DIMM endpoints.
Attached to a Loader object.
'''
class NodeDescriptor:
	hostname = ""
	ip = ""
	port = ""
	system_id =0
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

	def serialize(self):
		return json.dumps({"hostname": self.hostname, "ip": self.ip, "port": self.port})