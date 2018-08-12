
import os
import time
import json
import configparser
from multiprocessing import Manager, Process, Queue
from NodeDescriptor import *
from GameDescriptor import *
import gameboot


'''
STATUS CODES
-1 error
0 unused
1 connecting
2 uploading
3 booting
4 keep-alive

RETURN CODES
0 success
1 error
'''

'''
Basically just a container for organizational purposes
Also enables easy generation of JSON that we can send over through the UI
'''
class Loader:
    system_name = None
    status = 0
    error = 0
    game = None
    node = None
    pworker = None

    def serialize(self):
        #TODO: Check if self.game is valid GameDescriptor object and that self.node is valid NodeDescriptor object
        return json.dumps({"system_name": self.system_name, "status": self.status, "error": self.error, "node": self.node.serialize(), "game": self.game.serialize()})


'''
The actual loader. instantiated inside of Loader and launched by the main thread. That is, if Python will let me do that (It probably will, Python is a mess).
'''
class LoadWorker(Process):
    mq = None
    path = None
    host = None

    def __init__(self, queue, abs_path, host):
        Process.__init__(self)
        self.mq = queue
        self.path = abs_path
        self.host = host

    def __init__(self, queue, node, game):
        Process.__init__(self)
        self.mq = queue
        self.path = game.filepath
        self.host = node.ip

    def run(self):

        filename = self.path[:(len(self.path) - self.path.rfind(os.pathsep))]

        print("Uploading " + filename + " to " + self.host)

        try:
            message = message = [1, ("%s : connecting to %s" % (self.name, self.host))]
            self.mq.put(message)
            gameboot.connect(self.host, 10703)
        except Exception as ex:
            message = [-1, ("%s : connection to %s failed! exiting." % (self.name, self.host)), repr(ex)]
            self.mq.put(message)
            #print(("%s : connection to %s failed! exiting." % (self.name, self.host)))
            return 1

        try:
            message = [2, ("%s : Uploading " % (self.name, self.path, self.host))]
            self.mq.put(message)

            gameboot.HOST_SetMode(0, 1)
            # disable encryption by setting magic zero-key
            gameboot.SECURITY_SetKeycode("\x00" * 8)

            # uploads file. Also sets "dimm information" (file length and crc32)
            gameboot.DIMM_UploadFile(game_path)
            
            message = [3, ("%s : Booting " % (self.name, self.path, self.host))]
            self.mq.put(message)
            
            # restart host, this will boot into game
            gameboot.HOST_Restart()

        except Exception as ex:
            message = [-1, ("%s : Error booting game on hardware! " % (self.name, self.path, self.host)), repr(ex)]
            self.mq.put(message)
            return 1

        message = [4, ("%s : Entering Keep-alive loop. " % (self.name))]
        self.mq.put(message)

        while 1:
            try:
                # set time limit to 10h. According to some reports, this does not work.
                TIME_SetLimit(10*60*1000)
                time.sleep(5)
            except Exception as ex:
                #TODO: maybe check what the exception is and automatically determine whether or not to continue
                message = [-1, ("%s : Keep-alive failed! Continuing to attempt anyway." % (self.name, self.path, self.host)), repr(ex)]
                self.mq.put(message)
