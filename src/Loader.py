import os
import time
import json
import configparser
import logging
import typing as t

import os

on_raspi=False
if "raspberrypi" in os.uname():
	on_raspi=True
	import RPi.GPIO as GPIO

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
	CONNECTING = 3
	CONNECTED = 4
	PATCHING = 5
	TRANSFERRING = 6
	BOOTING = 7
	KEEPALIVE = 8

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
	_tick = 0
	_wait_tick = 0

	_do_boot = False
	_do_keepalive = False

	_patches = []

	'''
	Construct using bare minimum of information
	queue: Queue, for passing messages back to the main process
	abs_path: String, absolute path of ROM file
	host: String, IP Address of endpoint
	'''
	def __init__(self, node_id : str, abs_path: str, host: str, port: int):
		self.__logger = logging.getLogger("Loader " + str(id(self)))
		self.node_id: str = node_id
		self.rom_path: str = abs_path
		self.host: str = host
		self.port: int = port
		self._comm = NetComm()
		self._tick = time.time()
		self._wait_tick = time.time()
		self.enableGPIOReset = True
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
				self.__logger.debug("set " + self.node_id + " last state to " + str(self.state))
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
	def enableGPIOReset(self) -> bool:
		return self._enableGPIOReset

	@enableGPIOReset.setter
	def enableGPIOReset(self, value : bool):
		self._enableGPIOReset = value

	def bootGame(self) -> bool:
		self._do_boot = True
		self._do_keepalive = False

		ret = False

		# TODO: I don't think either of these functions will actually cause a disconnect, so we should be good to go
		# Although there probably isn't any harm in just creating a new connection.
		# Should investigate it through testing.
		if on_raspi and self.enableGPIOReset:
			self.__logger.info("doing GPIO Reset")
			self.doGPIOReset()
			ret = True
		elif self._comm.is_connected:
			self.__logger.info("doing NetDIMM Reset")
			self.doDIMMReset()
			ret = True

		# This state has a built-in 2 second delay to reconnect.
		# Should be enough time for the system to get started enough for us to work with it.
		self.state = LoaderState.CONNECTING
		return ret

	def doDIMMReset(self):
		if self._comm.is_connected:
			self._comm.HOST_Restart()

	def doGPIOReset(self):
		# No sense in doing anything if we're not running on something that supports the RPi GPIO lib
		if on_raspi:
			GPIO.setmode(GPIO.BOARD)
			GPIO.setup(40, GPIO.OUT)
			GPIO.output(40,1)
			time.sleep(0.4)
			GPIO.output(40,0)

	def tick(self):
		self._tick = time.time()
		try:
			_func = self.states.get(self.state, lambda self: self.INVALID)
			_func(self)
		except:
			pass
		#If we're not waiting, let's make sure our times stay in sync
		if self.state != LoaderState.WAITING and self.state != LoaderState.KEEPALIVE:
			self._wait_tick = self._tick

		#each state should only run once as each one will update the state machine (except keepalive)

	def INVALID(self):
		pass

	def upload_pct_callback(self, percent_complete):
		#TODO: deliver this number to UI and/or main thread via messagebus
		self.__logger.debug("upload cb: " + str(percent_complete) + "%")
		MBus.handle(Node_LoaderUploadPctMessage(payload=[self.node_id, str(percent_complete)]))

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
		return

	def waiting(self):
		#Wait 2 seconds between connection attempts
		if int(self._tick - self._wait_tick) > 2:
			self.__logger.debug(str(self._tick) + " " + str(self._wait_tick) + " " + str(self._tick - self._wait_tick))
			self.state = LoaderState.CONNECTING

	def connecting(self):
		# Open a connection to endpoint
		try:
			if not self._comm.connect(self.host, self.port):
				self.state = LoaderState.CONNECTION_FAILED
				return

			if self._do_boot:
				self.state = LoaderState.TRANSFERRING
			elif self._do_keepalive:
				self.state = LoaderState.KEEPALIVE
			else: self.state = LoaderState.CONNECTED

		except Exception as ex:
			self.__logger.error(repr(ex))
			self.state = LoaderState.CONNECTION_FAILED

	def connected(self):
		self.__logger.info("Connected")
		return

	def transferring(self):
		try:
			#Display "Now Loading..." on screen
			self._comm.HOST_SetMode(0, 1)

			# disable encryption by setting magic zero-key
			self._comm.SECURITY_SetKeycode("\x00" * 8)

			self.__logger.info("Uploading " + self.rom_path)
			# uploads file. Also sets "dimm information" (file length and crc32)
			self._comm.DIMM_UploadFile(self.rom_path, None, self.upload_pct_callback)
		except Exception as ex:
			self.__logger.error(repr(ex))
			#self.__logger.debug("Connection timed out or something. reconnecting.")
			self.state = LoaderState.CONNECTING
			return

		if self._do_boot:
			self.state = LoaderState.BOOTING

	def booting(self):
		# restart the endpoint system, this will boot into the game we just sent
		self._comm.HOST_Restart()
		self.state = LoaderState.KEEPALIVE
		self._do_boot = False # Finished booting. we don't want to reboot into the game automatically if we lose connection

	def keepalive(self):
		if int(self._tick - self._wait_tick) > 10:
			try:
				# set time limit to 10h. According to some reports, this does not work.
				self._comm.TIME_SetLimit(10*60*1000)
				self.__logger.info("Sent keepalive!")
				self._wait_tick = self._tick
			except Exception as ex:
				self._do_keepalive = True # return to keepalive if we lose connection
				#We lost our connection. Return to waiting state and attempt again once the DIMM is reachable.
				self.states = LoaderState.CONNECTION_LOST

		return

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
		print('help! computer')

	def __setitem__(self, key, item : Loader):
		#node id
		if type(key) is str:
			for index,elem in enumerate(self._loaders):
				if str(elem.node_id) == str(key): 
					self._loaders[index] = item

		if type(key) is int:
			self._loaders[key] = item

	def append(self, loader):
		self._loaders.append(loader)

	def clear(self):
		self._loaders.clear()

	def len(self):
		return len(self._loaders)
