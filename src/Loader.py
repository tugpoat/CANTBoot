import os
import time
import json
import configparser
import logging
from multiprocessing import Manager, Process, Queue
from mbus import *

from NetComm import *

from loader_events import *



'''
The actual loader. Attached to a NodeDescriptor in practical use, and runs as its own process.

TODO: run a ping against the NetDIMM. if it breaks, then restart the netboot cycle once reachable to maintain the desired state. 
This will effectively give us single-game functionality without compromise.
'''

#FIXME: STATUS MESSAGING IS A RESULT OF SOME MESSED UP IPC. 
#PYTHON BROKE IT I GUESS, IDK. TURN THIS INTO A SINGLE THREADED DOOHICKEY
class LoaderStates(Enum):
	BOOT_FAILED = -4
	TRANSFER_FAILED = -3
	CONNECTION_LOST = -2
	CONNECTION_FAILED = -1
	EXITED = 0
	WAITING = 1
	CONNECTING = 2
	TRANSFERRING = 3
	BOOTING = 4
	KEEPALIVE = 5

class Loader:

	states = {
		LoaderStates.BOOT_FAILED : "boot_failed",
		LoaderStates.TRANSFER_FAILED : "transfer_failed",
		LoaderStates.CONNECTION_LOST : "connection_lost",
		LoaderStates.CONNECTION_FAILED: "connection_failed",
		LoaderStates.EXITED : "exited",
		LoaderStates.WAITING : "waiting",
		LoaderStates.CONNECTING : "connecting",
		LoaderStates.TRANSFERRING : "transferring",
		LoaderStates.BOOTING : "booting",
		LoaderStates.KEEPALIVE : "keepalive"
	}

	path = None
	host = None
	port = None
	_comm = None
	_active = False

	'''
	Construct using bare minimum of information
	queue: Queue, for passing messages back to the main process
	abs_path: String, absolute path of ROM file
	host: String, IP Address of endpoint
	'''
	def __init__(self, abs_path: str, host: str, port: int):
		self.__logger = logging.getLogger("loader")
		super(Loader, self).__init__()
		self.path: str = abs_path
		self.host: str = host
		self.port: int = port
		self._comm = NetComm()
		self._state = LoaderStates.STATE_WAITING

	@property
	def state(self) -> str:
		return self._state

	@state.setter
	def state(self, value : str):
		self._state = value

	@property	
	def is_active(self) -> bool:
		return self._active

	def tick(self):
		print("tick!")
		func = self.states.get(LoaderStates, lambda: "INVALID")
		print(func())

	def exited(self):
		return "exited"

	def waiting(self):
		return "waiting"

	def connecting(self):
		filename = self.path[:(len(self.path) - self.path.rfind(os.pathsep))]

		# Open a connection to endpoint and notify the main thread that we are doing so.
		try:
			#MBus.handle(Node_LoaderStatusMessage(payload=[self.name, self.STATE_CONNECTING]))
			self._comm.connect(self.host, self.port)
		except Exception as ex:
			#MBus.handle(Node_LoaderStatusMessage(payload=[self.name, self.STATE_CONNECTION_FAILED]))
			#print(("%s : connection to %s failed! exiting." % (self.name, self.host)))
			self.state = LoaderStates.CONNECTION_FAILED

	def connection_failed(self):
		return "connection_failed"

	'''
	This is the function that does the actual work.
	It is invoked with LoadWorker.start() and runs until terminated.
	'''
	def run(self):
		self.__logger.debug("running LoadWorker for " + self.host)
		filename = self.path[:(len(self.path) - self.path.rfind(os.pathsep))]

		# Open a connection to endpoint and notify the main thread that we are doing so.
		try:
			#MBus.handle(Node_LoaderStatusMessage(payload=[self.name, self.STATE_CONNECTING]))
			self._comm.connect(self.host, self.port)
		except Exception as ex:
			#MBus.handle(Node_LoaderStatusMessage(payload=[self.name, self.STATE_CONNECTION_FAILED]))
			#print(("%s : connection to %s failed! exiting." % (self.name, self.host)))
			return 1

		# We have successfully connected to the endpoint. Let's shove our rom file down its throat.
		try:
			MBus.handle(Node_LoaderStatusMessage(payload=[self.name, self.STATE_UPLOADING]))

			self.uploadrom(game_path)

			#message = [3, ("%s : Booting " % (self.name, self.path, self.host))]
			MBus.handle(Node_LoaderStatusMessage(payload=[self.name, self.STATE_BOOTING]))

			# restart the endpoint system, this will boot into the game we just sent
			self._comm.HOST_Restart()

		except Exception as ex:
			MBus.handle(Node_LoaderExceptionMessage(payload=("%s : Error booting game on hardware! ex: %s" % (self.name, self.path, self.host, repr(ex)))))
			MBus.handle(Node_LoaderStatusMessage(payload=[self.name, self.node_id, self.STATE_EXITED]))
			return 1

		self._active = True

		MBus.handle(Node_LoaderStatusMessage(payload=[self.name, self.STATE_KEEPALIVE]))
		keepalive()

	def uploadrom(self, rom_path: str):
		self._comm.HOST_SetMode(0, 1)
		# disable encryption by setting magic zero-key
		self._comm.SECURITY_SetKeycode("\x00" * 8)

		# uploads file. Also sets "dimm information" (file length and crc32)
		self._comm.DIMM_UploadFile(rom_path, None, upload_pct_callback)

	def upload_pct_callback(percent_complete):
		#TODO: deliver this number to UI and/or main thread via messagebus
		self.__logger.debug("upload cb: " + percent_complete + "%")
		MBus.handle(Node_LoaderUploadPctMessage(payload=percent_complete))

	def keepalive(self):
		'''
		Some systems and games have some wacky time limit thing where they will stop working after a period of time.
		We get around this by sending a heartbeat to the endpoint.
		'''
		while 1:
			try:
				# set time limit to 10h. According to some reports, this does not work.
				TIME_SetLimit(10*60*1000)
				time.sleep(5)
			except Exception as ex:
				#We lost our connection. Return to waiting state and attempt again once the DIMM is reachable.
				print('wee')
				#TODO: maybe check what the exception is and automatically determine whether or not to continue
				#message = [-1, ("%s : Keep-alive failed! Continuing to attempt anyway." % (self.name, self.path, self.host)), repr(ex)]
