import socket
import json
import yaml
import io
import glob
import binascii

import GameDescriptor
from Loader import LoadWorker

from loader_events import Node_UploadCommandMessage


'''
Organizational container for DIMM endpoints.
'''
class NodeDescriptor(yaml.YAMLObject):
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
    _extension = None #TODO: for card reader emulators, VMU emulators, etc. will use multiprocessing.
    _loader = None

    def __init__(self, hostname, port):
        self.hostname = hostname
        #TODO: Error check DNS resolution
        self.ip = self._resolve_hostname(hostname) #automatically resolve hostnames if we can
        self.port = port
        self.node_id = binascii.crc32(self.hostname+self.ip+self.port) # we can probably use this to dynamically set up mbus subscribers

    # Copy constructor
    def __init__(self, other_obj):
        if not type(other_obj) is NodeDescriptor:
            return

        self.nickname = other_obj.nickname
        self.hostname = other_obj.hostname
        self.ip = other_obj.ip
        self.port = other_obj.port
        self.system = other_obj.system
        self.monitor = other_obj.monitor
        self.controls = other_obj.controls
        self.dimm_ram = other_obj.dimm_ram
        self.game = other_obj.game

    #If we have an active loader
    def is_active(self):
        return type(loader) is LoadWorker and loader.is_active()

    def _resolve_hostname(self, hostname):
        return socket.gethostbyname(hostname)

    def serialize(self):
        return json.dumps({"hostname": self.hostname, 
            "ip": self.ip,
            "port": self.port,
            "system": self.system,
            "monitor": self.monitor,
            "controls": self.controls,
            "dimm_ram": self.dimm_ram,
            "game": game})

    def load(self, gd):
        #if endpoint is DIMM, do this.
        return self.loadToDIMM(gd)
        #TODO: if endpoint is API slave, do something else. 
        #Like send the rom file and any player data/patches over TCP.

    def cb_terminate():
        print("Received termination request, stopping and terminating loadworker")
        self._loader.stop()
        self._loader = None

    def loadToDIMM(self, gd):
        #if not type(gd) is GameDescriptor:
        #   raise Exception('load failed, tried to load object of wrong type or invalid game descriptor object')

        #Validate game for node

        print("Validating " + gd.filename + " for node " + self.nickname + " (" + self.hostname + ")")

        # If the systems don't match up,
        # OR if the system is a NAOMI2:
        #   If the system id of the game isn't NAOMI, NAOMI2, or Atomiswave, and the game isn't a NAOMI2 conversion.....
        #
        # Side note: Hard coding ID's like this is bad practice. It's all 20 year old hardware though so fuck it.
        # If anyone's going to be messing with this they're gonna be gutting it anyways.
        if (self.system[0] != gd.getSystem()[0]) and not ((self.system[0] == 2 and int(gd.getSystem()[0]) in {1,2,3}) or (self.system[0] == 2 and gd.isNaomi2CV())) :
            # You dun goofed.
            print("Wrong system. Game wants " + gd.getSystem()[1] + " but this node is a " + self.system[1])
        else:
            print("system ok")

        if self.monitor[0] != gd.getMonitor()[0]:
            print('Wrong monitor type. Game wants ' + gd.getMonitor()[1] + " but node has " + self.monitor[1])
        else:
            print("monitor ok")
        if self.controls[0] != gd.getControls()[0]:
            print('Wrong control scheme, game wants ' + gd.getControls()[1] + " but this node has " + self.controls[1])
        else:
            print("controls ok")

        if self.dimm_ram[1].strip('MB') < gd.getDIMMRAMReq()[1].strip('MB'):
            print('Not enough RAM in NetDIMM node to load game, ' + gd.getDIMMRAMReq()[1] + "required")
        else:
            print("DIMM RAM ok")

        self.game = gd

        # Let's make it do the thing
        self._loader = LoadWorker(gd.filepath, self.ip, self.port)
        self._loader.start()
