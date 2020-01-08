import io
import os
import hashlib
import json
import yaml

class GameDescriptor(yaml.YAMLObject):
	yaml_loader = yaml.SafeLoader
	yaml_tag = u'tag:yaml.org,2002:python/object:GameDescriptor.GameDescriptor'

	# Things from ROM file
	filename = None
	filepath = None
	file_size = None
	file_checksum = None
	checksum_status = None
	system_name = None
	rom_title = None

	# For Atomiswave conversions
	_naomi2_cv = False

	# Things from DB
	game_id = None
	title = None
	attributes = [] # TODO: is this even needed?

	_system = None
	_control = None
	_max_players = None
	_monitor = None
	_dimm_ram = None

	def __init__(self, filepath: str, skip_checksum: bool = False):

		# Python doesn't support constructor overloading, let's do some weird hacky stuff.
		if type(filepath) is GameDescriptor:
			self.filename = filepath.filename
			self.filepath = filepath.filepath
			self.file_checksum = filepath.file_checksum
			self.checksum_status = filepath.checksum_status
			self.system_name = filepath.system_name
			self.rom_title = filepath.rom_title
			self._naomi2_cv = filepath._naomi2_cv
			self.game_id = filepath.game_id
			self.title = filepath.title
			self.attributes = filepath.attributes.copy() #important to copy because reference shenanigans
			self._system = filepath._system
			self._control = filepath._control
			self._max_players = filepath._max_players
			self._dimm_ram = filepath._dimm_ram
			return

		# Gather all the information we can from the filesystem
		self.filepath = filepath
		self.filename = os.path.basename(filepath)
		try:
			# Open the file up and get all the info we need from the header data
			self.file_size = os.stat(filepath).st_size
			self.system_name = self.__file_get_target_system
			self.rom_title = self.__file_get_title

			# Checksum the file if we want to do that
			if not skip_checksum:
				self.file_checksum = self.__checksum

		except Exception as ex:
			print('failed to construct GameDescriptor'+repr(ex))
			#TODO Actually do something
			return

	def setSystem(self, system: tuple):
		if type(system) is tuple:
			self._system = (system[0], system[1])

	@property
	def getSystem(self) -> tuple:
		return self._system

	@property
	def getControls(self) -> tuple:
		return self._control

	def getMaxPlayers(self):
		return self._max_players

	@property
	def getMonitor(self) -> tuple:
		return self._monitor

	@property
	def getDIMMRAMReq(self) -> tuple:
		return self._dimm_ram

	@property
	def getDIMMRAMReqMB(self) -> int:
		return int(self._dimm_ram[1].strip('MB'))

	@property
	def isNaomi2CV(self) -> bool:
		return self._naomi2_cv
	
	def setAttributes(self, attributes: list):
		# Example of valid attributes param:
		# [(7, 'Control', 'Normal'), (11, 'Players', '2'), (14, 'Monitor', 'Horizontal'), (18, 'DIMM Reset', 'Testing'), (20, 'DIMM RAM', '256MB')]
		self.attributes = attributes
		# I am sure there is a more elegant way to do this. Meh.
		for a in attributes:
			if a[1] == 'Control':
				self._control =(a[0], a[2])
			if a[1] == 'Players':
				self._max_players = (a[0], a[2])
			if a[1] == 'Monitor':
				self._monitor = (a[0], a[2])
			if a[1] == 'DIMM RAM':
				self._dimm_ram = (a[0], a[2])
	

	@property
	def __file_get_title(self) -> str:
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
				_naomi2_cv = True #Flag it as a conversion
				#Let's seek past the loader stub and snag the real title.
				fp.seek(0xFF30)
				title = fp.read(32).decode('utf-8').strip(' ')

			fp.close()
			return title
		except Exception as ex:
			print('gettitle failed'+repl(ex))
			# TODO: thing

	@property
	def __file_get_target_system(self) -> str:
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

		except Exception as ex:
			# TODO: the thing
			return False

	@property
	def __checksum(self) -> str:
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

	# Used for identifying this particular game to various parts of the program. way faster than checksumming the whole damn file.
	@property
	def __hash__(self) -> str:
		return hash((self.name, self.filepath, self.size)) & 0xffffffff

	@property
	def isValid(self) -> bool:
		return (self.system_name in ['NAOMI', 'NAOMI2', 'CHIHIRO', 'TRIFORCE'])

	@property
	def serialize(self) -> str:
		return json.dumps({"file_name": self.filename, "file_path": self.filepath, "file_checksum": self.file_checksum, "rom_title": self.rom_title, "game_id": self.game_id, "title": self.title, "attributes": json.dumps(self.attributes)})
