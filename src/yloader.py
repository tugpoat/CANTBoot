import yaml
from GameDescriptor import *
from NodeDescriptor import *

# Safe Loading!!!!! 
# yaml.load() deprecated
class YLoader(yaml.SafeLoader):
	def construct_python_tuple(self, node):
		return tuple(self.construct_sequence(node))
	def construct_gamedescriptor(self, node):
		return self.construct_mapping(node)
	def construct_nodedescriptor(self, node):
		return self.construct_mapping(node)

YLoader.add_constructor(u'tag:yaml.org,2002:python/tuple', YLoader.construct_python_tuple)