import socket
import json
import yaml
import io
import glob
import binascii
import copy
from yloader import *

# Does what it says on the box.
class NodeList():
	_nodes = []

	def __len__(self):
		return len(self._nodes)

	def __iter__(self):
		for elem in self._nodes:
			yield elem
			
	def __getitem__(self, key):
		#node id
		if type(key) is str:
			for elem in self._nodes:
				if str(elem.node_id) == str(key): 
					return elem

		#FIXME: what happens if id not found?
		
		if type(key) is int:
			return self._nodes[key]

		print('help!')

	def append(self, node):
		self._nodes.append(node)

	def clear(self):
		self._nodes.clear()

	def len(self):
		return len(self._nodes)

	def loadNodes(self, nodes_dir: str):
		nodefiles = glob.glob(nodes_dir+'/*.yml')
		tmplist = []
		for file in nodefiles:
			try:
				with open(file) as ifs:
					node = yaml.load(ifs, Loader=YLoader)
				tmplist.append(node)
			except Exception as ex:
				print("couldn't load nodes for some reason" + repr(ex))

		# Make sure we sort everything all nicely
		tmplist.sort(key = lambda tmplist: tmplist.nickname.lower())
		self._nodes = tmplist
		for elem in self._nodes:
			elem.setup()


	def exportNodes(self, nodes_dir: str):
		for elem in self._nodes:
			try:
				# We have to do it this way because there's a loader object in there that spawns its own process.
				# Can't cross our pickles, that'd be weird.
				tmp = NodeDescriptor(elem)
				print ("exporting to " + nodes_dir+"/"+tmp.nickname+'.yml')
				with open(nodes_dir+"/"+tmp.nickname+'.yml', 'w') as ofs:
					yaml.dump(tmp, ofs)
			except Exception as ex:
				print(ex)
