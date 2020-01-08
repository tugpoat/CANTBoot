import os
import time
import json
import configparser
import logging
import typing as t
from enum import Enum
from mbus import *

from NetComm import *

'''
Enum for Loader state machine
'''
class LoaderState(Enum):
	BOOT_FAILED = -5
	TRANSFER_FAILED = -4
	CONNECTION_LOST = -3
	CONNECTION_FAILED = -2
	PATCHING_FAILED = -1
	EXITED = 0
	WAITING = 1
	PATCHING = 2
	CONNECTING = 3
	TRANSFERRING = 4
	BOOTING = 5
	KEEPALIVE = 6

'''
Container class for State messages, so that the node we're associated with can be looked up
'''
class LoaderStateMsgObj():
	def __init__(self, nid, st):
		self.node_id = nid
		self.state = LoaderState(st)

'''
Message containers
'''
class Node_LoaderStateMessage(t.NamedTuple):
	payload: type(LoaderStateMsgObj)

class Node_LoaderUploadPctMessage(t.NamedTuple):
	#[node_id, % complete]
	payload: t.List[str]

class Node_LoaderExceptionMessage(t.NamedTuple):
	# [node_id, message]
	payload: t.List[str]

class Node_SetGameCommandMessage(t.NamedTuple):
	payload: t.List[str]

class Node_LaunchGameCommandMessage(t.NamedTuple):
	payload: str


'''
The actual loader. managed through NodeManager.
'''
class Loader:

	path = None
	host = None
	port = None
	_comm = None
	_active = False
	_tick = 0
	_wait_tick = 0

	_patches = []

	'''
	Construct using bare minimum of information
	queue: Queue, for passing messages back to the main process
	abs_path: String, absolute path of ROM file
	host: String, IP Address of endpoint
	'''
	def __init__(self, node_id : str, abs_path: str, host: str, port: int):
		self.__logger = logging.getLogger("loader")
		self.node_id: str = node_id
		self.rom_path: str = abs_path
		self.host: str = host
		self.port: int = port
		self._comm = NetComm()
		self._tick = time.time()
		self._wait_tick = time.time()
		self.last_state = LoaderState.WAITING # doesn't matter what this is on init as long as it's different from self.state
		self.state = LoaderState.EXITED # This should be EXITED so it doesn't automatically try and load games unless we tell it to

	@property
	def node_id(self) -> str:
		return self._node_id

	@node_id.setter
	def node_id(self, value : str):
		self._node_id = value

	@property
	def state(self) -> LoaderState:
		return self._state

	@state.setter
	def state(self, value : LoaderState):
		self.__logger.debug("set " + self.node_id + " state to " + str(value))
		# Only update last state if it's different from what we're trying to set
		# It should always be different, but might as well sanity-check
		if self.last_state != value:
			try:
				self.last_state = self.state
				self.__logger.debug("set last state to " + str(self.state))
			except:
				pass

		self._state = value

	@property
	def last_state(self) -> LoaderState:
		return self._last_state

	@last_state.setter
	def last_state(self, value : LoaderState):
		self._last_state = value

	@property
	def rom_path(self) -> str:
		return self._rom_path

	@rom_path.setter
	def rom_path(self, value : str):
		self._rom_path = value

	@property	
	def is_active(self) -> bool:
		return self._active

	def tick(self):
		self._tick = time.time()
		func = self.states.get(self.state, lambda: INVALID)
		func(self)

		#each state should only run once as each one will update the state machine (except keepalive)

	def upload_pct_callback(percent_complete):
		#TODO: deliver this number to UI and/or main thread via messagebus
		self.__logger.debug("upload cb: " + percent_complete + "%")
		MBus.handle(Node_LoaderUploadPctMessage(payload=percent_complete))

	def boot_failed(self):
		return

	def transfer_failed(self):
		return

	def connection_lost(self):
		return

	def connection_failed(self):
		self.state = LoaderState.WAITING
		return
	
	def patching_failed(self):
		return

	def exited(self):
		return

	def patching(self):
		return1

	def waiting(self):
		#Wait 5 seconds between connection attempts
		if int(self._tick - self._wait_tick) > 5:
			self.__logger.debug(str(self._tick) + " " + str(self._wait_tick) + " " + str(self._tick - self._wait_tick))
			self.state = LoaderState.CONNECTING

	def connecting(self):
		# Open a connection to endpoint
		try:
			self._comm.connect(self.host, self.port)
		except Exception as ex:
			self.state = LoaderState.CONNECTION_FAILED


	def transferring(self):
		#Display "Now Loading..." on screen
		self._comm.HOST_SetMode(0, 1)

		# disable encryption by setting magic zero-key
		self._comm.SECURITY_SetKeycode("\x00" * 8)

		# uploads file. Also sets "dimm information" (file length and crc32)
		self._comm.DIMM_UploadFile(rom_path, None, upload_pct_callback)

		self.state = LoaderState.BOOTING

	def booting(self):
		# restart the endpoint system, this will boot into the game we just sent
		self._comm.HOST_Restart()

		self.state = LoaderState.KEEPALIVE

	def keepalive(self):
		if int(self._tick - self._last_tick) < 5:
			try:
				# set time limit to 10h. According to some reports, this does not work.
				TIME_SetLimit(10*60*1000)
			except Exception as ex:
				#We lost our connection. Return to waiting state and attempt again once the DIMM is reachable.
				self.states = LoaderState.WAITING

	#Additional translation for functions
	states = {
		LoaderState.BOOT_FAILED : boot_failed,
		LoaderState.TRANSFER_FAILED : transfer_failed,
		LoaderState.CONNECTION_LOST : connection_lost,
		LoaderState.CONNECTION_FAILED: connection_failed,
		LoaderState.PATCHING_FAILED: patching_failed,
		LoaderState.EXITED : exited,
		LoaderState.WAITING : waiting,
		LoaderState.PATCHING : patching,
		LoaderState.CONNECTING : connecting,
		LoaderState.TRANSFERRING : transferring,
		LoaderState.BOOTING : booting,
		LoaderState.KEEPALIVE : keepalive
	}


class LoaderList():
	_loaders = []
	def __len__(self):
		return len(self._loaders)

	def __iter__(self):
		for elem in self._loaders:
			yield elem
			
	def __getitem__(self, key):
		#node id
		if type(key) is str:
			for elem in self._loaders:
				if str(elem.node_id) == str(key): 
					return elem

		if type(key) is int:
			return self._loaders[key]

		#FIXME: what happens if id not found?
		print('help!')

	def append(self, node):
		self._loaders.append(node)

	def clear(self):
		self._loaders.clear()

	def len(self):
		return len(self._loaders)
