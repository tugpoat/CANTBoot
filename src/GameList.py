from GameDescriptor import GameDescriptor
import configparser
import os
import yaml

class GameList():
	_cfg_dir = ""
	_games_dir = ""
	_games = []

	def __init__(self):
		return

	def __init__(self, cfgdir, gamesdir):
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

		return self._games[key]

	def append(self, game):
		self._games.append(game)

	def len(self):
		return len(self._games)

	def loadExisting(self):
		listfile = self._cfg_dir+"/gamelist.yml"

		if os.path.isfile(listfile):
			try:
				with open(listfile) as ifs:
					self._games = yaml.load(ifs)
			except Exception as ex:
				print("couldn't load games for some reason" + repr(ex))

	def exportList(self):
		if os.path.isfile(self._cfg_dir+'/gamelist.yml'): os.remove(self._cfg_dir+'/gamelist.yml')

		try:
			# We have to do it this way because there's a loader object in there that spawns its own process.
			# Can't cross our pickles, that'd be weird.
			with open(self._cfg_dir+'/gamelist.yml', 'a+') as ofs:
				yaml.dump(self._games, ofs)
		except Exception as ex:
			print(repr(ex))

	def verifyFiles(self):
		#TODO: Run thru list and hash check everything.
		print("sup")

	def scanForNewGames(self, database):
		#TODO
		old_len = len(self._games)
		#2. scan directory for files that aren't in the existing list
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
					print("not valid or compatible rom file: ", file)
					continue

				identity = database.getGameInformation(tgame.rom_title)

				if identity:

					# We know what it is. Let's fill in everything from the DB.
					tgame.game_id = identity[0]
					tgame.title = identity[1]

					tgame.setSystem(database.getGameSystem(identity[0]))
					tgame.attributes = database.getGameAttributes(identity[0])
					tgame.setAttributes(database.getGameAttributes(identity[0]))
					self.append(tgame)
					print("\tAdded " + tgame.title)
				else:
					# We were unable to retrieve information about this game from the database. 
					# Just fill in whatever we can and pass it along.
					print("\tUnable to identify " + file)
					tgame.game_id = 0
					tgame.checksum_status = True
					tgame.title = filename
					tgame.attributes = []
					tgame.setSystem(database.getSystemFromName(tgame.system_name.upper()))
					self.append(tgame)

		if old_len != self.len():
			tmplist = self._games
			# Sort our list of GameDescriptor objects if it's changed at all
			tmplist.sort(key = lambda tmplist: tmplist.title.lower())
			self._games = tmplist
			self.exportList()
