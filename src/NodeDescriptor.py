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

	def __init__(self, hostname, port):
		self.hostname = hostname
		#TODO: Error check DNS resolution
		self.ip = self._resolve_hostname(hostname) #automatically resolve hostnames if we can
		self.port = port

	def _resolve_hostname(self, hostname):
		return socket.gethostbyname(hostname)

	def serialize(self):
		return json.dumps({"hostname": self.hostname, "ip": self.ip, "port": self.port})