from gameboot import *
#NAOMI SRAM 0xA0200000 - 0xA0207FFF

# Same thing as above, but in chunks of 4 bytes
def HOST_DumpToFile4(file, addr, len):
	for x in range(addr, addr + len, 0x04):
#		if not (x & 0xFFF):
		sys.stderr.write("%08x\r" % x)
		file.write(HOST_Read4(x))

#Literally no idea if this works
def BackupNAOMI_SRAM(file):
	HOST_DumpToFile4(file, 0xA0200000, 0x7FFF)