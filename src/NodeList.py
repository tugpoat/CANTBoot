import socket
import json
import yaml
import io
import glob
import binascii
from NodeDescriptor import NodeDescriptor

# Does what it says on the box.
class NodeList():
    _nodes_dir = None
    _nodes = []
    def __init__(self, nodesdir):
        self._nodes_dir = nodesdir

    def __len__(self):
        return len(self._nodes)

    def __iter__(self):
        for elem in self._nodes:
            yield elem
            
    def __getitem__(self, key):
        if type(key) is str:
            #node id
            for elem in self._nodes:
                if elem.node_id == key: return elem

            #FIXME: what happens if id not found?

        return self._nodes[key]

    def append(self, node):
        self._nodes.append(node)

    def len(self):
        return len(self._nodes)

    def loadNodes(self):
        nodefiles = glob.glob(self._nodes_dir+'/*.yml')
        for file in nodefiles:
            try:
                with open(file) as ifs:
                    node = yaml.load(ifs)
                    node.setupHandlers() #Constructor isn't called here so we need  to manually tell it to set up event handlers

                self._nodes.append(node)
            except:
                print("couldn't load nodes for some reason")


    def exportNodes(self):
        for elem in self._nodes:
            try:
                # We have to do it this way because there's a loader object in there that spawns its own process.
                # Can't cross our pickles, that'd be weird.
                tmp = NodeDescriptor(elem)
                print ("exporting to " + self._nodes_dir+"/"+tmp.nickname+'.yml')
                with open(self._nodes_dir+"/"+tmp.nickname+'.yml', 'w') as ofs:
                    yaml.dump(tmp, ofs)
            except Exception as ex:
                print(ex)
