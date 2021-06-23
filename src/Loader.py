import os
import struct
import socket
import re
import time
import json
import configparser
import logging
import typing as t
import zlib

on_raspi=False
if "arm" in os.uname().machine:
	on_raspi=True
	import RPi.GPIO as GPIO
	GPIO.setwarnings(False)

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

# Common loader class. Shouldn't ever be used as-is, exists only to be inherited from
class Loader:
	host = None
	port = None

	_state = LoaderState.EXITED
	_last_state = LoaderState.EXITED

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
		# Only update last state if it's different from what we're trying to set
		# It should always be different, but might as well sanity-check
		if self.last_state != value:
			try:
				self.last_state = self._state
				self._logger.debug("set " + self.node_id + " last state to " + str(self._state))
			except:
				pass

		if self._state != value:
			self._state = value
			self._logger.debug("set " + self.node_id + " state to " + str(value))

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
		self.host: str = host
		self.port: int = port
		self.last_state = LoaderState.WAITING # doesn't matter what this is on init as long as it's different from self._state
		self.state = LoaderState.EXITED # This should be EXITED so it doesn't automatically try and load games unless we tell it to

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
Loader for endpoint nodes
'''
class DIMMLoader(Loader):

	_s = None
	_is_connected = False

	path = None

	_tick = 0
	_wait_tick = 0

	_do_transfer = False
	_do_boot = False
	_do_keepalive = False
	_enableFastboot = True

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
		self.enableGPIOReset = False
		self.last_state = LoaderState.WAITING # doesn't matter what this is on init as long as it's different from self._state
		self.state = LoaderState.EXITED # This should be EXITED so it doesn't automatically try and load games unless we tell it to

	@property
	def enableGPIOReset(self) -> bool:
		return self._enableGPIOReset

	@enableGPIOReset.setter
	def enableGPIOReset(self, value : bool):
		self._enableGPIOReset = value

	@property
	def enableFastboot(self) ->bool:
		return self._enableFastboot

	@enableFastboot.setter
	def enableFastboot(self, value : bool):
		self._enableFastboot = value


	'''
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	Network Routines
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	'''

	def connect(self, ip : str, port : int) -> bool:

		if self.is_connected and self._s != None:
			self._logger.debug("Called connect() with existant socket. Disconnecting and Reconnecting.")
			self.disconnect()

		self._logger.info("Connecting to " + ip + ":" + str(port))
		try:
			self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self._s.settimeout(4)
			self._s.connect((ip, port))
			self._s.settimeout(None)
			self._is_connected = True
			self._logger.info("Connected.")
		except Exception as ex:
			self._logger.error("Connection failed! " + repr(ex))
			self._is_connected = False
			return False

		return True

	def reconnect(self) -> bool:
		return self.connect(self.host, int(self.port))

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

	'''
	Must be called immediately after SECURITY_Setkeycode (probably)

	courtesy of :
	@mathieulh
	@bobbydilley
	@chunksin
	@whatnot
	https://www.arcade-projects.com/forums/index.php?thread/14549-no-more-pesky-memory-checkings-on-netdimm/&pageNo=1
	'''
	def DIMM_CheckDisable(self):
		self._s.send(struct.pack(">IIIIIIIIH", 0x00000001, 0x1a008104, 0x01000000, 0xf0fffe3f, 0x0000ffff, 0xffffffff, 0xffff0000, 0x00000000, 0x0000))

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
	def DIMM_UploadFile(self, name, key = None, progress_cb = None, chunk_len=0x8000):
		self._logger.debug("DIMM_UploadFile")
		patchdata = self.compilePatchData()

		data = 'hi' #init with length > 0 so we enter the loop

		crc = 0
		f_sz = os.stat(name).st_size
		a = open(name, "rb")
		addr = 0
		if key:
			d = DES.new(key[::-1], DES.MODE_ECB)

		prg_counter = 0

		# Set up our patching flags, bookmarks, and iterators
		patch_continue = 0
		if len(patchdata) < 1:
			# This will make the following loop never check for patch data or attempt to apply any.
			# Because we don't have any patches to apply.
			patched = False
			next_patch = False
		else:
			patched = True #we want to load the first patch on the first iteration
			patch_iter = iter(patchdata)

		while len(data) > 0:

			# patch continue is set to the index of whatever patch data we need to continue on with the next chunk.
			# if zero, we don't need to continue. load the next patch if we have already patched the one we were looking for.
			if patched and patch_continue == 0:
				#TODO: comment this out for release. no sense in slowing this down with debug output.
				self._logger.debug("loading next patch.")
				next_patch = next(patch_iter)
				patched = False

			#sys.stderr.write("%08x\r" % addr)
			data = a.read(0x8000)

			# Only process patch data if:
			# 1. If we have patch data and the start address of the patch is within the chunk we are going to send
			# 2. We have patch data and are continuing a patch from a previous chunk.
			# Algorithm inside this if block is generic to both circumstances.
			if next_patch and ((next_patch[0] >= addr and next_patch [0] <= addr + chunk_len) or patch_continue > 0):
				chunk_end_addr = addr + chunk_len

				# do some operations up front to save on processing.
				patch_start_addr = next_patch[0]
				patch_end_addr = next_patch[0] + len(next_patch[1]) * 0xff
				patch_data_length = patch_end_addr - patch_start_addr

				# patch information solely as far as the current chunk is concerned follows.

				# if we are not continuing with a patch, patch_continue will be 0, and therefore ignored. Neat!
				# We're wasting a number of operations the circumstances that A: there is nothing to apply in this chunk and B: patch_continue is 0....
				# However I am prioritizing readability and maintainability in this project as much as possible.

				# address to start patching at within this chunk
				chunk_patch_start_addr = next_patch[0] + (0xff * patch_continue)
				# address to end patching at within this chunk
				chunk_patch_end_addr = (next_patch[0] + (0xff * patch_continue)) + (len(next_patch[1]) * 0xff)
				# length of the data to patch within this chunk
				chunk_patch_data_length = chunk_patch_end_addr - chunk_patch_start_addr
				# number of bytes to patch within this chunkW
				chunk_patch_data_nbytes = chunk_patch_data_length / 0xff

				#TODO: comment these out for release. no sense in slowing this down with debug output.
				self._logger.debug("patch start %08x end %08x len %08x" % (patch_start_addr, patch_end_addr, patch_data_length))
				self._logger.debug("chunk patch start %08x end %08x len %08x" % (chunk_patch_start_addr, chunk_patch_end_addr, chunk_patch_data_length))

				# are we patching anything in this chunk?
				# we need to account for how far through this patch we are.
				if chunk_patch_start_addr >= addr and chunk_patch_end_addr <= chunk_end_addr:
					#we need to patch data in this chunk.

					#TODO: loop each byte to patch from chunk_patch_start_addr and replace the indexed byte in data

					# we need to check if the patch extends beyond this chunk, and if so: how far?
					# lvalue = end address of patch
					# rvalue = end address of this chunk
					if patch_end_addr > chunk_end_addr:

						# patch continues beyond the end of this chunk. Find out how far, and turn it into an byte-array indexable value.
						patch_continue = (patch_end_addr - chunk_end_addr) / 0xff

						#TODO: comment this out for release. no sense in slowing this down with debug output.
						self._logger.debug("patch data continues %08x (%d bytes) beyond this chunk" % ((patch_end_addr - chunk_end_addr), patch_continue))
					else:
						#TODO: comment these out for release. no sense in slowing this down with debug output.
						self._logger.debug("patch from %08x done." % patch_start_addr)
						patched = True
						patch_continue = 0

			if key:
				data = d.encrypt(data[::-1])[::-1]


			self.DIMM_Upload(addr, data, 0)
			crc = zlib.crc32(data, crc)
			addr += chunk_len

			# It is faster to use a counter than to do a modulus operation every time we xfer a chunk.
			# Definitely not the biggest bottleneck in this function by any means but I'd like to save where I can
			prg_counter += 1
			if prg_counter > 10:
				if callable(progress_cb):
					progress_cb(round((addr / f_sz) * 100, 2))
				prg_counter = 0

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

		#TODO: search through patches and find any conflicting addresses/overlaps.
		#for patch in self._patches:
        
		#combine into one large binpatch for more efficient application during rom transfer.
		biglist = [inner for outer in self._patches for inner in outer]

		#return resulting string.
		print(biglist)

		return biglist

	# Firstly, line up our special flags so the state machine does what we want.
	# Then, reboot the system so that it will accept a new upload using the configured method
	# Lastly, give the state machine the green light to proceed
	def bootGame(self) -> bool:
		self._do_transfer = True
		self._do_boot = True
		self._do_keepalive = False

		ret = False

		self.connect(self.host, int(self.port))

		# TODO: I don't think either of these functions will actually cause a disconnect, so we should be good to go
		# Although there probably isn't any harm in just creating a new connection.
		# Should investigate it through testing.
		self._logger.info("NetDIMM Reset")
		self.doDIMMReset()
		if on_raspi and self.enableGPIOReset:
			self._logger.info("GPIO Reset")
			self.doGPIOReset()

		self.disconnect()

		# This state has a built-in 2 second delay to reconnect.
		# Should be enough time for the system to get started enough for us to work with it.
		self.state = LoaderState.CONNECTING
		return True

	def doDIMMReset(self):
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
		#self._logger.debug("tick")
		self._tick = time.time()
		try:
			_func = self._states.get(self.state, lambda self: self.INVALID)
			_func(self)
		except:
			self._logger.debug("call failed: " + _func)

		#If we're not waiting, let's make sure our times stay in sync
		if self.state != LoaderState.WAITING and self.state != LoaderState.KEEPALIVE:
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
		# deliver this to UI and/or main thread(s) via messagebus
		#self._logger.debug("upload cb: " + str(percent_complete) + "%")
		MBus.handle(Node_LoaderUploadPctMessage(payload=[self.node_id, str(percent_complete)]))

	def boot_failed(self):
		return

	def transfer_failed(self):
		return

	def connection_lost(self):
		self.state = LoaderState.WAITING
		return

	def connection_failed(self):
		self.state = LoaderState.WAITING
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
			self.state = LoaderState.CONNECTING

	def connecting(self):
		# Open a connection to endpoint
		try:
			if not self.connect(self.host, int(self.port)):
				self.state = LoaderState.CONNECTION_FAILED
				return

			#branch our state machine according to flags
			if self._do_transfer:
				self.state = LoaderState.TRANSFERRING
			elif self._do_boot:
				self.state = LoaderState.BOOTING
			elif self._do_keepalive:
				self.state = LoaderState.KEEPALIVE
			else:
				self.state = LoaderState.CONNECTED

		except Exception as ex:
			self._logger.error(repr(ex))
			self.state = LoaderState.CONNECTION_FAILED

	def connected(self):
		return

	def transferring(self):
		try:
			#Display "Now Loading..." on screen
			self.HOST_SetMode(0, 1)

			# disable encryption by setting magic zero-key
			self.SECURITY_SetKeycode("\x00" * 8)

			if self.enableFastboot:
				self.DIMM_CheckDisable()

			self._logger.info("Uploading " + self.rom_path)
			# uploads file. Also sets "dimm information" (file length and crc32)
			self.DIMM_UploadFile(self.rom_path, None, self.upload_pct_callback)
			self._logger.info("Upload completed.")
			self._do_transfer = False # Boot game next time
		except Exception as ex:
			self._logger.error(repr(ex))
			#self._logger.debug("Connection timed out or something. reconnecting.")

		#Force a reconnect on exception or if we've finished uploading
		self.state = LoaderState.CONNECTION_LOST

	def booting(self):
		try:
			self._logger.info("Rebooting into game")

			# restart the endpoint system, this will boot into the game we just sent
			self._logger.info("NetDIMM Reset")
			self.doDIMMReset()

			if on_raspi and self.enableGPIOReset:
				self._logger.info("GPIO Reset")
				self.doGPIOReset()
				

			self.state = LoaderState.KEEPALIVE
			self._do_boot = False # Finished booting. we don't want to reboot into the game automatically if we lose connection
			self._do_keepalive = True # Do keepalive next time
		except Exception as ex:
				self._logger.error(repr(ex))
				#We lost our connection. Return to waiting state and attempt again once the DIMM is reachable.
				self.state = LoaderState.CONNECTION_LOST


	def keepalive(self):
		if int(self._tick - self._wait_tick) > 100:
			try:
				self._logger.debug("trying keepalive")
				# set time limit to 10h. According to some reports, this does not work.
				self.TIME_SetLimit(10*60*1000)
				self._logger.info("Sent keepalive!")
				self._wait_tick = self._tick
			except Exception as ex:
				self._logger.error(repr(ex))
				#We lost our connection. Return to waiting state and attempt again once the DIMM is reachable.
				self.state = LoaderState.CONNECTION_LOST

		return

	#Additional translation for functions
	_states = {
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
