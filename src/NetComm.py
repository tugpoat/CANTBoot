# Triforce Netfirm Toolbox, put into the public domain.
# Please attribute properly, but only if you want.

# Modified by Wesley Castro for NaomiWeb.
# Also messed with by Pat Murphy.

import struct, sys
import socket
import time
from Crypto.Cipher import DES

# connect to the Triforce. Port is tcp/10703.
# note that this port is only open on
#	- all Type-3 triforces,
#	- pre-type3 triforces jumpered to satellite mode.
# - it *should* work on naomi and chihiro, but due to lack of hardware, i didn't try.
class NetComm:
	s = None

	#print("connecting...")
	#s.settimeout(5)
	#s.connect((triforce_ip, 10703))
	#print("ok!")

	def connect(self, ip, port):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.settimeout(20)
		self.s.connect((ip, port))

	def disconnect(self):
		self.s.close()
		self.s = None

	# a function to receive a number of bytes with hard blocking
	def readsocket(self, n):
		res = "".encode()
		while len(res) < n:
			res += self.s.recv(n - len(res))
		return res

	# Peeks 16 bytes from Host (gamecube) memory
	def HOST_Read16(self, addr):
		self.s.send(struct.pack("<II", 0xf0000004, addr))
		data = readsocket(0x20)
		res = ""
		for d in range(0x10):
			res += data[4 + (d ^ 3)]
		return res

	# same, but 4 bytes.
	def HOST_Read4(self, addr, type = 0):
		self.s.send(struct.pack("<III", 0x10000008, addr, type))
		return self.s.recv(0xc)[8:]

	def HOST_Poke4(self, addr, data):
		self.s.send(struct.pack("<IIII", 0x1100000C, addr, 0, data))

	def HOST_Restart(self):
		self.s.send(struct.pack("<I", 0x0A000000))

	# Read a number of bytes (up to 32k) from DIMM memory (i.e. where the game is). Probably doesn't work for NAND-based games.
	def DIMM_Read(self, addr, size):
		self.s.send(struct.pack("<III", 0x05000008, addr, size))
		return readsocket(size + 0xE)[0xE:]

	def DIMM_GetInformation(self):
		self.s.send(struct.pack("<I", 0x18000000))
		return readsocket(0x10)

	def DIMM_SetInformation(self, crc, length):
		print(("length: {0:b}".format(length)))
		self.s.send(struct.pack("<IIII", 0x1900000C, crc & 0xFFFFFFFF, length, 0))

	def DIMM_Upload(self, addr, data, mark):
		self.s.send(struct.pack("<IIIH", 0x04800000 | (len(data) + 0xA) | (mark << 16), 0, addr, 0) + data)

	def NETFIRM_GetInformation(self):
		self.s.send(struct.pack("<I", 0x1e000000))
		return s.recv(0x404)

	def CONTROL_Read(self, addr):
		self.s.send(struct.pack("<II", 0xf2000004, addr))
		return s.recv(0xC)

	def SECURITY_SetKeycode(self, data):
		assert len(data) == 8
		self.s.send(struct.pack("<I", 0x7F000008) + data.encode())

	def HOST_SetMode(self, v_and, v_or):
		self.s.send(struct.pack("<II", 0x07000004, (v_and << 8) | v_or))
		return readsocket(0x8)

	def DIMM_SetMode(self, v_and, v_or):
		self.s.send(struct.pack("<II", 0x08000004, (v_and << 8) | v_or))
		return readsocket(0x8)

	def DIMM22(self, data):
		assert len(data) >= 8
		self.s.send(struct.pack("<I", 0x22000000 | len(data)) + data)

	def MEDIA_SetInformation(self, data):
		assert len(data) >= 8
		self.s.send(struct.pack("<I",	0x25000000 | len(data)) + data)

	def MEDIA_Format(self, data):
		self.s.send(struct.pack("<II", 0x21000004, data))

	def TIME_SetLimit(self, data):
		self.s.send(struct.pack("<II", 0x17000004, data))

	def DIMM_DumpToFile(self, file):
		for x in range(0, 0x20000, 1):
			file.write(DIMM_Read(x * 0x8000, 0x8000))
			sys.stderr.write("%08x\r" % x)

	def HOST_DumpToFile(self, file, addr, len):
		for x in range(addr, addr + len, 0x10):
#			if not (x & 0xFFF):
			sys.stderr.write("%08x\r" % x)
			file.write(HOST_Read16(x))

	# upload a file into DIMM memory, and optionally encrypt for the given key.
	# note that the re-encryption is obsoleted by just setting a zero-key, which
	# is a magic to disable the decryption.
	def DIMM_UploadFile(self, name, key = None):
		import zlib
		crc = 0
		a = open(name, "rb")
		addr = 0
		if key:
			d = DES.new(key[::-1], DES.MODE_ECB)
		while True:
			sys.stderr.write("%08x\r" % addr)
			data = a.read(0x8000)
			if not len(data):
				break
			if key:
				data = d.encrypt(data[::-1])[::-1]
			DIMM_Upload(addr, data, 0)
			crc = zlib.crc32(data, crc)
			addr += len(data)
		a.close()
		crc = ~crc
		DIMM_Upload(addr, "12345678".encode(), 1)
		DIMM_SetInformation(crc, addr)

	# obsolete
	def PATCH_MakeProgressCode(self, x):
		#addr = 0x80066ed8 # 2.03
		#addr = 0x8005a9c0 # 1.07
		#addr = 0x80068304 # 2.15
		addr = 0x80068e0c # 3.01
		HOST_Poke4(addr + 0, 0x4e800020)
		HOST_Poke4(addr + 4, 0x38a00000 | x)
		HOST_Poke4(addr + 8, 0x90a30000)
		HOST_Poke4(addr + 12, 0x38a00000)
		HOST_Poke4(addr + 16, 0x60000000)
		HOST_Poke4(addr + 20, 0x4e800020)
		HOST_Poke4(addr + 0, 0x60000000)

	#obsolete
	def PATCH_MakeContentError(self, x):
		#addr = 0x80066b30 # 2.03
		#addr = 0x8005a72c # 1.07
		#addr = 0x80067f5c # 2.15
		addr = 0x8005a72c # 3.01
		HOST_Poke4(addr + 0, 0x4e800020)
		HOST_Poke4(addr + 4, 0x38a00000 | x)
		HOST_Poke4(addr + 8, 0x90a30000)
		HOST_Poke4(addr + 12, 0x38a00000)
		HOST_Poke4(addr + 16, 0x60000000)
		HOST_Poke4(addr + 20, 0x4e800020)
		HOST_Poke4(addr + 0, 0x60000000)

	# this essentially removes a region check, and is triforce-specific; It's also segaboot-version specific.
	# - look for string: "CLogo::CheckBootId: skipped."
	# - binary-search for lower 16bit of address
	def PATCH_CheckBootID(self):

		# 3.01
		addr = 0x8000dc5c
		HOST_Poke4(addr + 0, 0x4800001C)
		return

		addr = 0x8000CC6C # 2.03, 2.15
		#addr = 0x8000d8a0 # 1.07
		HOST_Poke4(addr + 0, 0x4e800020)
		HOST_Poke4(addr + 4, 0x38600000)
		HOST_Poke4(addr + 8, 0x4e800020)
		HOST_Poke4(addr + 0, 0x60000000)

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
			file.write(HOST_Read16(0x80000000 + x * 0x10))
			sys.stderr.write("%08x\r" % x)

	# PRM - Dump memory to file in chunks of 4 bytes
	def HOST_DumpToFile4(self, file, addr, len):
		for x in range(addr, addr + len, 0x04):
	#		if not (x & 0xFFF):
			sys.stderr.write("%08x\r" % x)
			file.write(HOST_Read4(x))

#if 1:
#	# display "now loading..."
#	HOST_SetMode(0, 1)
#	# disable encryption by setting magic zero-key
#	SECURITY_SetKeycode("\x00" * 8)
#	
#	# uploads file. Also sets "dimm information" (file length and crc32)
#	#DIMM_UploadFile(sys.argv[2])
#	DIMM_UploadFile(sys.argv[1])
#	# restart host, this wil boot into game
#	#print "restarting in 10 seconds..."
#	#time.sleep(10)
#	HOST_Restart()
#	print("time limit hack looping...")
#	while 1:
#	# set time limit to 10h. According to some reports, this does not work.
#		TIME_SetLimit(10*60*1000)
#		time.sleep(5)

#if 0:
	# this is triforce-specific, and will remove the "region check"
#	PATCH_CheckBootID()

# this is not required anymore:
#	PATCH_MakeContentError(2)
#	PATCH_MakeProgressCode(5)
