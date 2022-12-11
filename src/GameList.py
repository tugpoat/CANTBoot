from GameDescriptor import *
import configparser
import os
import typing as t
import yaml
from yloader import *
from mbus import *

class GameList_ScanEventMessage(t.NamedTuple):
	payload: str

class GameList():
	_cfg_dir = ""
	_games_dir = ""
	_games = []

	def __init__(self, cfgdir: str = None, gamesdir: str = None):
		if type(cfgdir) is None:
			pass

		self.__logger = logging.getLogger("GameList")
		self.__logger.debug("init logger")
		self._cfg_dir = cfgdir
		self._games_dir = gamesdir

		self.loadExisting()

	def __len__(self):
		return len(self._games)

	def __iter__(self):
		for elem in self._games:
			yield elem
			
	def __getitem__(self, key):
		if type(key) is str:
			#checksum/hash
			for elem in self._games:
				if elem.file_checksum == key: return elem

			#FIXME: what happens if hash not found?
		if type(key) is int:
			return self._games[key]

		print("help! computer")
		return

	def append(self, game):
		self._games.append(game)

	def len(self) -> int:
		return len(self._games)

	def loadExisting(self):
		listfile = self._cfg_dir+"/gamelist.yml"

		if os.path.isfile(listfile):
			try:
				with open(listfile) as ifs:
					self._games = yaml.load(ifs, Loader=YLoader)
			except Exception as ex:
				self.__logger.error("couldn't load games for some reason" + repr(ex))

	def exportList(self):
		if os.path.isfile(self._cfg_dir+'/gamelist.yml'): os.remove(self._cfg_dir+'/gamelist.yml')

		try:
			# We have to do it this way because there's a loader object in there that spawns its own process.
			# Can't cross our pickles, that'd be weird.
			with open(self._cfg_dir+'/gamelist.yml', 'a+') as ofs:
				yaml.dump(self._games, ofs)
		except Exception as ex:
			self.__logger.error(repr(ex))

	def verifyFiles(self):
		#TODO: Run thru list and ensure that the files in our list exist.
		for elem in self._games:
			if not os.path.isfile(self._games_dir+"/"+elem.filename):
				self.__logger.debug('File '+elem.filename+' does not exist, removing from game list')
				self._games.remove(elem)

	def scanForNewGames(self, database):
		old_len = len(self._games)
		#scan directory for files that aren't in the existing list
		if os.path.isdir(self._games_dir):
			for file in os.listdir(self._games_dir):
				game_exists = False
				for igame in self._games:
					if igame.filename == file:
						#just assume it's the same thing for now (a reasonable assumption), don't spend forever hashing everything ffs
						game_exists = True
						break

				if game_exists: continue
				tgame = GameDescriptor(self._games_dir+"/"+file)

				if not tgame.isValid:
					self.__logger.error("not valid or compatible rom file: ", file)
					continue

				MBus.handle(GameList_ScanEventMessage(payload=file))

				#identity = database.getGameInformation(tgame.rom_title)
				identity = database.getGameInformationByChecksum(tgame.checksum)

				if identity:

					# We know what it is. Let's fill in everything from the DB.
					tgame.game_id = identity[0]
					tgame.title = identity[1]
					tgame.description = identity[2]

					tgame.setSystem(database.getGameSystem(identity[0]))
					tgame.setAttributes(database.getGameAttributes(identity[0]))
					self.__logger.info("\tAdded via checksum: " + tgame.title)
				else:
					#TODO: Fallback to less accurate method of checking the header and comparing it to what we know.
					identity = database.getGameInformation(tgame.rom_title)
					
					if identity:
						tgame.game_id = identity[0]
						tgame.title = identity[1]
						tgame.setSystem(database.getGameSystem(identity[0]))
						tgame.setAttributes(database.getGameAttributes(identity[0]))
						self.__logger.info("\tAdded via header ident: " + tgame.title)
					else:
						# We were unable to retrieve information about this game from the database. 
						# Just fill in whatever we can and pass it along.
						self.__logger.info("\tUnable to identify " + file)
						tgame.game_id = 0
						tgame.checksum_status = True
						tgame.title = file
						tgame.attributes = []
						tgame.setSystem(database.getSystemFromName(tgame.system_name.upper()))
				
				self.append(tgame)

		if old_len != self.len():
			tmplist = self._games
			# Sort our list of GameDescriptor objects if it's changed at all
			tmplist.sort(key = lambda tmplist: tmplist.title.lower())
			self._games = tmplist
			self.exportList()

		MBus.handle(GameList_ScanEventMessage(payload="donelol"))
