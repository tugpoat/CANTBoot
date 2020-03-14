import os
import re
import time
import json
import configparser
import logging
import typing as t
import zlib

on_raspi=False
if "raspberrypi" in os.uname():
	on_raspi=True
	import RPi.GPIO as GPIO

from enum import Enum
from mbus import *

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
	UPLOADING = 5
	TRANSFERRING = 6
	BOOTING = 7
	KEEPALIVE = 8

'''
Container class for State messages, so that the node we're associated with can be looked up
'''
class LoaderStateMsgObj():
	def __init__(self, nid, st):
		self.node_id = nid
		self._state = LoaderState(st)

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

# Common loader class. Shouldn't ever be used as-is, exists only to be inherited from
class Loader:
	host = None
	port = None

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
		self._logger.debug("set " + self.node_id + " state to " + str(value))
		# Only update last state if it's different from what we're trying to set
		# It should always be different, but might as well sanity-check
		if self.last_state != value:
			try:
				self.last_state = self._state
				self._logger.debug("set " + self.node_id + " last state to " + str(self._state))
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

	def __init__(self, node_id : str, abs_path: str, host: str, port: int):
		self.node_id: str = node_id
		self.rom_path: str = abs_path
		self.host: str = host
		self.port: int = port
		self._tick = time.time()
		self._wait_tick = time.time()
		self.enableGPIOReset = True
		self.last_state = LoaderState.WAITING # doesn't matter what this is on init as long as it's different from self._state
		self._state = LoaderState.EXITED # This should be EXITED so it doesn't automatically try and load games unless we tell it to

	def tick(self):
		pass


'''
'''
class APILoader(Loader):
	# This will serve as an intermediary, and will run on the master.
	# It will upload rom and patch data to the slave node
	# Loader state will be mirrored from the slave node.
	pass

'''
Lo
'''
class DIMMLoader(Loader):

	_s = None
	_is_connected = False

	path = None

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
		self._logger = logging.getLogger("DIMMLoader " + str(id(self)))
		self.node_id: str = node_id
		self.rom_path: str = abs_path
		self.host: str = host
		self.port: int = port
		self._tick = time.time()
		self._wait_tick = time.time()
		self.enableGPIOReset = True
		self.last_state = LoaderState.WAITING # doesn't matter what this is on init as long as it's different from self._state
		self._state = LoaderState.EXITED # This should be EXITED so it doesn't automatically try and load games unless we tell it to

	@property
	def enableGPIOReset(self) -> bool:
		return self._enableGPIOReset

	@enableGPIOReset.setter
	def enableGPIOReset(self, value : bool):
		self._enableGPIOReset = value

	'''
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	Network Routines
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	'''

	def connect(self, ip : str, port : int) -> bool:

		if self.is_connected and self._s != None:
			self._logger.debug("Called connect() with existant socket. Disconnecting.")
			self.disconnect()

		self._logger.info("Connecting to " + ip + ":" + str(port))
		try:
			self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self._s.settimeout(0.25)
			self._s.connect((ip, port))
			self._s.settimeout(None)
			self._is_connected = True
			self._logger.info("Connected.")
		except Exception as ex:
			self._logger.error("Connection failed! " + repr(ex))
			self._is_connected = False
			return False

		return True

	def disconnect(self):
		self._s.close()
		self._s = None
		self._is_connected = False

	@property
	def is_connected(self) -> bool:
		return self._is_connected

	# a function to receive a number of bytes with hard blocking
	def readsocket(self, n) -> bytes:
		res = "".encode()
		while len(res) < n:
			res += self._s.recv(n - len(res))
		return res

	# Peeks 16 bytes from Host (gamecube) memory
	def HOST_Read16(self, addr) -> bytes:
		self._s.send(struct.pack("<II", 0xf0000004, addr))
		data = readsocket(0x20)
		res = ""
		for d in range(0x10):
			res += data[4 + (d ^ 3)]
		return res

	# same, but 4 bytes.
	def HOST_Read4(self, addr, type = 0) -> bytes:
		self._s.send(struct.pack("<III", 0x10000008, addr, type))
		return self._s.recv(0xc)[8:]

	def HOST_Poke4(self, addr, data):
		self._s.send(struct.pack("<IIII", 0x1100000C, addr, 0, data))

	def HOST_Restart(self):
		self._s.send(struct.pack("<I", 0x0A000000))

	# Read a number of bytes (up to 32k) from DIMM memory (i.e. where the game is). Probably doesn't work for NAND-based games.
	def DIMM_Read(self, addr, size) -> bytes:
		self._s.send(struct.pack("<III", 0x05000008, addr, size))
		return self.readsocket(size + 0xE)[0xE:]

	def DIMM_GetInformation(self) -> bytes:
		self._s.send(struct.pack("<I", 0x18000000))
		return self.readsocket(0x10)

	def DIMM_SetInformation(self, crc, length):
		#print(("length: {0:b}".format(length)))
		self._s.send(struct.pack("<IIII", 0x1900000C, crc & 0xFFFFFFFF, length, 0))

	def DIMM_Upload(self, addr, data, mark):
		self._s.send(struct.pack("<IIIH", 0x04800000 | (len(data) + 0xA) | (mark << 16), 0, addr, 0) + data)

	def NETFIRM_GetInformation(self) -> bytes:
		self._s.send(struct.pack("<I", 0x1e000000))
		return s.recv(0x404)

	def CONTROL_Read(self, addr) -> bytes:
		self._s.send(struct.pack("<II", 0xf2000004, addr))
		return s.recv(0xC)

	def SECURITY_SetKeycode(self, data):
		assert len(data) == 8
		self._s.send(struct.pack("<I", 0x7F000008) + data.encode())

	def HOST_SetMode(self, v_and, v_or) -> bytes:
		self._s.send(struct.pack("<II", 0x07000004, (v_and << 8) | v_or))
		return self.readsocket(0x8)

	def DIMM_SetMode(self, v_and, v_or):
		self._s.send(struct.pack("<II", 0x08000004, (v_and << 8) | v_or))
		return self.readsocket(0x8)

	def DIMM22(self, data):
		assert len(data) >= 8
		self._s.send(struct.pack("<I", 0x22000000 | len(data)) + data)

	def MEDIA_SetInformation(self, data):
		assert len(data) >= 8
		self._s.send(struct.pack("<I",	0x25000000 | len(data)) + data)

	def MEDIA_Format(self, data):
		self._s.send(struct.pack("<II", 0x21000004, data))

	def TIME_SetLimit(self, data):
		self._s.send(struct.pack("<II", 0x17000004, data))

	def DIMM_DumpToFile(self, file):
		for x in range(0, 0x20000, 1):
			file.write(self.DIMM_Read(x * 0x8000, 0x8000))
			sys.stderr.write("%08x\r" % x)

	def HOST_DumpToFile(self, file, addr, len):
		for x in range(addr, addr + len, 0x10):
#			if not (x & 0xFFF):
			sys.stderr.write("%08x\r" % x)
			file.write(self.HOST_Read16(x))

	# upload a file into DIMM memory, and optionally encrypt for the given key.
	# note that the re-encryption is obsoleted by just setting a zero-key, which
	# is a magic to disable the decryption.
	def DIMM_UploadFile(self, name, key = None, progress_cb = None):
		patchdata = self.compilePatchData()

		crc = 0
		f_sz = os.stat(name).st_size
		a = open(name, "rb")
		addr = 0
		if key:
			d = DES.new(key[::-1], DES.MODE_ECB)

		#patch_continue = False

		while True:
			#sys.stderr.write("%08x\r" % addr)
			data = a.read(0x8000)
			datalen = len(data)
'''
			#TODO
			#check patch data to see if there is a patchable address within this chunk.
			#if there is, then check to see if it extends beyond the length of this chunk.
				#if yes, set a flag that we are continuing the specified patch data at the beginning of the next chunk.

				#overwrite the data in this chunk, then remove it from the patch data to be applied.
				#in the case of a partial application, only remove the bytes that we have applied.

			#FIXME: OH GOD THIS IS SLOW WHY AM I DOING IT THIS WAY FIX THIS
			for e in patchdata:
				for a, b in e
					print()
					if a > addr and a < addr + datalen:
						#found a patch for this data
'''



			if not len(data):
				break
			if key:
				data = d.encrypt(data[::-1])[::-1]


			self.DIMM_Upload(addr, data, 0)
			crc = zlib.crc32(data, crc)
			addr += datalen


			# -- prm edit 2019/12/16
			#Callback for percent progress
			if callable(progress_cb):
				progress_cb(round((addr / f_sz) * 100, 2))

		a.close()
		crc = ~crc
		self.DIMM_Upload(addr, "12345678".encode(), 1)
		self.DIMM_SetInformation(crc, addr)

	# obsolete
	def PATCH_MakeProgressCode(self, x):
		#addr = 0x80066ed8 # 2.03
		#addr = 0x8005a9c0 # 1.07
		#addr = 0x80068304 # 2.15
		addr = 0x80068e0c # 3.01
		self.HOST_Poke4(addr + 0, 0x4e800020)
		self.HOST_Poke4(addr + 4, 0x38a00000 | x)
		self.HOST_Poke4(addr + 8, 0x90a30000)
		self.HOST_Poke4(addr + 12, 0x38a00000)
		self.HOST_Poke4(addr + 16, 0x60000000)
		self.HOST_Poke4(addr + 20, 0x4e800020)
		self.HOST_Poke4(addr + 0, 0x60000000)

	#obsolete
	def PATCH_MakeContentError(self, x):
		#addr = 0x80066b30 # 2.03
		#addr = 0x8005a72c # 1.07
		#addr = 0x80067f5c # 2.15
		addr = 0x8005a72c # 3.01
		self.HOST_Poke4(addr + 0, 0x4e800020)
		self.HOST_Poke4(addr + 4, 0x38a00000 | x)
		self.HOST_Poke4(addr + 8, 0x90a30000)
		self.HOST_Poke4(addr + 12, 0x38a00000)
		self.HOST_Poke4(addr + 16, 0x60000000)
		self.HOST_Poke4(addr + 20, 0x4e800020)
		self.HOST_Poke4(addr + 0, 0x60000000)

	# this essentially removes a region check, and is triforce-specific; It's also segaboot-version specific.
	# - look for string: "CLogo::CheckBootId: skipped."
	# - binary-search for lower 16bit of address
	def PATCH_CheckBootID(self):

		# 3.01
		addr = 0x8000dc5c
		self.HOST_Poke4(addr + 0, 0x4800001C)
		return

		addr = 0x8000CC6C # 2.03, 2.15
		#addr = 0x8000d8a0 # 1.07
		self.HOST_Poke4(addr + 0, 0x4e800020)
		self.HOST_Poke4(addr + 4, 0x38600000)
		self.HOST_Poke4(addr + 8, 0x4e800020)
		self.HOST_Poke4(addr + 0, 0x60000000)

# ok, now you're on your own, the tools are there.
# We see the DIMM space as it's seen by the dimm-board (i.e. as on the disc).
# It will be transparently decrypted when accessed from Host, unless a
# zero-key has been set. We do this before uploading something, so we don't
# have to bother with the inserted key chip. Still, some key chip must be
# present.
# You need to configure the triforce to boot in "satellite mode", 
# which can be done using the dipswitches on the board (type-3) or jumpers 
# (VxWorks-style). 
# The dipswitch for type-3 must be in the following position:
#	- SW1: ON ON *
#	- It shouldn't wait for a GDROM anymore, but display error 31. 
# For the VxWorks-Style:
#	- Locate JP1..JP3 on the upper board in the DIMM board. They are near 
#		the GDROM-connector. 
#		The jumpers must be in this position for satellite mode:
#		1		3
#		[. .].	JP1
#		[. .].	JP2
#		 .[. .] JP3
#	- when you switch on the triforce, it should say "waiting for network..."
#
# Good Luck. Warez are evil.

	def HOST_DumpToFile(self, file):
		for x in range(0, 0x10000, 1):
			file.write(self.HOST_Read16(0x80000000 + x * 0x10))
			sys.stderr.write("%08x\r" % x)

	# PRM - Dump memory to file in chunks of 4 bytes
	def HOST_DumpToFile4(self, file, addr, len):
		for x in range(addr, addr + len, 0x04):
	#		if not (x & 0xFFF):
			sys.stderr.write("%08x\r" % x)
			file.write(self.HOST_Read4(x))


	'''
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	High Level Routines
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	'''

	'''
	Queue up a binpatch for application during loading
	'''
	def addPatch(self, patchdata : str):
		tmpl = []
		tkeys = []

		#FIXME: THERE'S A WAY MORE EFFICIENT METHOD TO STRUCTURE THIS DATA. FUCK THIS IS DUMB
		for line in patchdata.split('\n'):

			# If it's a comment we don't care about this line
			if len(line) < 1 or line[0] == '#':
				continue
			# Split the line into target address, search bytes, and replace bytes
			print(line)
			e = re.compile("^([A-F0-9]+):\s+([A-F0-9]+)\s+->\s([A-F0-9]+)$").split(line)
			# Make a tuple of the data indexable by the target address, in a dict.
			# Then put it into our temporary list
			tmpl.append({e[1]: (e[2], e[3])})
			# Keep track of the target addresses (keys) we use so we can ensure they are sorted properly
			tkeys.append(e[1])

		tmpl.sort(key=lambda d: [k in d for k in tkeys], reverse=True)
		print(tmpl)
		print('------')
		self._patches.append(tmpl)
		print(self._patches)



	def compilePatchData(self) -> dict:

		#search through patches and find any conflicting addresses/overlaps.
		#for patch in self._patches:
		#combine into one large binpatch for more efficient application during rom transfer.
		biglist = [inner for outer in self._patches for inner in outer]

		#return resulting string.
		print(biglist)

		return biglist

	def bootGame(self) -> bool:
		self._do_boot = True
		self._do_keepalive = False

		ret = False

		# TODO: I don't think either of these functions will actually cause a disconnect, so we should be good to go
		# Although there probably isn't any harm in just creating a new connection.
		# Should investigate it through testing.
		if on_raspi and self.enableGPIOReset:
			self._logger.info("GPIO Reset")
			self.doGPIOReset()
			ret = True
		elif self.is_connected:
			self._logger.info("NetDIMM Reset")
			self.doDIMMReset()
			ret = True

		# This state has a built-in 2 second delay to reconnect.
		# Should be enough time for the system to get started enough for us to work with it.
		self._state = LoaderState.CONNECTING
		return ret

	def doDIMMReset(self):
		if self.is_connected:
			self.HOST_Restart()

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
			_func = self._states.get(self._state, lambda self: self.INVALID)
			_func(self)
		except:
			pass
		#If we're not waiting, let's make sure our times stay in sync
		if self._state != LoaderState.WAITING and self._state != LoaderState.KEEPALIVE:
			self._wait_tick = self._tick

		#each state should only run once as each one will update the state machine (except keepalive)

	'''
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	Loader States
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	'''

	def INVALID(self):
		pass

	def upload_pct_callback(self, percent_complete):
		#TODO: deliver this number to UI and/or main thread via messagebus
		self._logger.debug("upload cb: " + str(percent_complete) + "%")
		MBus.handle(Node_LoaderUploadPctMessage(payload=[self.node_id, str(percent_complete)]))

	def boot_failed(self):
		return

	def transfer_failed(self):
		return

	def connection_lost(self):
		self._state = LoaderState.WAITING
		return

	def connection_failed(self):
		self._state = LoaderState.WAITING
		return
	
	def patching_failed(self):
		return

	def exited(self):
		return

	def uploading(self):
		return

	def waiting(self):
		#Wait 2 seconds between connection attempts
		if int(self._tick - self._wait_tick) > 2:
			self._logger.debug(str(self._tick) + " " + str(self._wait_tick) + " " + str(self._tick - self._wait_tick))
			self._state = LoaderState.CONNECTING

	def connecting(self):
		# Open a connection to endpoint
		try:
			if not self.connect(self.host, self.port):
				self._state = LoaderState.CONNECTION_FAILED
				return

			if self._do_boot:
				self._state = LoaderState.TRANSFERRING
			elif self._do_keepalive:
				self._state = LoaderState.KEEPALIVE
			else:
				self._state = LoaderState.CONNECTED

		except Exception as ex:
			self._logger.error(repr(ex))
			self._state = LoaderState.CONNECTION_FAILED

	def connected(self):
		self._logger.info("Connected")
		return

	def transferring(self):
		try:
			#Display "Now Loading..." on screen
			self.HOST_SetMode(0, 1)

			# disable encryption by setting magic zero-key
			self.SECURITY_SetKeycode("\x00" * 8)

			self._logger.info("Uploading " + self.rom_path)
			# uploads file. Also sets "dimm information" (file length and crc32)
			self.DIMM_UploadFile(self.rom_path, None, self.upload_pct_callback)
		except Exception as ex:
			self._logger.error(repr(ex))
			#self._logger.debug("Connection timed out or something. reconnecting.")
			self._state = LoaderState.CONNECTING
			return

		if self._do_boot:
			self._state = LoaderState.BOOTING

	def booting(self):
		# restart the endpoint system, this will boot into the game we just sent
		self.HOST_Restart()
		self._state = LoaderState.KEEPALIVE
		self._do_boot = False # Finished booting. we don't want to reboot into the game automatically if we lose connection

	def keepalive(self):
		if int(self._tick - self._wait_tick) > 10:
			try:
				# set time limit to 10h. According to some reports, this does not work.
				self.TIME_SetLimit(10*60*1000)
				self._logger.info("Sent keepalive!")
				self._wait_tick = self._tick
			except Exception as ex:
				self._do_keepalive = True # return to keepalive if we lose connection
				#We lost our connection. Return to waiting state and attempt again once the DIMM is reachable.
				self._states = LoaderState.CONNECTION_LOST

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
		LoaderState.UPLOADING : uploading,
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
			
	def __getitem__(self, key) -> Loader:
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

	def len(self) -> int:
		return len(self._loaders)
