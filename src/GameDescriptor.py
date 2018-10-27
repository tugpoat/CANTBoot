import io
import os
import hashlib
import json

class GameDescriptor:
	# Things from ROM file
	filename = None
	filepath = None
	file_size = None
	file_checksum = None
	checksum_status = None
	system_name = None
	rom_title = None

	# Things from DB
	game_id = None
	title = None
	attributes = []

	def __init__(self, filepath, skip_checksum = False):
		# Gather all the information we can from the filesystem
		self.filepath = filepath
		self.filename = os.path.basename(filepath)

		try:
			# Open the file up and get all the info we need from the header data
			self.file_size = os.stat(filepath).st_size
			self.system_name = self.__file_get_target_system()
			self.rom_title = self.__file_get_title()

			# Checksum the file if we want to do that
			if not skip_checksum:
				self.file_checksum = self.__checksum()

		except Exception:
			#TODO Actually do something
			return

	def __file_get_title(self):
		'Get game title from rom file.'
		try:
			fp = open(self.filepath, 'rb')
			# We only care about the japanese title
			fp.seek(0x30)
			title = fp.read(32).decode('utf-8').strip(' ')

			'''
			Dangit Darksoft lmao
			Also, I didn't quite do my research, and ended up lifting this bit from some dude who forked off.
			Hi ldindon! Keep at it :)
			'''
			if title == "AWNAOMI":
				fp.seek(0xFF30)
				title = fp.read(32).decode('utf-8').strip(' ')

			fp.close()
			return title
		except Exception:
			print('poop')
			# TODO: thing

	def __file_get_target_system(self):
		'Get the system that this game is meant to run on from the header'
		try:
			fp = open(self.filepath, 'rb')
			header_magic = fp.read(8).decode('utf-8')
			fp.close()
			if header_magic[:5] == 'NAOMI':
				return 'NAOMI'
			elif header_magic[:6] == 'Naomi2':
				return 'NAOMI2'
			elif header_magic[:4] == 'FATX':
				return 'CHIHIRO'
			# TODO: Triforce has some weird, maybe game-specific junk at offset 0x0. Can probably do title detection with that.
			#elif header_magic == 'TRIFORCE':
			#	return 'TRIFORCE'
			else:
				return False

		except Exception:
			# TODO: the thing
			return False

	def __checksum(self):
		try:
			m = hashlib.md5()
			with open(self.filepath, 'rb') as fh:
				while True:
					data = fh.read(2048000) #read in 2MB chunks so we don't make things slower with a crapload of I/O operations
					if not data:
						break
					m.update(data)
					
			return m.hexdigest()
		except:
			# TODO: Better error checking
			return False

	def __hash__(self):
		return hash((self.name, self.filepath, self.size)) & 0xffffffff

	def isValid(self):
		return (self.system_name in ['NAOMI', 'NAOMI2', 'CHIHIRO', 'TRIFORCE'])

	def serialize(self):
		return json.dumps({"file_name": self.filename, "file_path": self.filepath, "file_checksum": self.file_checksum, "rom_title": self.rom_title, "game_id": self.game_id, "title": self.title, "attributes": json.dumps(self.attributes)})